import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

BASELINE_FIFA_POINTS = 1000.0
BASELINE_ELO = 1500.0
TEAM_FEATURE_COLUMNS = [
    "history_matches_used",
    "history_weight_sum",
    "goals_for_avg_weighted",
    "goals_against_avg_weighted",
    "goal_difference_avg_weighted",
    "points_avg_weighted",
    "win_rate_weighted",
    "draw_rate_weighted",
    "loss_rate_weighted",
    "clean_sheet_rate_weighted",
    "failed_to_score_rate_weighted",
    "attack_adjusted_elo_avg_weighted",
    "defense_adjusted_elo_avg_weighted",
    "attack_adjusted_fifa_avg_weighted",
    "defense_adjusted_fifa_avg_weighted",
]


@dataclass(frozen=True, slots=True)
class FeatureBuildConfig:
    half_life_days: float = 365.0
    max_history_days: int = 365 * 5


@dataclass(frozen=True, slots=True)
class FeatureBuildResult:
    match_features: pd.DataFrame
    fixture_features: pd.DataFrame
    report: dict[str, object]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float | None:
    valid = values.notna() & weights.notna()
    if not valid.any():
        return None
    valid_values = values.loc[valid].astype("float64")
    valid_weights = weights.loc[valid].astype("float64")
    weight_sum = float(valid_weights.sum())
    if weight_sum <= 0:
        return None
    return float((valid_values * valid_weights).sum() / weight_sum)


def _opponent_elo_factor(series: pd.Series) -> pd.Series:
    return 10 ** ((series.astype("float64") - BASELINE_ELO) / 400.0)


def _opponent_fifa_factor(series: pd.Series) -> pd.Series:
    return (series.astype("float64") / BASELINE_FIFA_POINTS).clip(lower=0.5, upper=2.5)


def _with_team_perspective(match_ratings: pd.DataFrame) -> pd.DataFrame:
    ordered = match_ratings.copy()
    ordered["kickoff_date"] = pd.to_datetime(ordered["kickoff_date"])

    home_rows = pd.DataFrame(
        {
            "match_id": ordered["match_id"],
            "kickoff_date": ordered["kickoff_date"],
            "team_id": ordered["home_team_id"],
            "opponent_team_id": ordered["away_team_id"],
            "team_side": "home",
            "goals_for": ordered["home_score_90"],
            "goals_against": ordered["away_score_90"],
            "team_elo_pre": ordered["home_elo_pre"],
            "opponent_elo_pre": ordered["away_elo_pre"],
            "team_fifa_points_pre": ordered["home_fifa_points_pre"],
            "opponent_fifa_points_pre": ordered["away_fifa_points_pre"],
        }
    )
    away_rows = pd.DataFrame(
        {
            "match_id": ordered["match_id"],
            "kickoff_date": ordered["kickoff_date"],
            "team_id": ordered["away_team_id"],
            "opponent_team_id": ordered["home_team_id"],
            "team_side": "away",
            "goals_for": ordered["away_score_90"],
            "goals_against": ordered["home_score_90"],
            "team_elo_pre": ordered["away_elo_pre"],
            "opponent_elo_pre": ordered["home_elo_pre"],
            "team_fifa_points_pre": ordered["away_fifa_points_pre"],
            "opponent_fifa_points_pre": ordered["home_fifa_points_pre"],
        }
    )

    team_matches = pd.concat([home_rows, away_rows], ignore_index=True)
    team_matches["goal_difference"] = team_matches["goals_for"] - team_matches["goals_against"]
    team_matches["points"] = 1.0
    team_matches.loc[team_matches["goals_for"] > team_matches["goals_against"], "points"] = 3.0
    team_matches.loc[team_matches["goals_for"] < team_matches["goals_against"], "points"] = 0.0
    team_matches["win"] = (team_matches["goals_for"] > team_matches["goals_against"]).astype(
        "float64"
    )
    team_matches["draw"] = (team_matches["goals_for"] == team_matches["goals_against"]).astype(
        "float64"
    )
    team_matches["loss"] = (team_matches["goals_for"] < team_matches["goals_against"]).astype(
        "float64"
    )
    team_matches["clean_sheet"] = (team_matches["goals_against"] == 0).astype("float64")
    team_matches["failed_to_score"] = (team_matches["goals_for"] == 0).astype("float64")

    elo_factor = _opponent_elo_factor(team_matches["opponent_elo_pre"])
    fifa_factor = _opponent_fifa_factor(team_matches["opponent_fifa_points_pre"])
    team_matches["attack_adjusted_elo"] = team_matches["goals_for"] * elo_factor
    team_matches["defense_adjusted_elo"] = team_matches["goals_against"] / elo_factor
    team_matches["attack_adjusted_fifa"] = team_matches["goals_for"] * fifa_factor
    team_matches["defense_adjusted_fifa"] = team_matches["goals_against"] / fifa_factor

    return team_matches.sort_values(["team_id", "kickoff_date", "match_id"]).reset_index(drop=True)


