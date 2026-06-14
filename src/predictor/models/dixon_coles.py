from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.stats import poisson

EPSILON = 1e-12


@dataclass(frozen=True, slots=True)
class DixonColesConfig:
    rho_min: float = -0.2
    rho_max: float = 0.2
    max_probability_goals: int = 10


def _tau(
    home_goals: int,
    away_goals: int,
    home_lambda: float,
    away_lambda: float,
    rho: float,
) -> float:
    if home_goals == 0 and away_goals == 0:
        return 1.0 - (home_lambda * away_lambda * rho)
    if home_goals == 0 and away_goals == 1:
        return 1.0 + (home_lambda * rho)
    if home_goals == 1 and away_goals == 0:
        return 1.0 + (away_lambda * rho)
    if home_goals == 1 and away_goals == 1:
        return 1.0 - rho
    return 1.0


def exact_score_probability(
    home_goals: int,
    away_goals: int,
    home_lambda: float,
    away_lambda: float,
    rho: float = 0.0,
) -> float:
    tau = _tau(home_goals, away_goals, home_lambda, away_lambda, rho)
    if tau <= 0:
        return EPSILON
    probability = (
        poisson.pmf(home_goals, home_lambda)
        * poisson.pmf(away_goals, away_lambda)
        * tau
    )
    return float(max(probability, EPSILON))


def exact_score_log_loss(
    home_goals: np.ndarray,
    away_goals: np.ndarray,
    home_lambda: np.ndarray,
    away_lambda: np.ndarray,
    *,
    rho: float = 0.0,
) -> float:
    probabilities = [
        exact_score_probability(
            int(home_score),
            int(away_score),
            float(home_rate),
            float(away_rate),
            rho,
        )
        for home_score, away_score, home_rate, away_rate in zip(
            home_goals,
            away_goals,
            home_lambda,
            away_lambda,
            strict=True,
        )
    ]
    return float(-np.mean(np.log(np.clip(probabilities, EPSILON, None))))


def fit_dixon_coles_rho(
    home_goals: np.ndarray,
    away_goals: np.ndarray,
    home_lambda: np.ndarray,
    away_lambda: np.ndarray,
    *,
    config: DixonColesConfig | None = None,
) -> float:
    config = config or DixonColesConfig()

    def objective(rho: float) -> float:
        return exact_score_log_loss(
            home_goals,
            away_goals,
            home_lambda,
            away_lambda,
            rho=rho,
        )

    result = minimize_scalar(
        objective,
        bounds=(config.rho_min, config.rho_max),
        method="bounded",
    )
    return float(result.x)


def score_matrix(
    home_lambda: float,
    away_lambda: float,
    *,
    rho: float = 0.0,
    max_goals: int = 10,
) -> np.ndarray:
    size = max_goals + 1
    matrix = np.zeros((size, size), dtype="float64")
    for home_goals in range(max_goals):
        for away_goals in range(max_goals):
            matrix[home_goals, away_goals] = exact_score_probability(
                home_goals,
                away_goals,
                home_lambda,
                away_lambda,
                rho,
            )

    home_tail = 1.0 - poisson.cdf(max_goals - 1, home_lambda)
    away_tail = 1.0 - poisson.cdf(max_goals - 1, away_lambda)

    for goals in range(max_goals):
        matrix[goals, max_goals] = poisson.pmf(goals, home_lambda) * away_tail
        matrix[max_goals, goals] = home_tail * poisson.pmf(goals, away_lambda)
    matrix[max_goals, max_goals] = home_tail * away_tail

    total = matrix.sum()
    return matrix / total if total > 0 else matrix


def outcome_probabilities_from_matrix(matrix: np.ndarray) -> tuple[float, float, float]:
    home_win = float(np.tril(matrix, k=-1).sum())
    draw = float(np.trace(matrix))
    away_win = float(np.triu(matrix, k=1).sum())
    return home_win, draw, away_win
