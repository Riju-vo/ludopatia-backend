import json
from pathlib import Path

import pandas as pd

from predictor.inference import predict_fixtures, write_fixture_predictions
from predictor.training import TrainModelConfig, train_model, write_train_result
from tests.unit.test_training import _build_match_features_frame


def _build_fixture_features_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": "f1",
                "kickoff_date": "2021-02-15",
                "status": "scheduled",
                "home_team_id": "H1",
                "away_team_id": "A2",
                "competition_id": "friendly",
                "location_id": "loc1",
                "neutral": False,
                "home_is_tournament_host": False,
                "away_is_tournament_host": False,
                "home_elo_pre": 1510.0,
                "away_elo_pre": 1495.0,
                "elo_difference_pre": 15.0,
                "home_elo_matches_pre": 8,
                "away_elo_matches_pre": 7,
                "applied_home_advantage": 50.0,
                "expected_home_score": 0.58,
                "home_fifa_points_pre": 1215.0,
                "home_fifa_rank_pre": 38.0,
                "home_previous_rank": 39.0,
                "home_previous_points": 1205.0,
                "home_fifa_confederation": "UEFA",
                "home_ranking_age_days": 8,
                "away_fifa_points_pre": 1188.0,
                "away_fifa_rank_pre": 46.0,
                "away_previous_rank": 47.0,
                "away_previous_points": 1180.0,
                "away_fifa_confederation": "CONMEBOL",
                "away_ranking_age_days": 9,
                "fifa_points_difference_pre": 27.0,
                "fifa_rank_difference_pre": 8.0,
                "home_history_matches_used": 7,
                "home_history_weight_sum": 6.8,
                "home_goals_for_avg_weighted": 1.45,
                "home_goals_against_avg_weighted": 0.95,
                "home_goal_difference_avg_weighted": 0.50,
                "home_points_avg_weighted": 1.7,
                "home_win_rate_weighted": 0.48,
                "home_draw_rate_weighted": 0.24,
                "home_loss_rate_weighted": 0.28,
                "home_clean_sheet_rate_weighted": 0.30,
                "home_failed_to_score_rate_weighted": 0.18,
                "home_attack_adjusted_elo_avg_weighted": 1.55,
                "home_defense_adjusted_elo_avg_weighted": 0.84,
                "home_attack_adjusted_fifa_avg_weighted": 1.50,
                "home_defense_adjusted_fifa_avg_weighted": 0.87,
                "away_history_matches_used": 6,
                "away_history_weight_sum": 5.9,
                "away_goals_for_avg_weighted": 1.12,
                "away_goals_against_avg_weighted": 1.08,
                "away_goal_difference_avg_weighted": 0.04,
                "away_points_avg_weighted": 1.28,
                "away_win_rate_weighted": 0.36,
                "away_draw_rate_weighted": 0.20,
                "away_loss_rate_weighted": 0.44,
                "away_clean_sheet_rate_weighted": 0.22,
                "away_failed_to_score_rate_weighted": 0.24,
                "away_attack_adjusted_elo_avg_weighted": 1.20,
                "away_defense_adjusted_elo_avg_weighted": 0.98,
                "away_attack_adjusted_fifa_avg_weighted": 1.16,
                "away_defense_adjusted_fifa_avg_weighted": 1.00,
                "history_matches_used_difference": 1.0,
                "history_weight_sum_difference": 0.9,
                "goals_for_avg_weighted_difference": 0.33,
                "goals_against_avg_weighted_difference": -0.13,
                "goal_difference_avg_weighted_difference": 0.46,
                "points_avg_weighted_difference": 0.42,
                "win_rate_weighted_difference": 0.12,
                "draw_rate_weighted_difference": 0.04,
                "loss_rate_weighted_difference": -0.16,
                "clean_sheet_rate_weighted_difference": 0.08,
                "failed_to_score_rate_weighted_difference": -0.06,
                "attack_adjusted_elo_avg_weighted_difference": 0.35,
                "defense_adjusted_elo_avg_weighted_difference": -0.14,
                "attack_adjusted_fifa_avg_weighted_difference": 0.34,
                "defense_adjusted_fifa_avg_weighted_difference": -0.13,
            }
        ]
    )


def test_predict_fixtures_uses_trained_model_and_writes_outputs(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True)
    _build_match_features_frame().to_csv(processed_dir / "match_features.csv", index=False)
    _build_fixture_features_frame().to_csv(processed_dir / "fixture_features.csv", index=False)

    model_root = tmp_path / "models"
    trained = train_model(
        data_dir=data_dir,
        model_dir=model_root,
        config=TrainModelConfig(validation_days=3, alpha=0.5, max_iter=200),
    )
    write_train_result(trained, model_dir=model_root)

    result = predict_fixtures(data_dir=data_dir, model_dir=model_root)
    write_fixture_predictions(result, data_dir=data_dir, model_dir=model_root)

    assert len(result.predictions) == 1
    assert result.predictions["predicted_home_lambda"].gt(0).all()
    assert result.predictions["home_win_probability"].between(0, 1).all()
    assert abs(
        result.predictions.loc[0, "home_win_probability"]
        + result.predictions.loc[0, "draw_probability"]
        + result.predictions.loc[0, "away_win_probability"]
        - 1.0
    ) < 1e-9

    latest_json = json.loads((data_dir / "predictions" / "fixture_score_matrices.json").read_text())
    assert latest_json["model_version"] == result.model_version
    assert latest_json["predictions"][0]["match_id"] == "f1"
