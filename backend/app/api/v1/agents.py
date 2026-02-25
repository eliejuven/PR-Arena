import secrets
from datetime import datetime, timezone

from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_api_key, verify_api_key
from app.db.session import SessionLocal
from app.models.agent import Agent
from app.schemas.agent import AgentRegisterRequest, AgentResponse


router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_api_key() -> str:
    return secrets.token_urlsafe(32)


def get_current_agent(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> Agent:
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")

    # We cannot look up agents by API key directly since only a hash is stored.
    # Iterate through agents and return the first one whose hash matches.
    for agent in db.query(Agent).all():
        if verify_api_key(x_api_key, agent.api_key_hash):
            return agent

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@router.post("/register", response_model=AgentResponse)
def register_agent(payload: AgentRegisterRequest, db: Session = Depends(get_db)) -> AgentResponse:
    api_key = generate_api_key()
    now = datetime.now(timezone.utc)

    agent = Agent(
        display_name=payload.display_name,
        api_key_hash=hash_api_key(api_key),
        created_at=now,
        is_verified=True,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

    return AgentResponse(
        agent_id=agent.id,
        display_name=agent.display_name,
        api_key=api_key,
        created_at=agent.created_at,
    )

