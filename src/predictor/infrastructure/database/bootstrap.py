import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import delete, insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from predictor.infrastructure.database.models import (
    CompetitionModel,
    EloRatingModel,
    FeatureSnapshotModel,
    LocationModel,
    MatchModel,
    ModelVersionModel,
    PredictionModel,
    PredictionScoreMatrixModel,
    RankingFifaModel,
    TeamModel,
    TournamentGroupModel,
    TournamentGroupTeamModel,
    TournamentHostModel,
)


@dataclass(frozen=True, slots=True)
class SeedDatabasePayload:
    teams: list[dict[str, Any]]
    competitions: list[dict[str, Any]]
    locations: list[dict[str, Any]]
    tournament_hosts: list[dict[str, Any]]
    tournament_groups: list[dict[str, Any]]
    tournament_group_teams: list[dict[str, Any]]
    matches: list[dict[str, Any]]
    rankings_fifa: list[dict[str, Any]]
    elo_ratings: list[dict[str, Any]]
    feature_snapshots: list[dict[str, Any]]
    model_versions: list[dict[str, Any]]
    predictions: list[dict[str, Any]]
    prediction_score_matrices: list[dict[str, Any]]
    report: dict[str, Any]


def build_seed_payload(*, data_dir: Path, model_dir: Path) -> SeedDatabasePayload:
    created_at = datetime.now(UTC)
    teams = _load_teams(data_dir)
    competitions = _load_competitions(data_dir)
    locations = _load_locations(data_dir)
    tournament_hosts = _load_tournament_hosts(data_dir)
    tournament_groups, tournament_group_teams = _load_tournament_groups(data_dir)
    matches = _load_matches(data_dir, created_at=created_at)
    rankings_fifa, ranking_report = _load_rankings_fifa(data_dir, teams=teams)
    elo_ratings = _load_elo_ratings(data_dir)
    feature_snapshots = _load_feature_snapshots(data_dir, created_at=created_at)
    model_versions = _load_model_versions(model_dir, created_at=created_at)
    predictions, prediction_score_matrices = _load_predictions(
        data_dir,
        created_at=created_at,
    )

    report = {
        "seeded_at_utc": created_at.isoformat(),
        "teams": len(teams),
        "competitions": len(competitions),
        "locations": len(locations),
        "tournament_hosts": len(tournament_hosts),
        "tournament_groups": len(tournament_groups),
        "tournament_group_teams": len(tournament_group_teams),
        "matches": len(matches),
        "rankings_fifa": len(rankings_fifa),
        "elo_ratings": len(elo_ratings),
        "feature_snapshots": len(feature_snapshots),
        "model_versions": len(model_versions),
        "predictions": len(predictions),
        "prediction_score_matrices": len(prediction_score_matrices),
        "ranking_mapping": ranking_report,
    }
    return SeedDatabasePayload(
        teams=teams,
        competitions=competitions,
        locations=locations,
        tournament_hosts=tournament_hosts,
        tournament_groups=tournament_groups,
        tournament_group_teams=tournament_group_teams,
        matches=matches,
        rankings_fifa=rankings_fifa,
        elo_ratings=elo_ratings,
        feature_snapshots=feature_snapshots,
        model_versions=model_versions,
        predictions=predictions,
        prediction_score_matrices=prediction_score_matrices,
        report=report,
    )


