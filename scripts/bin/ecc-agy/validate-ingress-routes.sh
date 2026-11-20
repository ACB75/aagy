#!/usr/bin/env bash
# Forwarding proxy towards canonical scripts/sh/validate-ingress-routes.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CANONICAL_SCRIPT="$SCRIPT_DIR/../../sh/validate-ingress-routes.sh"
exec bash "$CANONICAL_SCRIPT" "$@"
