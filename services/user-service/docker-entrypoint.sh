#!/bin/sh
set -e
export PYTHONPATH="/app/src:${PYTHONPATH:-}"
cd /app
alembic upgrade head
exec "$@"
