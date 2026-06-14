from pathlib import Path

from predictor.evaluation import build_segment_diagnostics, write_segment_diagnostics_result

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_segment_diagnostics_generates_real_reports(tmp_path: Path) -> None:
    result = build_segment_diagnostics(data_dir=DATA_DIR)
    write_segment_diagnostics_result(result, data_dir=tmp_path)

    assert not result.baseline_segments.empty
    assert not result.dixon_coles_segments.empty
    assert result.report["rows_compared"] > 0
    assert (tmp_path / "reports" / "segment_diagnostics_report.json").exists()
