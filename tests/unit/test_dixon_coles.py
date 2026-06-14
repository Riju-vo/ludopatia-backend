import numpy as np

from predictor.models import (
    DixonColesConfig,
    exact_score_log_loss,
    fit_dixon_coles_rho,
    outcome_probabilities_from_matrix,
    score_matrix,
)


def test_score_matrix_sums_to_one() -> None:
    matrix = score_matrix(1.7, 0.9, rho=-0.08, max_goals=10)
    assert abs(float(matrix.sum()) - 1.0) < 1e-9


def test_fit_dixon_coles_rho_returns_value_inside_bounds() -> None:
    rho = fit_dixon_coles_rho(
        np.array([0, 1, 0, 2, 1]),
        np.array([0, 1, 1, 0, 0]),
        np.array([1.2, 1.4, 1.0, 1.8, 1.1]),
        np.array([0.8, 1.1, 1.2, 0.7, 0.9]),
        config=DixonColesConfig(rho_min=-0.2, rho_max=0.2),
    )
    assert -0.2 <= rho <= 0.2


def test_dixon_coles_changes_low_score_probabilities() -> None:
    baseline = score_matrix(1.4, 1.0, rho=0.0, max_goals=10)
    corrected = score_matrix(1.4, 1.0, rho=-0.1, max_goals=10)

    assert corrected[0, 0] != baseline[0, 0]
    assert corrected[1, 1] != baseline[1, 1]
    assert outcome_probabilities_from_matrix(corrected) != outcome_probabilities_from_matrix(
        baseline
    )
    assert exact_score_log_loss(
        np.array([0]),
        np.array([0]),
        np.array([1.4]),
        np.array([1.0]),
        rho=-0.1,
    ) > 0
