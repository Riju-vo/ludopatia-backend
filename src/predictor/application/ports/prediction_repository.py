from collections.abc import Sequence
from datetime import date
from typing import Any, Protocol


class PredictionReadRepository(Protocol):
    async def list_matches_by_date(
        self,
        *,
        target_date: date,
    ) -> Sequence[dict[str, Any]]: ...

    async def list_upcoming_matches(
        self,
        *,
        start_date: date,
        limit: int,
    ) -> Sequence[dict[str, Any]]: ...

    async def get_match(self, match_id: str) -> dict[str, Any] | None: ...

    async def get_match_prediction(self, match_id: str) -> dict[str, Any] | None: ...

    async def get_current_model(self) -> dict[str, Any] | None: ...

    async def get_team_profile(self, team_id: str) -> dict[str, Any] | None: ...

    async def get_groups(self) -> Sequence[dict[str, Any]]: ...
