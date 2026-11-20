#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/audit-pg-locks.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/audit-pg-locks.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
