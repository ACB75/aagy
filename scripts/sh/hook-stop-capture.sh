#!/usr/bin/env bash
# ==============================================================================
# Script: hook-stop-capture.sh (Debian 12 / Linux / WSL)
# Descripción: Hook pasivo Stop de captura de aprendizajes sub-segundo (< 500 ms).
# Finales de línea estrictamente POSIX LF (\n).
# ==============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY_SCRIPT="$ROOT_DIR/scripts/py/self_improve.py"
TARGET_ROOT="${1:-$ROOT_DIR}"

if [[ -f "$PY_SCRIPT" ]]; then
    python3 "$PY_SCRIPT" --capture-stop --repo-root "$TARGET_ROOT" 2>/dev/null || echo "{}"
else
    echo "{}"
fi
exit 0
