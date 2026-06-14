from pathlib import Path

from predictor.inference import predict_fixtures, write_fixture_predictions

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
MODEL_DIR = Path(__file__).resolve().parents[2] / "artifacts" / "models"


def test_predict_fixtures_uses_latest_real_model(tmp_path: Path) -> None:
    result = predict_fixtures(data_dir=DATA_DIR, model_dir=MODEL_DIR)
    write_fixture_predictions(result, data_dir=tmp_path, model_dir=tmp_path / "models")

    assert not result.predictions.empty
    assert len(result.score_matrices) == len(result.predictions)
    assert result.predictions["predicted_home_lambda"].gt(0).all()
    assert (tmp_path / "predictions" / "fixture_predictions.csv").exists()
