import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.stats import poisson
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import PoissonRegressor
from sklearn.metrics import log_loss, mean_absolute_error, mean_poisson_deviance
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

DEFAULT_CATEGORICAL_COLUMNS = [
    "competition_id",
    "home_fifa_confederation",
    "away_fifa_confederation",
]
EXCLUDED_COLUMNS = {
    "match_id",
    "kickoff_date",
    "status",
    "home_team_id",
    "away_team_id",
    "location_id",
    "data_quality_status",
    "source_name",
    "home_score_90",
    "away_score_90",
    "home_elo_post",
    "away_elo_post",
    "k_factor",
    "margin_multiplier",
    "actual_home_score",
    "has_shootout_evidence",
    "has_post_90_goal",
    "home_fifa_code",
    "away_fifa_code",
    "home_fifa_team_name",
    "away_fifa_team_name",
    "home_ranking_snapshot_date",
    "away_ranking_snapshot_date",
    "home_ranking_snapshot_id",
    "away_ranking_snapshot_id",
    "home_fifa_data_source",
    "away_fifa_data_source",
    "home_fifa_rank_source",
    "away_fifa_rank_source",
}
OUTCOME_LABELS = ["home_win", "draw", "away_win"]
METRIC_OUTCOME_LABELS = ["away_win", "draw", "home_win"]


@dataclass(frozen=True, slots=True)
class TrainModelConfig:
    validation_days: int = 365
    alpha: float = 1.0
    max_iter: int = 500
    max_probability_goals: int = 10


@dataclass(frozen=True, slots=True)
class TrainModelResult:
    model_version: str
    model_bundle: dict[str, Any]
    validation_predictions: pd.DataFrame
    metadata: dict[str, Any]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _resolve_validation_mask(
    dates: pd.Series,
    *,
    validation_days: int,
) -> tuple[pd.Series, pd.Timestamp]:
    max_date = dates.max()
    cutoff = max_date - pd.Timedelta(days=validation_days)
    validation_mask = dates > cutoff
    if int(validation_mask.sum()) == 0:
        fallback_index = max(1, int(len(dates) * 0.2))
        ordered = dates.sort_values()
        fallback_cutoff = ordered.iloc[-fallback_index]
        validation_mask = dates >= fallback_cutoff
        cutoff = fallback_cutoff
    if int((~validation_mask).sum()) == 0:
        validation_mask.iloc[-1] = True
    return validation_mask, cutoff


def _select_feature_columns(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    categorical_columns = [
        column for column in DEFAULT_CATEGORICAL_COLUMNS if column in frame.columns
    ]
    numeric_columns = [
        column
        for column in frame.columns
        if column not in EXCLUDED_COLUMNS
        and column not in categorical_columns
        and pd.api.types.is_numeric_dtype(frame[column])
    ]
    return numeric_columns, categorical_columns


def _build_regression_pipeline(
    *,
    numeric_columns: list[str],
    categorical_columns: list[str],
    config: TrainModelConfig,
) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_columns,
            ),
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        (
                            "encoder",
                            OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                        ),
                    ]
                ),
                categorical_columns,
            ),
        ],
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                PoissonRegressor(
                    alpha=config.alpha,
                    max_iter=config.max_iter,
                ),
            ),
        ]
    )


def _clip_lambdas(values: np.ndarray) -> np.ndarray:
    return np.clip(values.astype("float64"), 1e-6, None)


def _outcome_probabilities(
    home_lambda: float,
    away_lambda: float,
    *,
    max_goals: int,
) -> tuple[float, float, float]:
    score_range = np.arange(max_goals + 1)
    home_probs = poisson.pmf(score_range, home_lambda)
    away_probs = poisson.pmf(score_range, away_lambda)
    matrix = np.outer(home_probs, away_probs)

    home_win = float(np.tril(matrix, k=-1).sum())
    draw = float(np.trace(matrix))
    away_win = float(np.triu(matrix, k=1).sum())

    residual = max(0.0, 1.0 - (home_win + draw + away_win))
    draw = min(1.0, draw + residual)
    return home_win, draw, away_win


def _actual_outcome(home_goals: pd.Series, away_goals: pd.Series) -> list[str]:
    labels: list[str] = []
    for home_score, away_score in zip(home_goals, away_goals, strict=True):
        if home_score > away_score:
            labels.append("home_win")
        elif home_score < away_score:
            labels.append("away_win")
        else:
            labels.append("draw")
    return labels


def _multiclass_brier_score(probabilities: np.ndarray, labels: list[str]) -> float:
    target = np.zeros_like(probabilities)
    for index, label in enumerate(labels):
        target[index, OUTCOME_LABELS.index(label)] = 1.0
    return float(np.mean(np.sum((probabilities - target) ** 2, axis=1)))


