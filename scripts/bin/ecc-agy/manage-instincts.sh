#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/manage-instincts.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/manage-instincts.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
