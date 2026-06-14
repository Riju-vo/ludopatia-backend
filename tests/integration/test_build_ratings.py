from pathlib import Path

from predictor.ratings.build import build_ratings

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def test_build_ratings_covers_matches_and_fixtures() -> None:
    result = build_ratings(data_dir=DATA_DIR)

    assert not result.match_ratings.empty
    assert not result.fixture_ratings.empty
    assert result.report["match_ratings_rows"] == len(result.match_ratings)
    assert result.report["fixture_ratings_rows"] == len(result.fixture_ratings)
    assert result.match_ratings["home_elo_pre"].notna().all()
    assert result.match_ratings["away_elo_pre"].notna().all()
    assert result.fixture_ratings["home_fifa_points_pre"].notna().all()
    assert result.fixture_ratings["away_fifa_points_pre"].notna().all()
