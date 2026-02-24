from fastapi.testclient import TestClient


def _register_agent(client: TestClient) -> str:
    resp = client.post("/v1/agents/register", json={"display_name": "Emitter"})
    assert resp.status_code == 200
    return resp.json()["api_key"]


def test_emit_creates_event_with_actor(client: TestClient) -> None:
    api_key = _register_agent(client)

    resp = client.post(
        "/v1/events/emit",
        json={"type": "debug", "payload": {"foo": "bar"}},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["actor_agent_id"] is not None
    assert data["type"] == "debug"
    assert data["payload"]["foo"] == "bar"


def test_get_events_returns_emitted_event(client: TestClient) -> None:
    api_key = _register_agent(client)
    client.post(
        "/v1/events/emit",
        json={"type": "debug", "payload": {"msg": "one"}},
        headers={"X-API-Key": api_key},
    )

    resp = client.get("/v1/events?limit=50")
    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert len(body["items"]) >= 1
    types = {item["type"] for item in body["items"]}
    assert "debug" in types


def test_pagination_two_pages(client: TestClient) -> None:
    api_key = _register_agent(client)

    for i in range(3):
        client.post(
            "/v1/events/emit",
            json={"type": f"debug-{i}", "payload": {"i": i}},
            headers={"X-API-Key": api_key},
        )

    first = client.get("/v1/events?limit=2")
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body["items"]) == 2
    assert first_body["next_cursor"] is not None

    second = client.get(f"/v1/events?cursor={first_body['next_cursor']}&limit=2")
    assert second.status_code == 200
    second_body = second.json()
    # There should be at least one remaining event, but not more than 2
    assert 1 <= len(second_body["items"]) <= 2

