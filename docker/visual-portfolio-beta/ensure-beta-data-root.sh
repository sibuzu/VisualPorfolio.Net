#!/usr/bin/env bash
set -euo pipefail

configured_root="${BETA_DATA_ROOT:-}"
if [[ -z "${configured_root}" ]]; then
  echo "[beta-guard] BETA_DATA_ROOT is required" >&2
  exit 1
fi

if [[ "${configured_root}" != *"data-beta"* ]]; then
  echo "[beta-guard] Refusing to start: BETA_DATA_ROOT must point to data-beta. got='${configured_root}'" >&2
  exit 1
fi

if [[ ! -d /app/data ]]; then
  mkdir -p /app/data
fi

if [[ ! -w /app/data ]]; then
  echo "[beta-guard] /app/data is not writable" >&2
  echo "[beta-guard] container user: $(id -u):$(id -g)" >&2
  if command -v stat >/dev/null 2>&1; then
    echo "[beta-guard] /app/data owner/perms: $(stat -c '%u:%g %A' /app/data 2>/dev/null || true)" >&2
  fi
  echo "[beta-guard] fix on host:" >&2
  echo "[beta-guard]   export APP_UID=\$(id -u); export APP_GID=\$(id -g)" >&2
  echo "[beta-guard]   ./scripts/prepare-beta-data-dir.sh ./data-beta" >&2
  exit 1
fi

echo "[beta-guard] data mount verified for beta: ${configured_root} -> /app/data"
exec "$@"
