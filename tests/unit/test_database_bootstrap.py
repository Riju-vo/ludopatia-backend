from predictor.infrastructure.config import get_settings
from predictor.infrastructure.database.bootstrap import build_seed_payload


def test_build_seed_payload_returns_non_empty_sections() -> None:
    settings = get_settings()

    payload = build_seed_payload(
        data_dir=settings.data_dir,
        model_dir=settings.model_dir,
    )

    assert payload.report["teams"] > 0
    assert payload.report["matches"] > 0
    assert payload.report["feature_snapshots"] > 0
    assert payload.report["predictions"] > 0
    assert payload.report["tournament_groups"] == 12
    assert payload.report["tournament_group_teams"] == 48
    assert payload.report["prediction_score_matrices"] == payload.report["predictions"]


def test_build_seed_payload_marks_one_current_model() -> None:
    settings = get_settings()

    payload = build_seed_payload(
        data_dir=settings.data_dir,
        model_dir=settings.model_dir,
    )

    current_models = [row for row in payload.model_versions if row["is_current"]]
    assert len(current_models) == 1
    assert current_models[0]["model_version"].startswith("baseline_poisson_")
