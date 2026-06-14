from pathlib import Path

import pandas as pd

from predictor.evaluation import (
    BacktestConfig,
    FeatureSearchConfig,
    compare_feature_configs,
    write_feature_search_result,
)


def _match_ratings_frame() -> pd.DataFrame:
    rows = []
    for index in range(12):
        rows.append(
            {
                "match_id": f"m{index}",
                "kickoff_date": f"2021-01-{index + 1:02d}",
                "home_team_id": f"H{index % 3}",
                "away_team_id": f"A{(index + 1) % 3}",
                "competition_id": "friendly" if index % 2 == 0 else "qualifier",
                "neutral": False,
                "home_score_90": index % 3,
                "away_score_90": (index + 1) % 2,
                "home_elo_pre": 1500.0 + index * 6,
                "away_elo_pre": 1490.0 + index * 4,
                "home_fifa_points_pre": 1200.0 + index * 2,
                "away_fifa_points_pre": 1180.0 + index * 2,
            }
        )
    return pd.DataFrame(rows)


def _fixture_ratings_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": "f1",
                "kickoff_date": "2021-02-20",
                "home_team_id": "H1",
                "away_team_id": "A2",
                "competition_id": "friendly",
                "neutral": False,
                "home_score_90": None,
                "away_score_90": None,
                "home_elo_pre": 1520.0,
                "away_elo_pre": 1495.0,
                "home_fifa_points_pre": 1215.0,
                "away_fifa_points_pre": 1188.0,
            }
        ]
    )


def test_compare_feature_configs_ranks_multiple_configurations(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True)
    _match_ratings_frame().to_csv(processed_dir / "match_ratings.csv", index=False)
    _fixture_ratings_frame().to_csv(processed_dir / "fixture_ratings.csv", index=False)

    result = compare_feature_configs(
        data_dir=data_dir,
        config=FeatureSearchConfig(
            half_life_days=(180.0, 365.0),
            history_years=(3, 5),
            backtest=BacktestConfig(
                initial_train_days=5,
                validation_window_days=3,
                step_days=3,
                alpha=0.5,
                max_iter=200,
            ),
        ),
    )
    write_feature_search_result(result, data_dir=data_dir)

    assert len(result.rankings) == 4
    assert "outcome_log_loss" in result.rankings.columns
    assert result.report["searched_configurations"] == 4
    assert result.report["best_configuration"] is not None
    assert (data_dir / "reports" / "feature_config_rankings.csv").exists()
