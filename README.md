<div align="center">

# TerraScale

**Design at planetary scale. Proof in a single service.**

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker Compose](https://img.shields.io/badge/stack-Docker%20Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

</div>

---

TerraScale is two things in one repository: a **written architecture** for a hypothetical global social network, and a **small but serious sample** you can run today—a User Service with migrations, caching, structured logs, optional distributed tracing, and continuous integration. The goal is not to simulate a billion users locally; it is to show how the ideas in the design doc translate into maintainable code and operable defaults.

---

## Table of contents

- [What lives here](#what-lives-here)
- [Quick start](#quick-start)
- [Endpoints and API](#endpoints-and-api)
- [Configuration](#configuration)
- [Development and CI](#development-and-ci)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)

---

## What lives here

### Narrative architecture

The long-form target system—regions, sharding, streaming, observability stacks—is in **[ARCHITECTURE.md](ARCHITECTURE.md)**. That document describes *where you could go*; this README focuses on *what runs out of the box*.

### Runnable stack

| Piece | Role |
|------:|------|
| **[docker-compose.yml](docker-compose.yml)** | Wires **User Service**, **PostgreSQL 16**, and **Redis 7** for local development. |
| **[services/user-service/](services/user-service/)** | FastAPI app, SQLAlchemy 2, Alembic, Redis cache-aside, structlog, optional OTLP export, tests, and Dockerfile. |
| **[.env.example](.env.example)** | Copy to `.env` at the repo root when you want explicit overrides; Compose still works without it thanks to defaults. |
| **[.github/workflows/ci.yml](.github/workflows/ci.yml)** | Lint, format, types, tests (with Testcontainers), image build, and a Trivy pass over the image. |

### Stack highlights

The User Service is built with [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy 2](https://www.sqlalchemy.org/), [Alembic](https://alembic.sqlalchemy.org/), and [Redis](https://redis.io/). Logs go through [structlog](https://www.structlog.org/); traces can be sent over OTLP HTTP when you set an endpoint. The container entrypoint applies migrations, then starts **Gunicorn** with **Uvicorn** workers—closer to production than a dev-only server.

---

## Quick start

**You need:** Docker with Compose (`docker compose`).

**Optional:** Copy [.env.example](.env.example) to `.env` in the repository root and adjust values. If you skip this step, documented defaults still apply.

From the **repository root**:

```bash
docker compose up --build
```

When the stack is healthy, open the [interactive API docs](http://localhost:5000/docs) at `http://localhost:5000/docs`.

---

## Endpoints and API

### Operations & documentation

| What | Where |
|------|--------|
| Service banner | [http://localhost:5000/](http://localhost:5000/) |
| Liveness | `GET /health` |
| Readiness (DB + Redis) | `GET /ready` |
| Swagger UI | [http://localhost:5000/docs](http://localhost:5000/docs) |
| OpenAPI JSON | [http://localhost:5000/openapi.json](http://localhost:5000/openapi.json) |

### User API (JSON)

| Method | Path | Behavior |
|:------:|------|----------|
| `POST` | `/users/` | Body: `{"username": "..."}`. **201** with `id` and `username` on success. **409** if the username already exists (`detail` follows RFC 9457-style problem semantics). |
| `GET` | `/users/{id}` | Returns `id`, `username`, and `cached`—`true` when the response is satisfied from Redis. |

On startup, the image runs `alembic upgrade head` before the application workers bind to port **5000**.

---

## Configuration

The service loads settings with [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) (environment variable names are matched case-insensitively). Compose forwards variables from your root `.env` or uses the defaults embedded in [docker-compose.yml](docker-compose.yml).

| Variable | Meaning |
|----------|---------|
| `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Database URL used by SQLAlchemy and Alembic |
| `REDIS_HOST`, `REDIS_PORT` | Redis connection |
| `CACHE_TTL_SECONDS` | Time-to-live for cached usernames in Redis |
| `DEBUG` | Richer console-oriented logs when enabled; structured output suited for aggregation when disabled |
| `LOG_LEVEL` | Root log level (for example `INFO` or `DEBUG`) |
| `OTLP_ENDPOINT` | Optional OTLP/HTTP tracing endpoint (include path if your collector requires it, e.g. `…/v1/traces`) |
| `OTEL_SERVICE_NAME` | `service.name` in exported traces (default: `user-service`) |

For **Alembic** from your laptop (outside Compose), you may set `DATABASE_URL` to a full SQLAlchemy URL. Step-by-step notes live in [services/user-service/README.md](services/user-service/README.md).

---

## Development and CI

| If you want to… | Start here |
|-----------------|------------|
| Install deps, run migrations, use `uvicorn`, run Ruff / Pyright / pytest | [services/user-service/README.md](services/user-service/README.md) |
| Mirror what CI runs | Same README: commands are aligned with the workflow file |

Continuous integration runs on pushes and pull requests to **`main`**: Ruff check and format on `src`, `tests`, and `alembic`; Pyright; pytest with a coverage threshold; Docker build for the User Service image; and a **Trivy** scan (currently non-blocking on severity). See [.github/workflows/ci.yml](.github/workflows/ci.yml).

Integration tests rely on **Testcontainers** and expect a working Docker engine.

---

## Contributing

1. Run the checks under `services/user-service/` before opening a PR, or rely on CI for feedback.
2. Prefer small, reviewable changes that match existing formatting and typing discipline.
3. Never commit secrets; keep real `.env` files local (they are gitignored).

---

## Roadmap

- More microservices (posts, feeds, notifications) and **Kafka**-style event flows, as sketched in [ARCHITECTURE.md](ARCHITECTURE.md).
- Kubernetes manifests and richer multi-region **simulation** material.
- Metrics and centralized logging alongside the optional **OpenTelemetry** trace export.

---

## License

This project is released under the [MIT License](LICENSE).
