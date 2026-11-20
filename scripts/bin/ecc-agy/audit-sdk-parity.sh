#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/audit-sdk-parity.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/audit-sdk-parity.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