def _history_snapshot(
    history: pd.DataFrame,
    *,
    reference_date: pd.Timestamp,
    config: FeatureBuildConfig,
) -> dict[str, float | int | None]:
    age_days = (reference_date - history["kickoff_date"]).dt.days
    eligible = history.loc[(age_days > 0) & (age_days <= config.max_history_days)].copy()
    if eligible.empty:
        return {
            "history_matches_used": 0,
            "history_weight_sum": 0.0,
            **{column: None for column in TEAM_FEATURE_COLUMNS[2:]},
        }

    eligible["age_days"] = (reference_date - eligible["kickoff_date"]).dt.days.astype("float64")
    eligible["weight"] = 0.5 ** (eligible["age_days"] / config.half_life_days)

    return {
        "history_matches_used": int(len(eligible)),
        "history_weight_sum": round(float(eligible["weight"].sum()), 6),
        "goals_for_avg_weighted": _weighted_mean(eligible["goals_for"], eligible["weight"]),
        "goals_against_avg_weighted": _weighted_mean(
            eligible["goals_against"], eligible["weight"]
        ),
        "goal_difference_avg_weighted": _weighted_mean(
            eligible["goal_difference"], eligible["weight"]
        ),
        "points_avg_weighted": _weighted_mean(eligible["points"], eligible["weight"]),
        "win_rate_weighted": _weighted_mean(eligible["win"], eligible["weight"]),
        "draw_rate_weighted": _weighted_mean(eligible["draw"], eligible["weight"]),
        "loss_rate_weighted": _weighted_mean(eligible["loss"], eligible["weight"]),
        "clean_sheet_rate_weighted": _weighted_mean(
            eligible["clean_sheet"], eligible["weight"]
        ),
        "failed_to_score_rate_weighted": _weighted_mean(
            eligible["failed_to_score"], eligible["weight"]
        ),
        "attack_adjusted_elo_avg_weighted": _weighted_mean(
            eligible["attack_adjusted_elo"], eligible["weight"]
        ),
        "defense_adjusted_elo_avg_weighted": _weighted_mean(
            eligible["defense_adjusted_elo"], eligible["weight"]
        ),
        "attack_adjusted_fifa_avg_weighted": _weighted_mean(
            eligible["attack_adjusted_fifa"], eligible["weight"]
        ),
        "defense_adjusted_fifa_avg_weighted": _weighted_mean(
            eligible["defense_adjusted_fifa"], eligible["weight"]
        ),
    }


