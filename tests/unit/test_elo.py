import pandas as pd

from predictor.ratings.elo import EloConfig, build_elo_history


def test_elo_pre_match_is_not_affected_by_future_results() -> None:
    competitions = pd.DataFrame(
        [
            {"competition_id": "friendly", "importance_level": 1},
        ]
    )
    base_matches = pd.DataFrame(
        [
            {
                "match_id": "m1",
                "kickoff_date": "2021-01-01",
                "home_team_id": "A",
                "away_team_id": "B",
                "competition_id": "friendly",
                "neutral": False,
                "home_score_90": 1,
                "away_score_90": 0,
            },
            {
                "match_id": "m2",
                "kickoff_date": "2021-01-10",
                "home_team_id": "B",
                "away_team_id": "A",
                "competition_id": "friendly",
                "neutral": False,
                "home_score_90": 0,
                "away_score_90": 1,
            },
        ]
    )
    changed_future = base_matches.copy()
    changed_future.loc[1, "home_score_90"] = 5
    changed_future.loc[1, "away_score_90"] = 0

    original = build_elo_history(base_matches, competitions, EloConfig())
    modified = build_elo_history(changed_future, competitions, EloConfig())

    assert original.loc[0, "home_elo_pre"] == modified.loc[0, "home_elo_pre"]
    assert original.loc[0, "away_elo_pre"] == modified.loc[0, "away_elo_pre"]
    assert original.loc[0, "home_elo_post"] == modified.loc[0, "home_elo_post"]
