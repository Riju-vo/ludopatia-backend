import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from predictor.ratings.elo import EloConfig, build_elo_history, build_fixture_elo_snapshots
from predictor.ratings.fifa import build_fifa_snapshots


@dataclass(frozen=True, slots=True)
class RatingsBuildResult:
    match_ratings: pd.DataFrame
    fixture_ratings: pd.DataFrame
    team_elo_latest: pd.DataFrame
    report: dict[str, object]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def build_ratings(
    *,
    data_dir: Path,
    elo_config: EloConfig | None = None,
) -> RatingsBuildResult:
    elo_config = elo_config or EloConfig()

    processed_dir = data_dir / "processed"
    matches = pd.read_csv(processed_dir / "matches.csv")
    fixtures = pd.read_csv(processed_dir / "fixtures.csv")
    competitions = pd.read_csv(data_dir / "reference" / "competitions.csv")
    teams = pd.read_csv(data_dir / "reference" / "teams.csv")
    rankings = pd.read_csv(data_dir / "ranking_fifa_historical_complete.csv", low_memory=False)

    match_elo = build_elo_history(matches, competitions, elo_config)
    fixture_elo = build_fixture_elo_snapshots(fixtures, match_elo, elo_config)

    match_fifa = build_fifa_snapshots(matches, teams, rankings)
    fixture_fifa = build_fifa_snapshots(fixtures, teams, rankings)
    match_fifa.snapshots["kickoff_date"] = pd.to_datetime(
        match_fifa.snapshots["kickoff_date"]
    ).dt.strftime("%Y-%m-%d")
    fixture_fifa.snapshots["kickoff_date"] = pd.to_datetime(
        fixture_fifa.snapshots["kickoff_date"]
    ).dt.strftime("%Y-%m-%d")

    match_ratings = matches.merge(
        match_elo.drop(columns=["home_team_id", "away_team_id"]),
        on=["match_id", "kickoff_date"],
        how="left",
    ).merge(
        match_fifa.snapshots.drop(columns=["home_team_id", "away_team_id"]),
        on=["match_id", "kickoff_date"],
        how="left",
    )

    fixture_ratings = fixtures.merge(
        fixture_elo.drop(columns=["home_team_id", "away_team_id"]),
        on=["match_id", "kickoff_date"],
        how="left",
    ).merge(
        fixture_fifa.snapshots.drop(columns=["home_team_id", "away_team_id"]),
        on=["match_id", "kickoff_date"],
        how="left",
    )

    team_latest_rows = []
    if not match_elo.empty:
        latest_match = match_elo.sort_values(["kickoff_date", "match_id"])
        latest_ratings: dict[str, dict[str, object]] = {}
        for row in latest_match.itertuples(index=False):
            latest_ratings[row.home_team_id] = {
                "team_id": row.home_team_id,
                "latest_match_id": row.match_id,
                "latest_kickoff_date": row.kickoff_date,
                "elo_current": row.home_elo_post,
                "elo_matches_played": row.home_elo_matches_pre + 1,
            }
            latest_ratings[row.away_team_id] = {
                "team_id": row.away_team_id,
                "latest_match_id": row.match_id,
                "latest_kickoff_date": row.kickoff_date,
                "elo_current": row.away_elo_post,
                "elo_matches_played": row.away_elo_matches_pre + 1,
            }
        team_latest_rows = list(latest_ratings.values())
    team_elo_latest = pd.DataFrame(team_latest_rows).sort_values("team_id").reset_index(drop=True)

    report = {
        "elo_config": {
            "initial_rating": elo_config.initial_rating,
            "home_advantage": elo_config.home_advantage,
        },
        "match_ratings_rows": int(len(match_ratings)),
        "fixture_ratings_rows": int(len(fixture_ratings)),
        "team_elo_latest_rows": int(len(team_elo_latest)),
        "match_fifa_coverage": match_fifa.coverage,
        "fixture_fifa_coverage": fixture_fifa.coverage,
    }
    return RatingsBuildResult(
        match_ratings=match_ratings,
        fixture_ratings=fixture_ratings,
        team_elo_latest=team_elo_latest,
        report=report,
    )


def write_ratings_result(result: RatingsBuildResult, *, data_dir: Path) -> None:
    processed_dir = data_dir / "processed"
    reports_dir = data_dir / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    match_ratings_path = processed_dir / "match_ratings.csv"
    fixture_ratings_path = processed_dir / "fixture_ratings.csv"
    team_elo_latest_path = processed_dir / "team_elo_latest.csv"
    report_path = reports_dir / "ratings_quality.json"

    result.match_ratings.to_csv(match_ratings_path, index=False)
    result.fixture_ratings.to_csv(fixture_ratings_path, index=False)
    result.team_elo_latest.to_csv(team_elo_latest_path, index=False)

    result.report["output_files"] = {
        "match_ratings": {
            "path": "data/processed/match_ratings.csv",
            "sha256": _sha256(match_ratings_path),
        },
        "fixture_ratings": {
            "path": "data/processed/fixture_ratings.csv",
            "sha256": _sha256(fixture_ratings_path),
        },
        "team_elo_latest": {
            "path": "data/processed/team_elo_latest.csv",
            "sha256": _sha256(team_elo_latest_path),
        },
    }

    report_path.write_text(
        json.dumps(result.report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
