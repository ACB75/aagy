#!/usr/bin/env bash
# ==============================================================================
# generate-postmortem.sh - Generador de autopsia Post-Mortem 5W para ramas fix/*
# Entorno: Debian 12 / Linux / WSL (POSIX LF)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PY_SCRIPT="${WORKSPACE_ROOT}/scripts/py/generate_postmortem.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
    echo "[ERROR] No se encuentra el script en ${PY_SCRIPT}" >&2
    exit 1
fi

python3 "${PY_SCRIPT}" --repo-root "${WORKSPACE_ROOT}" "$@"
