import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_api_key
from app.db.session import SessionLocal
from app.models.agent import Agent
from app.models.onboarding import AgentOnboarding

logger = logging.getLogger(__name__)
router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _verification_base_url(request: Request) -> Tuple[str, str]:
    """
    Return (base_url, source) for building verification_url.
    Prefer FRONTEND_PUBLIC_BASE from env; else X-Forwarded-Proto + X-Forwarded-Host; else request base.
    """
    settings = get_settings()
    base_from_env = (settings.frontend_public_base or "").strip()
    if base_from_env:
        base = base_from_env.rstrip("/")
        logger.debug("verification base URL from FRONTEND_PUBLIC_BASE: %s", base)
        return base, "env"
    proto = request.headers.get("x-forwarded-proto") or request.url.scheme
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or ""
    if host:
        base = f"{proto}://{host}".rstrip("/")
        logger.debug("verification base URL from forwarded headers / request host: %s", base)
        return base, "request"
    base = str(request.base_url).rstrip("/")
    logger.debug("verification base URL from request.base_url: %s", base)
    return base, "request"


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

    base, _source = _verification_base_url(request)
    verification_url = f"{base}/verify?token={human_token}"

    # Protection: when FRONTEND_PUBLIC_BASE is set, verification_url must point to frontend (not backend)
    settings = get_settings()
    if (settings.frontend_public_base or "").strip():
        expected_prefix = (settings.frontend_public_base or "").strip().rstrip("/")
        if not verification_url.startswith(expected_prefix) or "/verify?token=" not in verification_url:
            logger.warning(
                "verification_url built with FRONTEND_PUBLIC_BASE but result does not match; base=%s",
                expected_prefix,
            )

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
