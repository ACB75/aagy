#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/auto-evolve.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/auto-evolve.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
