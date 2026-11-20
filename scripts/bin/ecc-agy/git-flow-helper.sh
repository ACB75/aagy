#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/git-flow-helper.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/git-flow-helper.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
