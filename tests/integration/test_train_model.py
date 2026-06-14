from pathlib import Path

from predictor.training import train_model, write_train_result

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_train_model_generates_artifact_from_real_features(tmp_path: Path) -> None:
    result = train_model(data_dir=DATA_DIR, model_dir=tmp_path)
    write_train_result(result, model_dir=tmp_path)

    version_dir = tmp_path / result.model_version

    assert version_dir.exists()
    assert (version_dir / "model.joblib").exists()
    assert (version_dir / "metadata.json").exists()
    assert (version_dir / "validation_predictions.csv").exists()
    assert result.metadata["feature_count"] > 0
    assert result.metadata["validation_rows"] > 0
