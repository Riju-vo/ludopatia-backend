import pandas as pd

from predictor.features.build import FeatureBuildConfig, build_features_from_frames


def _match_ratings_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": "m1",
                "kickoff_date": "2021-01-01",
                "status": "finished",
                "home_team_id": "A",
                "away_team_id": "B",
                "competition_id": "friendly",
                "location_id": "loc1",
                "neutral": False,
                "home_is_tournament_host": False,
                "away_is_tournament_host": False,
                "home_score_90": 2,
                "away_score_90": 0,
                "home_elo_pre": 1500.0,
                "away_elo_pre": 1500.0,
                "home_fifa_points_pre": 1200.0,
                "away_fifa_points_pre": 1100.0,
            },
            {
                "match_id": "m2",
                "kickoff_date": "2021-01-10",
                "status": "finished",
                "home_team_id": "C",
                "away_team_id": "A",
                "competition_id": "friendly",
                "location_id": "loc2",
                "neutral": False,
                "home_is_tournament_host": False,
                "away_is_tournament_host": False,
                "home_score_90": 1,
                "away_score_90": 1,
                "home_elo_pre": 1520.0,
                "away_elo_pre": 1510.0,
                "home_fifa_points_pre": 1250.0,
                "away_fifa_points_pre": 1210.0,
            },
            {
                "match_id": "m3",
                "kickoff_date": "2021-02-01",
                "status": "finished",
                "home_team_id": "A",
                "away_team_id": "D",
                "competition_id": "friendly",
                "location_id": "loc3",
                "neutral": False,
                "home_is_tournament_host": False,
                "away_is_tournament_host": False,
                "home_score_90": 0,
                "away_score_90": 3,
                "home_elo_pre": 1515.0,
                "away_elo_pre": 1490.0,
                "home_fifa_points_pre": 1220.0,
                "away_fifa_points_pre": 1180.0,
            },
        ]
    )


def _fixture_ratings_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "match_id": "f1",
                "kickoff_date": "2021-02-10",
                "status": "scheduled",
                "home_team_id": "A",
                "away_team_id": "B",
                "competition_id": "friendly",
                "location_id": "loc4",
                "neutral": False,
                "home_is_tournament_host": False,
                "away_is_tournament_host": False,
                "home_elo_pre": 1490.0,
                "away_elo_pre": 1485.0,
                "home_fifa_points_pre": 1200.0,
                "away_fifa_points_pre": 1105.0,
            }
        ]
    )


def test_features_do_not_change_for_past_matches_when_future_results_change() -> None:
    matches = _match_ratings_frame()
    fixtures = _fixture_ratings_frame()
    modified = matches.copy()
    modified.loc[2, "home_score_90"] = 8
    modified.loc[2, "away_score_90"] = 0

    original_result = build_features_from_frames(
        match_ratings=matches,
        fixture_ratings=fixtures,
        config=FeatureBuildConfig(half_life_days=365.0, max_history_days=365 * 5),
    )
    modified_result = build_features_from_frames(
        match_ratings=modified,
        fixture_ratings=fixtures,
        config=FeatureBuildConfig(half_life_days=365.0, max_history_days=365 * 5),
    )

    columns = [
        "home_history_matches_used",
        "away_history_matches_used",
        "home_goals_for_avg_weighted",
        "away_goals_for_avg_weighted",
        "home_points_avg_weighted",
        "away_points_avg_weighted",
    ]
    pd.testing.assert_series_equal(
        original_result.match_features.loc[0, columns],
        modified_result.match_features.loc[0, columns],
    )
    pd.testing.assert_series_equal(
        original_result.match_features.loc[1, columns],
        modified_result.match_features.loc[1, columns],
    )


def test_fixture_features_use_accumulated_team_history() -> None:
    result = build_features_from_frames(
        match_ratings=_match_ratings_frame(),
        fixture_ratings=_fixture_ratings_frame(),
        config=FeatureBuildConfig(half_life_days=365.0, max_history_days=365 * 5),
    )

    fixture = result.fixture_features.iloc[0]

    assert fixture["home_history_matches_used"] == 3
    assert fixture["away_history_matches_used"] == 1
    assert fixture["home_goals_for_avg_weighted"] > 0
    assert fixture["home_attack_adjusted_elo_avg_weighted"] > 0