def train_model(
    *,
    data_dir: Path,
    model_dir: Path,
    config: TrainModelConfig | None = None,
) -> TrainModelResult:
    config = config or TrainModelConfig()
    features = pd.read_csv(data_dir / "processed" / "match_features.csv")
    features["kickoff_date"] = pd.to_datetime(features["kickoff_date"])
    features = features.sort_values(["kickoff_date", "match_id"]).reset_index(drop=True)

    numeric_columns, categorical_columns = _select_feature_columns(features)
    training_columns = numeric_columns + categorical_columns

    validation_mask, cutoff = _resolve_validation_mask(
        features["kickoff_date"],
        validation_days=config.validation_days,
    )
    train_frame = features.loc[~validation_mask].copy()
    validation_frame = features.loc[validation_mask].copy()

    home_pipeline = _build_regression_pipeline(
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        config=config,
    )
    away_pipeline = _build_regression_pipeline(
        numeric_columns=numeric_columns,
        categorical_columns=categorical_columns,
        config=config,
    )

    home_pipeline.fit(train_frame[training_columns], train_frame["home_score_90"])
    away_pipeline.fit(train_frame[training_columns], train_frame["away_score_90"])

    home_lambda = _clip_lambdas(home_pipeline.predict(validation_frame[training_columns]))
    away_lambda = _clip_lambdas(away_pipeline.predict(validation_frame[training_columns]))

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

    validation_predictions = validation_frame.loc[
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
    validation_predictions["predicted_home_lambda"] = home_lambda
    validation_predictions["predicted_away_lambda"] = away_lambda
    validation_predictions["home_win_probability"] = outcome_probabilities[:, 0]
    validation_predictions["draw_probability"] = outcome_probabilities[:, 1]
    validation_predictions["away_win_probability"] = outcome_probabilities[:, 2]
    validation_predictions["predicted_total_goals"] = home_lambda + away_lambda
    validation_predictions["actual_outcome"] = actual_labels

    trained_at = datetime.now(UTC)
    model_version = (
        f"baseline_poisson_{trained_at.strftime('%Y%m%dT%H%M%SZ')}"
    )

    model_bundle: dict[str, Any] = {
        "model_version": model_version,
        "trained_at_utc": trained_at.isoformat(),
        "model_family": "independent_poisson_regressor",
        "numeric_features": numeric_columns,
        "categorical_features": categorical_columns,
        "feature_columns": training_columns,
        "max_probability_goals": config.max_probability_goals,
        "home_goals_model": home_pipeline,
        "away_goals_model": away_pipeline,
        "train_cutoff_exclusive": cutoff.strftime("%Y-%m-%d"),
    }

    metadata = {
        "model_version": model_version,
        "trained_at_utc": trained_at.isoformat(),
        "model_family": "independent_poisson_regressor",
        "artifact_format": "joblib",
        "training_rows": int(len(train_frame)),
        "validation_rows": int(len(validation_frame)),
        "max_training_date": train_frame["kickoff_date"].max().strftime("%Y-%m-%d"),
        "validation_start_date": validation_frame["kickoff_date"].min().strftime("%Y-%m-%d"),
        "validation_end_date": validation_frame["kickoff_date"].max().strftime("%Y-%m-%d"),
        "data_source": "data/processed/match_features.csv",
        "feature_count": len(training_columns),
        "numeric_feature_count": len(numeric_columns),
        "categorical_feature_count": len(categorical_columns),
        "feature_columns": training_columns,
        "config": {
            "validation_days": config.validation_days,
            "alpha": config.alpha,
            "max_iter": config.max_iter,
            "max_probability_goals": config.max_probability_goals,
        },
        "metrics": {
            "home_goal_mae": float(
                mean_absolute_error(validation_frame["home_score_90"], home_lambda)
            ),
            "away_goal_mae": float(
                mean_absolute_error(validation_frame["away_score_90"], away_lambda)
            ),
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
            "outcome_brier_score": _multiclass_brier_score(
                outcome_probabilities,
                actual_labels,
            ),
        },
    }

    return TrainModelResult(
        model_version=model_version,
        model_bundle=model_bundle,
        validation_predictions=validation_predictions,
        metadata=metadata,
    )


def write_train_result(result: TrainModelResult, *, model_dir: Path) -> None:
    version_dir = model_dir / result.model_version
    version_dir.mkdir(parents=True, exist_ok=True)

    model_path = version_dir / "model.joblib"
    metadata_path = version_dir / "metadata.json"
    predictions_path = version_dir / "validation_predictions.csv"

    joblib.dump(result.model_bundle, model_path)
    result.validation_predictions.to_csv(predictions_path, index=False)

    metadata = dict(result.metadata)
    metadata["artifact_files"] = {
        "model": {
            "path": f"artifacts/models/{result.model_version}/model.joblib",
            "sha256": _sha256(model_path),
        },
        "metadata": {
            "path": f"artifacts/models/{result.model_version}/metadata.json",
        },
        "validation_predictions": {
            "path": f"artifacts/models/{result.model_version}/validation_predictions.csv",
            "sha256": _sha256(predictions_path),
        },
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
