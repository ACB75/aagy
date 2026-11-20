#!/usr/bin/env sh
# Wrapper POSIX para el linter de paridad estatica de contratos SDK.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/ecc-agy/audit_sdk_parity.py"

python3 "$PY_SCRIPT" "$@"
