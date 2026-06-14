from predictor.application.use_cases.health import GetHealth


def test_health_use_case() -> None:
    result = GetHealth().execute()

    assert result.status == "ok"
    assert result.service == "world-cup-predictor"
