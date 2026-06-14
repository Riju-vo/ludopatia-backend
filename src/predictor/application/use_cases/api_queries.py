from dataclasses import dataclass
from datetime import date
from typing import Any

from predictor.application.ports.prediction_repository import PredictionReadRepository


@dataclass(frozen=True, slots=True)
class ListMatchesForDate:
    repository: PredictionReadRepository

    async def execute(self, *, target_date: date) -> list[dict[str, Any]]:
        return list(await self.repository.list_matches_by_date(target_date=target_date))


@dataclass(frozen=True, slots=True)
class ListUpcomingMatches:
    repository: PredictionReadRepository

    async def execute(self, *, start_date: date, limit: int = 20) -> list[dict[str, Any]]:
        return list(
            await self.repository.list_upcoming_matches(
                start_date=start_date,
                limit=limit,
            )
        )


@dataclass(frozen=True, slots=True)
class GetMatchDetail:
    repository: PredictionReadRepository

    async def execute(self, *, match_id: str) -> dict[str, Any] | None:
        return await self.repository.get_match(match_id)


@dataclass(frozen=True, slots=True)
class GetMatchPrediction:
    repository: PredictionReadRepository

    async def execute(self, *, match_id: str) -> dict[str, Any] | None:
        return await self.repository.get_match_prediction(match_id)


@dataclass(frozen=True, slots=True)
class GetCurrentModel:
    repository: PredictionReadRepository

    async def execute(self) -> dict[str, Any] | None:
        return await self.repository.get_current_model()


@dataclass(frozen=True, slots=True)
class GetTeamProfile:
    repository: PredictionReadRepository

    async def execute(self, *, team_id: str) -> dict[str, Any] | None:
        return await self.repository.get_team_profile(team_id)


@dataclass(frozen=True, slots=True)
class GetGroups:
    repository: PredictionReadRepository

    async def execute(self) -> list[dict[str, Any]]:
        return list(await self.repository.get_groups())
