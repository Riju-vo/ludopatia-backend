from collections.abc import Sequence
from typing import Protocol

from predictor.domain.models import CanonicalMatch


class MatchRepository(Protocol):
    async def save_many(self, matches: Sequence[CanonicalMatch]) -> None: ...
