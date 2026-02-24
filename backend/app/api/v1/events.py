import base64
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.v1.agents import get_current_agent, get_db
from app.models.event import Event
from app.schemas.event import EventEmitRequest, EventItem, EventsPage
from app.services.events import log_event


router = APIRouter()


def _encode_cursor(created_at: datetime, event_id: uuid.UUID) -> str:
    raw = f"{created_at.isoformat()}|{event_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def _decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        created_str, id_str = raw.split("|", 1)
        created_at = datetime.fromisoformat(created_str)
        event_id = uuid.UUID(id_str)
        return created_at, event_id
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cursor",
        ) from exc


@router.post("/emit", response_model=EventItem)
def emit_event(
    payload: EventEmitRequest,
    db: Session = Depends(get_db),
    agent=Depends(get_current_agent),
) -> EventItem:
    event = log_event(db, event_type=payload.type, payload=payload.payload, actor_agent_id=agent.id)
    return EventItem.model_validate(event)


@router.get("", response_model=EventsPage)
def list_events(
    cursor: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> EventsPage:
    query = db.query(Event)

    if cursor:
        created_at_cursor, event_id_cursor = _decode_cursor(cursor)
        query = query.filter(
            or_(
                Event.created_at > created_at_cursor,
                and_(
                    Event.created_at == created_at_cursor,
                    Event.id > event_id_cursor,
                ),
            )
        )

    query = query.order_by(Event.created_at.asc(), Event.id.asc())

    rows = query.limit(limit + 1).all()

    items = [EventItem.model_validate(row) for row in rows[:limit]]
    next_cursor: Optional[str] = None

    if len(rows) > limit:
        last = rows[limit - 1]
        next_cursor = _encode_cursor(last.created_at, last.id)

    return EventsPage(items=items, next_cursor=next_cursor)

