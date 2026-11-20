#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/sync-ideas-todo.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/sync-ideas-todo.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
