#!/usr/bin/env sh
# Wrapper POSIX para el linter de paridad multi-harness aagy <-> ecc.
# Finales de línea estrictamente POSIX LF (\n).
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/ecc-agy/audit_plugin_parity.py"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$PY_SCRIPT" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$PY_SCRIPT" "$@"
elif command -v py >/dev/null 2>&1; then
    exec py "$PY_SCRIPT" "$@"
else
    echo "Python no detectado en el entorno POSIX." >&2
    exit 0
fi
