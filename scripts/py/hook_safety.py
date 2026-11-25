#!/usr/bin/env python3
"""
Safety gate (hook_safety.py), PreToolUse de los dos plugins con un solo motor.

Bloquea comandos de riesgo catastrófico (``rm -rf /``, ``mkfs``, ``DROP DATABASE``,
escritura directa a discos) y los comandos git que crean o publican ramas fuera
de ``<tipo>/<proyecto>/<nombre>`` (validate_branch.py).

- ``--format claude``: lee ``tool_input.command``; responde ``permissionDecision=deny``.
- ``--format agy``: lee ``toolCall.args.CommandLine``; responde ``{"decision": "allow|deny"}``.

Solo stdlib. Ante cualquier error deja pasar (fail-open). Se espeja en
aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, Optional, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from validate_branch import command_rejection
except ImportError:  # fail-open: sin validador no se bloquea nada
    def command_rejection(command: str, current_branch=None) -> str:  # type: ignore[misc]
        return ""

FMT_CLAUDE = "claude"
FMT_AGY = "agy"
DANGEROUS_PATTERNS = (
    r"rm\s+-rf\s+/(?:[^a-zA-Z0-9_]|$)",
    r"mkfs(\.[a-zA-Z0-9]+)?\s+",
    r"DROP\s+DATABASE",
    r">\s*/dev/sd[a-z]",
    r"dd\s+if=.*of=/dev/sd",
)


def find_dangerous(command: str) -> Optional[str]:
    """El patrón que casa con el comando, o None si es seguro."""
    return next((p for p in DANGEROUS_PATTERNS if re.search(p, command, flags=re.IGNORECASE)), None)


def deny_reason(command: str) -> str:
    if not command:
        return ""
    if find_dangerous(command) is not None:
        return f"[SAFETY-GUARD] Comando bloqueado por regla de seguridad aagy: {command}"
    return command_rejection(command)


def response(reason: str, fmt: str) -> Dict[str, Any]:
    if fmt == FMT_AGY:
        return {"decision": "deny", "reason": reason} if reason else {"decision": "allow"}
    if not reason:
        return {}
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def build_response(command: str, fmt: str = FMT_CLAUDE) -> Dict[str, Any]:
    return response(deny_reason(command), fmt)


def extract_command(payload: Any, fmt: str) -> str:
    if not isinstance(payload, dict):
        return ""
    if fmt == FMT_AGY:
        args = (payload.get("toolCall") or {}).get("args") or {}
        return str(args.get("CommandLine") or "") if isinstance(args, dict) else ""
    tool_input = payload.get("tool_input")
    return str(tool_input.get("command") or "") if isinstance(tool_input, dict) else ""


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Safety gate PreToolUse (Claude Code y Antigravity).")
    parser.add_argument("--format", choices=(FMT_CLAUDE, FMT_AGY), default=FMT_CLAUDE)
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        out = build_response(extract_command(json.loads(raw) if raw.strip() else {}, args.format), args.format)
    except Exception:  # noqa: BLE001 - fail-open
        out = response("", args.format)
    if out:
        print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
