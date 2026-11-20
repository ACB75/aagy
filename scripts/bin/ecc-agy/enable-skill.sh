#!/usr/bin/env sh
# Promueve una skill especializada de Tier 2 a Tier 1 (plugin activo)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/ecc-agy/skill_promotion.py"

PYTHON_BIN="python"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

if [ "$1" = "--list" ] || [ "$1" = "-l" ] || [ -z "$1" ]; then
    exec "$PYTHON_BIN" "$PY_SCRIPT" --list
fi

exec "$PYTHON_BIN" "$PY_SCRIPT" --promote "$1"
