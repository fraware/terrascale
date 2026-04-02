from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from user_service.core.config import Settings


def setup_telemetry_provider(settings: Settings) -> bool:
    """Configure OTLP export. Returns True when tracing is active."""
    if not settings.otlp_endpoint:
        return False

    resource = Resource.create(
        {
            "service.name": settings.otel_service_name,
        }
    )
    provider = TracerProvider(resource=resource)
    exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return True


def instrument_redis() -> None:
    RedisInstrumentor().instrument()


def instrument_sqlalchemy_engine(engine: Any) -> None:
    SQLAlchemyInstrumentor().instrument(engine=engine)


def instrument_fastapi_app(app: Any) -> None:
    FastAPIInstrumentor.instrument_app(app)
