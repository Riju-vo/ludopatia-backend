from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from predictor.infrastructure.config import Settings


class DatabaseNotConfiguredError(RuntimeError):
    pass


class Base(DeclarativeBase):
    pass


def create_database_engine(settings: Settings) -> AsyncEngine:
    if not settings.database_url:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not configured. Add it to .env before using persistence."
        )

    return create_async_engine(settings.database_url, pool_pre_ping=True)


def create_session_factory_from_engine(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


def create_session_factory(settings: Settings) -> async_sessionmaker[AsyncSession]:
    return create_session_factory_from_engine(create_database_engine(settings))


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        yield session
