#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/install-git-hooks.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/install-git-hooks.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
