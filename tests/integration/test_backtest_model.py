from pathlib import Path

from predictor.evaluation import backtest_model, write_backtest_result

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_backtest_model_generates_real_reports(tmp_path: Path) -> None:
    result = backtest_model(data_dir=DATA_DIR)
    write_backtest_result(result, data_dir=tmp_path)

    assert not result.fold_metrics.empty
    assert not result.predictions.empty
    assert result.report["folds"] >= 1
    assert "aggregate_metrics" in result.report
    assert (tmp_path / "reports" / "backtest_fold_metrics.csv").exists()
