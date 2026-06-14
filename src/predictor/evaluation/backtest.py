import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss, mean_absolute_error, mean_poisson_deviance

from predictor.training.train import (
    METRIC_OUTCOME_LABELS,
    OUTCOME_LABELS,
    TrainModelConfig,
    _actual_outcome,
    _build_regression_pipeline,
    _clip_lambdas,
    _multiclass_brier_score,
    _outcome_probabilities,
    _select_feature_columns,
)


@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_train_days: int = 730
    validation_window_days: int = 180
    step_days: int = 180
    alpha: float = 1.0
    max_iter: int = 500
    max_probability_goals: int = 10


@dataclass(frozen=True, slots=True)
class BacktestResult:
    fold_metrics: pd.DataFrame
    predictions: pd.DataFrame
    report: dict[str, Any]


def _validate_backtest_window(
    dates: pd.Series,
    *,
    config: BacktestConfig,
) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    min_date = dates.min()
    max_date = dates.max()
    first_cutoff = min_date + pd.Timedelta(days=config.initial_train_days)
    windows: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    train_end = first_cutoff

    while train_end < max_date:
        validation_end = min(train_end + pd.Timedelta(days=config.validation_window_days), max_date)
        windows.append((train_end, validation_end))
        train_end = train_end + pd.Timedelta(days=config.step_days)

    return windows


def _predicted_outcome_label(probabilities: np.ndarray) -> list[str]:
    indices = probabilities.argmax(axis=1)
    return [OUTCOME_LABELS[index] for index in indices]


def _active_feature_columns(
    train_frame: pd.DataFrame,
    *,
    numeric_columns: list[str],
    categorical_columns: list[str],
) -> tuple[list[str], list[str]]:
    active_numeric = [
        column for column in numeric_columns if train_frame[column].notna().any()
    ]
    active_categorical = [
        column for column in categorical_columns if train_frame[column].notna().any()
    ]
    return active_numeric, active_categorical


def _fold_metrics(
    validation_frame: pd.DataFrame,
    home_lambda: np.ndarray,
    away_lambda: np.ndarray,
    outcome_probabilities: np.ndarray,
    actual_labels: list[str],
    *,
    fold_number: int,
    train_rows: int,
    train_end: pd.Timestamp,
    validation_end: pd.Timestamp,
) -> dict[str, Any]:
    predicted_labels = _predicted_outcome_label(outcome_probabilities)
    return {
        "fold": fold_number,
        "training_rows": train_rows,
        "validation_rows": int(len(validation_frame)),
        "train_end_date": train_end.strftime("%Y-%m-%d"),
        "validation_end_date": validation_end.strftime("%Y-%m-%d"),
        "home_goal_mae": float(mean_absolute_error(validation_frame["home_score_90"], home_lambda)),
        "away_goal_mae": float(mean_absolute_error(validation_frame["away_score_90"], away_lambda)),
        "home_goal_poisson_deviance": float(
            mean_poisson_deviance(validation_frame["home_score_90"], home_lambda)
        ),
        "away_goal_poisson_deviance": float(
            mean_poisson_deviance(validation_frame["away_score_90"], away_lambda)
        ),
        "outcome_log_loss": float(
            log_loss(
                actual_labels,
                outcome_probabilities[:, [2, 1, 0]],
                labels=METRIC_OUTCOME_LABELS,
            )
        ),
        "outcome_brier_score": _multiclass_brier_score(outcome_probabilities, actual_labels),
        "outcome_accuracy": float(accuracy_score(actual_labels, predicted_labels)),
    }


