#!/usr/bin/env bash
set -euo pipefail
echo "Running alembic migrations..."
alembic upgrade head

echo "Starting app..."
exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:"${PORT:-8000}"
