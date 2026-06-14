import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.metrics import accuracy_score, log_loss

from predictor.training.train import METRIC_OUTCOME_LABELS, _multiclass_brier_score


@dataclass(frozen=True, slots=True)
class SegmentDiagnosticsResult:
    baseline_segments: pd.DataFrame
    dixon_coles_segments: pd.DataFrame
    report: dict[str, Any]


def _elo_gap_bucket(series: pd.Series) -> pd.Series:
    return pd.cut(
        series.astype("float64"),
        bins=[-10_000, -100, -25, 25, 100, 10_000],
        labels=[
            "away_strong",
            "away_edge",
            "balanced",
            "home_edge",
            "home_strong",
        ],
        include_lowest=True,
    ).astype("string")


def _join_segment_context(data_dir: Path) -> pd.DataFrame:
    base = pd.read_csv(data_dir / "reports" / "backtest_predictions.csv")
    dixon = pd.read_csv(data_dir / "reports" / "dixon_coles_backtest_predictions.csv")
    matches = pd.read_csv(data_dir / "processed" / "match_features.csv")
    competitions = pd.read_csv(data_dir / "reference" / "competitions.csv")

    competition_context = competitions.loc[
        :,
        ["competition_id", "competition_type", "organizer_scope"],
    ].drop_duplicates(subset=["competition_id"])

    context = matches.loc[
        :,
        [
            "match_id",
            "neutral",
            "home_is_tournament_host",
            "away_is_tournament_host",
            "competition_id",
            "elo_difference_pre",
        ],
    ].merge(
        competition_context,
        on="competition_id",
        how="left",
    )
    context["elo_gap_bucket"] = _elo_gap_bucket(context["elo_difference_pre"])
    context["host_context"] = "none"
    context.loc[context["home_is_tournament_host"], "host_context"] = "home_host"
    context.loc[context["away_is_tournament_host"], "host_context"] = "away_host"

    merged = base.merge(
        dixon.drop(
            columns=[
                "kickoff_date",
                "home_team_id",
                "away_team_id",
                "home_score_90",
                "away_score_90",
                "actual_outcome",
                "train_end_date",
                "validation_end_date",
            ]
        ),
        on=["match_id", "fold"],
        how="inner",
    ).merge(context, on="match_id", how="left")

    return merged


def _segment_metrics(
    frame: pd.DataFrame,
    *,
    segment_column: str,
    prefix: str,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for segment_value, group in frame.groupby(segment_column, dropna=False):
        probabilities = group.loc[
            :,
            [
                f"{prefix}_home_win_probability",
                f"{prefix}_draw_probability",
                f"{prefix}_away_win_probability",
            ],
        ].to_numpy()
        labels = group["actual_outcome"].tolist()
        rows.append(
            {
                "segment": segment_column,
                "segment_value": str(segment_value),
                "matches": int(len(group)),
                "outcome_log_loss": float(
                    log_loss(
                        labels,
                        probabilities[:, [2, 1, 0]],
                        labels=METRIC_OUTCOME_LABELS,
                    )
                ),
                "outcome_brier_score": _multiclass_brier_score(probabilities, labels),
                "outcome_accuracy": float(
                    accuracy_score(labels, group[f"{prefix}_predicted_outcome"])
                ),
            }
        )
    return pd.DataFrame(rows)


def build_segment_diagnostics(*, data_dir: Path) -> SegmentDiagnosticsResult:
    merged = _join_segment_context(data_dir)
    segment_columns = [
        "neutral",
        "competition_type",
        "organizer_scope",
        "elo_gap_bucket",
        "host_context",
    ]

    baseline_parts = [
        _segment_metrics(merged, segment_column=column, prefix="baseline")
        for column in segment_columns
    ]
    dixon_parts = [
        _segment_metrics(merged, segment_column=column, prefix="dixon_coles")
        for column in segment_columns
    ]

    baseline_segments = pd.concat(baseline_parts, ignore_index=True)
    dixon_coles_segments = pd.concat(dixon_parts, ignore_index=True)
    comparison = baseline_segments.merge(
        dixon_coles_segments,
        on=["segment", "segment_value", "matches"],
        suffixes=("_baseline", "_dixon_coles"),
    )
    comparison["delta_outcome_log_loss"] = (
        comparison["outcome_log_loss_dixon_coles"]
        - comparison["outcome_log_loss_baseline"]
    )
    comparison["delta_outcome_brier_score"] = (
        comparison["outcome_brier_score_dixon_coles"]
        - comparison["outcome_brier_score_baseline"]
    )
    comparison["delta_outcome_accuracy"] = (
        comparison["outcome_accuracy_dixon_coles"]
        - comparison["outcome_accuracy_baseline"]
    )

    report = {
        "rows_compared": int(len(merged)),
        "segments": comparison.to_dict(orient="records"),
    }
    return SegmentDiagnosticsResult(
        baseline_segments=baseline_segments,
        dixon_coles_segments=dixon_coles_segments,
        report=report,
    )


def write_segment_diagnostics_result(
    result: SegmentDiagnosticsResult,
    *,
    data_dir: Path,
) -> None:
    reports_dir = data_dir / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    baseline_path = reports_dir / "segment_diagnostics_baseline.csv"
    dixon_path = reports_dir / "segment_diagnostics_dixon_coles.csv"
    report_path = reports_dir / "segment_diagnostics_report.json"

    result.baseline_segments.to_csv(baseline_path, index=False)
    result.dixon_coles_segments.to_csv(dixon_path, index=False)
    report_path.write_text(
        json.dumps(result.report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
