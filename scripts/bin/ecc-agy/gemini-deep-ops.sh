#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/gemini-deep-ops.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/gemini-deep-ops.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
