#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/sonar-audit.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/sonar-audit.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
