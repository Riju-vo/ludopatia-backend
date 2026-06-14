from predictor.infrastructure.database.models import (
    CompetitionModel,
    EloRatingModel,
    FeatureSnapshotModel,
    LocationModel,
    MatchModel,
    ModelVersionModel,
    PredictionModel,
    PredictionScoreMatrixModel,
    RankingFifaModel,
    TeamModel,
    TournamentGroupModel,
    TournamentGroupTeamModel,
    TournamentHostModel,
)
from predictor.infrastructure.database.session import Base


def test_database_schema_registers_expected_tables() -> None:
    expected_tables = {
        "teams": TeamModel,
        "competitions": CompetitionModel,
        "locations": LocationModel,
        "tournament_hosts": TournamentHostModel,
        "tournament_groups": TournamentGroupModel,
        "tournament_group_teams": TournamentGroupTeamModel,
        "matches": MatchModel,
        "rankings_fifa": RankingFifaModel,
        "elo_ratings": EloRatingModel,
        "feature_snapshots": FeatureSnapshotModel,
        "model_versions": ModelVersionModel,
        "predictions": PredictionModel,
        "prediction_score_matrices": PredictionScoreMatrixModel,
    }

    for table_name in expected_tables:
        assert table_name in Base.metadata.tables


def test_predictions_table_contains_core_probability_columns() -> None:
    prediction_columns = Base.metadata.tables["predictions"].columns.keys()

    assert "predicted_home_lambda" in prediction_columns
    assert "predicted_away_lambda" in prediction_columns
    assert "home_win_probability" in prediction_columns
    assert "draw_probability" in prediction_columns
    assert "away_win_probability" in prediction_columns
