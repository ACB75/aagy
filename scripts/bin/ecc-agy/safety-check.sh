#!/usr/bin/env bash
# Hook de seguridad determinista ejecutado antes de run_command (PreToolUse).
set -euo pipefail

CMD="${1:-}"

if [[ -n "$CMD" ]]; then
    if echo "$CMD" | grep -Ei -q "rm[[:space:]]+-rf[[:space:]]+/[^a-zA-Z0-9_]?|mkfs|DROP[[:space:]]+DATABASE|dd[[:space:]]+if=.*of=/dev/sd"; then
        echo "[SAFETY-GUARD] Comando bloqueado por regla de seguridad: $CMD" >&2
        exit 1
    fi
fi
exit 0
