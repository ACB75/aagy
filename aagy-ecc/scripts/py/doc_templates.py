#!/usr/bin/env python3
"""
Plantilla base de documentos (doc_templates.py): esqueleto común y extensiones.

Todos los documentos del harness (REQ, PLAN, DOCS, REVIEW, ADR, POSTMORTEM...)
heredan ``TEMPLATE_BASE.md``: cabecera, ``0. Estado actual``, ``1. Contexto y
objetivos``, el cuerpo propio del tipo, ``Criterios de aceptación``, ``Paridad``,
``Preguntas abiertas`` y ``Referencias``, en ese orden.

Puntos de extensión: el repo consumidor declara en ``.governance/docs-map.json``

    {"template_extensions": {"REQ": ["ruta/seccion.md"], "*": ["ruta/comun.md"]}}

y su contenido se inserta en el marcador ``<!-- aagy-extensions -->`` al instanciar
la plantilla, sin tocar el plugin. ``*`` vale para todos los tipos.

Si el repo no tiene una plantilla, se usa la que trae el plugin.

Issues, PR y notas de tarea comparten ``WORK_ITEM_SECTIONS`` (#93); ``check``
también revisa ``.github/`` del repo.

Uso::

    python doc_templates.py check [carpeta] [--repo <raíz>]

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Dict, Iterable, List, Optional, Sequence

_HERE = Path(__file__).resolve().parent
ENCODING = "utf-8"
EXTENSION_MARKER = "<!-- aagy-extensions -->"
EXTENSIONS_KEY = "template_extensions"
ALL_KINDS = "*"
DOCS_MAP_REL = Path(".governance") / "docs-map.json"
BASE_TEMPLATE = "TEMPLATE_BASE.md"
HEADER_FIELDS = ("**ID de Tarea**", "**Fecha**", "**Estado**", "**Ubicación en el repo**")
LEADING_SECTIONS = ("Estado actual", "Contexto y objetivos")
TRAILING_SECTIONS = ("Criterios de aceptación", "Paridad", "Preguntas abiertas", "Referencias")
# Issues, PR y tareas de TODO.md comparten estas secciones, en este orden (#93).
WORK_ITEM_SECTIONS = ("Motivación", "Criterios de aceptación", "Paridad", "Artefactos")
GITHUB_TEMPLATES = (".github/pull_request_template.md", ".github/ISSUE_TEMPLATE")
_HEADING = re.compile(r"^## (?:\d+\.\s*)?(?P<title>.+?)\s*$", re.MULTILINE)

# Plantillas que trae el plugin: en aagy viven en doc/; en aagy-ecc, en templates/lifecycle/.
PLUGIN_TEMPLATE_DIRS = (
    _HERE.parent.parent / "doc" / "00-governance" / "templates",
    _HERE.parent.parent / "templates" / "lifecycle",
)


def section_titles(text: str) -> List[str]:
    """Títulos de las secciones ``##`` sin su número."""
    return [m.group("title") for m in _HEADING.finditer(text)]


def _index_of(titles: Sequence[str], wanted: str) -> int:
    return next((i for i, t in enumerate(titles) if t.startswith(wanted)), -1)


def check_template(text: str) -> List[str]:
    """Problemas de esqueleto de una plantilla (lista vacía si cumple la base)."""
    problems = [f"falta {field} en la cabecera" for field in HEADER_FIELDS if field not in text]
    titles = section_titles(text)
    for pos, wanted in enumerate(LEADING_SECTIONS):
        if _index_of(titles, wanted) != pos:
            problems.append(f"'{wanted}' debe ser la sección {pos}")
    positions = [_index_of(titles, wanted) for wanted in TRAILING_SECTIONS]
    for wanted, pos in zip(TRAILING_SECTIONS, positions):
        if pos < 0:
            problems.append(f"falta la sección '{wanted}'")
    found = [p for p in positions if p >= 0]
    if found != sorted(found) or (found and found[-1] != len(titles) - 1):
        problems.append("las secciones finales deben ir en orden: " + ", ".join(TRAILING_SECTIONS))
    criteria = next((m.start() for m in _HEADING.finditer(text) if m.group("title").startswith(TRAILING_SECTIONS[0])), -1)
    if EXTENSION_MARKER not in text:
        problems.append(f"falta el marcador {EXTENSION_MARKER}")
    elif criteria >= 0 and text.index(EXTENSION_MARKER) > criteria:
        problems.append(f"el marcador de extensiones debe ir antes de '{TRAILING_SECTIONS[0]}'")
    return problems


