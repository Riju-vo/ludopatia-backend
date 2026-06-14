"""Evaluation package."""

from predictor.evaluation.backtest import (
    BacktestConfig,
    BacktestResult,
    backtest_model,
    backtest_model_from_frame,
    write_backtest_result,
)
from predictor.evaluation.dixon_coles_backtest import (
    DixonColesBacktestResult,
    backtest_dixon_coles,
    write_dixon_coles_backtest_result,
)
from predictor.evaluation.feature_search import (
    FeatureSearchConfig,
    FeatureSearchResult,
    compare_feature_configs,
    write_feature_search_result,
)
from predictor.evaluation.segment_diagnostics import (
    SegmentDiagnosticsResult,
    build_segment_diagnostics,
    write_segment_diagnostics_result,
)

__all__ = [
    "BacktestConfig",
    "BacktestResult",
    "DixonColesBacktestResult",
    "FeatureSearchConfig",
    "FeatureSearchResult",
    "SegmentDiagnosticsResult",
    "backtest_model",
    "backtest_model_from_frame",
    "backtest_dixon_coles",
    "build_segment_diagnostics",
    "compare_feature_configs",
    "write_backtest_result",
    "write_dixon_coles_backtest_result",
    "write_feature_search_result",
    "write_segment_diagnostics_result",
]
