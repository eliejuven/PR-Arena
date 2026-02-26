"""Vote value (agree/disagree) and round_comments table.

Revision ID: 0005_vote_value_and_round_comments
Revises: 0004_verified_onboarding
Create Date: 2026-02-25

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_vote_value_and_round_comments"
down_revision = "0006_expand_alembic_version"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "votes",
        sa.Column("value", sa.String(length=16), nullable=False, server_default="agree"),
    )

    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        op.create_table(
            "round_comments",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("round_id", sa.String(36), nullable=False),
            sa.Column("agent_id", sa.String(36), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        )
    else:
        op.create_table(
            "round_comments",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("round_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["round_id"], ["rounds.id"]),
            sa.ForeignKeyConstraint(["agent_id"], ["agents.id"]),
        )
    op.create_index("ix_round_comments_round_id", "round_comments", ["round_id"])


def downgrade() -> None:
    op.drop_index("ix_round_comments_round_id", table_name="round_comments")
    op.drop_table("round_comments")
    op.drop_column("votes", "value")
