#!/usr/bin/env bash
# ==============================================================================
# new-lifecycle-task.sh - Instancia artefactos del Engineering Lifecycle
# Soporta --phase ALL|IDEAS|REQ|PLAN|TODO|DOCS|REVIEW, --issue <N> y docs-map.json
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

ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -Issue) ARGS+=("--issue" "${2:?Falta valor para -Issue}"); shift 2 ;;
        -TaskId) ARGS+=("--task-id" "${2:?Falta valor para -TaskId}"); shift 2 ;;
        -Phase) ARGS+=("--phase" "${2:?Falta valor para -Phase}"); shift 2 ;;
        -OutputDir) ARGS+=("--output-dir" "${2:?Falta valor para -OutputDir}"); shift 2 ;;
        -Force) ARGS+=("--force"); shift ;;
        -DryRun) ARGS+=("--dry-run"); shift ;;
        *) ARGS+=("$1"); shift ;;
    esac
done

PY_BIN="$(command -v python3 || command -v python)"
"$PY_BIN" "$PY_SCRIPT" --repo-root "$REPO_ROOT" "${ARGS[@]}"