def _build_match_team_features(
    team_matches: pd.DataFrame,
    *,
    config: FeatureBuildConfig,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    for team_id, group in team_matches.groupby("team_id", sort=False):
        ordered = group.sort_values(["kickoff_date", "match_id"]).reset_index(drop=True)
        for index, row in ordered.iterrows():
            prior = ordered.iloc[:index]
            snapshot = _history_snapshot(
                prior,
                reference_date=row["kickoff_date"],
                config=config,
            )
            rows.append(
                {
                    "match_id": row["match_id"],
                    "kickoff_date": row["kickoff_date"].strftime("%Y-%m-%d"),
                    "team_id": team_id,
                    "team_side": row["team_side"],
                    **snapshot,
                }
            )

    return pd.DataFrame(rows)


def _build_fixture_team_features(
    fixture_ratings: pd.DataFrame,
    team_matches: pd.DataFrame,
    *,
    config: FeatureBuildConfig,
) -> pd.DataFrame:
    history_by_team = {
        team_id: group.sort_values(["kickoff_date", "match_id"]).reset_index(drop=True)
        for team_id, group in team_matches.groupby("team_id", sort=False)
    }

    fixtures = fixture_ratings.copy()
    fixtures["kickoff_date"] = pd.to_datetime(fixtures["kickoff_date"])

    rows: list[dict[str, object]] = []
    for row in fixtures.itertuples(index=False):
        for side in ("home", "away"):
            team_id = getattr(row, f"{side}_team_id")
            history = history_by_team.get(team_id, pd.DataFrame(columns=team_matches.columns))
            snapshot = _history_snapshot(
                history,
                reference_date=row.kickoff_date,
                config=config,
            )
            rows.append(
                {
                    "match_id": row.match_id,
                    "kickoff_date": row.kickoff_date.strftime("%Y-%m-%d"),
                    "team_id": team_id,
                    "team_side": side,
                    **snapshot,
                }
            )

    return pd.DataFrame(rows)


def _merge_team_features(
    base: pd.DataFrame,
    team_features: pd.DataFrame,
) -> pd.DataFrame:
    merge_columns = [
        column for column in team_features.columns if column not in {"team_id", "team_side"}
    ]

    home_rows = team_features.loc[
        team_features["team_side"] == "home",
        merge_columns + ["team_id"],
    ]
    away_rows = team_features.loc[
        team_features["team_side"] == "away",
        merge_columns + ["team_id"],
    ]

    home = home_rows.rename(
        columns={
            "team_id": "home_team_id",
            **{column: f"home_{column}" for column in TEAM_FEATURE_COLUMNS},
        }
    )
    away = away_rows.rename(
        columns={
            "team_id": "away_team_id",
            **{column: f"away_{column}" for column in TEAM_FEATURE_COLUMNS},
        }
    )

    merged = base.merge(
        home,
        on=["match_id", "kickoff_date", "home_team_id"],
        how="left",
    ).merge(
        away,
        on=["match_id", "kickoff_date", "away_team_id"],
        how="left",
    )

    for column in TEAM_FEATURE_COLUMNS:
        merged[f"{column}_difference"] = merged[f"home_{column}"] - merged[f"away_{column}"]

    return merged


def _coverage(frame: pd.DataFrame) -> dict[str, int]:
    return {
        column: int(frame[column].notna().sum())
        for column in frame.columns
        if column.endswith("_weighted")
        or column.endswith("_difference")
        or column.endswith("_used")
    }


def build_features_from_frames(
    *,
    match_ratings: pd.DataFrame,
    fixture_ratings: pd.DataFrame,
    config: FeatureBuildConfig | None = None,
) -> FeatureBuildResult:
    config = config or FeatureBuildConfig()
    team_matches = _with_team_perspective(match_ratings)
    match_team_features = _build_match_team_features(team_matches, config=config)
    fixture_team_features = _build_fixture_team_features(
        fixture_ratings,
        team_matches,
        config=config,
    )

    match_features = _merge_team_features(match_ratings.copy(), match_team_features)
    fixture_features = _merge_team_features(fixture_ratings.copy(), fixture_team_features)

    report = {
        "feature_config": {
            "half_life_days": config.half_life_days,
            "max_history_days": config.max_history_days,
        },
        "match_features_rows": int(len(match_features)),
        "fixture_features_rows": int(len(fixture_features)),
        "team_history_rows": int(len(team_matches)),
        "match_feature_coverage": _coverage(match_features),
        "fixture_feature_coverage": _coverage(fixture_features),
    }
    return FeatureBuildResult(
        match_features=match_features,
        fixture_features=fixture_features,
        report=report,
    )


def build_features(
    *,
    data_dir: Path,
    config: FeatureBuildConfig | None = None,
) -> FeatureBuildResult:
    processed_dir = data_dir / "processed"
    match_ratings = pd.read_csv(processed_dir / "match_ratings.csv")
    fixture_ratings = pd.read_csv(processed_dir / "fixture_ratings.csv")
    return build_features_from_frames(
        match_ratings=match_ratings,
        fixture_ratings=fixture_ratings,
        config=config,
    )


def write_features_result(result: FeatureBuildResult, *, data_dir: Path) -> None:
    processed_dir = data_dir / "processed"
    reports_dir = data_dir / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    match_features_path = processed_dir / "match_features.csv"
    fixture_features_path = processed_dir / "fixture_features.csv"
    report_path = reports_dir / "features_quality.json"

    result.match_features.to_csv(match_features_path, index=False)
    result.fixture_features.to_csv(fixture_features_path, index=False)

    result.report["output_files"] = {
        "match_features": {
            "path": "data/processed/match_features.csv",
            "sha256": _sha256(match_features_path),
        },
        "fixture_features": {
            "path": "data/processed/fixture_features.csv",
            "sha256": _sha256(fixture_features_path),
        },
    }

    report_path.write_text(
        json.dumps(result.report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
