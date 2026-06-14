import logging
from contextlib import asynccontextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from predictor.application.use_cases.api_queries import (
    GetCurrentModel,
    GetGroups,
    GetMatchDetail,
    GetMatchPrediction,
    GetTeamProfile,
    ListMatchesForDate,
    ListUpcomingMatches,
)
from predictor.application.use_cases.health import GetHealth
from predictor.infrastructure.config.settings import get_settings
from predictor.infrastructure.database.session import (
    create_database_engine,
    create_session_factory_from_engine,
)
from predictor.infrastructure.repositories.database_prediction_repository import (
    DatabasePredictionRepository,
)
from predictor.infrastructure.repositories.static_prediction_repository import (
    StaticPredictionRepository,
)
from predictor.presentation.api.schemas import (
    CurrentModelResponse,
    GroupsResponse,
    HealthResponse,
    MatchDetailResponse,
    MatchListResponse,
    MatchPredictionResponse,
    TeamProfileResponse,
)

logger = logging.getLogger(__name__)


def _build_repository(settings):
    backend = settings.effective_repository_backend
    engine = None

    if backend == "database":
        if not settings.database_url:
            raise RuntimeError(
                "effective_repository_backend resolved to 'database' but DATABASE_URL is missing"
            )
        engine = create_database_engine(settings)
        repository = DatabasePredictionRepository(
            factory=create_session_factory_from_engine(engine),
        )
    else:
        repository = StaticPredictionRepository(
            data_dir=settings.data_dir,
            model_dir=settings.model_dir,
        )

    return backend, engine, repository


def _get_repository(request: Request):
    repository = getattr(request.app.state, "repository", None)
    repository_error = getattr(request.app.state, "repository_error", None)
    if repository is None:
        detail = "Prediction repository is unavailable."
        if repository_error:
            detail = f"{detail} {repository_error}"
        raise HTTPException(status_code=503, detail=detail)
    return repository


def create_app() -> FastAPI:
    settings = get_settings()
    backend = settings.effective_repository_backend
    engine = None
    repository = None
    repository_error = None

    try:
        backend, engine, repository = _build_repository(settings)
    except Exception as exc:  # pragma: no cover - deployment hardening path
        repository_error = str(exc)
        logger.exception(
            "Failed to initialize prediction repository | effective=%s | configured=%s | has_database_url=%s | app_env=%s",
            backend,
            settings.api_repository_backend,
            bool(settings.database_url),
            settings.app_env,
        )
    else:
        logger.warning(
            "API repository backend selected: %s | configured=%s | has_database_url=%s | app_env=%s",
            backend,
            settings.api_repository_backend,
            bool(settings.database_url),
            settings.app_env,
        )

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            if engine is not None:
                await engine.dispose()

    app = FastAPI(
        title="World Cup Predictor API",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.repository = repository
    app.state.repository_backend = backend
    app.state.repository_error = repository_error
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", tags=["system"])
    async def root() -> dict[str, str]:
        return {"service": "world-cup-predictor-api", "status": "ok"}

    @app.get("/health", tags=["system"], response_model=HealthResponse)
    async def health() -> HealthResponse:
        result = GetHealth().execute()
        return HealthResponse(status=result.status, service=result.service)

    @app.get("/matches/today", tags=["matches"], response_model=MatchListResponse)
    async def matches_today(request: Request) -> MatchListResponse:
        today = datetime.now(ZoneInfo("America/La_Paz")).date()
        repository = _get_repository(request)
        matches = await ListMatchesForDate(repository).execute(target_date=today)
        return MatchListResponse(date=today.isoformat(), matches=matches)

    @app.get("/matches/upcoming", tags=["matches"], response_model=MatchListResponse)
    async def matches_upcoming(request: Request, limit: int = 20) -> MatchListResponse:
        start_date = datetime.now(ZoneInfo("America/La_Paz")).date()
        repository = _get_repository(request)
        matches = await ListUpcomingMatches(repository).execute(
            start_date=start_date,
            limit=limit,
        )
        return MatchListResponse(date=start_date.isoformat(), matches=matches)

    @app.get("/matches/{match_id}", tags=["matches"], response_model=MatchDetailResponse)
    async def match_detail(request: Request, match_id: str) -> MatchDetailResponse:
        repository = _get_repository(request)
        match = await GetMatchDetail(repository).execute(match_id=match_id)
        if match is None:
            raise HTTPException(status_code=404, detail="Match not found")
        return MatchDetailResponse(match=match)

    @app.get(
        "/matches/{match_id}/prediction",
        tags=["predictions"],
        response_model=MatchPredictionResponse,
    )
    async def match_prediction(request: Request, match_id: str) -> MatchPredictionResponse:
        repository = _get_repository(request)
        prediction = await GetMatchPrediction(repository).execute(match_id=match_id)
        if prediction is None:
            raise HTTPException(status_code=404, detail="Prediction not found")
        return MatchPredictionResponse(prediction=prediction)

    @app.get("/models/current", tags=["models"], response_model=CurrentModelResponse)
    async def current_model(request: Request) -> CurrentModelResponse:
        repository = _get_repository(request)
        model = await GetCurrentModel(repository).execute()
        if model is None:
            raise HTTPException(status_code=404, detail="No model available")
        return CurrentModelResponse(model=model)

    @app.get("/teams/{team_id}", tags=["teams"], response_model=TeamProfileResponse)
    async def team_profile(request: Request, team_id: str) -> TeamProfileResponse:
        repository = _get_repository(request)
        team = await GetTeamProfile(repository).execute(team_id=team_id)
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")
        return TeamProfileResponse(team=team)

    @app.get("/groups", tags=["groups"], response_model=GroupsResponse)
    async def groups(request: Request) -> GroupsResponse:
        repository = _get_repository(request)
        payload = await GetGroups(repository).execute()
        return GroupsResponse(
            competition_id="fifa_world_cup",
            groups=payload,
        )

    return app


app = create_app()
