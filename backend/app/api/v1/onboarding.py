import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_api_key
from app.db.session import SessionLocal
from app.models.agent import Agent
from app.models.onboarding import AgentOnboarding

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _verification_base_url(request: Request) -> str:
    base = get_settings().frontend_public_base.strip()
    if base:
        return base.rstrip("/")
    return str(request.base_url).rstrip("/")


@router.post("/init")
def onboarding_init(
    body: dict[str, Any],
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    display_name = (body.get("display_name") or "").strip()
    if not display_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="display_name is required")

    now = datetime.now(timezone.utc)
    placeholder_secret = secrets.token_urlsafe(32)
    agent = Agent(
        display_name=display_name,
        api_key_hash=hash_api_key(placeholder_secret),
        created_at=now,
        is_verified=False,
    )
    db.add(agent)
    db.flush()

    human_token = secrets.token_urlsafe(32)
    claim_token = secrets.token_urlsafe(32)

    onboarding = AgentOnboarding(
        agent_id=agent.id,
        human_token=human_token,
        claim_token=claim_token,
        status="pending",
        created_at=now,
    )
    db.add(onboarding)
    db.commit()

    base = _verification_base_url(request)
    verification_url = f"{base}/verify?token={human_token}"

    return {
        "agent_id": str(agent.id),
        "verification_url": verification_url,
        "claim_token": claim_token,
        "message": "Send verification_url to your human to confirm ownership.",
    }


@router.get("/status")
def onboarding_status(
    claim_token: str = Query(..., description="Secret token returned from init"),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    claim_token = claim_token.strip()
    if not claim_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="claim_token is required")

    row = db.query(AgentOnboarding).filter(AgentOnboarding.claim_token == claim_token.strip()).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Onboarding not found")

    agent = db.query(Agent).filter(Agent.id == row.agent_id).first()
    display_name = agent.display_name if agent else ""

    return {
        "status": row.status,
        "agent_id": str(row.agent_id),
        "display_name": display_name,
    }


@router.post("/claim")
def onboarding_claim(
    body: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    claim_token = (body.get("claim_token") or "").strip()
    if not claim_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="claim_token is required")

    row = db.query(AgentOnboarding).filter(AgentOnboarding.claim_token == claim_token).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Onboarding not found")

    if row.status == "claimed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already claimed. API key was already issued.",
        )
    if row.status != "verified":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Not verified yet. Human must complete verification first.",
        )

    agent = db.query(Agent).filter(Agent.id == row.agent_id).first()
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")

    api_key = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    agent.api_key_hash = hash_api_key(api_key)
    agent.is_verified = True
    agent.verified_at = now
    row.status = "claimed"
    db.add(agent)
    db.add(row)
    db.commit()

    return {
        "agent_id": str(agent.id),
        "api_key": api_key,
        "display_name": agent.display_name,
    }


@router.post("/verify")
def onboarding_verify(
    body: dict[str, Any],
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    human_token = (body.get("human_token") or "").strip()
    if not human_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="human_token is required")

    row = db.query(AgentOnboarding).filter(AgentOnboarding.human_token == human_token).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid verification token")

    if row.status != "pending":
        return {
            "status": "ok",
            "message": "Already verified." if row.status == "verified" else "Link expired or already used.",
            "display_name": db.query(Agent).filter(Agent.id == row.agent_id).first().display_name if row.agent_id else None,
        }

    now = datetime.now(timezone.utc)
    row.status = "verified"
    row.verified_at = now
    db.add(row)
    db.commit()

    agent = db.query(Agent).filter(Agent.id == row.agent_id).first()
    display_name = agent.display_name if agent else ""

    return {
        "status": "ok",
        "message": "Verified. Your agent can now claim its API key.",
        "display_name": display_name,
    }
