from fastapi.testclient import TestClient

from predictor.presentation.api.main import create_app


def test_matches_today_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/matches/today")

    assert response.status_code == 200
    payload = response.json()
    assert payload["date"] == "2026-06-13"
    assert len(payload["matches"]) == 4
    assert all(match["kickoff_date"] == "2026-06-13" for match in payload["matches"])


def test_match_detail_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/matches/match_d51aaaab1f140fd81d8d")

    assert response.status_code == 200
    payload = response.json()["match"]
    assert payload["home_team"]["name"] == "Qatar"
    assert payload["away_team"]["name"] == "Switzerland"
    assert payload["competition"]["competition_id"] == "fifa_world_cup"
    assert "feature_snapshot" in payload


def test_match_prediction_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/matches/match_d51aaaab1f140fd81d8d/prediction")

    assert response.status_code == 200
    payload = response.json()["prediction"]
    assert payload["model_version"].startswith("baseline_poisson_")
    assert (
        payload["outcome_probabilities"]["away_win"]
        > payload["outcome_probabilities"]["home_win"]
    )
    assert len(payload["top_scorelines"]) == 5
    assert payload["score_matrix"]["labels"][-1] == "10+"
