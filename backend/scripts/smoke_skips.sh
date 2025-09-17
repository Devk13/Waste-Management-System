#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${1:-http://127.0.0.1:8000}"
echo "==> Probing $BASE_URL/__debug/routes"
curl -fsS "$BASE_URL/__debug/routes" | jq '[.[] | select(.path | startswith("/skips"))]'
echo "==> Probing $BASE_URL/skips/__smoke"
curl -fsS "$BASE_URL/skips/__smoke" | jq .
echo "OK"
