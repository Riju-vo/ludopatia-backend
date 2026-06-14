import pandas as pd

from predictor.ratings.fifa import build_fifa_snapshots


def test_fifa_snapshots_use_last_publication_before_match() -> None:
    matches = pd.DataFrame(
        [
            {
                "match_id": "m1",
                "kickoff_date": "2024-10-01",
                "home_team_id": "fifa_arg",
                "away_team_id": "fifa_bra",
            }
        ]
    )
    teams = pd.DataFrame(
        [
            {"team_id": "fifa_arg", "fifa_code": "ARG"},
            {"team_id": "fifa_bra", "fifa_code": "BRA"},
        ]
    )
    rankings = pd.DataFrame(
        [
            {
                "team_short": "ARG",
                "date": "2024-09-19",
                "id": "id1",
                "team": "Argentina",
                "total_points": 10,
                "rank": 1,
                "previous_rank": 1,
                "previous_points": 9,
                "confederation": "CONMEBOL",
            },
            {
                "team_short": "ARG",
                "date": "2024-10-24",
                "id": "id2",
                "team": "Argentina",
                "total_points": 11,
                "rank": 1,
                "previous_rank": 1,
                "previous_points": 10,
                "confederation": "CONMEBOL",
            },
            {
                "team_short": "BRA",
                "date": "2024-09-19",
                "id": "id1",
                "team": "Brazil",
                "total_points": 8,
                "rank": 5,
                "previous_rank": 6,
                "previous_points": 7,
                "confederation": "CONMEBOL",
            },
            {
                "team_short": "BRA",
                "date": "2024-10-24",
                "id": "id2",
                "team": "Brazil",
                "total_points": 12,
                "rank": 2,
                "previous_rank": 5,
                "previous_points": 8,
                "confederation": "CONMEBOL",
            },
        ]
    )

    result = build_fifa_snapshots(matches, teams, rankings)
    row = result.snapshots.iloc[0]

    assert str(row["home_ranking_snapshot_date"].date()) == "2024-09-19"
    assert str(row["away_ranking_snapshot_date"].date()) == "2024-09-19"
    assert row["home_fifa_points_pre"] == 10
    assert row["away_fifa_points_pre"] == 8
