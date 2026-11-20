#!/usr/bin/env sh
# Wrapper POSIX para el validador de congruencia Ingress, Split-DNS y Portal.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
PY_SCRIPT="$REPO_ROOT/scripts/ecc-agy/validate_ingress_routes.py"

python3 "$PY_SCRIPT" "$@"