def backtest_model(
    *,
    data_dir: Path,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    features = pd.read_csv(data_dir / "processed" / "match_features.csv")
    return backtest_model_from_frame(features=features, config=config)


def backtest_model_from_frame(
    *,
    features: pd.DataFrame,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    config = config or BacktestConfig()
    features["kickoff_date"] = pd.to_datetime(features["kickoff_date"])
    features = features.sort_values(["kickoff_date", "match_id"]).reset_index(drop=True)

    numeric_columns, categorical_columns = _select_feature_columns(features)
    windows = _validate_backtest_window(features["kickoff_date"], config=config)

    fold_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []
    training_config = TrainModelConfig(
        alpha=config.alpha,
        max_iter=config.max_iter,
        max_probability_goals=config.max_probability_goals,
    )

    for fold_number, (train_end, validation_end) in enumerate(windows, start=1):
        train_mask = features["kickoff_date"] <= train_end
        validation_mask = (features["kickoff_date"] > train_end) & (
            features["kickoff_date"] <= validation_end
        )
        train_frame = features.loc[train_mask].copy()
        validation_frame = features.loc[validation_mask].copy()

        if train_frame.empty or validation_frame.empty:
            continue

        active_numeric, active_categorical = _active_feature_columns(
            train_frame,
            numeric_columns=numeric_columns,
            categorical_columns=categorical_columns,
        )
        active_training_columns = active_numeric + active_categorical

        home_pipeline = _build_regression_pipeline(
            numeric_columns=active_numeric,
            categorical_columns=active_categorical,
            config=training_config,
        )
        away_pipeline = _build_regression_pipeline(
            numeric_columns=active_numeric,
            categorical_columns=active_categorical,
            config=training_config,
        )
        home_pipeline.fit(train_frame[active_training_columns], train_frame["home_score_90"])
        away_pipeline.fit(train_frame[active_training_columns], train_frame["away_score_90"])

        home_lambda = _clip_lambdas(
            home_pipeline.predict(validation_frame[active_training_columns])
        )
        away_lambda = _clip_lambdas(
            away_pipeline.predict(validation_frame[active_training_columns])
        )
        outcome_probabilities = np.array(
            [
                _outcome_probabilities(
                    float(home_rate),
                    float(away_rate),
                    max_goals=config.max_probability_goals,
                )
                for home_rate, away_rate in zip(home_lambda, away_lambda, strict=True)
            ]
        )
        actual_labels = _actual_outcome(
            validation_frame["home_score_90"],
            validation_frame["away_score_90"],
        )
        fold_rows.append(
            _fold_metrics(
                validation_frame,
                home_lambda,
                away_lambda,
                outcome_probabilities,
                actual_labels,
                fold_number=fold_number,
                train_rows=len(train_frame),
                train_end=train_end,
                validation_end=validation_end,
            )
        )

        fold_predictions = validation_frame.loc[
            :,
            [
                "match_id",
                "kickoff_date",
                "home_team_id",
                "away_team_id",
                "home_score_90",
                "away_score_90",
            ],
        ].copy()
        fold_predictions["fold"] = fold_number
        fold_predictions["train_end_date"] = train_end.strftime("%Y-%m-%d")
        fold_predictions["validation_end_date"] = validation_end.strftime("%Y-%m-%d")
        fold_predictions["active_feature_count"] = len(active_training_columns)
        fold_predictions["predicted_home_lambda"] = home_lambda
        fold_predictions["predicted_away_lambda"] = away_lambda
        fold_predictions["home_win_probability"] = outcome_probabilities[:, 0]
        fold_predictions["draw_probability"] = outcome_probabilities[:, 1]
        fold_predictions["away_win_probability"] = outcome_probabilities[:, 2]
        fold_predictions["actual_outcome"] = actual_labels
        fold_predictions["predicted_outcome"] = _predicted_outcome_label(outcome_probabilities)
        prediction_frames.append(fold_predictions)

    fold_metrics = pd.DataFrame(fold_rows)
    predictions = (
        pd.concat(prediction_frames, ignore_index=True)
        if prediction_frames
        else pd.DataFrame()
    )

    report = {
        "config": {
            "initial_train_days": config.initial_train_days,
            "validation_window_days": config.validation_window_days,
            "step_days": config.step_days,
            "alpha": config.alpha,
            "max_iter": config.max_iter,
            "max_probability_goals": config.max_probability_goals,
        },
        "folds": int(len(fold_metrics)),
        "total_backtest_predictions": int(len(predictions)),
        "date_range": {
            "min_match_date": features["kickoff_date"].min().strftime("%Y-%m-%d"),
            "max_match_date": features["kickoff_date"].max().strftime("%Y-%m-%d"),
        },
        "aggregate_metrics": {},
    }

    if not fold_metrics.empty:
        metric_columns = [
            "home_goal_mae",
            "away_goal_mae",
            "home_goal_poisson_deviance",
            "away_goal_poisson_deviance",
            "outcome_log_loss",
            "outcome_brier_score",
            "outcome_accuracy",
        ]
        report["aggregate_metrics"] = {
            metric: float(fold_metrics[metric].mean()) for metric in metric_columns
        }
        report["fold_summaries"] = fold_metrics.to_dict(orient="records")

    return BacktestResult(
        fold_metrics=fold_metrics,
        predictions=predictions,
        report=report,
    )


def write_backtest_result(result: BacktestResult, *, data_dir: Path) -> None:
    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    folds_path = reports_dir / "backtest_fold_metrics.csv"
    predictions_path = reports_dir / "backtest_predictions.csv"
    report_path = reports_dir / "backtest_report.json"

    result.fold_metrics.to_csv(folds_path, index=False)
    result.predictions.to_csv(predictions_path, index=False)
    report_path.write_text(
        json.dumps(result.report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
