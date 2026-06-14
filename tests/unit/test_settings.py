from predictor.infrastructure.config.settings import Settings


def test_database_url_is_optional_during_data_work() -> None:
    settings = Settings(_env_file=None)

    assert settings.database_url is None


def test_railway_postgres_url_is_normalized_for_async_sqlalchemy() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql://user:password@host:5432/database",
    )

    assert settings.database_url == ("postgresql+asyncpg://user:password@host:5432/database")


def test_neon_sslmode_query_is_normalized_for_asyncpg() -> None:
    settings = Settings(
        _env_file=None,
        database_url=(
            "postgresql://user:password@host:5432/database"
            "?sslmode=require&channel_binding=require"
        ),
    )

    assert settings.database_url == (
        "postgresql+asyncpg://user:password@host:5432/database"
        "?ssl=require&channel_binding=require"
    )
