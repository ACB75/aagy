#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/complete-task-pr.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/complete-task-pr.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
