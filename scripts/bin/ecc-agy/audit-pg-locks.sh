#!/usr/bin/env sh
# Wrapper POSIX para el analizador estatico de bloqueos DDL en PostgreSQL LTS.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/ecc-agy/audit_pg_locks.py"

python3 "$PY_SCRIPT" "$@"
