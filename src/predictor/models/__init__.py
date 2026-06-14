"""Statistical goal models."""

from predictor.models.dixon_coles import (
    DixonColesConfig,
    exact_score_log_loss,
    fit_dixon_coles_rho,
    outcome_probabilities_from_matrix,
    score_matrix,
)

__all__ = [
    "DixonColesConfig",
    "exact_score_log_loss",
    "fit_dixon_coles_rho",
    "outcome_probabilities_from_matrix",
    "score_matrix",
]
