from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

import redis
import structlog
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from user_service.api.routes import users_router
from user_service.core.config import Settings
from user_service.core.logging_config import configure_logging
from user_service.core.telemetry import (
    instrument_fastapi_app,
    instrument_redis,
    instrument_sqlalchemy_engine,
    setup_telemetry_provider,
)
from user_service.db.session import create_engine_from_settings, create_session_factory

log = structlog.get_logger()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    configure_logging(settings)

    engine = create_engine_from_settings(settings)
    session_factory = create_session_factory(engine)

    telemetry_enabled = setup_telemetry_provider(settings)
    if telemetry_enabled:
        instrument_redis()
        instrument_sqlalchemy_engine(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True,
        )
        redis_client.ping()
        app.state.redis = redis_client
        log.info("service_started")
        yield
        redis_client.close()
        log.info("service_stopped")

    app = FastAPI(
        title="User Service",
        description="TerraScale user API",
        lifespan=lifespan,
        version="0.1.0",
    )
    app.state.settings = settings
    app.state.session_factory = session_factory

    @app.middleware("http")
    async def access_log_middleware(request: Request, call_next: Any) -> Response:
        path = request.url.path
        method = request.method
        response = await call_next(request)
        log.info(
            "http_request",
            method=method,
            path=path,
            status_code=response.status_code,
        )
        return response

    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next: Any) -> Response:
        request_id = request.headers.get("x-request-id") or str(uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/", response_class=PlainTextResponse)
    def index() -> str:
        return "User Service is up and running!"

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    def ready(request: Request) -> dict[str, str]:
        session_factory = request.app.state.session_factory
        session = session_factory()
        try:
            session.execute(text("SELECT 1"))
        except Exception:
            log.exception("readiness_db_failed")
            raise HTTPException(
                status_code=503,
                detail={"message": "database_unavailable"},
            ) from None
        finally:
            session.close()

        try:
            request.app.state.redis.ping()
        except Exception:
            log.exception("readiness_redis_failed")
            raise HTTPException(
                status_code=503,
                detail={"message": "redis_unavailable"},
            ) from None

        return {"status": "ready"}

    app.include_router(users_router, prefix="/users", tags=["users"])

    if telemetry_enabled:
        instrument_fastapi_app(app)

    return app


app = create_app()
