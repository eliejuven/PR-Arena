from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.api.v1 import agents as agents_api
from app.api.v1 import events as events_api
from app.api.v1 import arena as arena_api
from app.db.base import Base
from app.models import agent as agent_model  # noqa: F401
from app.models import event as event_model  # noqa: F401
from app.models import arena as arena_model  # noqa: F401


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, future=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


def override_get_db() -> Generator:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database() -> Generator:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Wire FastAPI dependency overrides so agents, events, arena use the test DB.
    app.dependency_overrides[agents_api.get_db] = override_get_db
    app.dependency_overrides[events_api.get_db] = override_get_db
    app.dependency_overrides[arena_api.get_db] = override_get_db

    yield

    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)

