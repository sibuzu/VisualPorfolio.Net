#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECKLIST_PATH="$ROOT_DIR/docs/deploy/checklists/beta-validation.md"

if [[ ! -f "$CHECKLIST_PATH" ]]; then
  echo "[gate] Missing checklist: $CHECKLIST_PATH" >&2
  exit 1
fi

"$ROOT_DIR/docker/visual-portfolio-beta/smoke-test.sh"

echo "[gate] Smoke checks passed."
echo "[gate] Complete manual checklist before production release:"
echo "       $CHECKLIST_PATH"
