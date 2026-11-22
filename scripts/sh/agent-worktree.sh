#!/usr/bin/env bash
# ==============================================================================
# agent-worktree.sh - Un git worktree fijo por agente (aagy / aagy-ecc)
# Opera sobre el repositorio de la carpeta actual (no sobre la del script).
# Ejemplos:
#   bash scripts/sh/agent-worktree.sh init
#   bash scripts/sh/agent-worktree.sh status
#   bash scripts/sh/agent-worktree.sh recycle --agent claude
# Entorno: Debian 12 / Linux / WSL (POSIX LF)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="${SCRIPT_DIR}/../py/agent_worktree.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
    echo "[ERROR] No se encuentra el script en ${PY_SCRIPT}" >&2
    exit 1
fi

PY_BIN="$(command -v python3 || command -v python)"
exec "${PY_BIN}" "${PY_SCRIPT}" "$@"
