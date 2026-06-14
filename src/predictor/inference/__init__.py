"""Inference package."""

from predictor.inference.predict import (
    FixturePredictionResult,
    predict_fixtures,
    write_fixture_predictions,
)

__all__ = [
    "FixturePredictionResult",
    "predict_fixtures",
    "write_fixture_predictions",
]
