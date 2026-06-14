from pathlib import Path

from predictor.features.build import build_features

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_build_features_covers_matches_and_fixtures() -> None:
    result = build_features(data_dir=DATA_DIR)

    assert not result.match_features.empty
    assert not result.fixture_features.empty
    assert result.report["match_features_rows"] == len(result.match_features)
    assert result.report["fixture_features_rows"] == len(result.fixture_features)
    assert "home_goals_for_avg_weighted" in result.match_features.columns
    assert "away_attack_adjusted_elo_avg_weighted" in result.fixture_features.columns
    assert result.fixture_features["home_history_matches_used"].ge(0).all()
