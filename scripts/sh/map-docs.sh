#!/usr/bin/env bash
# ==============================================================================
# map-docs.sh - Auditoría de enlaces Markdown y .governance/docs-map.json
# Entorno: Debian 12 / Linux / WSL (POSIX LF)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PY_SCRIPT="${WORKSPACE_ROOT}/scripts/py/map_docs.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
    echo "[ERROR] No se encuentra el script en ${PY_SCRIPT}" >&2
    exit 1
fi

python3 "${PY_SCRIPT}" --repo-root "${WORKSPACE_ROOT}" --check-docs-map "$@"
