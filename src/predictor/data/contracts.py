from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SourcePaths:
    results: Path
    teams: Path
    competitions: Path
    locations: Path
    goalscorers: Path
    shootouts: Path

    @classmethod
    def from_data_dir(cls, data_dir: Path) -> "SourcePaths":
        return cls(
            results=data_dir / "results.csv",
            teams=data_dir / "reference" / "teams.csv",
            competitions=data_dir / "reference" / "competitions.csv",
            locations=data_dir / "reference" / "locations.csv",
            goalscorers=data_dir / "raw" / "goalscorers.csv",
            shootouts=data_dir / "raw" / "shootouts.csv",
        )


REQUIRED_COLUMNS = {
    "results": {
        "date",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "tournament",
        "city",
        "country",
        "neutral",
    },
    "teams": {"team_id", "source_name", "membership_status", "model_scope"},
    "competitions": {"competition_id", "source_label", "model_scope"},
    "locations": {"location_id", "source_city", "source_country"},
    "goalscorers": {"date", "home_team", "away_team", "minute"},
    "shootouts": {"date", "home_team", "away_team"},
}
