from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class FifaSnapshotBuildResult:
    snapshots: pd.DataFrame
    coverage: dict[str, int]


def build_fifa_snapshots(
    matches: pd.DataFrame,
    teams: pd.DataFrame,
    rankings: pd.DataFrame,
) -> FifaSnapshotBuildResult:
    team_codes = (
        teams.loc[:, ["team_id", "fifa_code"]]
        .drop_duplicates(subset=["team_id"])
        .set_index("team_id")["fifa_code"]
    )

    ranking_frame = rankings.copy()
    ranking_frame["date"] = pd.to_datetime(ranking_frame["date"])
    ranking_frame["total_points"] = pd.to_numeric(ranking_frame["total_points"], errors="coerce")
    ranking_frame["rank"] = pd.to_numeric(ranking_frame["rank"], errors="coerce")
    ranking_frame = ranking_frame.sort_values(["team_short", "date"]).reset_index(drop=True)

    base = matches.loc[:, ["match_id", "kickoff_date", "home_team_id", "away_team_id"]].copy()
    base["kickoff_date"] = pd.to_datetime(base["kickoff_date"])

    rows = []
    for side in ("home", "away"):
        side_frame = base.loc[:, ["match_id", "kickoff_date", f"{side}_team_id"]].copy()
        side_frame = side_frame.rename(columns={f"{side}_team_id": "team_id"})
        side_frame["side"] = side
        side_frame["fifa_code"] = side_frame["team_id"].map(team_codes)
        rows.append(side_frame)
    long_frame = pd.concat(rows, ignore_index=True)
    long_frame = long_frame.sort_values(["fifa_code", "kickoff_date", "match_id"]).reset_index(
        drop=True
    )

    merged_parts: list[pd.DataFrame] = []

    no_code = long_frame[long_frame["fifa_code"].isna()].copy()
    if not no_code.empty:
        for column in ranking_frame.columns:
            if column not in no_code.columns:
                no_code[column] = pd.NA
        merged_parts.append(no_code)

    with_code = long_frame[long_frame["fifa_code"].notna()].copy()
    for fifa_code, left_group in with_code.groupby("fifa_code", sort=False):
        right_group = ranking_frame.loc[ranking_frame["team_short"] == fifa_code].copy()
        left_group = left_group.sort_values(["kickoff_date", "match_id"]).reset_index(drop=True)
        right_group = right_group.sort_values("date").reset_index(drop=True)
        merged_group = pd.merge_asof(
            left_group,
            right_group,
            left_on="kickoff_date",
            right_on="date",
            direction="backward",
            allow_exact_matches=True,
        )
        merged_parts.append(merged_group)

    merged = pd.concat(merged_parts, ignore_index=True)
    merged = merged.sort_values(["match_id", "side"]).reset_index(drop=True)
    merged["ranking_age_days"] = (merged["kickoff_date"] - merged["date"]).dt.days

    renamed = merged.rename(
        columns={
            "fifa_code": "team_fifa_code",
            "date": "ranking_snapshot_date",
            "id": "ranking_snapshot_id",
            "total_points": "fifa_points_pre",
            "rank": "fifa_rank_pre",
        }
    )

    home = (
        renamed.loc[renamed["side"] == "home"]
        .drop(columns=["side"])
        .rename(
            columns={
                "team_id": "home_team_id",
                "team_fifa_code": "home_fifa_code",
                "team": "home_fifa_team_name",
                "ranking_snapshot_date": "home_ranking_snapshot_date",
                "ranking_snapshot_id": "home_ranking_snapshot_id",
                "fifa_points_pre": "home_fifa_points_pre",
                "fifa_rank_pre": "home_fifa_rank_pre",
                "ranking_age_days": "home_ranking_age_days",
                "previous_rank": "home_previous_rank",
                "previous_points": "home_previous_points",
                "confederation": "home_fifa_confederation",
                "data_source": "home_fifa_data_source",
                "rank_source": "home_fifa_rank_source",
            }
        )
    )
    away = (
        renamed.loc[renamed["side"] == "away"]
        .drop(columns=["side"])
        .rename(
            columns={
                "team_id": "away_team_id",
                "team_fifa_code": "away_fifa_code",
                "team": "away_fifa_team_name",
                "ranking_snapshot_date": "away_ranking_snapshot_date",
                "ranking_snapshot_id": "away_ranking_snapshot_id",
                "fifa_points_pre": "away_fifa_points_pre",
                "fifa_rank_pre": "away_fifa_rank_pre",
                "ranking_age_days": "away_ranking_age_days",
                "previous_rank": "away_previous_rank",
                "previous_points": "away_previous_points",
                "confederation": "away_fifa_confederation",
                "data_source": "away_fifa_data_source",
                "rank_source": "away_fifa_rank_source",
            }
        )
    )

    snapshots = home.merge(away, on=["match_id", "kickoff_date"], how="inner")
    drop_columns = [column for column in snapshots.columns if column.startswith("team_short_")]
    if drop_columns:
        snapshots = snapshots.drop(columns=drop_columns)
    snapshots["fifa_points_difference_pre"] = (
        snapshots["home_fifa_points_pre"] - snapshots["away_fifa_points_pre"]
    )
    snapshots["fifa_rank_difference_pre"] = (
        snapshots["away_fifa_rank_pre"] - snapshots["home_fifa_rank_pre"]
    )

    coverage = {
        "rows": int(len(snapshots)),
        "home_with_points": int(snapshots["home_fifa_points_pre"].notna().sum()),
        "away_with_points": int(snapshots["away_fifa_points_pre"].notna().sum()),
        "complete_rows": int(
            snapshots["home_fifa_points_pre"]
            .notna()
            .mul(snapshots["away_fifa_points_pre"].notna())
            .sum()
        ),
    }
    return FifaSnapshotBuildResult(snapshots=snapshots, coverage=coverage)
