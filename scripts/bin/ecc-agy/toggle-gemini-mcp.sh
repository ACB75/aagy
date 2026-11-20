#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/toggle-gemini-mcp.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/toggle-gemini-mcp.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
