"""Tests for public skill discovery endpoints."""

from fastapi.testclient import TestClient


def test_get_skill_returns_200_and_required_keys(client: TestClient) -> None:
    resp = client.get("/skill")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert "description" in data
    assert "authentication" in data
    assert "base_url" in data
    assert "capabilities" in data
    assert "rules" in data
    assert data["name"] == "PR Arena"
    assert data["authentication"]["header"] == "X-API-Key"
    assert data["authentication"]["registration_endpoint"] == "/v1/agents/register"
    assert isinstance(data["capabilities"], list)
    assert len(data["capabilities"]) >= 4
    assert isinstance(data["rules"], list)


def test_get_skill_md_returns_200_and_includes_preferred_onboarding(client: TestClient) -> None:
    """GET /skill.md returns 200 and body includes known substring (Preferred: Verified onboarding)."""
    resp = client.get("/skill.md")
    assert resp.status_code == 200
    assert "text/plain" in (resp.headers.get("content-type") or "")
    body = resp.text
    assert "Preferred: Verified onboarding" in body
