import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Round(Base):
    __tablename__ = "rounds"
    __table_args__ = (Index("ix_rounds_status", "status"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    status: Mapped[str] = mapped_column(String(length=16), nullable=False)  # "open" or "closed"
    round_number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False, default="General", server_default="General")
    proposer_agent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=True,
    )

    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="round")
    proposer_agent: Mapped[Optional["Agent"]] = relationship("Agent")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("round_id", "agent_id", name="uq_submissions_round_agent"),
        Index("ix_submissions_round_id", "round_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    round_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rounds.id"),
        nullable=False,
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id"),
        nullable=False,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    round: Mapped["Round"] = relationship("Round", back_populates="submissions")
    agent: Mapped["Agent"] = relationship("Agent")
    votes: Mapped[list["Vote"]] = relationship("Vote", back_populates="submission")


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("submission_id", "voter_key", name="uq_votes_submission_voter"),
        Index("ix_votes_submission_id", "submission_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submissions.id"),
        nullable=False,
    )
    voter_key: Mapped[str] = mapped_column(String(length=255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="votes")

