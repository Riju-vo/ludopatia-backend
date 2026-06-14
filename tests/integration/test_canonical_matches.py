from datetime import date
from pathlib import Path

from predictor.data.canonical_matches import build_canonical_matches
from predictor.data.contracts import SourcePaths

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_build_canonical_matches_has_no_unknown_references() -> None:
    result = build_canonical_matches(
        SourcePaths.from_data_dir(DATA_DIR),
        minimum_date=date(2021, 1, 1),
    )

    assert not result.matches.empty
    assert result.matches["home_team_id"].notna().all()
    assert result.matches["away_team_id"].notna().all()
    assert result.matches["competition_id"].notna().all()
    assert result.matches["location_id"].notna().all()


def test_ambiguous_extra_time_is_not_used_for_training() -> None:
    result = build_canonical_matches(
        SourcePaths.from_data_dir(DATA_DIR),
        minimum_date=date(2021, 1, 1),
    )

    assert not result.matches["has_shootout_evidence"].any()
    assert not result.matches["has_post_90_goal"].any()
    assert "ambiguous_extra_time" in set(result.exclusions["exclusion_reason"])


def test_finished_scores_are_integer_and_non_negative() -> None:
    result = build_canonical_matches(
        SourcePaths.from_data_dir(DATA_DIR),
        minimum_date=date(2021, 1, 1),
    )

    assert (result.matches["home_score_90"] >= 0).all()
    assert (result.matches["away_score_90"] >= 0).all()
    assert result.matches["home_score_90"].dtype.kind in {"i", "u"}
    assert result.matches["away_score_90"].dtype.kind in {"i", "u"}


def test_fixtures_have_complete_references() -> None:
    result = build_canonical_matches(
        SourcePaths.from_data_dir(DATA_DIR),
        minimum_date=date(2021, 1, 1),
    )

    reference_columns = [
        "home_team_id",
        "away_team_id",
        "competition_id",
        "location_id",
    ]
    assert result.fixtures[reference_columns].notna().all().all()
