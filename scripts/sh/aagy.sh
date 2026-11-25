#!/usr/bin/env bash
# Lanzador único de aagy: `aagy.sh <comando> [args]` ejecuta scripts/py/<comando>.py
# (los guiones del comando pasan a guion bajo) con los mismos argumentos.
# `aagy.sh help` lista los comandos. Finales de línea LF.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_DIR="$SCRIPT_DIR/../py"
PYTHON="$(command -v python3 || command -v python || true)"
if [ -z "$PYTHON" ]; then
    echo "[aagy] Falta Python 3 en el PATH." >&2
    exit 127
fi

CMD="${1:-help}"
if [ "$CMD" = "help" ] || [ "$CMD" = "-h" ] || [ "$CMD" = "--help" ]; then
    echo "Uso: aagy <comando> [args]   (ej. aagy complete-task-pr --review-only)"
    echo "Comandos:"
    grep -l "__main__" "$PY_DIR"/*.py | xargs -n1 basename | sed 's/\.py$//; s/_/-/g; s/^/  /'
    exit 0
fi
shift
SCRIPT="$PY_DIR/${CMD//-/_}.py"
# Los motores propios de aagy-ecc (aagy-ecc-doctor) viven en su carpeta.
[ -f "$SCRIPT" ] || SCRIPT="$SCRIPT_DIR/../../aagy-ecc/scripts/py/${CMD//-/_}.py"
if [ ! -f "$SCRIPT" ]; then
    echo "[aagy] Comando desconocido: '$CMD'. Ejecuta 'aagy help'." >&2
    exit 2
fi
exec "$PYTHON" "$SCRIPT" "$@"