async def seed_database(
    *,
    factory: async_sessionmaker,
    payload: SeedDatabasePayload,
) -> dict[str, Any]:
    async with factory() as session:
        for model in (
            PredictionScoreMatrixModel,
            PredictionModel,
            ModelVersionModel,
            FeatureSnapshotModel,
            EloRatingModel,
            RankingFifaModel,
            MatchModel,
            TournamentGroupTeamModel,
            TournamentGroupModel,
            TournamentHostModel,
            LocationModel,
            CompetitionModel,
            TeamModel,
        ):
            await session.execute(delete(model))

        await session.execute(insert(TeamModel), payload.teams)
        await session.execute(insert(CompetitionModel), payload.competitions)
        await session.execute(insert(LocationModel), payload.locations)
        await session.execute(insert(TournamentHostModel), payload.tournament_hosts)
        await session.execute(insert(TournamentGroupModel), payload.tournament_groups)
        await session.execute(insert(TournamentGroupTeamModel), payload.tournament_group_teams)
        await session.execute(insert(MatchModel), payload.matches)
        await session.execute(insert(RankingFifaModel), payload.rankings_fifa)
        await session.execute(insert(EloRatingModel), payload.elo_ratings)
        await session.execute(insert(FeatureSnapshotModel), payload.feature_snapshots)
        await session.execute(insert(ModelVersionModel), payload.model_versions)
        await session.execute(insert(PredictionModel), payload.predictions)
        await session.execute(
            insert(PredictionScoreMatrixModel),
            payload.prediction_score_matrices,
        )
        await session.commit()

    return payload.report


def _load_teams(data_dir: Path) -> list[dict[str, Any]]:
    frame = (
        pd.read_csv(data_dir / "reference" / "teams.csv")
        .drop_duplicates(subset=["team_id"], keep="first")
        .fillna(value=pd.NA)
    )
    return _frame_to_records(frame)


def _load_competitions(data_dir: Path) -> list[dict[str, Any]]:
    frame = (
        pd.read_csv(data_dir / "reference" / "competitions.csv")
        .drop_duplicates(subset=["competition_id"], keep="first")
        .fillna(value=pd.NA)
    )
    return _frame_to_records(frame)


