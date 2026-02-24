from fastapi import APIRouter

from app.api.v1 import agents as agents_router
from app.api.v1 import events as events_router
from app.api.v1 import arena as arena_router


api_router = APIRouter()

api_router.include_router(agents_router.router, prefix="/v1/agents", tags=["agents"])
api_router.include_router(events_router.router, prefix="/v1/events", tags=["events"])
api_router.include_router(arena_router.router, prefix="/v1/arena", tags=["arena"])

