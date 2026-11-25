#!/usr/bin/env python3
"""
Esqueleto común de workflows (workflow_skeleton.py): skills, comandos y agentes.

Secciones comunes, en este orden y antes de cualquier otra (RF-05):
``Cuándo usarlo``, ``Uso``, ``Qué hacer``, ``Reglas`` y ``Paridad``. La sección
``Paridad`` nombra el equivalente en el otro plugin o declara la asimetría (RF-06).

- Workflows propios de aagy (``OWN_WORKFLOWS``): el esqueleto es obligatorio (FAIL).
- Heredados de ECC: solo aviso (WARN) y se aceptan sus nombres en inglés
  (P-01). El aviso pasa a FAIL cuando termine la revisión final (#97).

Uso::

    python workflow_skeleton.py [--repo <raíz>] [--json] [--strict]

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
from typing import Dict, Iterator, List, Optional, Sequence, Tuple

ENCODING = "utf-8"
SECTIONS: Tuple[str, ...] = ("Cuándo usarlo", "Uso", "Qué hacer", "Reglas", "Paridad")
SECTION_PARITY = SECTIONS[-1]
LEVEL_FAIL = "FAIL"
LEVEL_WARN = "WARN"

# Nombres equivalentes: "Cuándo usarla" en las propias y los de ECC en las heredadas.
ALIASES: Dict[str, Tuple[str, ...]] = {
    "Cuándo usarlo": ("Cuándo usarla", "When to Use", "When to Activate", "When Activated", "Trigger"),
    "Uso": ("Usage", "How to Use"),
    "Qué hacer": ("What to Do", "Process", "Workflow", "How It Works", "Steps"),
    "Reglas": ("Rules", "Guardrails", "Non-Negotiable Rules", "Key Principles"),
    "Paridad": ("Parity",),
}

OWN_ALIASES: Dict[str, Tuple[str, ...]] = {"Cuándo usarlo": ("Cuándo usarla",)}

# Workflows propios de aagy: deben cumplir el esqueleto exacto (en español y en orden).
OWN_WORKFLOWS = frozenset({
    "skills/aagy-doctor", "skills/aagy-local", "skills/agent-worktrees", "skills/shared-backlog",
    "skills/engineering-lifecycle", "skills/todo-lifecycle", "skills/gemini-deep-ops",
    "commands/aagy-ecc-doctor", "commands/aagy-local", "commands/aagy-todo", "commands/aagy-worktree",
    "commands/epic-claim", "commands/epic-close", "commands/epic-decompose", "commands/epic-sync",
    "agents/lifecycle-coordinator", "agents/todo-archiver",
})


@dataclass(frozen=True)
class Finding:
    key: str
    level: str
    problems: Tuple[str, ...]


def headings(text: str) -> List[str]:
    """Títulos ``##`` fuera de bloques de código."""
    titles: List[str] = []
    fenced = False
    for line in text.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and line.startswith("## "):
            titles.append(re.sub(r"^\d+\.\s*", "", line[3:].strip()))
    return titles


def _canonical(title: str, own: bool) -> Optional[str]:
    for section in SECTIONS:
        names = (section, *OWN_ALIASES.get(section, ())) if own else (section, *ALIASES[section])
        if any(title.lower().startswith(n.lower()) for n in names):
            return section
    return None


def _parity_body(text: str) -> str:
    match = re.search(r"^## (?:Paridad|Parity)\b[^\n]*\n(?P<body>.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    return match.group("body").strip() if match else ""


def check_text(text: str, own: bool) -> List[str]:
    """Problemas de esqueleto de un workflow."""
    mapped = [_canonical(t, own) for t in headings(text)]
    present = [m for m in mapped if m]
    problems = [f"falta '{s}'" for s in SECTIONS if s not in present]
    if not own:
        return problems
    leading = mapped[: len(SECTIONS)]
    if not problems and leading != list(SECTIONS):
        problems.append("las secciones comunes deben ir primero y en orden: " + ", ".join(SECTIONS))
    if SECTION_PARITY in present and not re.search(r"`[^`]+`|asimetr", _parity_body(text), re.IGNORECASE):
        problems.append("'Paridad' debe nombrar el equivalente (`...`) o declarar la asimetría")
    return problems


def workflow_files(repo_root: Path) -> Iterator[Tuple[str, Path]]:
    """(clave, ruta) de las skills, agentes y comandos fuente (no los espejos de aagy-ecc)."""
    for path in sorted((repo_root / "skills").glob("*/SKILL.md")):
        yield f"skills/{path.parent.name}", path
    for path in sorted((repo_root / "agents").glob("*.md")):
        yield f"agents/{path.stem}", path
    for path in sorted((repo_root / "aagy-ecc" / "commands").glob("*.md")):
        yield f"commands/{path.stem}", path


def audit(repo_root: Path) -> List[Finding]:
    findings: List[Finding] = []
    for key, path in workflow_files(repo_root):
        own = key in OWN_WORKFLOWS
        problems = check_text(path.read_text(encoding=ENCODING, errors="replace"), own)
        if problems:
            findings.append(Finding(key, LEVEL_FAIL if own else LEVEL_WARN, tuple(problems)))
    return findings


def summary_line(findings: Sequence[Finding]) -> str:
    fails = sum(1 for f in findings if f.level == LEVEL_FAIL)
    warns = len(findings) - fails
    return f"[workflow-skeleton] propios con fallos: {fails}; heredados sin esqueleto completo: {warns}"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Esqueleto común de skills, comandos y agentes.")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="Los WARN también fallan.")
    parser.add_argument("--verbose", action="store_true", help="Lista también los WARN.")
    args = parser.parse_args(argv)
    findings = audit(args.repo.resolve())
    if args.json:
        print(json.dumps([f.__dict__ for f in findings], ensure_ascii=False, indent=2))
    else:
        for item in findings:
            if item.level == LEVEL_FAIL or args.verbose:
                print(f"[{item.level}] {item.key}: {'; '.join(item.problems)}")
        print(summary_line(findings))
    failing = [f for f in findings if f.level == LEVEL_FAIL or args.strict]
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
