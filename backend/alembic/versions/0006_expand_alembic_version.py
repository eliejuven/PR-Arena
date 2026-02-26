"""Expand alembic_version.version_num for long revision IDs (e.g. 0005_vote_value_and_round_comments).

Revision ID: 0006_expand_alembic_version
Revises: 0004_verified_onboarding
Create Date: 2026-02-25

Postgres creates alembic_version.version_num as VARCHAR(32); revision IDs longer than 32 chars
(e.g. 0005_vote_value_and_round_comments) cause StringDataRightTruncation on upgrade.
This migration widens the column to VARCHAR(255) on Postgres before 0005 runs.
SQLite does not enforce the same limit; no-op there.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_expand_alembic_version"
down_revision = "0004_verified_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.alter_column(
            "alembic_version",
            "version_num",
            existing_type=sa.String(32),
            type_=sa.String(255),
            existing_nullable=False,
        )
    # SQLite: no-op; it does not enforce varchar length, so long revision IDs work.


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        op.alter_column(
            "alembic_version",
            "version_num",
            existing_type=sa.String(255),
            type_=sa.String(32),
            existing_nullable=False,
        )
    # SQLite: no-op.
