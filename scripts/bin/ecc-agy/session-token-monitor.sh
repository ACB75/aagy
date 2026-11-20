#!/usr/bin/env sh
# Monitor de telemetría de tokens en sesión de Antigravity

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/ecc-agy/session_token_monitor.py"

PYTHON_BIN="python"
if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
fi

exec "$PYTHON_BIN" "$PY_SCRIPT" "$@"
