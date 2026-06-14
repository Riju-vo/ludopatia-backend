from fastapi.testclient import TestClient

from predictor.presentation.api.main import create_app


def test_groups_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/groups")

    assert response.status_code == 200
    payload = response.json()
    assert payload["competition_id"] == "fifa_world_cup"
    assert len(payload["groups"]) == 12

    group_a = next(group for group in payload["groups"] if group["group_code"] == "A")
    assert [team["team"]["name"] for team in group_a["teams"]] == [
        "Mexico",
        "South Africa",
        "Korea Republic",
        "Czechia",
    ]
    assert len(group_a["fixtures"]) == 6
    assert group_a["fixtures"][0]["matchday"] == 1
    assert any(fixture["prediction"] is not None for fixture in group_a["fixtures"])
