from fastapi.testclient import TestClient

from predictor.presentation.api.main import create_app


def test_current_model_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/models/current")

    assert response.status_code == 200
    payload = response.json()["model"]
    assert payload["model_version"].startswith("baseline_poisson_")
    assert payload["model_family"] == "independent_poisson_regressor"
    assert payload["training_rows"] > 0
    assert payload["validation_rows"] > 0
    assert "backtest_summary" in payload
