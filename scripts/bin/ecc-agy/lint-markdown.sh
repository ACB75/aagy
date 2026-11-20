#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/lint-markdown.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/lint-markdown.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
