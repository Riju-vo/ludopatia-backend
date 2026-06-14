from pathlib import Path

from predictor.evaluation import BacktestConfig, backtest_model, write_backtest_result
from tests.unit.test_training import _build_match_features_frame


def test_backtest_generates_fold_metrics_and_predictions(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    processed_dir = data_dir / "processed"
    processed_dir.mkdir(parents=True)
    _build_match_features_frame().to_csv(processed_dir / "match_features.csv", index=False)

    result = backtest_model(
        data_dir=data_dir,
        config=BacktestConfig(
            initial_train_days=5,
            validation_window_days=3,
            step_days=3,
            alpha=0.5,
            max_iter=200,
        ),
    )
    write_backtest_result(result, data_dir=data_dir)

    assert not result.fold_metrics.empty
    assert not result.predictions.empty
    assert "outcome_log_loss" in result.fold_metrics.columns
    assert result.report["folds"] >= 1
    assert (data_dir / "reports" / "backtest_report.json").exists()
