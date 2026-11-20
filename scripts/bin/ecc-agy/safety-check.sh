#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/safety-check.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/safety-check.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
