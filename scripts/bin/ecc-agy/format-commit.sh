#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/format-commit.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/format-commit.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
