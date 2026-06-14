from typing import Any

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class MatchListResponse(BaseModel):
    date: str
    matches: list[dict[str, Any]]


class MatchDetailResponse(BaseModel):
    match: dict[str, Any]


class MatchPredictionResponse(BaseModel):
    prediction: dict[str, Any]


class CurrentModelResponse(BaseModel):
    model: dict[str, Any]


class TeamProfileResponse(BaseModel):
    team: dict[str, Any]


class GroupsResponse(BaseModel):
    competition_id: str
    groups: list[dict[str, Any]]
