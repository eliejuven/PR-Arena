from fastapi.testclient import TestClient


def test_register_returns_api_key(client: TestClient) -> None:
    resp = client.post("/v1/agents/register", json={"display_name": "Agent One"})
    assert resp.status_code == 200
    data = resp.json()
    assert "api_key" in data
    assert data["display_name"] == "Agent One"
    assert data["agent_id"]


def test_invalid_api_key_is_unauthorized_on_emit(client: TestClient) -> None:
    resp = client.post(
        "/v1/events/emit",
        json={"type": "debug", "payload": {"msg": "hello"}},
        headers={"X-API-Key": "invalid"},
    )
    assert resp.status_code == 401


def test_valid_api_key_authenticates_on_emit(client: TestClient) -> None:
    reg = client.post("/v1/agents/register", json={"display_name": "Agent Two"})
    assert reg.status_code == 200
    api_key = reg.json()["api_key"]

    resp = client.post(
        "/v1/events/emit",
        json={"type": "debug", "payload": {"msg": "ok"}},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200

