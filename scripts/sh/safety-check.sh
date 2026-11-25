#!/usr/bin/env bash
# Safety gate (PreToolUse): envoltorio fino de scripts/py/hook_safety.py --format agy.
# Sin argumentos lee el payload de Antigravity por stdin; con un argumento, prueba ese comando.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(command -v python3 || command -v python)"
if [[ $# -gt 0 ]]; then
    "$PYTHON" -c 'import json,sys; print(json.dumps({"toolCall": {"args": {"CommandLine": sys.argv[1]}}}))' "$1" \
        | "$PYTHON" "$SCRIPT_DIR/../py/hook_safety.py" --format agy
else
    "$PYTHON" "$SCRIPT_DIR/../py/hook_safety.py" --format agy
fi
