#!/usr/bin/env bash
# ==============================================================================
# backlog.sh - Backlog compartido entre Claude Code (aagy-ecc) y Antigravity (aagy)
# Opera sobre el repositorio de la carpeta actual (no sobre la del script).
# Ejemplos:
#   bash scripts/sh/backlog.sh list
#   bash scripts/sh/backlog.sh claim <id> --agent agy
#   bash scripts/sh/backlog.sh handoff --agent claude --note "falta X"
# Entorno: Debian 12 / Linux / WSL (POSIX LF)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/../py/backlog.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
    echo "[ERROR] No se encuentra el script en ${PY_SCRIPT}" >&2
    exit 1
fi

PY_BIN="$(command -v python3 || command -v python)"
exec "${PY_BIN}" "${PY_SCRIPT}" "$@"
