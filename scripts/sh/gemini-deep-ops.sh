#!/usr/bin/env bash
# CLI determinista para diagnóstico multimodal y análisis de logs con Gemini.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/py/gemini_deep_ops.py"

if [[ ! -f "$PY_SCRIPT" ]]; then
    echo "[ERROR] No se encuentra $PY_SCRIPT" >&2
    exit 1
fi

python3 "$PY_SCRIPT" "$@"
