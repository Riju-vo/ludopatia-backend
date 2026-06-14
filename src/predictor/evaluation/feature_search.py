import json
from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Any

import pandas as pd

from predictor.evaluation.backtest import (
    BacktestConfig,
    backtest_model_from_frame,
)
from predictor.features.build import FeatureBuildConfig, build_features_from_frames


@dataclass(frozen=True, slots=True)
class FeatureSearchConfig:
    half_life_days: tuple[float, ...] = (180.0, 365.0, 540.0)
    history_years: tuple[int, ...] = (3, 5, 8)
    backtest: BacktestConfig = BacktestConfig()


@dataclass(frozen=True, slots=True)
class FeatureSearchResult:
    rankings: pd.DataFrame
    report: dict[str, Any]


def compare_feature_configs(
    *,
    data_dir: Path,
    config: FeatureSearchConfig | None = None,
) -> FeatureSearchResult:
    config = config or FeatureSearchConfig()
    processed_dir = data_dir / "processed"
    match_ratings = pd.read_csv(processed_dir / "match_ratings.csv")
    fixture_ratings = pd.read_csv(processed_dir / "fixture_ratings.csv")

    rows: list[dict[str, Any]] = []
    detailed_results: list[dict[str, Any]] = []

    for half_life_days, history_years in product(config.half_life_days, config.history_years):
        feature_config = FeatureBuildConfig(
            half_life_days=float(half_life_days),
            max_history_days=int(history_years * 365),
        )
        features_result = build_features_from_frames(
            match_ratings=match_ratings,
            fixture_ratings=fixture_ratings,
            config=feature_config,
        )
        backtest_result = backtest_model_from_frame(
            features=features_result.match_features,
            config=config.backtest,
        )
        aggregate_metrics = backtest_result.report.get("aggregate_metrics", {})
        row = {
            "half_life_days": float(half_life_days),
            "history_years": int(history_years),
            "max_history_days": int(history_years * 365),
            "folds": int(backtest_result.report.get("folds", 0)),
            "total_backtest_predictions": int(
                backtest_result.report.get("total_backtest_predictions", 0)
            ),
            **aggregate_metrics,
        }
        rows.append(row)
        detailed_results.append(
            {
                "feature_config": {
                    "half_life_days": float(half_life_days),
                    "history_years": int(history_years),
                    "max_history_days": int(history_years * 365),
                },
                "backtest_report": backtest_result.report,
            }
        )

    rankings = pd.DataFrame(rows).sort_values(
        ["outcome_log_loss", "outcome_brier_score", "away_goal_poisson_deviance"],
        ascending=[True, True, True],
    ).reset_index(drop=True)

    report = {
        "searched_configurations": int(len(rankings)),
        "backtest_config": {
            "initial_train_days": config.backtest.initial_train_days,
            "validation_window_days": config.backtest.validation_window_days,
            "step_days": config.backtest.step_days,
            "alpha": config.backtest.alpha,
            "max_iter": config.backtest.max_iter,
            "max_probability_goals": config.backtest.max_probability_goals,
        },
        "rankings": rankings.to_dict(orient="records"),
        "best_configuration": rankings.iloc[0].to_dict() if not rankings.empty else None,
        "detailed_results": detailed_results,
    }
    return FeatureSearchResult(rankings=rankings, report=report)


def write_feature_search_result(result: FeatureSearchResult, *, data_dir: Path) -> None:
    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    rankings_path = reports_dir / "feature_config_rankings.csv"
    report_path = reports_dir / "feature_config_search.json"

    result.rankings.to_csv(rankings_path, index=False)
    report_path.write_text(
        json.dumps(result.report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
