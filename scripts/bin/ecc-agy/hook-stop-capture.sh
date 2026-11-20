#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/hook-stop-capture.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/hook-stop-capture.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
