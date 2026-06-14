from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HealthStatus:
    status: str
    service: str


class GetHealth:
    def execute(self) -> HealthStatus:
        return HealthStatus(status="ok", service="world-cup-predictor")
