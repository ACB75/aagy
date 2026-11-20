#!/usr/bin/env sh
# Retira una skill temporalmente promovida del plugin activo

set -e

if [ -z "$1" ]; then
    echo "Uso: $0 <nombre-de-skill>" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/py/skill_promotion.py"

PYTHON_BIN="python"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" "$PY_SCRIPT" --demote "$1"
