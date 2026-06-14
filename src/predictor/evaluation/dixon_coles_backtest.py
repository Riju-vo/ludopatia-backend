import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss

from predictor.evaluation.backtest import (
    BacktestConfig,
    _active_feature_columns,
    _predicted_outcome_label,
    _validate_backtest_window,
)
from predictor.models import (
    DixonColesConfig,
    exact_score_log_loss,
    fit_dixon_coles_rho,
    outcome_probabilities_from_matrix,
    score_matrix,
)
from predictor.training.train import (
    METRIC_OUTCOME_LABELS,
    TrainModelConfig,
    _actual_outcome,
    _build_regression_pipeline,
    _clip_lambdas,
    _multiclass_brier_score,
    _outcome_probabilities,
    _select_feature_columns,
)


@dataclass(frozen=True, slots=True)
class DixonColesBacktestResult:
    fold_metrics: pd.DataFrame
    predictions: pd.DataFrame
    report: dict[str, Any]


def backtest_dixon_coles(
    *,
    data_dir: Path,
    config: BacktestConfig | None = None,
    dixon_coles_config: DixonColesConfig | None = None,
) -> DixonColesBacktestResult:
    config = config or BacktestConfig()
    dixon_coles_config = dixon_coles_config or DixonColesConfig(
        max_probability_goals=config.max_probability_goals
    )

    features = pd.read_csv(data_dir / "processed" / "match_features.csv")
    features["kickoff_date"] = pd.to_datetime(features["kickoff_date"])
    features = features.sort_values(["kickoff_date", "match_id"]).reset_index(drop=True)

    numeric_columns, categorical_columns = _select_feature_columns(features)
    windows = _validate_backtest_window(features["kickoff_date"], config=config)
    training_config = TrainModelConfig(
        alpha=config.alpha,
        max_iter=config.max_iter,
        max_probability_goals=config.max_probability_goals,
    )

    rows: list[dict[str, Any]] = []
    prediction_rows: list[dict[str, Any]] = []
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

        train_home_lambda = _clip_lambdas(
            home_pipeline.predict(train_frame[active_training_columns])
        )
        train_away_lambda = _clip_lambdas(
            away_pipeline.predict(train_frame[active_training_columns])
        )
        validation_home_lambda = _clip_lambdas(
            home_pipeline.predict(validation_frame[active_training_columns])
        )
        validation_away_lambda = _clip_lambdas(
            away_pipeline.predict(validation_frame[active_training_columns])
        )

        rho = fit_dixon_coles_rho(
            train_frame["home_score_90"].to_numpy(),
            train_frame["away_score_90"].to_numpy(),
            train_home_lambda,
            train_away_lambda,
            config=dixon_coles_config,
        )

        baseline_outcome_probabilities = np.array(
            [
                _outcome_probabilities(
                    float(home_rate),
                    float(away_rate),
                    max_goals=config.max_probability_goals,
                )
                for home_rate, away_rate in zip(
                    validation_home_lambda,
                    validation_away_lambda,
                    strict=True,
                )
            ]
        )
        dixon_coles_outcome_probabilities = np.array(
            [
                outcome_probabilities_from_matrix(
                    score_matrix(
                        float(home_rate),
                        float(away_rate),
                        rho=rho,
                        max_goals=config.max_probability_goals,
                    )
                )
                for home_rate, away_rate in zip(
                    validation_home_lambda,
                    validation_away_lambda,
                    strict=True,
                )
            ]
        )
        actual_labels = _actual_outcome(
            validation_frame["home_score_90"],
            validation_frame["away_score_90"],
        )

        baseline_predicted_labels = _predicted_outcome_label(baseline_outcome_probabilities)
        dixon_predicted_labels = _predicted_outcome_label(dixon_coles_outcome_probabilities)
        baseline_exact_score_log_loss = exact_score_log_loss(
            validation_frame["home_score_90"].to_numpy(),
            validation_frame["away_score_90"].to_numpy(),
            validation_home_lambda,
            validation_away_lambda,
            rho=0.0,
        )
        dixon_exact_score_log_loss = exact_score_log_loss(
            validation_frame["home_score_90"].to_numpy(),
            validation_frame["away_score_90"].to_numpy(),
            validation_home_lambda,
            validation_away_lambda,
            rho=rho,
        )

        rows.append(
            {
                "fold": fold_number,
                "training_rows": int(len(train_frame)),
                "validation_rows": int(len(validation_frame)),
                "train_end_date": train_end.strftime("%Y-%m-%d"),
                "validation_end_date": validation_end.strftime("%Y-%m-%d"),
                "rho": rho,
                "baseline_outcome_log_loss": float(
                    log_loss(
                        actual_labels,
                        baseline_outcome_probabilities[:, [2, 1, 0]],
                        labels=METRIC_OUTCOME_LABELS,
                    )
                ),
                "dixon_coles_outcome_log_loss": float(
                    log_loss(
                        actual_labels,
                        dixon_coles_outcome_probabilities[:, [2, 1, 0]],
                        labels=METRIC_OUTCOME_LABELS,
                    )
                ),
                "baseline_outcome_brier_score": _multiclass_brier_score(
                    baseline_outcome_probabilities,
                    actual_labels,
                ),
                "dixon_coles_outcome_brier_score": _multiclass_brier_score(
                    dixon_coles_outcome_probabilities,
                    actual_labels,
                ),
                "baseline_outcome_accuracy": float(
                    accuracy_score(actual_labels, baseline_predicted_labels)
                ),
                "dixon_coles_outcome_accuracy": float(
                    accuracy_score(actual_labels, dixon_predicted_labels)
                ),
                "baseline_exact_score_log_loss": baseline_exact_score_log_loss,
                "dixon_coles_exact_score_log_loss": dixon_exact_score_log_loss,
                "delta_outcome_log_loss": float(
                    log_loss(
                        actual_labels,
                        dixon_coles_outcome_probabilities[:, [2, 1, 0]],
                        labels=METRIC_OUTCOME_LABELS,
                    )
                    - log_loss(
                        actual_labels,
                        baseline_outcome_probabilities[:, [2, 1, 0]],
                        labels=METRIC_OUTCOME_LABELS,
                    )
                ),
                "delta_exact_score_log_loss": dixon_exact_score_log_loss
                - baseline_exact_score_log_loss,
            }
        )
        for (
            validation_row,
            baseline_probs,
            dixon_probs,
            actual_label,
            predicted_label,
            dixon_label,
        ) in zip(
            validation_frame.itertuples(index=False),
            baseline_outcome_probabilities,
            dixon_coles_outcome_probabilities,
            actual_labels,
            baseline_predicted_labels,
            dixon_predicted_labels,
            strict=True,
        ):
            prediction_rows.append(
                {
                    "match_id": validation_row.match_id,
                    "kickoff_date": validation_row.kickoff_date.strftime("%Y-%m-%d"),
                    "home_team_id": validation_row.home_team_id,
                    "away_team_id": validation_row.away_team_id,
                    "fold": fold_number,
                    "train_end_date": train_end.strftime("%Y-%m-%d"),
                    "validation_end_date": validation_end.strftime("%Y-%m-%d"),
                    "rho": rho,
                    "home_score_90": int(validation_row.home_score_90),
                    "away_score_90": int(validation_row.away_score_90),
                    "actual_outcome": actual_label,
                    "baseline_home_win_probability": float(baseline_probs[0]),
                    "baseline_draw_probability": float(baseline_probs[1]),
                    "baseline_away_win_probability": float(baseline_probs[2]),
                    "baseline_predicted_outcome": predicted_label,
                    "dixon_coles_home_win_probability": float(dixon_probs[0]),
                    "dixon_coles_draw_probability": float(dixon_probs[1]),
                    "dixon_coles_away_win_probability": float(dixon_probs[2]),
                    "dixon_coles_predicted_outcome": dixon_label,
                }
            )

    fold_metrics = pd.DataFrame(rows)
    predictions = pd.DataFrame(prediction_rows)
    report = {
        "config": {
            "initial_train_days": config.initial_train_days,
            "validation_window_days": config.validation_window_days,
            "step_days": config.step_days,
            "alpha": config.alpha,
            "max_iter": config.max_iter,
            "max_probability_goals": config.max_probability_goals,
            "rho_min": dixon_coles_config.rho_min,
            "rho_max": dixon_coles_config.rho_max,
        },
        "folds": int(len(fold_metrics)),
        "aggregate_metrics": {},
    }
    if not fold_metrics.empty:
        metric_columns = [
            "rho",
            "baseline_outcome_log_loss",
            "dixon_coles_outcome_log_loss",
            "baseline_outcome_brier_score",
            "dixon_coles_outcome_brier_score",
            "baseline_outcome_accuracy",
            "dixon_coles_outcome_accuracy",
            "baseline_exact_score_log_loss",
            "dixon_coles_exact_score_log_loss",
            "delta_outcome_log_loss",
            "delta_exact_score_log_loss",
        ]
        report["aggregate_metrics"] = {
            metric: float(fold_metrics[metric].mean()) for metric in metric_columns
        }
        report["fold_summaries"] = fold_metrics.to_dict(orient="records")

    return DixonColesBacktestResult(
        fold_metrics=fold_metrics,
        predictions=predictions,
        report=report,
    )


def write_dixon_coles_backtest_result(
    result: DixonColesBacktestResult,
    *,
    data_dir: Path,
) -> None:
    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    folds_path = reports_dir / "dixon_coles_backtest_fold_metrics.csv"
    predictions_path = reports_dir / "dixon_coles_backtest_predictions.csv"
    report_path = reports_dir / "dixon_coles_backtest_report.json"

    result.fold_metrics.to_csv(folds_path, index=False)
    result.predictions.to_csv(predictions_path, index=False)
    report_path.write_text(
        json.dumps(result.report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
