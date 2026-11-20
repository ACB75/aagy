#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/session-token-monitor.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/session-token-monitor.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
