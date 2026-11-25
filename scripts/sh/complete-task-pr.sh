#!/usr/bin/env bash
# Fase 4: envoltorio fino de scripts/py/complete_task_pr.py (motor único de aagy y aagy-ecc).
# Sin auto-merge: solo fusiona con --merge, cuando una persona lo pide. Finales de línea LF.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(command -v python3 || command -v python)"
ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -ReviewOnly) ARGS+=(--review-only); shift ;;
        -Yes|-y) ARGS+=(--yes); shift ;;
        -Merge) ARGS+=(--merge); shift ;;
        -TargetBranch|--target-branch) ARGS+=(--target "$2"); shift 2 ;;
        -Issue) ARGS+=(--issue "$2"); shift 2 ;;
        -Title) ARGS+=(--title "$2"); shift 2 ;;
        -Body) ARGS+=(--body "$2"); shift 2 ;;
        *) ARGS+=("$1"); shift ;;
    esac
done
exec "$PYTHON" "$SCRIPT_DIR/../py/complete_task_pr.py" ${ARGS[@]+"${ARGS[@]}"}
