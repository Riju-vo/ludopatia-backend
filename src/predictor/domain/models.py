from dataclasses import dataclass
from datetime import date

from predictor.domain.enums import MatchQuality, MatchStatus


@dataclass(frozen=True, slots=True)
class CanonicalMatch:
    match_id: str
    kickoff_date: date
    status: MatchStatus
    home_team_id: str
    away_team_id: str
    competition_id: str
    location_id: str
    neutral: bool
    home_score_90: int | None
    away_score_90: int | None
    data_quality_status: MatchQuality
    source_name: str
