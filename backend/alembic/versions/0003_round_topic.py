"""Add topic and proposer to rounds.

Revision ID: 0003_round_topic
Revises: 0002_arena_game
Create Date: 2026-02-24

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_round_topic"
down_revision = "0002_arena_game"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rounds",
        sa.Column("topic", sa.Text(), nullable=False, server_default="General"),
    )
    # Use dialect-appropriate type for UUID column (SQLite has no native UUID)
    conn = op.get_bind()
    if conn.dialect.name == "sqlite":
        op.add_column(
            "rounds",
            sa.Column("proposer_agent_id", sa.String(36), nullable=True),
        )
    else:
        op.add_column(
            "rounds",
            sa.Column("proposer_agent_id", postgresql.UUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_rounds_proposer_agent_id",
            "rounds",
            "agents",
            ["proposer_agent_id"],
            ["id"],
        )
    op.create_index("ix_rounds_status", "rounds", ["status"])


def downgrade() -> None:
    op.drop_index("ix_rounds_status", table_name="rounds")
    conn = op.get_bind()
    if conn.dialect.name != "sqlite":
        op.drop_constraint("fk_rounds_proposer_agent_id", "rounds", type_="foreignkey")
    op.drop_column("rounds", "proposer_agent_id")
    op.drop_column("rounds", "topic")
