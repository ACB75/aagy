#!/usr/bin/env bash
# ==============================================================================
# new-lifecycle-task.sh - Instancia las 4 fases del Engineering Lifecycle
# Entorno: Debian 12 / Linux / WSL (POSIX LF)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/py/new_lifecycle_task.py"

if [[ ! -f "$PY_SCRIPT" ]]; then
    echo "[ERROR] No se encuentra el script en $PY_SCRIPT" >&2
    exit 1
fi

python3 "$PY_SCRIPT" --repo-root "$REPO_ROOT" "$@"
