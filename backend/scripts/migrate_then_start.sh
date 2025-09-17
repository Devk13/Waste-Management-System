# path: scripts/migrate_then_start.sh
# make executable:   git add --chmod=+x scripts/migrate_then_start.sh
set -euo pipefail

echo "[entry] sha=${RENDER_GIT_COMMIT:-unknown} env=${ENV:-prod} PWD=$(pwd)"

# --- locate app dir (works whether Root Directory is repo root or /backend) ---
if [[ -n "${APP_DIR:-}" ]]; then
  APP_DIR="$APP_DIR"
elif [[ -f "backend/app/main.py" ]]; then
  APP_DIR="backend"
elif [[ -f "app/main.py" ]]; then
  APP_DIR="."
else
  echo "[entry] FATAL: cannot find app/main.py. tree -L 2:"
  (command -v tree >/dev/null && tree -L 2) || ls -la
  exit 1
fi
echo "[entry] APP_DIR=$APP_DIR"

# --- run alembic if present inside APP_DIR ---
if [[ -f "$APP_DIR/alembic.ini" ]]; then
  echo "[entry] alembic upgrade head (in $APP_DIR)"
  pushd "$APP_DIR" >/dev/null
  alembic upgrade head || true
  popd >/dev/null
else
  echo "[entry] skip alembic (no $APP_DIR/alembic.ini)"
fi

# --- start uvicorn, always pointing to the app dir we detected ---
echo "[entry] starting uvicorn with --app-dir $APP_DIR"
exec python -m uvicorn app.main:app \
  --app-dir "$APP_DIR" \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
