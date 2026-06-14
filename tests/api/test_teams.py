from fastapi.testclient import TestClient

from predictor.presentation.api.main import create_app


def test_team_profile_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/teams/fifa_arg")

    assert response.status_code == 200
    payload = response.json()["team"]
    assert payload["name"] == "Argentina"
    assert payload["fifa_code"] == "ARG"
    assert payload["current_elo"] is not None
    assert payload["current_fifa"] is not None
    assert len(payload["recent_results"]) > 0
