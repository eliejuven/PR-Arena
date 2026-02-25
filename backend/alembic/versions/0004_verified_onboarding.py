"""Add verified onboarding: agents is_verified/verified_at, agent_onboarding table.

Revision ID: 0004_verified_onboarding
Revises: 0003_round_topic
Create Date: 2026-02-24

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_verified_onboarding"
down_revision = "0003_round_topic"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Agents: add is_verified, verified_at; make api_key_hash nullable for onboarding
    op.add_column(
        "agents",
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "agents",
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Existing agents are considered verified (they have api_key from legacy register)
    op.execute("UPDATE agents SET is_verified = true")

    # agent_onboarding table
    op.create_table(
        "agent_onboarding",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("human_token", sa.String(length=255), nullable=False),
        sa.Column("claim_token", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("human_token", name="uq_agent_onboarding_human_token"),
        sa.UniqueConstraint("claim_token", name="uq_agent_onboarding_claim_token"),
    )
    op.create_index("ix_agent_onboarding_agent_id", "agent_onboarding", ["agent_id"])
    op.create_index("ix_agent_onboarding_claim_token", "agent_onboarding", ["claim_token"])
    op.create_index("ix_agent_onboarding_human_token", "agent_onboarding", ["human_token"])


def downgrade() -> None:
    op.drop_index("ix_agent_onboarding_human_token", table_name="agent_onboarding")
    op.drop_index("ix_agent_onboarding_claim_token", table_name="agent_onboarding")
    op.drop_index("ix_agent_onboarding_agent_id", table_name="agent_onboarding")
    op.drop_table("agent_onboarding")
    op.drop_column("agents", "verified_at")
    op.drop_column("agents", "is_verified")
