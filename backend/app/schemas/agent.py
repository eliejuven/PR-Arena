from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AgentRegisterRequest(BaseModel):
    display_name: str


class AgentResponse(BaseModel):
    agent_id: UUID
    display_name: str
    api_key: str
    created_at: datetime

    class Config:
        from_attributes = True


