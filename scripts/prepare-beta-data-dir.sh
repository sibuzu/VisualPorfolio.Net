#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR="${1:-$ROOT_DIR/data-beta}"
TARGET_UID="${APP_UID:-$(id -u)}"
TARGET_GID="${APP_GID:-$(id -g)}"

mkdir -p "$TARGET_DIR"

if chown "$TARGET_UID:$TARGET_GID" "$TARGET_DIR" 2>/dev/null; then
  :
else
  echo "[prepare-beta-data] chown without sudo failed; trying sudo..." >&2
  sudo chown "$TARGET_UID:$TARGET_GID" "$TARGET_DIR"
fi

chmod 775 "$TARGET_DIR"

echo "[prepare-beta-data] ready: $TARGET_DIR"
echo "[prepare-beta-data] owner: $(stat -c '%U:%G (%u:%g)' "$TARGET_DIR")"
echo "[prepare-beta-data] perms: $(stat -c '%A' "$TARGET_DIR")"
