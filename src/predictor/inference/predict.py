import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.stats import poisson

DEFAULT_MAX_PROBABILITY_GOALS = 10


@dataclass(frozen=True, slots=True)
class FixturePredictionResult:
    model_version: str
    predictions: pd.DataFrame
    score_matrices: list[dict[str, Any]]
    metadata: dict[str, Any]


def _resolve_model_version(model_dir: Path, model_version: str | None) -> str:
    if model_version:
        target = model_dir / model_version
        if not target.exists():
            raise FileNotFoundError(f"Model version not found: {model_version}")
        return model_version

    candidates = [path.name for path in model_dir.iterdir() if path.is_dir()]
    if not candidates:
        raise FileNotFoundError("No trained model versions found in artifacts/models.")
    return sorted(candidates)[-1]


def _load_model_bundle(version_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    model_bundle = joblib.load(version_dir / "model.joblib")
    metadata = json.loads((version_dir / "metadata.json").read_text(encoding="utf-8"))
    return model_bundle, metadata


def _score_distribution_with_overflow(rate: float, *, max_goals: int) -> np.ndarray:
    exact_goals = np.arange(max_goals)
    exact_probabilities = poisson.pmf(exact_goals, rate)
    overflow_probability = float(1.0 - exact_probabilities.sum())
    return np.append(exact_probabilities, max(0.0, overflow_probability))


def _score_matrix(home_lambda: float, away_lambda: float, *, max_goals: int) -> np.ndarray:
    home_distribution = _score_distribution_with_overflow(home_lambda, max_goals=max_goals)
    away_distribution = _score_distribution_with_overflow(away_lambda, max_goals=max_goals)
    matrix = np.outer(home_distribution, away_distribution)
    return matrix / matrix.sum()


def _outcome_probabilities(matrix: np.ndarray) -> tuple[float, float, float]:
    home_win = float(np.tril(matrix, k=-1).sum())
    draw = float(np.trace(matrix))
    away_win = float(np.triu(matrix, k=1).sum())
    return home_win, draw, away_win


def _top_scoreline(matrix: np.ndarray, *, max_goals: int) -> tuple[str, float]:
    home_index, away_index = np.unravel_index(np.argmax(matrix), matrix.shape)
    home_label = str(home_index) if home_index < max_goals else f"{max_goals}+"
    away_label = str(away_index) if away_index < max_goals else f"{max_goals}+"
    return f"{home_label}-{away_label}", float(matrix[home_index, away_index])


def predict_fixtures(
    *,
    data_dir: Path,
    model_dir: Path,
    model_version: str | None = None,
) -> FixturePredictionResult:
    resolved_version = _resolve_model_version(model_dir, model_version)
    version_dir = model_dir / resolved_version
    model_bundle, training_metadata = _load_model_bundle(version_dir)

    fixture_features = pd.read_csv(data_dir / "processed" / "fixture_features.csv")
    feature_columns = list(model_bundle["feature_columns"])
    max_goals = int(
        model_bundle.get(
            "max_probability_goals",
            training_metadata.get("config", {}).get(
                "max_probability_goals",
                DEFAULT_MAX_PROBABILITY_GOALS,
            ),
        )
    )

    home_lambda = np.clip(
        model_bundle["home_goals_model"].predict(fixture_features[feature_columns]),
        1e-6,
        None,
    )
    away_lambda = np.clip(
        model_bundle["away_goals_model"].predict(fixture_features[feature_columns]),
        1e-6,
        None,
    )

    prediction_rows: list[dict[str, Any]] = []
    score_matrices: list[dict[str, Any]] = []
    score_labels = [str(value) for value in range(max_goals)] + [f"{max_goals}+"]

    for row, predicted_home_lambda, predicted_away_lambda in zip(
        fixture_features.itertuples(index=False),
        home_lambda,
        away_lambda,
        strict=True,
    ):
        matrix = _score_matrix(
            float(predicted_home_lambda),
            float(predicted_away_lambda),
            max_goals=max_goals,
        )
        home_win_probability, draw_probability, away_win_probability = _outcome_probabilities(
            matrix
        )
        top_scoreline, top_scoreline_probability = _top_scoreline(
            matrix,
            max_goals=max_goals,
        )

        prediction_rows.append(
            {
                "match_id": row.match_id,
                "kickoff_date": row.kickoff_date,
                "home_team_id": row.home_team_id,
                "away_team_id": row.away_team_id,
                "competition_id": row.competition_id,
                "model_version": resolved_version,
                "predicted_home_lambda": float(predicted_home_lambda),
                "predicted_away_lambda": float(predicted_away_lambda),
                "predicted_total_goals": float(predicted_home_lambda + predicted_away_lambda),
                "home_win_probability": home_win_probability,
                "draw_probability": draw_probability,
                "away_win_probability": away_win_probability,
                "top_scoreline": top_scoreline,
                "top_scoreline_probability": top_scoreline_probability,
            }
        )
        score_matrices.append(
            {
                "match_id": row.match_id,
                "model_version": resolved_version,
                "score_labels": score_labels,
                "matrix": matrix.round(10).tolist(),
            }
        )

    predictions = pd.DataFrame(prediction_rows)
    metadata = {
        "model_version": resolved_version,
        "fixture_rows": int(len(predictions)),
        "score_matrix_labels": score_labels,
        "source_features_path": "data/processed/fixture_features.csv",
    }
    return FixturePredictionResult(
        model_version=resolved_version,
        predictions=predictions,
        score_matrices=score_matrices,
        metadata=metadata,
    )


def write_fixture_predictions(
    result: FixturePredictionResult,
    *,
    data_dir: Path,
    model_dir: Path,
) -> None:
    predictions_dir = data_dir / "predictions"
    predictions_dir.mkdir(parents=True, exist_ok=True)

    version_dir = model_dir / result.model_version
    version_dir.mkdir(parents=True, exist_ok=True)

    latest_csv_path = predictions_dir / "fixture_predictions.csv"
    latest_json_path = predictions_dir / "fixture_score_matrices.json"
    version_csv_path = version_dir / "fixture_predictions.csv"
    version_json_path = version_dir / "fixture_score_matrices.json"

    result.predictions.to_csv(latest_csv_path, index=False)
    result.predictions.to_csv(version_csv_path, index=False)

    matrices_payload = {
        "model_version": result.model_version,
        "predictions": result.score_matrices,
    }
    json_text = json.dumps(matrices_payload, indent=2, ensure_ascii=True) + "\n"
    latest_json_path.write_text(json_text, encoding="utf-8")
    version_json_path.write_text(json_text, encoding="utf-8")
