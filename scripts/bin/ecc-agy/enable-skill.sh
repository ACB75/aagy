#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/enable-skill.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/enable-skill.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
