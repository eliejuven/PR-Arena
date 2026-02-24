from uuid import UUID

from fastapi.testclient import TestClient

from app.core.config import get_settings


def _admin_headers() -> dict[str, str]:
  settings = get_settings()
  return {"X-Admin-Key": settings.admin_key}


def _register_agent(client: TestClient, name: str = "Agent") -> str:
  resp = client.post("/v1/agents/register", json={"display_name": name})
  assert resp.status_code == 200
  return resp.json()["api_key"]


def test_admin_open_close_round_and_conflicts(client: TestClient) -> None:
  # Initially, no round – closing should 409
  resp = client.post("/v1/arena/rounds/close", headers=_admin_headers())
  assert resp.status_code == 409

  # Opening without admin key -> 401
  resp = client.post("/v1/arena/rounds/open")
  assert resp.status_code == 401

  # Open first round
  resp = client.post("/v1/arena/rounds/open", headers=_admin_headers())
  assert resp.status_code == 200
  data = resp.json()
  assert data["status"] == "open"
  round_id = UUID(data["round_id"])

  # Opening again while open -> 409
  resp = client.post("/v1/arena/rounds/open", headers=_admin_headers())
  assert resp.status_code == 409

  # Close round
  resp = client.post("/v1/arena/rounds/close", headers=_admin_headers())
  assert resp.status_code == 200
  data_close = resp.json()
  assert data_close["status"] == "closed"
  assert UUID(data_close["round_id"]) == round_id


def test_agent_can_submit_once_per_round(client: TestClient) -> None:
  client.post("/v1/arena/rounds/open", headers=_admin_headers())
  api_key = _register_agent(client, "Submitter")

  # First submit works
  resp = client.post(
      "/v1/arena/submit",
      json={"text": "My first pitch"},
      headers={"X-API-Key": api_key},
  )
  assert resp.status_code == 200

  # Second submit same round -> 409
  resp = client.post(
      "/v1/arena/submit",
      json={"text": "Second pitch"},
      headers={"X-API-Key": api_key},
  )
  assert resp.status_code == 409


def test_votes_require_voter_key_and_open_round_and_duplicate_behavior(client: TestClient) -> None:
  client.post("/v1/arena/rounds/open", headers=_admin_headers())
  api_key = _register_agent(client, "Voter-Agent")

  # Submit one entry
  submit_resp = client.post(
      "/v1/arena/submit",
      json={"text": "Vote for me"},
      headers={"X-API-Key": api_key},
  )
  assert submit_resp.status_code == 200
  submission_id = submit_resp.json()["id"]

  # Missing voter_key -> 400
  resp = client.post("/v1/arena/vote", json={"submission_id": submission_id})
  assert resp.status_code == 400

  # First vote OK
  voter_key = "test-voter-1"
  resp = client.post(
      "/v1/arena/vote",
      json={"submission_id": submission_id, "voter_key": voter_key},
  )
  assert resp.status_code == 200
  assert resp.json()["status"] == "ok"

  # Duplicate vote returns status duplicate, still 200
  resp = client.post(
      "/v1/arena/vote",
      json={"submission_id": submission_id, "voter_key": voter_key},
  )
  assert resp.status_code == 200
  assert resp.json()["status"] == "duplicate"

  # Close round, further votes get 409
  client.post("/v1/arena/rounds/close", headers=_admin_headers())
  resp = client.post(
      "/v1/arena/vote",
      json={"submission_id": submission_id, "voter_key": "another-voter"},
  )
  assert resp.status_code == 409


def test_state_endpoint_returns_counts_and_leaderboard(client: TestClient) -> None:
  client.post("/v1/arena/rounds/open", headers=_admin_headers())
  api_key_a = _register_agent(client, "Agent A")
  api_key_b = _register_agent(client, "Agent B")

  # Agent A & B submit
  sub_a = client.post(
      "/v1/arena/submit",
      json={"text": "A pitch"},
      headers={"X-API-Key": api_key_a},
  ).json()
  sub_b = client.post(
      "/v1/arena/submit",
      json={"text": "B pitch"},
      headers={"X-API-Key": api_key_b},
  ).json()

  # Votes: A gets 2 votes, B gets 1
  client.post(
      "/v1/arena/vote",
      json={"submission_id": sub_a["id"], "voter_key": "v1"},
  )
  client.post(
      "/v1/arena/vote",
      json={"submission_id": sub_a["id"], "voter_key": "v2"},
  )
  client.post(
      "/v1/arena/vote",
      json={"submission_id": sub_b["id"], "voter_key": "v3"},
  )

  state = client.get("/v1/arena/state")
  assert state.status_code == 200
  payload = state.json()

  assert payload["round"] is not None
  assert payload["round"]["status"] == "open"

  submissions = payload["submissions"]
  # Two submissions in this round
  assert len(submissions) == 2
  # Check votes per submission
  votes_by_text = {s["text"]: s["votes"] for s in submissions}
  assert votes_by_text["A pitch"] == 2
  assert votes_by_text["B pitch"] == 1

  leaderboard = payload["leaderboard"]
  # A should be first with score 2, B second with 1
  assert leaderboard[0]["score"] == 2
  assert leaderboard[1]["score"] == 1

