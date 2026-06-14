"""Initial persistence schema for predictor backend.

Revision ID: 20260613_01
Revises:
Create Date: 2026-06-13 15:30:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260613_01"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "teams",
        sa.Column("team_id", sa.String(length=64), primary_key=True),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("canonical_name", sa.String(length=128), nullable=False),
        sa.Column("fifa_code", sa.String(length=8), nullable=True),
        sa.Column("confederation", sa.String(length=32), nullable=True),
        sa.Column("membership_status", sa.String(length=64), nullable=True),
        sa.Column("model_scope", sa.String(length=32), nullable=False),
        sa.Column("aliases", sa.Text(), nullable=True),
        sa.Column("identity_source", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_table(
        "competitions",
        sa.Column("competition_id", sa.String(length=64), primary_key=True),
        sa.Column("source_label", sa.String(length=128), nullable=False),
        sa.Column("canonical_name", sa.String(length=128), nullable=False),
        sa.Column("organizer_scope", sa.String(length=64), nullable=True),
        sa.Column("competition_type", sa.String(length=64), nullable=False),
        sa.Column("importance_level", sa.Integer(), nullable=False),
        sa.Column("model_scope", sa.String(length=32), nullable=False),
        sa.Column("extra_time_possible", sa.Boolean(), nullable=False),
        sa.Column("normalization_source", sa.String(length=255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )

    op.create_table(
        "locations",
        sa.Column("location_id", sa.String(length=64), primary_key=True),
        sa.Column("source_city", sa.String(length=128), nullable=True),
        sa.Column("source_country", sa.String(length=128), nullable=True),
        sa.Column("canonical_name", sa.String(length=128), nullable=False),
        sa.Column("canonical_country_code", sa.String(length=8), nullable=True),
        sa.Column("canonical_country_name", sa.String(length=128), nullable=True),
        sa.Column("geoname_id", sa.Integer(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=True),
        sa.Column("feature_code", sa.String(length=32), nullable=True),
        sa.Column("resolution_method", sa.String(length=64), nullable=True),
        sa.Column("quality_status", sa.String(length=64), nullable=True),
        sa.Column("match_count", sa.Integer(), nullable=True),
        sa.Column("first_match_date", sa.Date(), nullable=True),
        sa.Column("last_match_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=255), nullable=True),
    )

    op.create_table(
        "tournament_hosts",
        sa.Column("host_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("competition_id", sa.String(length=64), nullable=False),
        sa.Column("edition_year", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.Column("host_role", sa.String(length=64), nullable=True),
        sa.Column("source_name", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.competition_id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"]),
    )

    op.create_table(
        "matches",
        sa.Column("match_id", sa.String(length=64), primary_key=True),
        sa.Column("kickoff_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("home_team_id", sa.String(length=64), nullable=False),
        sa.Column("away_team_id", sa.String(length=64), nullable=False),
        sa.Column("competition_id", sa.String(length=64), nullable=False),
        sa.Column("location_id", sa.String(length=64), nullable=False),
        sa.Column("neutral", sa.Boolean(), nullable=False),
        sa.Column("home_is_tournament_host", sa.Boolean(), nullable=False),
        sa.Column("away_is_tournament_host", sa.Boolean(), nullable=False),
        sa.Column("home_score_90", sa.Integer(), nullable=True),
        sa.Column("away_score_90", sa.Integer(), nullable=True),
        sa.Column("has_shootout_evidence", sa.Boolean(), nullable=False),
        sa.Column("has_post_90_goal", sa.Boolean(), nullable=False),
        sa.Column("data_quality_status", sa.String(length=64), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["away_team_id"], ["teams.team_id"]),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.competition_id"]),
        sa.ForeignKeyConstraint(["home_team_id"], ["teams.team_id"]),
        sa.ForeignKeyConstraint(["location_id"], ["locations.location_id"]),
    )
    op.create_index("ix_matches_kickoff_date", "matches", ["kickoff_date"])
    op.create_index("ix_matches_status", "matches", ["status"])

    op.create_table(
        "rankings_fifa",
        sa.Column("ranking_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("rank_position", sa.Integer(), nullable=True),
        sa.Column("points", sa.Float(), nullable=True),
        sa.Column("previous_rank", sa.Integer(), nullable=True),
        sa.Column("previous_points", sa.Float(), nullable=True),
        sa.Column("confederation", sa.String(length=32), nullable=True),
        sa.Column("source_dataset", sa.String(length=255), nullable=True),
        sa.Column("rank_source", sa.String(length=64), nullable=True),
        sa.Column("snapshot_external_id", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"]),
    )
    op.create_index("ix_rankings_fifa_team_id", "rankings_fifa", ["team_id"])
    op.create_index("ix_rankings_fifa_snapshot_date", "rankings_fifa", ["snapshot_date"])

    op.create_table(
        "elo_ratings",
        sa.Column("elo_rating_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("match_id", sa.String(length=64), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.Column("rating_pre", sa.Float(), nullable=False),
        sa.Column("rating_post", sa.Float(), nullable=False),
        sa.Column("matches_played_pre", sa.Integer(), nullable=False),
        sa.Column("k_factor", sa.Float(), nullable=False),
        sa.Column("margin_multiplier", sa.Float(), nullable=False),
        sa.Column("expected_score", sa.Float(), nullable=False),
        sa.Column("applied_home_advantage", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"]),
    )
    op.create_index("ix_elo_ratings_match_id", "elo_ratings", ["match_id"])
    op.create_index("ix_elo_ratings_team_id", "elo_ratings", ["team_id"])

    op.create_table(
        "feature_snapshots",
        sa.Column("snapshot_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("match_id", sa.String(length=64), nullable=False),
        sa.Column("scope", sa.String(length=32), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.UniqueConstraint("match_id"),
    )
    op.create_index("ix_feature_snapshots_match_id", "feature_snapshots", ["match_id"])

    op.create_table(
        "model_versions",
        sa.Column("model_version", sa.String(length=128), primary_key=True),
        sa.Column("trained_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_family", sa.String(length=128), nullable=False),
        sa.Column("artifact_format", sa.String(length=64), nullable=False),
        sa.Column("feature_count", sa.Integer(), nullable=False),
        sa.Column("training_rows", sa.Integer(), nullable=False),
        sa.Column("validation_rows", sa.Integer(), nullable=False),
        sa.Column("max_training_date", sa.Date(), nullable=False),
        sa.Column("validation_start_date", sa.Date(), nullable=False),
        sa.Column("validation_end_date", sa.Date(), nullable=False),
        sa.Column("data_source", sa.String(length=255), nullable=False),
        sa.Column("config", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=False),
        sa.Column("artifact_files", sa.JSON(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_model_versions_is_current", "model_versions", ["is_current"])

    op.create_table(
        "predictions",
        sa.Column("prediction_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("match_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=128), nullable=False),
        sa.Column("predicted_home_lambda", sa.Float(), nullable=False),
        sa.Column("predicted_away_lambda", sa.Float(), nullable=False),
        sa.Column("predicted_total_goals", sa.Float(), nullable=False),
        sa.Column("home_win_probability", sa.Float(), nullable=False),
        sa.Column("draw_probability", sa.Float(), nullable=False),
        sa.Column("away_win_probability", sa.Float(), nullable=False),
        sa.Column("top_scoreline", sa.String(length=32), nullable=False),
        sa.Column("top_scoreline_probability", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["match_id"], ["matches.match_id"]),
        sa.ForeignKeyConstraint(["model_version"], ["model_versions.model_version"]),
    )
    op.create_index("ix_predictions_match_id", "predictions", ["match_id"])
    op.create_index("ix_predictions_model_version", "predictions", ["model_version"])

    op.create_table(
        "prediction_score_matrices",
        sa.Column(
            "prediction_score_matrix_id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
        ),
        sa.Column("prediction_id", sa.Integer(), nullable=False),
        sa.Column("score_labels", sa.JSON(), nullable=False),
        sa.Column("matrix", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["prediction_id"], ["predictions.prediction_id"]),
        sa.UniqueConstraint("prediction_id"),
    )
    op.create_index(
        "ix_prediction_score_matrices_prediction_id",
        "prediction_score_matrices",
        ["prediction_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_prediction_score_matrices_prediction_id",
        table_name="prediction_score_matrices",
    )
    op.drop_table("prediction_score_matrices")
    op.drop_index("ix_predictions_model_version", table_name="predictions")
    op.drop_index("ix_predictions_match_id", table_name="predictions")
    op.drop_table("predictions")
    op.drop_index("ix_model_versions_is_current", table_name="model_versions")
    op.drop_table("model_versions")
    op.drop_index("ix_feature_snapshots_match_id", table_name="feature_snapshots")
    op.drop_table("feature_snapshots")
    op.drop_index("ix_elo_ratings_team_id", table_name="elo_ratings")
    op.drop_index("ix_elo_ratings_match_id", table_name="elo_ratings")
    op.drop_table("elo_ratings")
    op.drop_index("ix_rankings_fifa_snapshot_date", table_name="rankings_fifa")
    op.drop_index("ix_rankings_fifa_team_id", table_name="rankings_fifa")
    op.drop_table("rankings_fifa")
    op.drop_index("ix_matches_status", table_name="matches")
    op.drop_index("ix_matches_kickoff_date", table_name="matches")
    op.drop_table("matches")
    op.drop_table("tournament_hosts")
    op.drop_table("locations")
    op.drop_table("competitions")
    op.drop_table("teams")
