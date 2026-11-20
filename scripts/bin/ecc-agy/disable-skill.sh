#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/disable-skill.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/disable-skill.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
