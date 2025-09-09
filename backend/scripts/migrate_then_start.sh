#!/usr/bin/env bash
set -euo pipefail

# Run migrations first
python -m alembic upgrade head

# Start FastAPI (Render provides $PORT)
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
