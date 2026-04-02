# User Service

FastAPI microservice for TerraScale user records: create users in PostgreSQL, cache usernames in Redis (cache-aside), expose OpenAPI at `/docs`.

## Requirements

- **Python 3.12+** (see [.python-version](.python-version)).
- **[uv](https://github.com/astral-sh/uv)** for environments and locked dependencies ([pyproject.toml](pyproject.toml), [uv.lock](uv.lock)).
- **Docker** if you run **pytest** (integration tests use [Testcontainers](https://testcontainers.com/) for PostgreSQL and Redis).

All commands below assume your current working directory is **`services/user-service`**.

## Quick start (local API server)

1. Install dependencies and the package into a virtualenv:

   ```bash
   uv sync --group dev
   ```

2. Ensure PostgreSQL and Redis are reachable using the same settings as [Settings](src/user_service/core/config.py) (defaults: `localhost`, Postgres port `5432`, Redis `6379`). For a database URL that differs from the composed `POSTGRES_*` fields, set:

   ```bash
   set DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
   uv run alembic upgrade head
   ```

   On Unix shells use `export DATABASE_URL=...`. If unset, Alembic reads connection pieces from the same env vars as the app (`POSTGRES_HOST`, etc.).

3. Start the app with auto-reload:

   ```bash
   uv run uvicorn user_service.main:app --reload --host 0.0.0.0 --port 5000
   ```

   Open [http://localhost:5000/docs](http://localhost:5000/docs) for interactive API documentation.

Production-style serving (no reload) matches the container: **Gunicorn** + **Uvicorn** workers, for example:

```bash
uv run gunicorn user_service.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:5000 --workers 2
```

## Project structure

| Path | Purpose |
|------|---------|
| `src/user_service/` | Application package (`main.py`, `api/`, `core/`, `db/`, `models/`) |
| `alembic/` | Migration scripts; [alembic.ini](alembic.ini) |
| `tests/` | Pytest suite (unit + Testcontainers integration) |
| [Dockerfile](Dockerfile) | Multi-stage image: `uv sync`, non-root user, entrypoint runs migrations then Gunicorn |
| [docker-entrypoint.sh](docker-entrypoint.sh) | `alembic upgrade head` then `exec` CMD |

## Quality checks (align with CI)

```bash
uv python install 3.12
uv sync --group dev --frozen --python 3.12
uv run ruff check src tests alembic
uv run ruff format --check src tests alembic
uv run pyright
uv run pytest
```

Format in place:

```bash
uv run ruff format src tests alembic
```

## Tests

- **Unit:** Pydantic schema validation (`tests/test_schemas.py`).
- **Integration:** HTTP API against real Postgres and Redis in Docker (`tests/test_api.py`, `tests/conftest.py`).

Coverage and minimum threshold are configured in [pyproject.toml](pyproject.toml) (`pytest` / `coverage` sections).

## Docker only (no local Python)

From the **repository root**:

```bash
docker compose up --build
```

See root [README.md](../../README.md) for ports, environment variables, and API summary.

## Environment variables

The service uses [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/). Common variables are listed in the root [README.md](../../README.md) and [.env.example](../../.env.example).

Optional tracing: set `OTLP_ENDPOINT` (OTLP/HTTP, including path such as `/v1/traces` if required by your collector) and optionally `OTEL_SERVICE_NAME`.
