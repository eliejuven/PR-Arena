from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class EventEmitRequest(BaseModel):
    type: str
    payload: dict[str, Any]


class EventItem(BaseModel):
    id: UUID
    type: str
    payload: dict[str, Any]
    actor_agent_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EventsPage(BaseModel):
    items: List[EventItem] = Field(default_factory=list)
    next_cursor: Optional[str] = None

