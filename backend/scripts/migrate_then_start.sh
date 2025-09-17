# scripts/migrate_then_start.sh
# (idempotent, auto-detects app dir AND prints which app.main will load)
set -euo pipefail

echo "[entry] sha=${RENDER_GIT_COMMIT:-unknown} env=${ENV:-prod} PWD=$(pwd)"

# --- locate app dir ---
if [[ -n "${APP_DIR:-}" ]]; then
  APP_DIR="$APP_DIR"
elif [[ -f "backend/app/main.py" ]]; then
  APP_DIR="backend"
elif [[ -f "app/main.py" ]]; then
  APP_DIR="."
else
  echo "[entry] FATAL: cannot find app/main.py. tree -L 2 or ls:"; (command -v tree >/dev/null && tree -L 2) || ls -la; exit 1
fi
echo "[entry] APP_DIR=$APP_DIR"

# --- alembic (best-effort) ---
if [[ -f "$APP_DIR/alembic.ini" ]]; then
  echo "[entry] alembic upgrade head (in $APP_DIR)"
  pushd "$APP_DIR" >/dev/null
  alembic upgrade head || true
  popd >/dev/null
else
  echo "[entry] skip alembic (no $APP_DIR/alembic.ini)"
fi

# --- PRE-FLIGHT: show which app.main uvicorn will import ---
PYTHONPATH="$APP_DIR:${PYTHONPATH:-}" python - <<'PY'
import importlib, inspect, sys
try:
    m = importlib.import_module("app.main")
    app = getattr(m, "app", None)
    print("[entry] resolved app.main at", getattr(m, "__file__", "<no-file>"))
    print("[entry] app.title =", getattr(app, "title", "<no app or title>"))
except Exception as e:
    print("[entry] ERROR importing app.main:", type(e).__name__, e, file=sys.stderr)
PY

# --- start uvicorn from repo root, pointing at APP_DIR ---
echo "[entry] starting uvicorn with --app-dir $APP_DIR"
exec python -m uvicorn app.main:app \
  --app-dir "$APP_DIR" \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
