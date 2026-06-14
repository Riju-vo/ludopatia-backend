from pathlib import Path

import pandas as pd

from predictor.training import TrainModelConfig, train_model, write_train_result


def _build_match_features_frame() -> pd.DataFrame:
    rows = []
    for index in range(12):
        rows.append(
            {
                "match_id": f"m{index}",
                "kickoff_date": f"2021-01-{index + 1:02d}",
                "status": "finished",
                "home_team_id": f"H{index % 3}",
                "away_team_id": f"A{(index + 1) % 3}",
                "competition_id": "friendly" if index % 2 == 0 else "qualifier",
                "location_id": f"loc{index % 2}",
                "neutral": bool(index % 2),
                "home_is_tournament_host": False,
                "away_is_tournament_host": False,
                "home_score_90": index % 4,
                "away_score_90": (index + 1) % 3,
                "home_elo_pre": 1500.0 + index * 4,
                "away_elo_pre": 1490.0 + index * 3,
                "elo_difference_pre": 10.0 + index,
                "home_elo_matches_pre": index,
                "away_elo_matches_pre": index + 1,
                "applied_home_advantage": 50.0,
                "expected_home_score": 0.55,
                "home_fifa_points_pre": 1200.0 + index,
                "home_fifa_rank_pre": 40.0,
                "home_previous_rank": 41.0,
                "home_previous_points": 1190.0,
                "home_fifa_confederation": "UEFA",
                "home_ranking_age_days": 10,
                "away_fifa_points_pre": 1180.0 + index,
                "away_fifa_rank_pre": 45.0,
                "away_previous_rank": 44.0,
                "away_previous_points": 1175.0,
                "away_fifa_confederation": "CONMEBOL",
                "away_ranking_age_days": 12,
                "fifa_points_difference_pre": 20.0,
                "fifa_rank_difference_pre": 5.0,
                "home_history_matches_used": max(0, index - 1),
                "home_history_weight_sum": float(max(0, index - 1)),
                "home_goals_for_avg_weighted": 1.1 + index * 0.05,
                "home_goals_against_avg_weighted": 0.9 + index * 0.03,
                "home_goal_difference_avg_weighted": 0.2 + index * 0.02,
                "home_points_avg_weighted": 1.4 + index * 0.01,
                "home_win_rate_weighted": 0.4,
                "home_draw_rate_weighted": 0.3,
                "home_loss_rate_weighted": 0.3,
                "home_clean_sheet_rate_weighted": 0.25,
                "home_failed_to_score_rate_weighted": 0.2,
                "home_attack_adjusted_elo_avg_weighted": 1.3 + index * 0.04,
                "home_defense_adjusted_elo_avg_weighted": 0.8 + index * 0.02,
                "home_attack_adjusted_fifa_avg_weighted": 1.2 + index * 0.04,
                "home_defense_adjusted_fifa_avg_weighted": 0.85 + index * 0.02,
                "away_history_matches_used": max(0, index - 2),
                "away_history_weight_sum": float(max(0, index - 2)),
                "away_goals_for_avg_weighted": 1.0 + index * 0.04,
                "away_goals_against_avg_weighted": 1.1 + index * 0.03,
                "away_goal_difference_avg_weighted": -0.1 + index * 0.01,
                "away_points_avg_weighted": 1.2 + index * 0.01,
                "away_win_rate_weighted": 0.35,
                "away_draw_rate_weighted": 0.25,
                "away_loss_rate_weighted": 0.4,
                "away_clean_sheet_rate_weighted": 0.2,
                "away_failed_to_score_rate_weighted": 0.25,
                "away_attack_adjusted_elo_avg_weighted": 1.1 + index * 0.03,
                "away_defense_adjusted_elo_avg_weighted": 0.95 + index * 0.02,
                "away_attack_adjusted_fifa_avg_weighted": 1.0 + index * 0.03,
                "away_defense_adjusted_fifa_avg_weighted": 0.98 + index * 0.02,
                "history_matches_used_difference": 1.0,
                "history_weight_sum_difference": 1.0,
                "goals_for_avg_weighted_difference": 0.1,
                "goals_against_avg_weighted_difference": -0.2,
                "goal_difference_avg_weighted_difference": 0.3,
                "points_avg_weighted_difference": 0.2,
                "win_rate_weighted_difference": 0.05,
                "draw_rate_weighted_difference": 0.05,
                "loss_rate_weighted_difference": -0.1,
                "clean_sheet_rate_weighted_difference": 0.05,
                "failed_to_score_rate_weighted_difference": -0.05,
                "attack_adjusted_elo_avg_weighted_difference": 0.2,
                "defense_adjusted_elo_avg_weighted_difference": -0.1,
                "attack_adjusted_fifa_avg_weighted_difference": 0.2,
                "defense_adjusted_fifa_avg_weighted_difference": -0.13,
            }
        )
    return pd.DataFrame(rows)


def test_train_model_writes_versioned_artifact(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True)
    _build_match_features_frame().to_csv(processed_dir / "match_features.csv", index=False)

    result = train_model(
        data_dir=data_dir,
        model_dir=tmp_path / "models",
        config=TrainModelConfig(validation_days=3, alpha=0.5, max_iter=200),
    )
    write_train_result(result, model_dir=tmp_path / "models")

    version_dir = tmp_path / "models" / result.model_version

    assert version_dir.exists()
    assert (version_dir / "model.joblib").exists()
    assert (version_dir / "metadata.json").exists()
    assert (version_dir / "validation_predictions.csv").exists()
    assert result.metadata["training_rows"] > 0
    assert result.metadata["validation_rows"] > 0
    assert result.validation_predictions["predicted_home_lambda"].gt(0).all()
