#!/usr/bin/env sh
# Wrapper POSIX de scripts/py/sync_aagy_ecc.py: sincroniza skills, agentes,
# reglas y motores Python dentro de aagy-ecc/ (distribución Claude Code).
# Uso: scripts/sh/sync-aagy-ecc.sh [--check] [--json]
# Finales de línea estrictamente POSIX LF (\n).
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/py/sync_aagy_ecc.py"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$PY_SCRIPT" --repo-root "$REPO_ROOT" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$PY_SCRIPT" --repo-root "$REPO_ROOT" "$@"
else
    echo "Python no detectado en el entorno POSIX." >&2
    exit 1
fi