def _load_locations(data_dir: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(
        data_dir / "reference" / "locations.csv",
        parse_dates=["first_match_date", "last_match_date"],
    ).drop_duplicates(subset=["location_id"], keep="first").fillna(value=pd.NA)
    for column in ("geoname_id", "match_count"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce").astype("Int64")
    for column in ("first_match_date", "last_match_date"):
        frame[column] = frame[column].dt.date.where(frame[column].notna(), None)
    return _frame_to_records(frame)


def _load_tournament_hosts(data_dir: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(data_dir / "reference" / "tournament_hosts.csv").fillna(value=pd.NA)
    renamed = frame.rename(
        columns={
            "edition": "edition_year",
            "host_team_id": "team_id",
            "source": "source_name",
        }
    )
    renamed["edition_year"] = pd.to_numeric(
        renamed["edition_year"],
        errors="coerce",
    )
    renamed["played_year"] = pd.to_numeric(renamed["played_year"], errors="coerce")
    renamed["edition_year"] = renamed["edition_year"].fillna(renamed["played_year"]).astype("Int64")
    selected = renamed.loc[
        :,
        ["competition_id", "edition_year", "team_id", "stage_scope", "source_name"],
    ]
    return _frame_to_records(selected.rename(columns={"stage_scope": "host_role"}))


def _load_tournament_groups(
    data_dir: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    frame = pd.read_csv(data_dir / "reference" / "world_cup_2026_groups.csv").fillna(value=pd.NA)
    frame["position"] = pd.to_numeric(frame["position"], errors="coerce").astype("Int64")
    frame["group_id"] = frame["group_code"].map(
        lambda group_code: f"fifa_world_cup_2026_group_{str(group_code).lower()}"
    )

    groups = (
        frame.loc[:, ["group_id", "group_code"]]
        .drop_duplicates(subset=["group_id"], keep="first")
        .assign(
            competition_id="fifa_world_cup",
            edition_year=2026,
            stage_scope="group_stage",
            source_name="openfootball_worldcup_2026",
        )
    )
    groups = groups.loc[
        :,
        ["group_id", "competition_id", "edition_year", "group_code", "stage_scope", "source_name"],
    ]
    group_teams = frame.loc[:, ["group_id", "team_id", "position"]].rename(
        columns={"position": "seed_position"}
    )
    group_teams["source_name"] = "openfootball_worldcup_2026"
    return _frame_to_records(groups), _frame_to_records(group_teams)


def _load_matches(data_dir: Path, *, created_at: datetime) -> list[dict[str, Any]]:
    finished = pd.read_csv(data_dir / "processed" / "matches.csv", parse_dates=["kickoff_date"])
    fixtures = pd.read_csv(data_dir / "processed" / "fixtures.csv", parse_dates=["kickoff_date"])
    frame = pd.concat([finished, fixtures], ignore_index=True)
    frame["kickoff_date"] = frame["kickoff_date"].dt.date
    frame["created_at"] = created_at
    return _frame_to_records(frame)


def _load_rankings_fifa(
    data_dir: Path,
    *,
    teams: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    frame = pd.read_csv(
        data_dir / "ranking_fifa_historical_complete.csv",
        parse_dates=["date"],
        low_memory=False,
    )
    teams_frame = pd.DataFrame(teams)
    fifa_code_map = (
        teams_frame.dropna(subset=["fifa_code"])
        .drop_duplicates(subset=["fifa_code"])
        .set_index("fifa_code")["team_id"]
        .to_dict()
    )
    name_map = (
        teams_frame.drop_duplicates(subset=["canonical_name"])
        .set_index("canonical_name")["team_id"]
        .to_dict()
    )

    frame["team_id"] = frame["team_short"].map(fifa_code_map)
    missing_mask = frame["team_id"].isna()
    frame.loc[missing_mask, "team_id"] = frame.loc[missing_mask, "team"].map(name_map)

    matched = frame.loc[frame["team_id"].notna()].copy()
    matched["snapshot_date"] = matched["date"].dt.date
    matched = matched.rename(
        columns={
            "rank": "rank_position",
            "total_points": "points",
            "data_source": "source_dataset",
            "id": "snapshot_external_id",
        }
    )
    ranking_rows = matched.loc[
        :,
        [
            "team_id",
            "snapshot_date",
            "rank_position",
            "points",
            "previous_rank",
            "previous_points",
            "confederation",
            "source_dataset",
            "rank_source",
            "snapshot_external_id",
        ],
    ]
    for column in ("rank_position", "previous_rank"):
        ranking_rows[column] = pd.to_numeric(ranking_rows[column], errors="coerce").astype("Int64")
    report = {
        "source_rows": int(len(frame)),
        "mapped_rows": int(len(ranking_rows)),
        "unmapped_rows": int(len(frame) - len(ranking_rows)),
    }
    return (_frame_to_records(ranking_rows), report)


def _load_elo_ratings(data_dir: Path) -> list[dict[str, Any]]:
    frame = pd.read_csv(data_dir / "processed" / "match_ratings.csv")
    rows: list[dict[str, Any]] = []
    for record in frame.to_dict(orient="records"):
        rows.append(
            {
                "match_id": record["match_id"],
                "team_id": record["home_team_id"],
                "rating_pre": float(record["home_elo_pre"]),
                "rating_post": float(record["home_elo_post"]),
                "matches_played_pre": int(record["home_elo_matches_pre"]),
                "k_factor": float(record["k_factor"]),
                "margin_multiplier": float(record["margin_multiplier"]),
                "expected_score": float(record["expected_home_score"]),
                "applied_home_advantage": float(record["applied_home_advantage"]),
            }
        )
        rows.append(
            {
                "match_id": record["match_id"],
                "team_id": record["away_team_id"],
                "rating_pre": float(record["away_elo_pre"]),
                "rating_post": float(record["away_elo_post"]),
                "matches_played_pre": int(record["away_elo_matches_pre"]),
                "k_factor": float(record["k_factor"]),
                "margin_multiplier": float(record["margin_multiplier"]),
                "expected_score": float(1.0 - float(record["expected_home_score"])),
                "applied_home_advantage": float(-1.0 * float(record["applied_home_advantage"])),
            }
        )
    return rows


def _load_feature_snapshots(data_dir: Path, *, created_at: datetime) -> list[dict[str, Any]]:
    match_features = pd.read_csv(data_dir / "processed" / "match_features.csv")
    fixture_features = pd.read_csv(data_dir / "processed" / "fixture_features.csv")
    frame = pd.concat([match_features, fixture_features], ignore_index=True)
    rows: list[dict[str, Any]] = []
    for record in frame.to_dict(orient="records"):
        match_id = record.pop("match_id")
        rows.append(
            {
                "match_id": match_id,
                "scope": "pre_match",
                "features": _sanitize_record(record),
                "created_at": created_at,
            }
        )
    return rows


def _load_model_versions(model_dir: Path, *, created_at: datetime) -> list[dict[str, Any]]:
    version_dirs = sorted(path for path in model_dir.iterdir() if path.is_dir())
    if not version_dirs:
        raise FileNotFoundError("No trained model versions found in artifacts/models.")

    latest_version = version_dirs[-1].name
    rows: list[dict[str, Any]] = []
    for version_dir in version_dirs:
        metadata = json.loads((version_dir / "metadata.json").read_text(encoding="utf-8"))
        rows.append(
            {
                "model_version": metadata["model_version"],
                "trained_at_utc": datetime.fromisoformat(metadata["trained_at_utc"]),
                "model_family": metadata["model_family"],
                "artifact_format": metadata["artifact_format"],
                "feature_count": int(metadata["feature_count"]),
                "training_rows": int(metadata["training_rows"]),
                "validation_rows": int(metadata["validation_rows"]),
                "max_training_date": date_from_iso(metadata["max_training_date"]),
                "validation_start_date": date_from_iso(metadata["validation_start_date"]),
                "validation_end_date": date_from_iso(metadata["validation_end_date"]),
                "data_source": metadata["data_source"],
                "config": metadata["config"],
                "metrics": metadata["metrics"],
                "artifact_files": metadata.get("artifact_files"),
                "is_current": metadata["model_version"] == latest_version,
                "created_at": created_at,
            }
        )
    return rows


def _load_predictions(
    data_dir: Path,
    *,
    created_at: datetime,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    predictions = pd.read_csv(data_dir / "predictions" / "fixture_predictions.csv")
    matrices_payload = json.loads(
        (data_dir / "predictions" / "fixture_score_matrices.json").read_text(encoding="utf-8")
    )

    prediction_rows: list[dict[str, Any]] = []
    matrix_rows: list[dict[str, Any]] = []
    for prediction_id, record in enumerate(predictions.to_dict(orient="records"), start=1):
        prediction_rows.append(
            {
                "prediction_id": prediction_id,
                "match_id": record["match_id"],
                "model_version": record["model_version"],
                "predicted_home_lambda": float(record["predicted_home_lambda"]),
                "predicted_away_lambda": float(record["predicted_away_lambda"]),
                "predicted_total_goals": float(record["predicted_total_goals"]),
                "home_win_probability": float(record["home_win_probability"]),
                "draw_probability": float(record["draw_probability"]),
                "away_win_probability": float(record["away_win_probability"]),
                "top_scoreline": record["top_scoreline"],
                "top_scoreline_probability": float(record["top_scoreline_probability"]),
                "created_at": created_at,
            }
        )

    for prediction_id, payload in enumerate(matrices_payload["predictions"], start=1):
        matrix_rows.append(
            {
                "prediction_id": prediction_id,
                "score_labels": payload["score_labels"],
                "matrix": payload["matrix"],
            }
        )

    return prediction_rows, matrix_rows


def _sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    clean: dict[str, Any] = {}
    for key, value in record.items():
        if pd.isna(value):
            clean[key] = None
        elif hasattr(value, "item"):
            clean[key] = value.item()
        else:
            clean[key] = value
    return clean


def _frame_to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [_sanitize_record(record) for record in frame.to_dict(orient="records")]


def date_from_iso(value: str) -> datetime.date:
    return datetime.fromisoformat(f"{value}T00:00:00+00:00").date()
