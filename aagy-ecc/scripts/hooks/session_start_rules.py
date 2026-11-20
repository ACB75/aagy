#!/usr/bin/env python3
"""
Hook SessionStart de aagy-ecc para Claude Code.

En Antigravity, el plugin aagy carga siempre rules/AGENTS.md (Tier 1 global).
Claude Code no tiene reglas globales de plugin, así que este hook inyecta el
mismo archivo (copiado en aagy-ecc/rules/AGENTS.md por sync_aagy_ecc.py) como
contexto adicional al iniciar o reanudar sesión. Si falta, no hace nada.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict, Optional

RULES_REL = Path("rules") / "AGENTS.md"


def plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def build_response(rules_file: Optional[Path] = None) -> Dict[str, Any]:
    """Devuelve el JSON de SessionStart con las reglas, o {} si no hay reglas legibles."""
    target = rules_file or (plugin_root() / RULES_REL)
    try:
        text = target.read_text(encoding="utf-8").strip()
    except OSError:
        return {}
    if not text:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "Reglas globales Tier 1 de aagy (rules/AGENTS.md):\n\n" + text,
        }
    }


def main() -> int:
    if not sys.stdin.isatty():
        sys.stdin.read()
    response = build_response()
    if response:
        print(json.dumps(response, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
