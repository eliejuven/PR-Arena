from datetime import datetime, timezone
from typing import Any, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.event import Event


def log_event(
    db: Session,
    *,
    event_type: str,
    payload: dict[str, Any],
    actor_agent_id: Optional[uuid.UUID] = None,
) -> Event:
    now = datetime.now(timezone.utc)
    event = Event(
        type=event_type,
        payload=payload,
        actor_agent_id=actor_agent_id,
        created_at=now,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

