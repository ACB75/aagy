#!/usr/bin/env sh
# Wrapper POSIX de scripts/py/aagy_doctor.py: diagnóstico /aagy-doctor (Antigravity / Gemini)
# con el catálogo común DOC-01..DOC-14. Solo lectura salvo --fix.
# Uso: scripts/sh/aagy-doctor.sh [--json] [--fix] [--yes] [--strict] [--only DOC-05,DOC-09]
# Finales de línea estrictamente POSIX LF (\n).
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/py/aagy_doctor.py"

if command -v python3 >/dev/null 2>&1; then
    exec python3 "$PY_SCRIPT" --repo-root "$REPO_ROOT" "$@"
elif command -v python >/dev/null 2>&1; then
    exec python "$PY_SCRIPT" --repo-root "$REPO_ROOT" "$@"
else
    echo "Python no detectado en el entorno POSIX." >&2
    exit 1
fi
