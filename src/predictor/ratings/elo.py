import math
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class EloConfig:
    initial_rating: float = 1500.0
    home_advantage: float = 50.0

    def k_for_importance(self, importance_level: int) -> float:
        mapping = {
            5: 60.0,
            4: 50.0,
            3: 40.0,
            2: 30.0,
            1: 20.0,
            0: 20.0,
        }
        return mapping.get(int(importance_level), 20.0)


def _expected_score(home_rating: float, away_rating: float, home_advantage: float) -> float:
    return 1.0 / (1.0 + 10 ** (-(home_rating + home_advantage - away_rating) / 400.0))


def _actual_score(home_goals: int, away_goals: int) -> float:
    if home_goals > away_goals:
        return 1.0
    if home_goals < away_goals:
        return 0.0
    return 0.5


def _margin_multiplier(goal_difference: int, rating_gap: float) -> float:
    if goal_difference <= 1:
        return 1.0
    return math.log(goal_difference + 1.0) * (2.2 / (abs(rating_gap) * 0.001 + 2.2))


def build_elo_history(
    matches: pd.DataFrame, competitions: pd.DataFrame, config: EloConfig
) -> pd.DataFrame:
    competition_importance = (
        competitions.loc[:, ["competition_id", "importance_level"]]
        .drop_duplicates(subset=["competition_id"])
        .set_index("competition_id")["importance_level"]
        .astype("int64")
    )

    ordered = matches.copy()
    ordered["kickoff_date"] = pd.to_datetime(ordered["kickoff_date"])
    ordered["importance_level"] = ordered["competition_id"].map(competition_importance).fillna(1)
    ordered = ordered.sort_values(["kickoff_date", "match_id"]).reset_index(drop=True)

    ratings: dict[str, float] = {}
    match_counts: dict[str, int] = {}
    rows: list[dict[str, object]] = []

    for row in ordered.itertuples(index=False):
        home_team_id = row.home_team_id
        away_team_id = row.away_team_id
        home_pre = ratings.get(home_team_id, config.initial_rating)
        away_pre = ratings.get(away_team_id, config.initial_rating)
        home_matches_pre = match_counts.get(home_team_id, 0)
        away_matches_pre = match_counts.get(away_team_id, 0)

        applied_home_advantage = (
            0.0 if str(row.neutral).lower() == "true" else config.home_advantage
        )
        expected_home = _expected_score(home_pre, away_pre, applied_home_advantage)
        actual_home = _actual_score(int(row.home_score_90), int(row.away_score_90))
        goal_difference = abs(int(row.home_score_90) - int(row.away_score_90))
        rating_gap = (home_pre + applied_home_advantage) - away_pre
        margin_multiplier = _margin_multiplier(goal_difference, rating_gap)
        k_factor = config.k_for_importance(int(row.importance_level))
        delta = k_factor * margin_multiplier * (actual_home - expected_home)

        home_post = home_pre + delta
        away_post = away_pre - delta

        ratings[home_team_id] = home_post
        ratings[away_team_id] = away_post
        match_counts[home_team_id] = home_matches_pre + 1
        match_counts[away_team_id] = away_matches_pre + 1

        rows.append(
            {
                "match_id": row.match_id,
                "kickoff_date": row.kickoff_date.strftime("%Y-%m-%d"),
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
                "home_elo_pre": round(home_pre, 6),
                "away_elo_pre": round(away_pre, 6),
                "home_elo_post": round(home_post, 6),
                "away_elo_post": round(away_post, 6),
                "elo_difference_pre": round(home_pre - away_pre, 6),
                "home_elo_matches_pre": home_matches_pre,
                "away_elo_matches_pre": away_matches_pre,
                "k_factor": k_factor,
                "applied_home_advantage": applied_home_advantage,
                "margin_multiplier": round(margin_multiplier, 6),
                "expected_home_score": round(expected_home, 6),
                "actual_home_score": actual_home,
            }
        )

    return pd.DataFrame(rows)


def build_fixture_elo_snapshots(
    fixtures: pd.DataFrame,
    match_elo_history: pd.DataFrame,
    config: EloConfig,
) -> pd.DataFrame:
    latest_ratings: dict[str, tuple[float, int]] = {}
    for row in match_elo_history.itertuples(index=False):
        latest_ratings[row.home_team_id] = (
            float(row.home_elo_post),
            int(row.home_elo_matches_pre) + 1,
        )
        latest_ratings[row.away_team_id] = (
            float(row.away_elo_post),
            int(row.away_elo_matches_pre) + 1,
        )

    ordered = fixtures.copy()
    ordered["kickoff_date"] = pd.to_datetime(ordered["kickoff_date"])
    ordered = ordered.sort_values(["kickoff_date", "match_id"]).reset_index(drop=True)

    rows: list[dict[str, object]] = []
    for row in ordered.itertuples(index=False):
        home_pre, home_count = latest_ratings.get(row.home_team_id, (config.initial_rating, 0))
        away_pre, away_count = latest_ratings.get(row.away_team_id, (config.initial_rating, 0))
        applied_home_advantage = (
            0.0 if str(row.neutral).lower() == "true" else config.home_advantage
        )
        expected_home = _expected_score(home_pre, away_pre, applied_home_advantage)

        rows.append(
            {
                "match_id": row.match_id,
                "kickoff_date": row.kickoff_date.strftime("%Y-%m-%d"),
                "home_team_id": row.home_team_id,
                "away_team_id": row.away_team_id,
                "home_elo_pre": round(home_pre, 6),
                "away_elo_pre": round(away_pre, 6),
                "elo_difference_pre": round(home_pre - away_pre, 6),
                "home_elo_matches_pre": home_count,
                "away_elo_matches_pre": away_count,
                "applied_home_advantage": applied_home_advantage,
                "expected_home_score": round(expected_home, 6),
            }
        )

    return pd.DataFrame(rows)
