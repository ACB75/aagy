#!/usr/bin/env python3
"""
Hook PreToolUse (Bash / PowerShell) de aagy-ecc para Claude Code.

Equivalente a scripts/ps1/safety-check.ps1 del plugin aagy (Antigravity):
bloquea comandos de riesgo catastrófico (rm -rf /, mkfs, DROP DATABASE,
escritura directa a discos). Lee el contrato JSON de Claude Code por stdin
y responde con permissionDecision=deny cuando hay coincidencia.
Python 3 stdlib pura; ante cualquier error permite la ejecución (fail-open).
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict, Optional

DANGEROUS_PATTERNS = (
    r"rm\s+-rf\s+/(?:[^a-zA-Z0-9_]|$)",
    r"mkfs(\.[a-zA-Z0-9]+)?\s+",
    r"DROP\s+DATABASE",
    r">\s*/dev/sd[a-z]",
    r"dd\s+if=.*of=/dev/sd",
)


def find_dangerous(command: str) -> Optional[str]:
    """Devuelve el patrón que coincide con el comando, o None si es seguro."""
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return pattern
    return None


def build_response(command: str) -> Dict[str, Any]:
    """Construye la respuesta del hook para un comando dado."""
    if not command or find_dangerous(command) is None:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"[SAFETY-GUARD] Comando bloqueado por regla de seguridad aagy: {command}",
        }
    }


def _extract_command(raw: str) -> str:
    try:
        payload = json.loads(raw) if raw and raw.strip() else {}
    except ValueError:
        return ""
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    if isinstance(tool_input, dict):
        return str(tool_input.get("command") or "")
    return ""


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    response = build_response(_extract_command(raw))
    if response:
        print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
