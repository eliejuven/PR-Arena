"""Tests for verified agent onboarding flow."""

from fastapi.testclient import TestClient


def test_init_returns_verification_url_and_claim_token(client: TestClient) -> None:
    resp = client.post(
        "/v1/agents/onboarding/init",
        json={"display_name": "TestBot"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "agent_id" in data
    assert "verification_url" in data
    assert "claim_token" in data
    assert "message" in data
    assert "/verify?token=" in data["verification_url"]
    assert len(data["claim_token"]) > 10


def test_verify_marks_onboarding_verified(client: TestClient) -> None:
    init_resp = client.post(
        "/v1/agents/onboarding/init",
        json={"display_name": "VerifyMe"},
    )
    assert init_resp.status_code == 200
    init_data = init_resp.json()
    claim_token = init_data["claim_token"]
    # Extract human_token from verification_url (e.g. .../verify?token=XXX)
    verification_url = init_data["verification_url"]
    human_token = verification_url.split("token=")[1].split("&")[0]

    status_before = client.get(f"/v1/agents/onboarding/status?claim_token={claim_token}")
    assert status_before.json()["status"] == "pending"

    verify_resp = client.post(
        "/v1/agents/onboarding/verify",
        json={"human_token": human_token},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json().get("status") == "ok"

    status_after = client.get(f"/v1/agents/onboarding/status?claim_token={claim_token}")
    assert status_after.json()["status"] == "verified"


def test_claim_before_verify_returns_409(client: TestClient) -> None:
    init_resp = client.post(
        "/v1/agents/onboarding/init",
        json={"display_name": "NoVerify"},
    )
    assert init_resp.status_code == 200
    claim_token = init_resp.json()["claim_token"]

    claim_resp = client.post(
        "/v1/agents/onboarding/claim",
        json={"claim_token": claim_token},
    )
    assert claim_resp.status_code == 409


def test_claim_after_verify_returns_api_key_and_agent_is_verified(client: TestClient) -> None:
    init_resp = client.post(
        "/v1/agents/onboarding/init",
        json={"display_name": "FullFlow"},
    )
    assert init_resp.status_code == 200
    init_data = init_resp.json()
    claim_token = init_data["claim_token"]
    agent_id = init_data["agent_id"]
    verification_url = init_data["verification_url"]
    human_token = verification_url.split("token=")[1].split("&")[0]

    client.post("/v1/agents/onboarding/verify", json={"human_token": human_token})

    claim_resp = client.post(
        "/v1/agents/onboarding/claim",
        json={"claim_token": claim_token},
    )
    assert claim_resp.status_code == 200
    claim_data = claim_resp.json()
    assert "api_key" in claim_data
    assert claim_data["agent_id"] == agent_id
    assert claim_data["display_name"] == "FullFlow"
    assert len(claim_data["api_key"]) > 10


def test_claim_second_time_returns_409(client: TestClient) -> None:
    init_resp = client.post(
        "/v1/agents/onboarding/init",
        json={"display_name": "DoubleClaim"},
    )
    assert init_resp.status_code == 200
    init_data = init_resp.json()
    claim_token = init_data["claim_token"]
    verification_url = init_data["verification_url"]
    human_token = verification_url.split("token=")[1].split("&")[0]

    client.post("/v1/agents/onboarding/verify", json={"human_token": human_token})
    first_claim = client.post(
        "/v1/agents/onboarding/claim",
        json={"claim_token": claim_token},
    )
    assert first_claim.status_code == 200

    second_claim = client.post(
        "/v1/agents/onboarding/claim",
        json={"claim_token": claim_token},
    )
    assert second_claim.status_code == 409
