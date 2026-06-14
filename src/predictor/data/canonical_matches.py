import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd

from predictor.data.contracts import SourcePaths
from predictor.data.validation import validate_sources
from predictor.domain.enums import MatchQuality, MatchStatus

MATCH_KEY = ["date", "home_team", "away_team"]


@dataclass(frozen=True, slots=True)
class BuildResult:
    matches: pd.DataFrame
    fixtures: pd.DataFrame
    exclusions: pd.DataFrame
    report: dict[str, object]


def _stable_match_id(row: pd.Series) -> str:
    value = "|".join(
        [
            str(row["date"]),
            str(row["home_team"]),
            str(row["away_team"]),
            str(row["tournament"]),
            str(row["city"]),
            str(row["country"]),
        ]
    )
    return "match_" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _to_bool(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().map({"true": True, "false": False})


def build_canonical_matches(
    paths: SourcePaths,
    *,
    minimum_date: date = date(2021, 1, 1),
) -> BuildResult:
    validations = validate_sources(paths)

    results = pd.read_csv(paths.results, parse_dates=["date"])
    results = results.loc[results["date"].dt.date >= minimum_date].copy()
    results["date"] = results["date"].dt.strftime("%Y-%m-%d")
    results["neutral"] = _to_bool(results["neutral"])

    teams = pd.read_csv(paths.teams).set_index("source_name")
    competitions = pd.read_csv(paths.competitions).set_index("source_label")
    locations = pd.read_csv(paths.locations).set_index(["source_city", "source_country"])
    hosts = pd.read_csv(paths.locations.parent / "tournament_hosts.csv")

    results["home_team_id"] = results["home_team"].map(teams["team_id"])
    results["away_team_id"] = results["away_team"].map(teams["team_id"])
    results["home_model_scope"] = results["home_team"].map(teams["model_scope"])
    results["away_model_scope"] = results["away_team"].map(teams["model_scope"])
    results["competition_id"] = results["tournament"].map(competitions["competition_id"])
    results["competition_model_scope"] = results["tournament"].map(competitions["model_scope"])

    location_map = locations["location_id"].to_dict()
    results["location_id"] = [
        location_map.get((city, country))
        for city, country in zip(results["city"], results["country"], strict=True)
    ]

    shootouts = pd.read_csv(paths.shootouts, usecols=MATCH_KEY)
    shootouts["date"] = pd.to_datetime(shootouts["date"]).dt.strftime("%Y-%m-%d")
    shootout_keys = set(map(tuple, shootouts[MATCH_KEY].itertuples(index=False, name=None)))

    goals = pd.read_csv(paths.goalscorers, usecols=MATCH_KEY + ["minute"])
    goals["date"] = pd.to_datetime(goals["date"]).dt.strftime("%Y-%m-%d")
    extra_time_keys = set(
        map(
            tuple,
            goals.loc[goals["minute"] > 90, MATCH_KEY].itertuples(index=False, name=None),
        )
    )

    keys = list(results[MATCH_KEY].itertuples(index=False, name=None))
    results["has_shootout_evidence"] = [key in shootout_keys for key in keys]
    results["has_post_90_goal"] = [key in extra_time_keys for key in keys]
    results["match_id"] = results.apply(_stable_match_id, axis=1)
    results["source_name"] = "international_results"
    results["played_year"] = pd.to_datetime(results["date"]).dt.year

    host_lookup = (
        hosts.groupby(["competition_id", "played_year"])["host_team_id"]
        .agg(lambda values: frozenset(values))
        .to_dict()
    )
    host_sets = [
        host_lookup.get((competition_id, played_year), frozenset())
        for competition_id, played_year in zip(
            results["competition_id"], results["played_year"], strict=True
        )
    ]
    results["home_is_tournament_host"] = [
        team_id in host_set
        for team_id, host_set in zip(results["home_team_id"], host_sets, strict=True)
    ]
    results["away_is_tournament_host"] = [
        team_id in host_set
        for team_id, host_set in zip(results["away_team_id"], host_sets, strict=True)
    ]

    score_missing = results[["home_score", "away_score"]].isna().any(axis=1)
    score_partial = results[["home_score", "away_score"]].isna().any(axis=1) & ~results[
        ["home_score", "away_score"]
    ].isna().all(axis=1)
    results["status"] = MatchStatus.FINISHED.value
    results.loc[score_missing & ~score_partial, "status"] = MatchStatus.SCHEDULED.value
    results.loc[score_partial, "status"] = MatchStatus.UNKNOWN.value

    unknown_reference = (
        results[["home_team_id", "away_team_id", "competition_id", "location_id"]]
        .isna()
        .any(axis=1)
    )
    out_of_scope = (
        (results["home_model_scope"] != "include")
        | (results["away_model_scope"] != "include")
        | (results["competition_model_scope"] != "include")
    )
    ambiguous = results["has_shootout_evidence"] | results["has_post_90_goal"]

    results["data_quality_status"] = MatchQuality.VERIFIED_STANDARD_TIME.value
    results.loc[ambiguous, "data_quality_status"] = MatchQuality.AMBIGUOUS_EXTRA_TIME.value
    results.loc[out_of_scope, "data_quality_status"] = MatchQuality.OUT_OF_MODEL_SCOPE.value
    results.loc[unknown_reference, "data_quality_status"] = MatchQuality.UNKNOWN_REFERENCE.value
    results.loc[score_partial, "data_quality_status"] = MatchQuality.INVALID_SCORE.value

    results["exclusion_reason"] = ""
    results.loc[ambiguous, "exclusion_reason"] = "ambiguous_extra_time"
    results.loc[out_of_scope, "exclusion_reason"] = "out_of_model_scope"
    results.loc[unknown_reference, "exclusion_reason"] = "unknown_reference"
    results.loc[score_partial, "exclusion_reason"] = "partial_score"

    canonical_columns = [
        "match_id",
        "date",
        "status",
        "home_team_id",
        "away_team_id",
        "competition_id",
        "location_id",
        "neutral",
        "home_is_tournament_host",
        "away_is_tournament_host",
        "home_score",
        "away_score",
        "has_shootout_evidence",
        "has_post_90_goal",
        "data_quality_status",
        "source_name",
    ]

    fixture_mask = results["status"] == MatchStatus.SCHEDULED.value
    training_mask = (results["status"] == MatchStatus.FINISHED.value) & (
        results["data_quality_status"] == MatchQuality.VERIFIED_STANDARD_TIME.value
    )
    exclusion_mask = ~training_mask & ~fixture_mask

    matches = results.loc[training_mask, canonical_columns].copy()
    matches = matches.rename(
        columns={
            "date": "kickoff_date",
            "home_score": "home_score_90",
            "away_score": "away_score_90",
        }
    )
    matches[["home_score_90", "away_score_90"]] = matches[
        ["home_score_90", "away_score_90"]
    ].astype("int64")

    fixtures = results.loc[fixture_mask, canonical_columns].copy()
    fixtures = fixtures.rename(
        columns={
            "date": "kickoff_date",
            "home_score": "home_score_90",
            "away_score": "away_score_90",
        }
    )

    exclusions = results.loc[
        exclusion_mask,
        [
            "match_id",
            "date",
            "home_team",
            "away_team",
            "tournament",
            "city",
            "country",
            "exclusion_reason",
            "data_quality_status",
        ],
    ].copy()

    report = {
        "minimum_date": minimum_date.isoformat(),
        "source_rows": int(len(results)),
        "training_matches": int(len(matches)),
        "fixtures": int(len(fixtures)),
        "exclusions": int(len(exclusions)),
        "exclusions_by_reason": {
            str(key): int(value)
            for key, value in exclusions["exclusion_reason"].value_counts().items()
        },
        "ambiguous_extra_time": int(ambiguous.sum()),
        "unknown_references": int(unknown_reference.sum()),
        "source_validations": [
            {
                "name": item.name,
                "rows": item.rows,
                "valid": item.valid,
                "sha256": _sha256(item.path),
            }
            for item in validations
        ],
    }
    return BuildResult(
        matches=matches,
        fixtures=fixtures,
        exclusions=exclusions,
        report=report,
    )


def write_build_result(
    result: BuildResult,
    *,
    data_dir: Path,
) -> None:
    processed_dir = data_dir / "processed"
    reports_dir = data_dir / "reports"
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    result.matches.to_csv(processed_dir / "matches.csv", index=False)
    result.fixtures.to_csv(processed_dir / "fixtures.csv", index=False)
    result.exclusions.to_csv(reports_dir / "match_exclusions.csv", index=False)
    result.report["output_files"] = {
        "matches": {
            "path": "data/processed/matches.csv",
            "sha256": _sha256(processed_dir / "matches.csv"),
        },
        "fixtures": {
            "path": "data/processed/fixtures.csv",
            "sha256": _sha256(processed_dir / "fixtures.csv"),
        },
        "exclusions": {
            "path": "data/reports/match_exclusions.csv",
            "sha256": _sha256(reports_dir / "match_exclusions.csv"),
        },
    }
    (reports_dir / "data_quality.json").write_text(
        json.dumps(result.report, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
