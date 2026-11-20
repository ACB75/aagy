#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/new-lifecycle-task.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/new-lifecycle-task.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
