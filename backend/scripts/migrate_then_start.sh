# path: scripts/migrate_then_start.sh   (repo root)
# make executable: git add + chmod + commit this exact file
set -euo pipefail

echo "[entry] sha=${RENDER_GIT_COMMIT:-unknown} env=${ENV:-prod}"

APP_DIR="${APP_DIR:-backend}"
cd "$APP_DIR"

# Alembic migrations (quiet if no migrations)
echo "[entry] running alembic upgrade head"
alembic upgrade head || true

# Start uvicorn from repo root, telling it where the app package lives
cd ..
exec python -m uvicorn app.main:app \
  --app-dir backend \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
