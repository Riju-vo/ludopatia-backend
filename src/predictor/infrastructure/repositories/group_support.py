from collections.abc import Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd

WORLD_CUP_COMPETITION_ID = "fifa_world_cup"


def load_world_cup_group_members(*, data_dir: Path, teams: pd.DataFrame) -> pd.DataFrame:
    base = pd.read_csv(data_dir / "reference" / "world_cup_2026_groups.csv")
    enriched = base.merge(
        teams.loc[
            :,
            [
                "team_id",
                "team_name",
                "team_fifa_code",
                "team_confederation",
            ],
        ],
        on="team_id",
        how="left",
    )
    return enriched.sort_values(["group_code", "position"]).reset_index(drop=True)


def build_world_cup_groups_payload(
    *,
    group_members: pd.DataFrame,
    fixtures: pd.DataFrame,
    prediction_lookup: Mapping[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    membership = group_members.set_index("team_id")["group_code"].to_dict()
    group_fixtures = fixtures.loc[
        fixtures["competition_id"] == WORLD_CUP_COMPETITION_ID
    ].copy()
    group_fixtures["home_group_code"] = group_fixtures["home_team_id"].map(membership)
    group_fixtures["away_group_code"] = group_fixtures["away_team_id"].map(membership)
    group_fixtures = group_fixtures.loc[
        group_fixtures["home_group_code"].notna()
        & (group_fixtures["home_group_code"] == group_fixtures["away_group_code"])
    ].copy()
    group_fixtures["group_code"] = group_fixtures["home_group_code"]
    group_fixtures = group_fixtures.sort_values(["group_code", "kickoff_date", "match_id"])
    group_fixtures["matchday"] = group_fixtures.groupby("group_code").cumcount() // 2 + 1

    groups: list[dict[str, Any]] = []
    for group_code, team_rows in group_members.groupby("group_code", sort=True):
        fixtures_rows = group_fixtures.loc[group_fixtures["group_code"] == group_code]
        groups.append(
            {
                "group_code": group_code,
                "teams": [_serialize_group_team(row) for _, row in team_rows.iterrows()],
                "fixtures": [
                    _serialize_group_fixture(
                        row,
                        prediction=prediction_lookup.get(row["match_id"]),
                    )
                    for _, row in fixtures_rows.iterrows()
                ],
            }
        )

    return groups


def _serialize_group_team(row: pd.Series) -> dict[str, Any]:
    return {
        "position_seed": int(row["position"]),
        "team": {
            "team_id": row["team_id"],
            "name": row["team_name"],
            "fifa_code": row["team_fifa_code"],
            "confederation": row["team_confederation"],
        },
        "table": {
            "played": 0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_for": 0,
            "goals_against": 0,
            "goal_difference": 0,
            "points": 0,
        },
    }


def _serialize_group_fixture(
    row: pd.Series,
    *,
    prediction: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "match_id": row["match_id"],
        "matchday": int(row["matchday"]),
        "kickoff_date": _to_iso_date(row["kickoff_date"]),
        "status": row["status"],
        "location": {
            "location_id": row["location_id"],
            "name": row["location_name"],
            "country": row["location_country"],
            "timezone": row["timezone"],
        },
        "home_team": {
            "team_id": row["home_team_id"],
            "name": row["home_team_name"],
            "fifa_code": row["home_team_fifa_code"],
            "confederation": row["home_team_confederation"],
        },
        "away_team": {
            "team_id": row["away_team_id"],
            "name": row["away_team_name"],
            "fifa_code": row["away_team_fifa_code"],
            "confederation": row["away_team_confederation"],
        },
        "prediction": _serialize_prediction_summary(prediction),
    }


def _serialize_prediction_summary(
    prediction: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if prediction is None:
        return None
    return {
        "model_version": prediction["model_version"],
        "home_win_probability": float(prediction["home_win_probability"]),
        "draw_probability": float(prediction["draw_probability"]),
        "away_win_probability": float(prediction["away_win_probability"]),
        "top_scoreline": prediction["top_scoreline"],
        "top_scoreline_probability": float(prediction["top_scoreline_probability"]),
    }


def _to_iso_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return pd.to_datetime(value).date().isoformat()
