#!/usr/bin/env bash
set -euo pipefail

# Run migrations (create head if none exist)
if ! alembic upgrade head; then
  echo "No revisions? Creating initial revision..." >&2
  alembic revision --autogenerate -m "init schema"
  alembic upgrade head
fi

# Start API
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-10000}"