def check_dir(folder: Path) -> Dict[str, List[str]]:
    """Problemas por plantilla ``*.md`` de una carpeta (sin README)."""
    report: Dict[str, List[str]] = {}
    for path in sorted(folder.glob("*.md")):
        if path.name.upper() == "README.MD":
            continue
        problems = check_template(path.read_text(encoding=ENCODING))
        if problems:
            report[path.name] = problems
    return report


def check_work_item(text: str) -> List[str]:
    """Problemas de una issue, PR o nota de tarea frente a WORK_ITEM_SECTIONS."""
    titles = section_titles(text)
    positions = [_index_of(titles, wanted) for wanted in WORK_ITEM_SECTIONS]
    problems = [f"falta la sección '{w}'" for w, pos in zip(WORK_ITEM_SECTIONS, positions) if pos < 0]
    found = [p for p in positions if p >= 0]
    if found != sorted(found):
        problems.append("las secciones deben ir en orden: " + ", ".join(WORK_ITEM_SECTIONS))
    return problems


def check_github(repo_root: Path) -> Dict[str, List[str]]:
    """Problemas de las plantillas de issues y PR del repo (vacío si no tiene)."""
    paths: List[Path] = []
    for rel in GITHUB_TEMPLATES:
        target = repo_root / rel
        paths.extend(sorted(target.glob("*.md")) if target.is_dir() else [target] if target.is_file() else [])
    report: Dict[str, List[str]] = {}
    for path in paths:
        problems = check_work_item(path.read_text(encoding=ENCODING))
        if problems:
            report[path.relative_to(repo_root).as_posix()] = problems
    return report


def find_template(name: str, preferred: Path, extra: Iterable[Path] = PLUGIN_TEMPLATE_DIRS) -> Optional[Path]:
    """La plantilla del repo si existe; si no, la que trae el plugin."""
    for folder in (preferred, *extra):
        candidate = folder / name
        if candidate.is_file():
            return candidate
    return None


def declared_extensions(repo_root: Path) -> Dict[str, List[str]]:
    """``template_extensions`` de docs-map.json (vacío si no hay o es inválido)."""
    path = repo_root / DOCS_MAP_REL
    try:
        data = json.loads(path.read_text(encoding=ENCODING))
    except (OSError, ValueError):
        return {}
    raw = data.get(EXTENSIONS_KEY) if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {str(k).upper(): [str(p) for p in v] for k, v in raw.items() if isinstance(v, list)}


def _inside(root: Path, rel: str) -> Optional[Path]:
    candidate = (root / rel).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def extension_blocks(kind: str, repo_root: Path) -> List[str]:
    """Contenido de las extensiones de ``kind`` (y de ``*``); ignora rutas fuera del repo."""
    declared = declared_extensions(repo_root)
    rels = [*declared.get(ALL_KINDS, []), *declared.get(kind.upper(), [])]
    blocks = []
    for rel in rels:
        path = _inside(repo_root, rel)
        if path is None:
            print(f"[WARN] Extensión de plantilla no encontrada o fuera del repo: {rel}", file=sys.stderr)
            continue
        blocks.append(path.read_text(encoding=ENCODING).strip())
    return blocks


def apply_extensions(text: str, kind: str, repo_root: Path) -> str:
    """Inserta las extensiones en el marcador (o quita el marcador si no hay)."""
    blocks = extension_blocks(kind, repo_root)
    replacement = "\n\n".join(blocks)
    if EXTENSION_MARKER not in text:
        return text + ("\n\n" + replacement + "\n" if replacement else "")
    rendered = text.replace(EXTENSION_MARKER, replacement)
    return re.sub(r"\n{3,}", "\n\n", rendered)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Esqueleto común de plantillas de documentos.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_check = sub.add_parser("check", help="Comprueba el esqueleto de las plantillas de una carpeta.")
    p_check.add_argument("folder", nargs="?", type=Path, default=None)
    p_check.add_argument("--repo", type=Path, default=Path.cwd(), help="Repo cuyas plantillas de issues y PR se comprueban.")
    args = parser.parse_args(argv)
    folder = args.folder or next((d for d in PLUGIN_TEMPLATE_DIRS if d.is_dir()), PLUGIN_TEMPLATE_DIRS[0])
    report = {**check_dir(folder), **check_github(args.repo)}
    for name, problems in report.items():
        for problem in problems:
            print(f"[FAIL] {name}: {problem}")
    print(f"[doc-templates] {'FALLA' if report else 'OK'}: {folder}")
    return 1 if report else 0


if __name__ == "__main__":
    sys.exit(main())
