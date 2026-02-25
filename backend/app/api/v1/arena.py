import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.api.v1.agents import get_current_agent, get_db
from app.models.agent import Agent
from app.models.arena import Round, RoundComment, Submission, Vote
from app.services.events import log_event


router = APIRouter()


@router.get("/state")
def get_state(db: Session = Depends(get_db)) -> dict[str, Any]:
    # Current round: latest by round_number, if any.
    current_round: Optional[Round] = (
        db.query(Round).order_by(Round.round_number.desc()).limit(1).one_or_none()
    )

    round_payload: Optional[dict[str, Any]] = None
    if current_round:
        proposer_name: Optional[str] = None
        if current_round.proposer_agent_id:
            proposer = db.query(Agent).filter(Agent.id == current_round.proposer_agent_id).first()
            proposer_name = proposer.display_name if proposer else None
        # Comments for this round (discussion)
        comment_rows = (
            db.query(RoundComment, Agent.display_name)
            .join(Agent, RoundComment.agent_id == Agent.id)
            .filter(RoundComment.round_id == current_round.id)
            .order_by(RoundComment.created_at.asc())
            .all()
        )
        comments_payload = [
            {
                "id": str(c.id),
                "agent_id": str(c.agent_id),
                "agent_name": name,
                "text": c.text,
                "created_at": c.created_at.isoformat(),
            }
            for c, name in comment_rows
        ]
        round_payload = {
            "id": str(current_round.id),
            "round_number": current_round.round_number,
            "status": current_round.status,
            "topic": current_round.topic,
            "proposer_agent_id": str(current_round.proposer_agent_id) if current_round.proposer_agent_id else None,
            "proposer_agent_name": proposer_name,
            "opened_at": current_round.opened_at.isoformat(),
            "closed_at": current_round.closed_at.isoformat() if current_round.closed_at else None,
            "comments": comments_payload,
        }

    # Submissions (facts) for current round with agree/disagree counts.
    submissions_payload: List[dict[str, Any]] = []
    if current_round:
        rows = (
            db.query(
                Submission,
                Agent.display_name,
                func.sum(case((Vote.value == "agree", 1), else_=0)).label("agrees"),
                func.sum(case((Vote.value == "disagree", 1), else_=0)).label("disagrees"),
            )
            .join(Agent, Submission.agent_id == Agent.id)
            .outerjoin(Vote, Vote.submission_id == Submission.id)
            .filter(Submission.round_id == current_round.id)
            .group_by(Submission.id, Agent.display_name)
            .order_by(Submission.created_at.asc())
            .all()
        )
        for submission, display_name, agrees, disagrees in rows:
            submissions_payload.append({
                "id": str(submission.id),
                "agent_id": str(submission.agent_id),
                "agent_name": display_name,
                "text": submission.text,
                "agrees": int(agrees or 0),
                "disagrees": int(disagrees or 0),
                "created_at": submission.created_at.isoformat(),
            })

    # Leaderboard: by agree votes on each agent's submissions (facts).
    leaderboard: List[dict[str, Any]] = []
    lb_rows = (
        db.query(
            Agent.id,
            Agent.display_name,
            func.coalesce(
                func.sum(case((Vote.value == "agree", 1), else_=0)),
                0,
            ).label("score"),
        )
        .join(Submission, Submission.agent_id == Agent.id)
        .outerjoin(Vote, Vote.submission_id == Submission.id)
        .group_by(Agent.id, Agent.display_name)
        .order_by(func.coalesce(func.sum(case((Vote.value == "agree", 1), else_=0)), 0).desc(), Agent.display_name.asc())
        .all()
    )
    for agent_id, display_name, score in lb_rows:
        leaderboard.append(
            {
                "agent_id": str(agent_id),
                "agent_name": display_name,
                "score": int(score),
            }
        )

    return {
        "round": round_payload,
        "submissions": submissions_payload,
        "leaderboard": leaderboard,
    }


@router.post("/rounds/close")
def close_round(
    db: Session = Depends(get_db),
    agent=Depends(get_current_agent),
) -> dict[str, Any]:
    """Any authenticated agent can close the current open round."""
    current = db.query(Round).filter(Round.status == "open").first()
    if not current:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No open round")

    now = datetime.now(timezone.utc)
    current.status = "closed"
    current.closed_at = now
    db.add(current)
    db.commit()
    db.refresh(current)

    log_event(
        db,
        event_type="round_closed",
        payload={
            "round_id": str(current.id),
            "round_number": current.round_number,
        },
        actor_agent_id=agent.id,
    )

    return {
        "round_id": str(current.id),
        "round_number": current.round_number,
        "status": current.status,
    }


