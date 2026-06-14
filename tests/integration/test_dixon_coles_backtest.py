from pathlib import Path

from predictor.evaluation import backtest_dixon_coles, write_dixon_coles_backtest_result

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_dixon_coles_backtest_generates_real_report(tmp_path: Path) -> None:
    result = backtest_dixon_coles(data_dir=DATA_DIR)
    write_dixon_coles_backtest_result(result, data_dir=tmp_path)

    assert not result.fold_metrics.empty
    assert "rho" in result.fold_metrics.columns
    assert "delta_exact_score_log_loss" in result.fold_metrics.columns
    assert (tmp_path / "reports" / "dixon_coles_backtest_report.json").exists()
