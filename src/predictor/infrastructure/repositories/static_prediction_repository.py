import json
from datetime import date
from functools import cached_property
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from predictor.infrastructure.repositories.group_support import (
    build_world_cup_groups_payload,
    load_world_cup_group_members,
)


class StaticPredictionRepository:
    def __init__(self, *, data_dir: Path, model_dir: Path) -> None:
        self._data_dir = data_dir
        self._model_dir = model_dir

    @cached_property
    def _teams(self) -> pd.DataFrame:
        teams = pd.read_csv(self._data_dir / "reference" / "teams.csv")
        return teams.loc[
            :,
            ["team_id", "canonical_name", "fifa_code", "confederation"],
        ].rename(
            columns={
                "canonical_name": "team_name",
                "fifa_code": "team_fifa_code",
                "confederation": "team_confederation",
            }
        )

    @cached_property
    def _competitions(self) -> pd.DataFrame:
        competitions = pd.read_csv(self._data_dir / "reference" / "competitions.csv")
        return competitions.loc[
            :,
            [
                "competition_id",
                "canonical_name",
                "competition_type",
                "organizer_scope",
                "importance_level",
            ],
        ].rename(columns={"canonical_name": "competition_name"})

    @cached_property
    def _locations(self) -> pd.DataFrame:
        locations = pd.read_csv(self._data_dir / "reference" / "locations.csv")
        return locations.loc[
            :,
            [
                "location_id",
                "canonical_name",
                "canonical_country_name",
                "timezone",
            ],
        ].rename(
            columns={
                "canonical_name": "location_name",
                "canonical_country_name": "location_country",
            }
        )

    @cached_property
    def _rankings(self) -> pd.DataFrame:
        rankings = pd.read_csv(
            self._data_dir / "ranking_fifa_historical_complete.csv",
            parse_dates=["date"],
            low_memory=False,
        )
        rankings["date"] = rankings["date"].dt.date
        return rankings

    @cached_property
    def _fixtures(self) -> pd.DataFrame:
        fixtures = pd.read_csv(self._data_dir / "processed" / "fixtures.csv")
        fixtures["kickoff_date"] = pd.to_datetime(fixtures["kickoff_date"]).dt.date
        return self._enrich_matches(fixtures)

    @cached_property
    def _matches(self) -> pd.DataFrame:
        matches = pd.read_csv(self._data_dir / "processed" / "matches.csv")
        matches["kickoff_date"] = pd.to_datetime(matches["kickoff_date"]).dt.date
        return self._enrich_matches(matches)

    @cached_property
    def _team_elo_latest(self) -> pd.DataFrame:
        elo = pd.read_csv(self._data_dir / "processed" / "team_elo_latest.csv")
        elo["latest_kickoff_date"] = pd.to_datetime(elo["latest_kickoff_date"]).dt.date
        return elo.set_index("team_id", drop=False)

    @cached_property
    def _tournament_schedule(self) -> pd.DataFrame:
        schedule = pd.concat([self._matches, self._fixtures], ignore_index=True)
        return schedule.drop_duplicates(subset=["match_id"], keep="first").sort_values(
            ["kickoff_date", "match_id"]
        )

    @cached_property
    def _fixture_features(self) -> pd.DataFrame:
        features = pd.read_csv(self._data_dir / "processed" / "fixture_features.csv")
        return features.set_index("match_id", drop=False)

    @cached_property
    def _fixture_predictions(self) -> pd.DataFrame:
        predictions = pd.read_csv(self._data_dir / "predictions" / "fixture_predictions.csv")
        predictions["kickoff_date"] = pd.to_datetime(predictions["kickoff_date"]).dt.date
        return predictions.set_index("match_id", drop=False)

    @cached_property
    def _score_matrices(self) -> dict[str, dict[str, Any]]:
        payload = json.loads(
            (self._data_dir / "predictions" / "fixture_score_matrices.json").read_text(
                encoding="utf-8"
            )
        )
        return {
            prediction["match_id"]: prediction
            for prediction in payload.get("predictions", [])
        }

    @cached_property
    def _backtest_report(self) -> dict[str, Any] | None:
        report_path = self._data_dir / "reports" / "backtest_report.json"
        if not report_path.exists():
            return None
        return json.loads(report_path.read_text(encoding="utf-8"))

    @cached_property
    def _group_members(self) -> pd.DataFrame:
        return load_world_cup_group_members(data_dir=self._data_dir, teams=self._teams)

    def _enrich_matches(self, fixtures: pd.DataFrame) -> pd.DataFrame:
        home_teams = self._teams.rename(
            columns={
                "team_id": "home_team_id",
                "team_name": "home_team_name",
                "team_fifa_code": "home_team_fifa_code",
                "team_confederation": "home_team_confederation",
            }
        )
        away_teams = self._teams.rename(
            columns={
                "team_id": "away_team_id",
                "team_name": "away_team_name",
                "team_fifa_code": "away_team_fifa_code",
                "team_confederation": "away_team_confederation",
            }
        )

        enriched = fixtures.merge(home_teams, on="home_team_id", how="left")
        enriched = enriched.merge(away_teams, on="away_team_id", how="left")
        enriched = enriched.merge(self._competitions, on="competition_id", how="left")
        enriched = enriched.merge(self._locations, on="location_id", how="left")
        return enriched.sort_values(["kickoff_date", "match_id"]).reset_index(drop=True)

    async def list_matches_by_date(self, *, target_date: date) -> list[dict[str, Any]]:
        rows = self._fixtures.loc[self._fixtures["kickoff_date"] == target_date]
        return [self._serialize_match(row) for _, row in rows.iterrows()]

    async def list_upcoming_matches(
        self,
        *,
        start_date: date,
        limit: int,
    ) -> list[dict[str, Any]]:
        rows = self._fixtures.loc[self._fixtures["kickoff_date"] >= start_date]
        rows = rows.head(limit)
        return [self._serialize_match(row) for _, row in rows.iterrows()]

    async def get_match(self, match_id: str) -> dict[str, Any] | None:
        rows = self._fixtures.loc[self._fixtures["match_id"] == match_id]
        if rows.empty:
            return None
        row = rows.iloc[0]
        match_detail = self._serialize_match(row)
        features = self._fixture_features.loc[match_id].to_dict()
        match_detail["feature_snapshot"] = {
            "elo": {
                "home_pre": float(features["home_elo_pre"]),
                "away_pre": float(features["away_elo_pre"]),
                "difference_pre": float(features["elo_difference_pre"]),
            },
            "fifa": {
                "home_points_pre": float(features["home_fifa_points_pre"]),
                "away_points_pre": float(features["away_fifa_points_pre"]),
                "points_difference_pre": float(features["fifa_points_difference_pre"]),
                "home_rank_pre": int(features["home_fifa_rank_pre"]),
                "away_rank_pre": int(features["away_fifa_rank_pre"]),
            },
            "form": {
                "home_points_avg_weighted": float(features["home_points_avg_weighted"]),
                "away_points_avg_weighted": float(features["away_points_avg_weighted"]),
                "home_win_rate_weighted": float(features["home_win_rate_weighted"]),
                "away_win_rate_weighted": float(features["away_win_rate_weighted"]),
            },
            "attack_defense": {
                "home_attack_adjusted_elo_avg_weighted": float(
                    features["home_attack_adjusted_elo_avg_weighted"]
                ),
                "home_defense_adjusted_elo_avg_weighted": float(
                    features["home_defense_adjusted_elo_avg_weighted"]
                ),
                "away_attack_adjusted_elo_avg_weighted": float(
                    features["away_attack_adjusted_elo_avg_weighted"]
                ),
                "away_defense_adjusted_elo_avg_weighted": float(
                    features["away_defense_adjusted_elo_avg_weighted"]
                ),
            },
        }
        return match_detail

    async def get_match_prediction(self, match_id: str) -> dict[str, Any] | None:
        if match_id not in self._fixture_predictions.index:
            return None

        prediction = self._fixture_predictions.loc[match_id].to_dict()
        matrix_payload = self._score_matrices.get(match_id)
        if matrix_payload is None:
            return None

        matrix = np.array(matrix_payload["matrix"], dtype="float64")
        labels = list(matrix_payload["score_labels"])
        return {
            "match_id": match_id,
            "model_version": prediction["model_version"],
            "lambdas": {
                "home": float(prediction["predicted_home_lambda"]),
                "away": float(prediction["predicted_away_lambda"]),
                "total": float(prediction["predicted_total_goals"]),
            },
            "outcome_probabilities": {
                "home_win": float(prediction["home_win_probability"]),
                "draw": float(prediction["draw_probability"]),
                "away_win": float(prediction["away_win_probability"]),
            },
            "top_scoreline": {
                "score": prediction["top_scoreline"],
                "probability": float(prediction["top_scoreline_probability"]),
            },
            "top_scorelines": self._top_scorelines(matrix, labels, top_n=5),
            "score_matrix": {
                "labels": labels,
                "matrix": matrix_payload["matrix"],
            },
        }

    async def get_current_model(self) -> dict[str, Any] | None:
        model_versions = sorted(path for path in self._model_dir.iterdir() if path.is_dir())
        if not model_versions:
            return None

        current_version_dir = model_versions[-1]
        metadata = json.loads((current_version_dir / "metadata.json").read_text(encoding="utf-8"))
        result: dict[str, Any] = {
            "model_version": metadata["model_version"],
            "trained_at_utc": metadata["trained_at_utc"],
            "model_family": metadata["model_family"],
            "feature_count": metadata["feature_count"],
            "training_rows": metadata["training_rows"],
            "validation_rows": metadata["validation_rows"],
            "validation_window": {
                "start_date": metadata["validation_start_date"],
                "end_date": metadata["validation_end_date"],
            },
            "holdout_metrics": metadata["metrics"],
            "config": metadata["config"],
        }
        if self._backtest_report is not None:
            result["backtest_summary"] = self._backtest_report
        return result

    async def get_team_profile(self, team_id: str) -> dict[str, Any] | None:
        team_rows = self._teams.loc[self._teams["team_id"] == team_id]
        if team_rows.empty:
            return None

        team = team_rows.iloc[0]
        elo_payload = None
        if team_id in self._team_elo_latest.index:
            elo_row = self._team_elo_latest.loc[team_id]
            elo_payload = {
                "current": float(elo_row["elo_current"]),
                "matches_played": int(elo_row["elo_matches_played"]),
                "latest_match_id": elo_row["latest_match_id"],
                "latest_kickoff_date": elo_row["latest_kickoff_date"].isoformat(),
            }

        fifa_payload = self._latest_fifa_snapshot(team)
        recent_results = self._recent_team_results(team_id, limit=5)
        upcoming_matches = self._team_upcoming_matches(team_id, limit=5)
        return {
            "team_id": team["team_id"],
            "name": team["team_name"],
            "fifa_code": team["team_fifa_code"],
            "confederation": team["team_confederation"],
            "membership_status": team.get("membership_status"),
            "model_scope": team.get("model_scope"),
            "current_elo": elo_payload,
            "current_fifa": fifa_payload,
            "recent_results": recent_results,
            "upcoming_matches": upcoming_matches,
        }

    async def get_groups(self) -> list[dict[str, Any]]:
        prediction_lookup = {
            match_id: row.to_dict()
            for match_id, row in self._fixture_predictions.iterrows()
        }
        return build_world_cup_groups_payload(
            group_members=self._group_members,
            fixtures=self._tournament_schedule,
            prediction_lookup=prediction_lookup,
        )

    def _serialize_match(self, row: pd.Series) -> dict[str, Any]:
        return {
            "match_id": row["match_id"],
            "kickoff_date": row["kickoff_date"].isoformat(),
            "status": row["status"],
            "neutral": bool(row["neutral"]),
            "home_is_tournament_host": bool(row["home_is_tournament_host"]),
            "away_is_tournament_host": bool(row["away_is_tournament_host"]),
            "competition": {
                "competition_id": row["competition_id"],
                "name": row["competition_name"],
                "type": row["competition_type"],
                "organizer_scope": row["organizer_scope"],
                "importance_level": None
                if pd.isna(row["importance_level"])
                else int(row["importance_level"]),
            },
            "location": {
                "location_id": row["location_id"],
                "name": row["location_name"],
                "country": row["location_country"],
                "timezone": row["timezone"],
            },
            "home_team": {
                "team_id": row["home_team_id"],
                "name": row["home_team_name"],
                "fifa_code": row["home_team_fifa_code"],
                "confederation": row["home_team_confederation"],
            },
            "away_team": {
                "team_id": row["away_team_id"],
                "name": row["away_team_name"],
                "fifa_code": row["away_team_fifa_code"],
                "confederation": row["away_team_confederation"],
            },
        }

    def _latest_fifa_snapshot(self, team: pd.Series) -> dict[str, Any] | None:
        fifa_code = team["team_fifa_code"]
        team_name = team["team_name"]
        rankings = self._rankings
        candidate_rows = rankings.loc[rankings["team_short"] == fifa_code]
        if candidate_rows.empty:
            candidate_rows = rankings.loc[rankings["team"] == team_name]
        if candidate_rows.empty:
            return None
        latest = candidate_rows.sort_values(["date", "id"]).iloc[-1]
        return {
            "snapshot_date": latest["date"].isoformat(),
            "rank": None if pd.isna(latest["rank"]) else int(latest["rank"]),
            "points": None if pd.isna(latest["total_points"]) else float(latest["total_points"]),
            "previous_rank": (
                None if pd.isna(latest["previous_rank"]) else int(latest["previous_rank"])
            ),
            "previous_points": (
                None if pd.isna(latest["previous_points"]) else float(latest["previous_points"])
            ),
        }

    def _recent_team_results(self, team_id: str, *, limit: int) -> list[dict[str, Any]]:
        rows = self._matches.loc[
            (self._matches["home_team_id"] == team_id) | (self._matches["away_team_id"] == team_id)
        ].sort_values(["kickoff_date", "match_id"], ascending=[False, False]).head(limit)
        results: list[dict[str, Any]] = []
        for _, row in rows.iterrows():
            team_is_home = row["home_team_id"] == team_id
            team_score = int(row["home_score_90"] if team_is_home else row["away_score_90"])
            opponent_score = int(row["away_score_90"] if team_is_home else row["home_score_90"])
            if team_score > opponent_score:
                outcome = "win"
            elif team_score < opponent_score:
                outcome = "loss"
            else:
                outcome = "draw"
            results.append(
                {
                    "match_id": row["match_id"],
                    "kickoff_date": row["kickoff_date"].isoformat(),
                    "competition_id": row["competition_id"],
                    "is_home": team_is_home,
                    "opponent": row["away_team_name"] if team_is_home else row["home_team_name"],
                    "team_score": team_score,
                    "opponent_score": opponent_score,
                    "outcome": outcome,
                }
            )
        return results

    def _team_upcoming_matches(self, team_id: str, *, limit: int) -> list[dict[str, Any]]:
        rows = self._fixtures.loc[
            (self._fixtures["home_team_id"] == team_id)
            | (self._fixtures["away_team_id"] == team_id)
        ].sort_values(["kickoff_date", "match_id"]).head(limit)
        results: list[dict[str, Any]] = []
        for _, row in rows.iterrows():
            team_is_home = row["home_team_id"] == team_id
            prediction = None
            if row["match_id"] in self._fixture_predictions.index:
                prediction_row = self._fixture_predictions.loc[row["match_id"]]
                prediction = {
                    "home_win_probability": float(prediction_row["home_win_probability"]),
                    "draw_probability": float(prediction_row["draw_probability"]),
                    "away_win_probability": float(prediction_row["away_win_probability"]),
                    "top_scoreline": prediction_row["top_scoreline"],
                }
            results.append(
                {
                    "match_id": row["match_id"],
                    "kickoff_date": row["kickoff_date"].isoformat(),
                    "competition_id": row["competition_id"],
                    "is_home": team_is_home,
                    "opponent": row["away_team_name"] if team_is_home else row["home_team_name"],
                    "location": row["location_name"],
                    "prediction": prediction,
                }
            )
        return results

    def _top_scorelines(
        self,
        matrix: np.ndarray,
        labels: list[str],
        *,
        top_n: int,
    ) -> list[dict[str, Any]]:
        flattened = matrix.flatten()
        top_indexes = np.argsort(flattened)[::-1][:top_n]
        width = matrix.shape[1]
        results: list[dict[str, Any]] = []
        for index in top_indexes:
            home_index = int(index // width)
            away_index = int(index % width)
            results.append(
                {
                    "score": f"{labels[home_index]}-{labels[away_index]}",
                    "probability": float(flattened[index]),
                }
            )
        return results