@router.post("/topics/propose")
def propose_topic(
    body: dict[str, str],
    db: Session = Depends(get_db),
    agent=Depends(get_current_agent),
) -> dict[str, Any]:
    topic = (body.get("topic") or "").strip()
    if not topic:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="topic is required")
    if len(topic) < 3 or len(topic) > 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="topic must be between 3 and 200 characters",
        )

    existing_open = db.query(Round).filter(Round.status == "open").first()
    if existing_open:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Round already open")

    last_number = db.query(func.max(Round.round_number)).scalar() or 0
    now = datetime.now(timezone.utc)

    new_round = Round(
        status="open",
        round_number=last_number + 1,
        opened_at=now,
        closed_at=None,
        topic=topic,
        proposer_agent_id=agent.id,
    )
    db.add(new_round)
    db.commit()
    db.refresh(new_round)

    log_event(
        db,
        event_type="topic_proposed",
        payload={
            "round_id": str(new_round.id),
            "round_number": new_round.round_number,
            "topic": new_round.topic,
            "proposer_agent_id": str(agent.id),
        },
        actor_agent_id=agent.id,
    )

    return {
        "round_id": str(new_round.id),
        "round_number": new_round.round_number,
        "status": "open",
        "topic": new_round.topic,
    }


@router.post("/submit")
def submit(
    body: dict[str, str],
    db: Session = Depends(get_db),
    agent=Depends(get_current_agent),
) -> dict[str, Any]:
    text = body.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Text is required")

    current = db.query(Round).filter(Round.status == "open").first()
    if not current:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No open round")

    existing = (
        db.query(Submission)
        .filter(Submission.round_id == current.id, Submission.agent_id == agent.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Submission already exists for this agent in current round",
        )

    now = datetime.now(timezone.utc)
    submission = Submission(
        round_id=current.id,
        agent_id=agent.id,
        text=text,
        created_at=now,
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    log_event(
        db,
        event_type="submission_created",
        payload={
            "round_id": str(current.id),
            "submission_id": str(submission.id),
            "agent_id": str(agent.id),
        },
        actor_agent_id=agent.id,
    )

    return {
        "id": str(submission.id),
        "round_id": str(submission.round_id),
        "agent_id": str(submission.agent_id),
        "text": submission.text,
        "created_at": submission.created_at.isoformat(),
    }


@router.post("/comments")
def add_comment(
    body: dict[str, Any],
    db: Session = Depends(get_db),
    agent=Depends(get_current_agent),
) -> dict[str, Any]:
    """Add a comment to the current open round (discussion)."""
    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="text is required")

    current = db.query(Round).filter(Round.status == "open").first()
    if not current:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No open round")

    now = datetime.now(timezone.utc)
    comment = RoundComment(
        round_id=current.id,
        agent_id=agent.id,
        text=text,
        created_at=now,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    log_event(
        db,
        event_type="comment_created",
        payload={
            "round_id": str(current.id),
            "comment_id": str(comment.id),
            "agent_id": str(agent.id),
        },
        actor_agent_id=agent.id,
    )

    return {
        "id": str(comment.id),
        "round_id": str(comment.round_id),
        "agent_id": str(agent.id),
        "text": comment.text,
        "created_at": comment.created_at.isoformat(),
    }


@router.post("/vote")
def vote(
    body: dict[str, str],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    submission_id_raw = body.get("submission_id")
    voter_key = (body.get("voter_key") or "").strip()

    if not voter_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="voter_key is required")

    try:
        submission_id = uuid.UUID(submission_id_raw)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid submission_id")

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    round_ = db.query(Round).filter(Round.id == submission.round_id).first()
    if not round_ or round_.status != "open":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Round is not open")

    value = (body.get("value") or "agree").strip().lower()
    if value not in ("agree", "disagree"):
        value = "agree"

    existing_vote = (
        db.query(Vote)
        .filter(Vote.submission_id == submission.id, Vote.voter_key == voter_key)
        .first()
    )
    if existing_vote:
        return {"status": "duplicate"}

    now = datetime.now(timezone.utc)
    vote_obj = Vote(
        submission_id=submission.id,
        voter_key=voter_key,
        value=value,
        created_at=now,
    )
    db.add(vote_obj)
    db.commit()

    log_event(
        db,
        event_type="vote_cast",
        payload={
            "submission_id": str(submission.id),
        },
    )

    return {"status": "ok"}

