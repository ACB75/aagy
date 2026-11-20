#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/generate-postmortem.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/generate-postmortem.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
