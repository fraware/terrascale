from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.engine.url import make_url
from starlette.testclient import TestClient
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from user_service.core.config import Settings
from user_service.main import create_app

_SERVICE_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def redis_container() -> Generator[RedisContainer, None, None]:
    with RedisContainer("redis:7-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def migrated_db_url(postgres_container: PostgresContainer) -> Generator[str, None, None]:
    url = postgres_container.get_connection_url()
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    cfg = Config(str(_SERVICE_ROOT / "alembic.ini"))
    command.upgrade(cfg, "head")
    try:
        yield url
    finally:
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous


@pytest.fixture(scope="session")
def integration_settings(
    postgres_container: PostgresContainer,
    redis_container: RedisContainer,
    migrated_db_url: str,
) -> Settings:
    _ = postgres_container
    pg_url = make_url(migrated_db_url)
    redis_host = redis_container.get_container_host_ip()
    redis_port = int(redis_container.get_exposed_port(6379))
    return Settings(
        postgres_host=pg_url.host or "localhost",
        postgres_port=pg_url.port or 5432,
        postgres_db=pg_url.database or "test",
        postgres_user=pg_url.username or "test",
        postgres_password=pg_url.password or "test",
        redis_host=redis_host,
        redis_port=redis_port,
        debug=True,
    )


@pytest.fixture
def client(integration_settings: Settings) -> Generator[TestClient, None, None]:
    app = create_app(integration_settings)
    with TestClient(app) as test_client:
        yield test_client
