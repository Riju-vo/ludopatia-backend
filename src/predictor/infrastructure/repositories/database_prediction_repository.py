from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import selectinload

from predictor.infrastructure.database.models import (
    EloRatingModel,
    FeatureSnapshotModel,
    MatchModel,
    ModelVersionModel,
    PredictionModel,
    PredictionScoreMatrixModel,
    RankingFifaModel,
    TeamModel,
    TournamentGroupModel,
    TournamentGroupTeamModel,
)
from predictor.infrastructure.repositories.group_support import (
    WORLD_CUP_COMPETITION_ID,
    build_world_cup_groups_payload,
)


class DatabasePredictionRepository:
    def __init__(self, *, factory: async_sessionmaker) -> None:
        self._factory = factory

    async def list_matches_by_date(self, *, target_date: date) -> list[dict[str, Any]]:
        async with self._factory() as session:
            matches = await session.scalars(
                self._match_query().where(MatchModel.kickoff_date == target_date)
            )
            return [self._serialize_match(match) for match in matches.all()]

    async def list_upcoming_matches(
        self,
        *,
        start_date: date,
        limit: int,
    ) -> list[dict[str, Any]]:
        async with self._factory() as session:
            matches = await session.scalars(
                self._match_query()
                .where(MatchModel.kickoff_date >= start_date)
                .limit(limit)
            )
            return [self._serialize_match(match) for match in matches.all()]

    async def get_match(self, match_id: str) -> dict[str, Any] | None:
        async with self._factory() as session:
            match = await session.scalar(self._match_query().where(MatchModel.match_id == match_id))
            if match is None:
                return None

            feature_snapshot = await session.scalar(
                select(FeatureSnapshotModel).where(FeatureSnapshotModel.match_id == match_id)
            )
            payload = self._serialize_match(match)
            if feature_snapshot is not None:
                features = feature_snapshot.features
                payload["feature_snapshot"] = {
                    "elo": {
                        "home_pre": features["home_elo_pre"],
                        "away_pre": features["away_elo_pre"],
                        "difference_pre": features["elo_difference_pre"],
                    },
                    "fifa": {
                        "home_points_pre": features["home_fifa_points_pre"],
                        "away_points_pre": features["away_fifa_points_pre"],
                        "points_difference_pre": features["fifa_points_difference_pre"],
                        "home_rank_pre": features["home_fifa_rank_pre"],
                        "away_rank_pre": features["away_fifa_rank_pre"],
                    },
                    "form": {
                        "home_points_avg_weighted": features["home_points_avg_weighted"],
                        "away_points_avg_weighted": features["away_points_avg_weighted"],
                        "home_win_rate_weighted": features["home_win_rate_weighted"],
                        "away_win_rate_weighted": features["away_win_rate_weighted"],
                    },
                    "attack_defense": {
                        "home_attack_adjusted_elo_avg_weighted": features[
                            "home_attack_adjusted_elo_avg_weighted"
                        ],
                        "home_defense_adjusted_elo_avg_weighted": features[
                            "home_defense_adjusted_elo_avg_weighted"
                        ],
                        "away_attack_adjusted_elo_avg_weighted": features[
                            "away_attack_adjusted_elo_avg_weighted"
                        ],
                        "away_defense_adjusted_elo_avg_weighted": features[
                            "away_defense_adjusted_elo_avg_weighted"
                        ],
                    },
                }
            return payload

    async def get_match_prediction(self, match_id: str) -> dict[str, Any] | None:
        async with self._factory() as session:
            prediction = await session.scalar(
                select(PredictionModel)
                .where(PredictionModel.match_id == match_id)
                .order_by(PredictionModel.prediction_id.desc())
            )
            if prediction is None:
                return None

            matrix = await session.scalar(
                select(PredictionScoreMatrixModel).where(
                    PredictionScoreMatrixModel.prediction_id == prediction.prediction_id
                )
            )
            if matrix is None:
                return None

            top_scorelines = self._top_scorelines(matrix.matrix, matrix.score_labels, top_n=5)
            return {
                "match_id": match_id,
                "model_version": prediction.model_version,
                "lambdas": {
                    "home": prediction.predicted_home_lambda,
                    "away": prediction.predicted_away_lambda,
                    "total": prediction.predicted_total_goals,
                },
                "outcome_probabilities": {
                    "home_win": prediction.home_win_probability,
                    "draw": prediction.draw_probability,
                    "away_win": prediction.away_win_probability,
                },
                "top_scoreline": {
                    "score": prediction.top_scoreline,
                    "probability": prediction.top_scoreline_probability,
                },
                "top_scorelines": top_scorelines,
                "score_matrix": {
                    "labels": matrix.score_labels,
                    "matrix": matrix.matrix,
                },
            }

    async def get_current_model(self) -> dict[str, Any] | None:
        async with self._factory() as session:
            model = await session.scalar(
                select(ModelVersionModel)
                .where(ModelVersionModel.is_current.is_(True))
                .order_by(ModelVersionModel.trained_at_utc.desc())
            )
            if model is None:
                return None
            return {
                "model_version": model.model_version,
                "trained_at_utc": model.trained_at_utc.isoformat(),
                "model_family": model.model_family,
                "feature_count": model.feature_count,
                "training_rows": model.training_rows,
                "validation_rows": model.validation_rows,
                "validation_window": {
                    "start_date": model.validation_start_date.isoformat(),
                    "end_date": model.validation_end_date.isoformat(),
                },
                "holdout_metrics": model.metrics,
                "config": model.config,
            }

    async def get_team_profile(self, team_id: str) -> dict[str, Any] | None:
        async with self._factory() as session:
            team = await session.scalar(select(TeamModel).where(TeamModel.team_id == team_id))
            if team is None:
                return None

            latest_elo = await session.execute(
                select(EloRatingModel, MatchModel)
                .join(MatchModel, MatchModel.match_id == EloRatingModel.match_id)
                .where(EloRatingModel.team_id == team_id)
                .order_by(MatchModel.kickoff_date.desc(), MatchModel.match_id.desc())
                .limit(1)
            )
            elo_row = latest_elo.first()
            elo_payload = None
            if elo_row is not None:
                elo_rating, elo_match = elo_row
                elo_payload = {
                    "current": elo_rating.rating_post,
                    "matches_played": elo_rating.matches_played_pre + 1,
                    "latest_match_id": elo_match.match_id,
                    "latest_kickoff_date": elo_match.kickoff_date.isoformat(),
                }

            ranking = await session.scalar(
                select(RankingFifaModel)
                .where(RankingFifaModel.team_id == team_id)
                .order_by(
                    RankingFifaModel.snapshot_date.desc(),
                    RankingFifaModel.ranking_id.desc(),
                )
                .limit(1)
            )
            fifa_payload = None
            if ranking is not None:
                fifa_payload = {
                    "snapshot_date": ranking.snapshot_date.isoformat(),
                    "rank": ranking.rank_position,
                    "points": ranking.points,
                    "previous_rank": ranking.previous_rank,
                    "previous_points": ranking.previous_points,
                }

            recent_matches = await session.scalars(
                self._match_query()
                .where(or_(MatchModel.home_team_id == team_id, MatchModel.away_team_id == team_id))
                .where(MatchModel.status == "finished")
                .order_by(MatchModel.kickoff_date.desc(), MatchModel.match_id.desc())
                .limit(5)
            )
            upcoming_matches = await session.scalars(
                self._match_query()
                .where(or_(MatchModel.home_team_id == team_id, MatchModel.away_team_id == team_id))
                .where(MatchModel.status != "finished")
                .limit(5)
            )
            recent_match_rows = recent_matches.all()
            upcoming_match_rows = upcoming_matches.all()
            upcoming_match_ids = [match.match_id for match in upcoming_match_rows]
            upcoming_predictions_result = await session.scalars(
                select(PredictionModel).where(PredictionModel.match_id.in_(upcoming_match_ids))
            )
            upcoming_predictions = {
                row.match_id: row for row in upcoming_predictions_result.all()
            }

            return {
                "team_id": team.team_id,
                "name": team.canonical_name,
                "fifa_code": team.fifa_code,
                "confederation": team.confederation,
                "membership_status": team.membership_status,
                "model_scope": team.model_scope,
                "current_elo": elo_payload,
                "current_fifa": fifa_payload,
                "recent_results": [
                    self._serialize_team_result(match, team_id=team_id)
                    for match in recent_match_rows
                ],
                "upcoming_matches": [
                    self._serialize_team_upcoming_match(
                        match,
                        team_id=team_id,
                        prediction=upcoming_predictions.get(match.match_id),
                    )
                    for match in upcoming_match_rows
                ],
            }

    async def get_groups(self) -> list[dict[str, Any]]:
        async with self._factory() as session:
            group_rows = await session.execute(
                select(
                    TournamentGroupModel.group_code,
                    TournamentGroupTeamModel.seed_position,
                    TeamModel.team_id,
                    TeamModel.canonical_name,
                    TeamModel.fifa_code,
                    TeamModel.confederation,
                )
                .join(
                    TournamentGroupTeamModel,
                    TournamentGroupTeamModel.group_id == TournamentGroupModel.group_id,
                )
                .join(TeamModel, TeamModel.team_id == TournamentGroupTeamModel.team_id)
                .where(TournamentGroupModel.competition_id == WORLD_CUP_COMPETITION_ID)
                .where(TournamentGroupModel.edition_year == 2026)
                .order_by(
                    TournamentGroupModel.group_code,
                    TournamentGroupTeamModel.seed_position,
                )
            )
            group_members = pd.DataFrame(
                [
                    {
                        "group_code": row.group_code,
                        "position": row.seed_position,
                        "team_id": row.team_id,
                        "team_name": row.canonical_name,
                        "team_fifa_code": row.fifa_code,
                        "team_confederation": row.confederation,
                    }
                    for row in group_rows
                ]
            )

            matches_result = await session.scalars(
                self._match_query().where(
                    MatchModel.competition_id == WORLD_CUP_COMPETITION_ID
                )
            )
            matches = matches_result.all()
            fixtures = pd.DataFrame(
                [self._serialize_match_frame_row(match) for match in matches]
            )

            prediction_result = await session.scalars(
                select(PredictionModel).where(
                    PredictionModel.match_id.in_([match.match_id for match in matches])
                )
            )
            prediction_lookup = {
                prediction.match_id: {
                    "model_version": prediction.model_version,
                    "home_win_probability": prediction.home_win_probability,
                    "draw_probability": prediction.draw_probability,
                    "away_win_probability": prediction.away_win_probability,
                    "top_scoreline": prediction.top_scoreline,
                    "top_scoreline_probability": prediction.top_scoreline_probability,
                }
                for prediction in prediction_result.all()
            }

            return build_world_cup_groups_payload(
                group_members=group_members,
                fixtures=fixtures,
                prediction_lookup=prediction_lookup,
            )

    def _match_query(self):
        return (
            select(MatchModel)
            .options(
                selectinload(MatchModel.home_team),
                selectinload(MatchModel.away_team),
                selectinload(MatchModel.competition),
                selectinload(MatchModel.location),
            )
            .order_by(MatchModel.kickoff_date, MatchModel.match_id)
        )

    def _serialize_match(self, match: MatchModel) -> dict[str, Any]:
        home_team = match.home_team
        away_team = match.away_team
        competition = match.competition
        location = match.location
        return {
            "match_id": match.match_id,
            "kickoff_date": match.kickoff_date.isoformat(),
            "status": match.status,
            "neutral": match.neutral,
            "home_is_tournament_host": match.home_is_tournament_host,
            "away_is_tournament_host": match.away_is_tournament_host,
            "competition": {
                "competition_id": competition.competition_id,
                "name": competition.canonical_name,
                "type": competition.competition_type,
                "organizer_scope": competition.organizer_scope,
                "importance_level": competition.importance_level,
            },
            "location": {
                "location_id": location.location_id,
                "name": location.canonical_name,
                "country": location.canonical_country_name,
                "timezone": location.timezone,
            },
            "home_team": {
                "team_id": home_team.team_id,
                "name": home_team.canonical_name,
                "fifa_code": home_team.fifa_code,
                "confederation": home_team.confederation,
            },
            "away_team": {
                "team_id": away_team.team_id,
                "name": away_team.canonical_name,
                "fifa_code": away_team.fifa_code,
                "confederation": away_team.confederation,
            },
        }

    def _serialize_match_frame_row(self, match: MatchModel) -> dict[str, Any]:
        return {
            "match_id": match.match_id,
            "kickoff_date": match.kickoff_date,
            "status": match.status,
            "competition_id": match.competition_id,
            "location_id": match.location_id,
            "location_name": match.location.canonical_name,
            "location_country": match.location.canonical_country_name,
            "timezone": match.location.timezone,
            "home_team_id": match.home_team_id,
            "home_team_name": match.home_team.canonical_name,
            "home_team_fifa_code": match.home_team.fifa_code,
            "home_team_confederation": match.home_team.confederation,
            "away_team_id": match.away_team_id,
            "away_team_name": match.away_team.canonical_name,
            "away_team_fifa_code": match.away_team.fifa_code,
            "away_team_confederation": match.away_team.confederation,
        }

    def _top_scorelines(
        self,
        matrix: list[list[float]],
        labels: list[str],
        *,
        top_n: int,
    ) -> list[dict[str, Any]]:
        flattened: list[tuple[float, str]] = []
        for home_index, row in enumerate(matrix):
            for away_index, probability in enumerate(row):
                flattened.append(
                    (
                        float(probability),
                        f"{labels[home_index]}-{labels[away_index]}",
                    )
                )
        flattened.sort(key=lambda item: item[0], reverse=True)
        return [
            {"score": score, "probability": probability}
            for probability, score in flattened[:top_n]
        ]

    def _serialize_team_result(self, match: MatchModel, *, team_id: str) -> dict[str, Any]:
        team_is_home = match.home_team_id == team_id
        team_score = match.home_score_90 if team_is_home else match.away_score_90
        opponent_score = match.away_score_90 if team_is_home else match.home_score_90
        if team_score > opponent_score:
            outcome = "win"
        elif team_score < opponent_score:
            outcome = "loss"
        else:
            outcome = "draw"
        opponent_name = (
            match.away_team.canonical_name
            if team_is_home
            else match.home_team.canonical_name
        )
        return {
            "match_id": match.match_id,
            "kickoff_date": match.kickoff_date.isoformat(),
            "competition_id": match.competition_id,
            "is_home": team_is_home,
            "opponent": opponent_name,
            "team_score": team_score,
            "opponent_score": opponent_score,
            "outcome": outcome,
        }

    def _serialize_team_upcoming_match(
        self,
        match: MatchModel,
        *,
        team_id: str,
        prediction: PredictionModel | None,
    ) -> dict[str, Any]:
        team_is_home = match.home_team_id == team_id
        prediction_payload = None
        if prediction is not None:
            prediction_payload = {
                "home_win_probability": prediction.home_win_probability,
                "draw_probability": prediction.draw_probability,
                "away_win_probability": prediction.away_win_probability,
                "top_scoreline": prediction.top_scoreline,
            }
        opponent_name = (
            match.away_team.canonical_name
            if team_is_home
            else match.home_team.canonical_name
        )
        return {
            "match_id": match.match_id,
            "kickoff_date": match.kickoff_date.isoformat(),
            "competition_id": match.competition_id,
            "is_home": team_is_home,
            "opponent": opponent_name,
            "location": match.location.canonical_name,
            "prediction": prediction_payload,
        }
