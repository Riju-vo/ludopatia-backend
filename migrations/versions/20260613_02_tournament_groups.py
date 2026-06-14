"""Add tournament groups persistence.

Revision ID: 20260613_02
Revises: 20260613_01
Create Date: 2026-06-13 17:20:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260613_02"
down_revision: str | None = "20260613_01"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tournament_groups",
        sa.Column("group_id", sa.String(length=64), primary_key=True),
        sa.Column("competition_id", sa.String(length=64), nullable=False),
        sa.Column("edition_year", sa.Integer(), nullable=False),
        sa.Column("group_code", sa.String(length=16), nullable=False),
        sa.Column("stage_scope", sa.String(length=32), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["competition_id"], ["competitions.competition_id"]),
    )
    op.create_index(
        "ix_tournament_groups_competition_id",
        "tournament_groups",
        ["competition_id"],
    )
    op.create_index(
        "ix_tournament_groups_edition_year",
        "tournament_groups",
        ["edition_year"],
    )

    op.create_table(
        "tournament_group_teams",
        sa.Column("group_team_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("group_id", sa.String(length=64), nullable=False),
        sa.Column("team_id", sa.String(length=64), nullable=False),
        sa.Column("seed_position", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["tournament_groups.group_id"]),
        sa.ForeignKeyConstraint(["team_id"], ["teams.team_id"]),
    )
    op.create_index(
        "ix_tournament_group_teams_group_id",
        "tournament_group_teams",
        ["group_id"],
    )
    op.create_index(
        "ix_tournament_group_teams_team_id",
        "tournament_group_teams",
        ["team_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_tournament_group_teams_team_id", table_name="tournament_group_teams")
    op.drop_index("ix_tournament_group_teams_group_id", table_name="tournament_group_teams")
    op.drop_table("tournament_group_teams")
    op.drop_index("ix_tournament_groups_edition_year", table_name="tournament_groups")
    op.drop_index("ix_tournament_groups_competition_id", table_name="tournament_groups")
    op.drop_table("tournament_groups")
