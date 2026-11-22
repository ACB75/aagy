#!/usr/bin/env python3
"""
Hook PreToolUse de aagy-ecc: Claude Code solo escribe en su worktree fijo.

Si el repo tiene activados los worktrees por agente (agent_worktree.py init; lógica en agent_worktree_guard.py), deniega
escrituras y comandos que modifican el checkout principal de Master (`<repo>`) o el
worktree de Antigravity (`<repo>-aagy`), y el worktree nativo de Claude Code
(EnterWorktree, claude --worktree). Sin marcador no hace nada. Fail-open ante errores.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "py"))


def main() -> int:
    try:
        import agent_worktree_guard as guard  # noqa: PLC0415

        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        payload = json.loads(raw) if raw.strip() else {}
        reason = guard.guard_payload("claude", payload, "claude")
        response = guard.guard_response(reason, "claude")
    except Exception:  # noqa: BLE001 - fail-open: una guarda rota no bloquea el trabajo
        return 0
    if response:
        print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
