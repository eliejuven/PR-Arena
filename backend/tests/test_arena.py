from uuid import UUID

from fastapi.testclient import TestClient


def _register_agent(client: TestClient, name: str = "Agent") -> str:
  resp = client.post("/v1/agents/register", json={"display_name": name})
  assert resp.status_code == 200
  return resp.json()["api_key"]


def _open_round_via_agent(client: TestClient, api_key: str, topic: str = "Test round") -> None:
  resp = client.post(
      "/v1/arena/topics/propose",
      headers={"X-API-Key": api_key},
      json={"topic": topic},
  )
  assert resp.status_code == 200


def _close_round_via_agent(client: TestClient, api_key: str) -> None:
  resp = client.post("/v1/arena/rounds/close", headers={"X-API-Key": api_key})
  assert resp.status_code == 200


def test_agent_open_close_round_and_conflicts(client: TestClient) -> None:
  api_key = _register_agent(client, "Closer")
  # No round – closing should 409
  resp = client.post("/v1/arena/rounds/close", headers={"X-API-Key": api_key})
  assert resp.status_code == 409

  # Open round via propose
  _open_round_via_agent(client, api_key, "Agent-opened round")
  state = client.get("/v1/arena/state").json()
  assert state["round"]["status"] == "open"
  assert state["round"]["topic"] == "Agent-opened round"
  round_id = UUID(state["round"]["id"])

  # Propose again while open -> 409
  other_key = _register_agent(client, "Other")
  resp = client.post(
      "/v1/arena/topics/propose",
      headers={"X-API-Key": other_key},
      json={"topic": "Another topic"},
  )
  assert resp.status_code == 409

  # Close round (any agent)
  resp = client.post("/v1/arena/rounds/close", headers={"X-API-Key": api_key})
  assert resp.status_code == 200
  data_close = resp.json()
  assert data_close["status"] == "closed"
  assert UUID(data_close["round_id"]) == round_id


def test_agent_can_submit_once_per_round(client: TestClient) -> None:
  api_key = _register_agent(client, "Submitter")
  _open_round_via_agent(client, api_key, "Submit test round")

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
  _close_round_via_agent(client, api_key)


def test_votes_require_voter_key_and_open_round_and_duplicate_behavior(client: TestClient) -> None:
  api_key = _register_agent(client, "Voter-Agent")
  _open_round_via_agent(client, api_key, "Vote test round")

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

  # First vote OK (agree)
  voter_key = "test-voter-1"
  resp = client.post(
      "/v1/arena/vote",
      json={"submission_id": submission_id, "voter_key": voter_key, "value": "agree"},
  )
  assert resp.status_code == 200
  assert resp.json()["status"] == "ok"

  # Duplicate vote returns status duplicate, still 200
  resp = client.post(
      "/v1/arena/vote",
      json={"submission_id": submission_id, "voter_key": voter_key, "value": "disagree"},
  )
  assert resp.status_code == 200
  assert resp.json()["status"] == "duplicate"

  # Close round, further votes get 409
  _close_round_via_agent(client, api_key)
  resp = client.post(
      "/v1/arena/vote",
      json={"submission_id": submission_id, "voter_key": "another-voter"},
  )
  assert resp.status_code == 409
  # Round already closed; next tests need no open round (state test will open its own)


def test_state_endpoint_returns_agrees_disagrees_and_leaderboard(client: TestClient) -> None:
  api_key_a = _register_agent(client, "Agent A")
  api_key_b = _register_agent(client, "Agent B")
  _open_round_via_agent(client, api_key_a, "Leaderboard round")

  # Agent A & B submit
  sub_a = client.post(
      "/v1/arena/submit",
      json={"text": "A fact"},
      headers={"X-API-Key": api_key_a},
  ).json()
  sub_b = client.post(
      "/v1/arena/submit",
      json={"text": "B fact"},
      headers={"X-API-Key": api_key_b},
  ).json()

  # Votes: A gets 2 agree, B gets 1 agree
  client.post(
      "/v1/arena/vote",
      json={"submission_id": sub_a["id"], "voter_key": "v1", "value": "agree"},
  )
  client.post(
      "/v1/arena/vote",
      json={"submission_id": sub_a["id"], "voter_key": "v2", "value": "agree"},
  )
  client.post(
      "/v1/arena/vote",
      json={"submission_id": sub_b["id"], "voter_key": "v3", "value": "agree"},
  )

  state = client.get("/v1/arena/state")
  assert state.status_code == 200
  payload = state.json()

  assert payload["round"] is not None
  assert payload["round"]["status"] == "open"
  assert payload["round"]["topic"] == "Leaderboard round"
  assert "comments" in payload["round"]

  submissions = payload["submissions"]
  assert len(submissions) == 2
  by_text = {s["text"]: s for s in submissions}
  assert by_text["A fact"]["agrees"] == 2
  assert by_text["A fact"]["disagrees"] == 0
  assert by_text["B fact"]["agrees"] == 1
  assert by_text["B fact"]["disagrees"] == 0

  leaderboard = payload["leaderboard"]
  assert leaderboard[0]["score"] == 2
  assert leaderboard[1]["score"] == 1
  _close_round_via_agent(client, api_key_a)


def test_propose_topic_opens_round(client: TestClient) -> None:
  api_key = _register_agent(client, "Proposer")
  resp = client.post(
      "/v1/arena/topics/propose",
      headers={"X-API-Key": api_key},
      json={"topic": "Market a solar-powered backpack"},
  )
  assert resp.status_code == 200
  data = resp.json()
  assert data["status"] == "open"
  assert data["topic"] == "Market a solar-powered backpack"
  assert "round_id" in data
  assert data["round_number"] >= 1

  state = client.get("/v1/arena/state")
  assert state.status_code == 200
  payload = state.json()
  assert payload["round"] is not None
  assert payload["round"]["topic"] == "Market a solar-powered backpack"
  assert payload["round"]["proposer_agent_id"] is not None
  assert payload["round"]["proposer_agent_name"] == "Proposer"
  _close_round_via_agent(client, api_key)


def test_propose_when_round_already_open_returns_409(client: TestClient) -> None:
  api_key = _register_agent(client, "Proposer")
  _open_round_via_agent(client, api_key, "Existing round")
  resp = client.post(
      "/v1/arena/topics/propose",
      headers={"X-API-Key": api_key},
      json={"topic": "Another topic"},
  )
  assert resp.status_code == 409


def test_propose_requires_topic(client: TestClient) -> None:
  api_key = _register_agent(client, "Proposer")
  resp = client.post(
      "/v1/arena/topics/propose",
      headers={"X-API-Key": api_key},
      json={},
  )
  assert resp.status_code == 400

