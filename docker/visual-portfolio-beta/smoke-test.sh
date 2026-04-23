#!/usr/bin/env bash
set -euo pipefail

FRONTEND_URL="${BETA_FRONTEND_URL:-https://visualporforlio-beta.sibuzu.com}"
API_URL="${BETA_API_URL:-https://api-visualporforlio-beta.sibuzu.com}"

check_status() {
  local url="$1"
  local name="$2"
  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' "$url")"
  if [[ "$code" != "200" ]]; then
    echo "[smoke] FAIL $name $url -> HTTP $code" >&2
    return 1
  fi
  echo "[smoke] PASS $name $url -> HTTP $code"
}

check_status "$FRONTEND_URL/" "frontend-home"
check_status "$API_URL/healthz" "api-healthz"

echo "[smoke] All beta smoke checks passed"
