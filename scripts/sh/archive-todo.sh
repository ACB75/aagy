#!/usr/bin/env bash
# ==============================================================================
# archive-todo.sh - Archiva tareas completadas de TODO.md hacia done/
# Resuelve rutas vía .governance/docs-map.json con fallback clásico.
# Entorno: Debian 12 / Linux / WSL (POSIX LF)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
PY_SCRIPT="${WORKSPACE_ROOT}/scripts/py/archive_todo.py"
DOCS_MAP_SCRIPT="${WORKSPACE_ROOT}/scripts/py/docs_map.py"

if [[ ! -f "${PY_SCRIPT}" ]]; then
    echo "[ERROR] No se encuentra el script ${PY_SCRIPT}" >&2
    exit 1
fi

TODO_PATH="${WORKSPACE_ROOT}/doc/TODO.md"
DONE_DIR="${WORKSPACE_ROOT}/doc/TODO_DONE"
if [[ -f "${DOCS_MAP_SCRIPT}" ]]; then
    RESOLVED_TODO="$(python3 "${DOCS_MAP_SCRIPT}" --repo-root "${WORKSPACE_ROOT}" --key todo 2>/dev/null || true)"
    RESOLVED_DONE="$(python3 "${DOCS_MAP_SCRIPT}" --repo-root "${WORKSPACE_ROOT}" --key todo_done 2>/dev/null || true)"
    if [[ -n "${RESOLVED_TODO}" ]]; then
        TODO_PATH="${RESOLVED_TODO}"
    fi
    if [[ -n "${RESOLVED_DONE}" ]]; then
        DONE_DIR="${RESOLVED_DONE}"
    fi
fi

python3 "${PY_SCRIPT}" --repo-root "${WORKSPACE_ROOT}" "$@"

if [[ -f "${SCRIPT_DIR}/lint-markdown.sh" ]]; then
    if [[ -d "${DONE_DIR}" ]]; then
        bash "${SCRIPT_DIR}/lint-markdown.sh" --fix "${DONE_DIR}" >/dev/null 2>&1 || true
    fi
    if [[ -f "${TODO_PATH}" ]]; then
        bash "${SCRIPT_DIR}/lint-markdown.sh" --fix "${TODO_PATH}" >/dev/null 2>&1 || true
    fi
fi
