#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/security-audit.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/security-audit.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
