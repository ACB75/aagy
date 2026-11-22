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
se inyecta entero. Si falta, no hace nada. Si el repo usa worktrees por agente,
añade dónde tiene que trabajar Claude (agent_worktree.py).
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
# Invariantes que se inyectan con su texto completo aunque se condense el resto:
# sin el formato concreto, Claude Code crea ramas con su propio esquema (claude/*, worktree-*).
FULL_TEXT_LABELS = ("Mandatory Branch Naming",)
BRANCH_NOTE = (
    "Ramas: crea y publica solo <tipo>/<proyecto>/<nombre> (validate_branch.py), aunque el entorno "
    "te asigne otra rama (p. ej. claude/* en Claude Code web): renombra con git branch -m o publica "
    "con git push -u origin HEAD:<tipo>/<proyecto>/<nombre> y abre el PR desde esa rama."
)


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
        if match and match.group(1) in FULL_TEXT_LABELS:
            lines.append(line)
        elif match:
            lines.append(f"- {match.group(1)}{match.group(2) or ''}")
    lines.append("")
    lines.append(BRANCH_NOTE)
    lines.append(
        f"Índice resumido. Texto completo: {rules_file}. Léelo con Read antes de commits, PRs, "
        "cambios de contrato o tareas del ciclo de vida, y siempre que una de estas reglas aplique."
    )
    return "\n".join(lines)


def backlog_brief(cwd: Optional[str]) -> str:
    """Resumen del backlog compartido con Antigravity (scripts/py/backlog.py), o "" si no hay."""
    py_dir = str(plugin_root() / "scripts" / "py")
    try:
        if py_dir not in sys.path:
            sys.path.insert(0, py_dir)
        import backlog  # noqa: PLC0415 - módulo del plugin, cargado solo si existe

        start = Path(cwd) if cwd else Path.cwd()
        ctx = backlog.Context(repo=backlog.locate_repo(start), cwd=start)
        return "\n".join(backlog.brief_lines(ctx))
    except Exception:  # noqa: BLE001 - un hook de arranque nunca debe romper la sesión
        return ""


def worktree_notice(cwd: Optional[str]) -> str:
    """Aviso del worktree fijo de Claude (scripts/py/agent_worktree.py), o "" si el repo no lo usa."""
    py_dir = str(plugin_root() / "scripts" / "py")
    try:
        if py_dir not in sys.path:
            sys.path.insert(0, py_dir)
        import agent_worktree  # noqa: PLC0415 - módulo del plugin, cargado solo si existe

        return agent_worktree.session_notice("claude", Path(cwd) if cwd else Path.cwd())
    except Exception:  # noqa: BLE001 - un hook de arranque nunca debe romper la sesión
        return ""


def build_response(rules_file: Optional[Path] = None, extra: str = "") -> Dict[str, Any]:
    """Devuelve el JSON de SessionStart con las reglas (o su índice) y el backlog, o {} si no hay nada."""
    target = rules_file or (plugin_root() / RULES_REL)
    try:
        text = target.read_text(encoding="utf-8").strip()
    except OSError:
        text = ""
    parts: List[str] = []
    if text:
        body = text if len(text) <= FULL_TEXT_BUDGET else condense(text, target)
        parts.append(f"{HEADER}:\n\n{body}")
    if extra:
        parts.append(extra)
    if not parts:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n\n".join(parts),
        }
    }


def read_hook_input() -> Dict[str, Any]:
    if sys.stdin.isatty():
        return {}
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def main() -> int:
    payload = read_hook_input()
    extra = "\n\n".join(p for p in (worktree_notice(payload.get("cwd")), backlog_brief(payload.get("cwd"))) if p)
    response = build_response(extra=extra)
    if response:
        print(json.dumps(response))  # ASCII: independiente de la codificación de stdout
    return 0


if __name__ == "__main__":
    sys.exit(main())
