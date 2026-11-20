#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/archive-todo.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/archive-todo.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
