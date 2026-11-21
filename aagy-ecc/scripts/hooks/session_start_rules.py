#!/usr/bin/env python3
"""
Hook SessionStart de aagy-ecc para Claude Code.

En Antigravity, el plugin aagy carga siempre rules/AGENTS.md (Tier 1 global).
Claude Code no tiene reglas globales de plugin, así que este hook inyecta esas
reglas (copiadas en aagy-ecc/rules/AGENTS.md por sync_aagy_ecc.py) como contexto
adicional al iniciar sesión, tras /clear y tras compactar.

Para no gastar tokens en cada sesión (y no pasar el límite de additionalContext,
que Claude Code recorta a un fichero), se inyecta un índice compacto: los
encabezados y la etiqueta de cada invariante, más la ruta del texto completo para
leerlo con Read cuando una regla aplique. Si el fichero cabe en el presupuesto,
se inyecta entero. Si falta, no hace nada.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional

RULES_REL = Path("rules") / "AGENTS.md"
FULL_TEXT_BUDGET = 2500
_BULLET_LABEL = re.compile(r"^- \*\*(.+?)\*\*(\s*\([^)]*\))?")
HEADER = "Reglas globales Tier 1 de aagy (rules/AGENTS.md)"


def plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def condense(text: str, rules_file: Path) -> str:
    """Índice de las reglas: encabezados y etiquetas de cada invariante, con la ruta del original."""
    lines: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            lines.append(line)
            continue
        match = _BULLET_LABEL.match(line)
        if match:
            lines.append(f"- {match.group(1)}{match.group(2) or ''}")
    lines.append("")
    lines.append(
        f"Índice resumido. Texto completo: {rules_file}. Léelo con Read antes de commits, PRs, "
        "cambios de contrato o tareas del ciclo de vida, y siempre que una de estas reglas aplique."
    )
    return "\n".join(lines)


def build_response(rules_file: Optional[Path] = None) -> Dict[str, Any]:
    """Devuelve el JSON de SessionStart con las reglas (o su índice), o {} si no hay reglas legibles."""
    target = rules_file or (plugin_root() / RULES_REL)
    try:
        text = target.read_text(encoding="utf-8").strip()
    except OSError:
        return {}
    if not text:
        return {}
    body = text if len(text) <= FULL_TEXT_BUDGET else condense(text, target)
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": f"{HEADER}:\n\n{body}",
        }
    }


def main() -> int:
    if not sys.stdin.isatty():
        sys.stdin.read()
    response = build_response()
    if response:
        print(json.dumps(response))  # ASCII: independiente de la codificación de stdout
    return 0


if __name__ == "__main__":
    sys.exit(main())
