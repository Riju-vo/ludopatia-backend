from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from predictor.infrastructure.database.session import Base


class TeamModel(Base):
    __tablename__ = "teams"

    team_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(128), nullable=False)
    fifa_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    confederation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    membership_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    model_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    aliases: Mapped[str | None] = mapped_column(Text, nullable=True)
    identity_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CompetitionModel(Base):
    __tablename__ = "competitions"

    competition_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_label: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(128), nullable=False)
    organizer_scope: Mapped[str | None] = mapped_column(String(64), nullable=True)
    competition_type: Mapped[str] = mapped_column(String(64), nullable=False)
    importance_level: Mapped[int] = mapped_column(Integer, nullable=False)
    model_scope: Mapped[str] = mapped_column(String(32), nullable=False)
    extra_time_possible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    normalization_source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class LocationModel(Base):
    __tablename__ = "locations"

    location_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    source_city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source_country: Mapped[str | None] = mapped_column(String(128), nullable=True)
    canonical_name: Mapped[str] = mapped_column(String(128), nullable=False)
    canonical_country_code: Mapped[str | None] = mapped_column(String(8), nullable=True)
    canonical_country_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    geoname_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    feature_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    resolution_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    quality_status: Mapped[str | None] = mapped_column(String(64), nullable=True)
    match_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_match_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_match_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)


class TournamentHostModel(Base):
    __tablename__ = "tournament_hosts"

    host_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    competition_id: Mapped[str] = mapped_column(
        ForeignKey("competitions.competition_id"),
        nullable=False,
    )
    edition_year: Mapped[int] = mapped_column(Integer, nullable=False)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.team_id"), nullable=False)
    host_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True)


class TournamentGroupModel(Base):
    __tablename__ = "tournament_groups"

    group_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    competition_id: Mapped[str] = mapped_column(
        ForeignKey("competitions.competition_id"),
        nullable=False,
        index=True,
    )
    edition_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    group_code: Mapped[str] = mapped_column(String(16), nullable=False)
    stage_scope: Mapped[str] = mapped_column(String(32), nullable=False, default="group_stage")
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True)


class TournamentGroupTeamModel(Base):
    __tablename__ = "tournament_group_teams"

    group_team_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[str] = mapped_column(
        ForeignKey("tournament_groups.group_id"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.team_id"), nullable=False, index=True)
    seed_position: Mapped[int] = mapped_column(Integer, nullable=False)
    source_name: Mapped[str | None] = mapped_column(String(128), nullable=True)


class MatchModel(Base):
    __tablename__ = "matches"

    match_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    kickoff_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    home_team_id: Mapped[str] = mapped_column(ForeignKey("teams.team_id"), nullable=False)
    away_team_id: Mapped[str] = mapped_column(ForeignKey("teams.team_id"), nullable=False)
    competition_id: Mapped[str] = mapped_column(
        ForeignKey("competitions.competition_id"),
        nullable=False,
    )
    location_id: Mapped[str] = mapped_column(ForeignKey("locations.location_id"), nullable=False)
    neutral: Mapped[bool] = mapped_column(Boolean, nullable=False)
    home_is_tournament_host: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    away_is_tournament_host: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    home_score_90: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_score_90: Mapped[int | None] = mapped_column(Integer, nullable=True)
    has_shootout_evidence: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_post_90_goal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    data_quality_status: Mapped[str] = mapped_column(String(64), nullable=False)
    source_name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    home_team: Mapped[TeamModel] = relationship(foreign_keys=[home_team_id])
    away_team: Mapped[TeamModel] = relationship(foreign_keys=[away_team_id])
    competition: Mapped[CompetitionModel] = relationship()
    location: Mapped[LocationModel] = relationship()


class RankingFifaModel(Base):
    __tablename__ = "rankings_fifa"

    ranking_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.team_id"), nullable=False, index=True)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    rank_position: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    previous_points: Mapped[float | None] = mapped_column(Float, nullable=True)
    confederation: Mapped[str | None] = mapped_column(String(32), nullable=True)
    source_dataset: Mapped[str | None] = mapped_column(String(255), nullable=True)
    rank_source: Mapped[str | None] = mapped_column(String(64), nullable=True)
    snapshot_external_id: Mapped[str | None] = mapped_column(String(128), nullable=True)


class EloRatingModel(Base):
    __tablename__ = "elo_ratings"

    elo_rating_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(
        ForeignKey("matches.match_id"),
        nullable=False,
        index=True,
    )
    team_id: Mapped[str] = mapped_column(ForeignKey("teams.team_id"), nullable=False, index=True)
    rating_pre: Mapped[float] = mapped_column(Float, nullable=False)
    rating_post: Mapped[float] = mapped_column(Float, nullable=False)
    matches_played_pre: Mapped[int] = mapped_column(Integer, nullable=False)
    k_factor: Mapped[float] = mapped_column(Float, nullable=False)
    margin_multiplier: Mapped[float] = mapped_column(Float, nullable=False)
    expected_score: Mapped[float] = mapped_column(Float, nullable=False)
    applied_home_advantage: Mapped[float] = mapped_column(Float, nullable=False)


class FeatureSnapshotModel(Base):
    __tablename__ = "feature_snapshots"

    snapshot_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(
        ForeignKey("matches.match_id"),
        nullable=False,
        unique=True,
        index=True,
    )
    scope: Mapped[str] = mapped_column(String(32), nullable=False, default="pre_match")
    features: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ModelVersionModel(Base):
    __tablename__ = "model_versions"

    model_version: Mapped[str] = mapped_column(String(128), primary_key=True)
    trained_at_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    model_family: Mapped[str] = mapped_column(String(128), nullable=False)
    artifact_format: Mapped[str] = mapped_column(String(64), nullable=False)
    feature_count: Mapped[int] = mapped_column(Integer, nullable=False)
    training_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    validation_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    max_training_date: Mapped[date] = mapped_column(Date, nullable=False)
    validation_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    validation_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    data_source: Mapped[str] = mapped_column(String(255), nullable=False)
    config: Mapped[dict] = mapped_column(JSON, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    artifact_files: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PredictionModel(Base):
    __tablename__ = "predictions"

    prediction_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[str] = mapped_column(
        ForeignKey("matches.match_id"),
        nullable=False,
        index=True,
    )
    model_version: Mapped[str] = mapped_column(
        ForeignKey("model_versions.model_version"),
        nullable=False,
        index=True,
    )
    predicted_home_lambda: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_away_lambda: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_total_goals: Mapped[float] = mapped_column(Float, nullable=False)
    home_win_probability: Mapped[float] = mapped_column(Float, nullable=False)
    draw_probability: Mapped[float] = mapped_column(Float, nullable=False)
    away_win_probability: Mapped[float] = mapped_column(Float, nullable=False)
    top_scoreline: Mapped[str] = mapped_column(String(32), nullable=False)
    top_scoreline_probability: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PredictionScoreMatrixModel(Base):
    __tablename__ = "prediction_score_matrices"

    prediction_score_matrix_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    prediction_id: Mapped[int] = mapped_column(
        ForeignKey("predictions.prediction_id"),
        nullable=False,
        unique=True,
        index=True,
    )
    score_labels: Mapped[list] = mapped_column(JSON, nullable=False)
    matrix: Mapped[list] = mapped_column(JSON, nullable=False)
