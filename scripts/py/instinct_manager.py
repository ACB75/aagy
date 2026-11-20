#!/usr/bin/env python3
"""
Gestor de Instintos y Aprendizajes por Proyecto para Antigravity / Home-Lab (stdlib pura).

Permite capturar, almacenar y exportar instintos en .agents/instincts/*.md
desacoplados del prompt principal para no inflar AGENTS.md.
"""
from __future__ import annotations

import argparse
import datetime
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence

logger: logging.Logger = logging.getLogger("instinct-manager")

INSTINCTS_SUBDIR: str = ".agents/instincts"
DEFAULT_DOMAIN: str = "general"
HELP_ROOT: str = "Raíz del repositorio."
FRONTMATTER_REGEX: re.Pattern[str] = re.compile(r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$", re.DOTALL)


@dataclass(frozen=True)
class Instinct:
    instinct_id: str
    trigger: str
    learning: str
    domain: str
    confidence: float
    file_path: Path


def _parse_frontmatter_field(fm: str, key: str) -> Optional[str]:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", fm, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip("'\"")


def save_instinct(
    repo_root: Path,
    instinct_id: str,
    trigger: str,
    learning: str,
    domain: str = DEFAULT_DOMAIN,
    confidence: float = 0.9,
) -> Instinct:
    """Guarda o actualiza un instinto en .agents/instincts/<id>.md."""
    clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "_", instinct_id).strip("_").lower()
    instincts_dir = repo_root / ".agents" / "instincts"
    instincts_dir.mkdir(parents=True, exist_ok=True)

    target_file = instincts_dir / f"{clean_id}.md"
    today = datetime.date.today().isoformat()

    content = f"""---
id: "{clean_id}"
trigger: "{trigger}"
domain: "{domain}"
confidence: {confidence}
created_at: "{today}"
---

# Instinto: {clean_id}

> **Disparador Operativo**: `{trigger}` | **Dominio**: `{domain}`

{learning.strip()}
"""
    target_file.write_text(content, encoding="utf-8")
    logger.info("[OK] Instinto guardado en: %s", target_file)

    return Instinct(
        instinct_id=clean_id,
        trigger=trigger,
        learning=learning.strip(),
        domain=domain,
        confidence=confidence,
        file_path=target_file,
    )


def list_instincts(repo_root: Path) -> List[Instinct]:
    """Lista todos los instintos registrados en .agents/instincts/."""
    instincts_dir = repo_root / ".agents" / "instincts"
    if not instincts_dir.is_dir():
        return []

    instincts: List[Instinct] = []
    for file_path in sorted(instincts_dir.glob("*.md")):
        if file_path.name == "README.md":
            continue
        try:
            raw = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        match = FRONTMATTER_REGEX.match(raw)
        if not match:
            continue

        fm, body = match.group(1), match.group(2)
        inst_id = _parse_frontmatter_field(fm, "id") or file_path.stem
        trigger = _parse_frontmatter_field(fm, "trigger") or DEFAULT_DOMAIN
        domain = _parse_frontmatter_field(fm, "domain") or DEFAULT_DOMAIN
        conf_str = _parse_frontmatter_field(fm, "confidence") or "0.9"

        try:
            confidence = float(conf_str)
        except ValueError:
            confidence = 0.9

        instincts.append(
            Instinct(
                instinct_id=inst_id,
                trigger=trigger,
                learning=body.strip(),
                domain=domain,
                confidence=confidence,
                file_path=file_path,
            )
        )
    return instincts


def export_instincts(repo_root: Path) -> str:
    """Genera un resumen en Markdown de todos los instintos activos."""
    instincts = list_instincts(repo_root)
    if not instincts:
        return "No hay instintos registrados en este proyecto."

    lines = [
        "# Catálogo de Instintos del Proyecto",
        "",
        "| ID | Disparador | Dominio | Confianza | Archivo |",
        "| :--- | :--- | :---: | :---: | :--- |",
    ]
    for inst in instincts:
        lines.append(f"| `{inst.instinct_id}` | {inst.trigger} | {inst.domain} | {inst.confidence:.2f} | `{inst.file_path.name}` |")

    lines.append("\n## Directivas Detalladas\n")
    for inst in instincts:
        lines.append(f"### `{inst.instinct_id}` ({inst.domain})")
        lines.append(f"- **Trigger**: {inst.trigger}")
        lines.append(f"- **Aprendizaje**: {inst.learning}\n")

    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gestor de Instintos por Proyecto (.agents/instincts/).")
    subparsers = parser.add_subparsers(dest="subcommand", help="Comandos disponibles")

    # save
    p_save = subparsers.add_parser("save", help="Guarda un nuevo instinto.")
    p_save.add_argument("--id", required=True, help="ID o slug del instinto.")
    p_save.add_argument("--trigger", required=True, help="Palabra clave o disparador.")
    p_save.add_argument("--learning", required=True, help="Texto del aprendizaje o directriz.")
    p_save.add_argument("--domain", default=DEFAULT_DOMAIN, help="Dominio (database, backend, frontend, sre).")
    p_save.add_argument("--confidence", type=float, default=0.9, help="Nivel de confianza (0.0 a 1.0).")
    p_save.add_argument("--root", type=Path, default=None, help=HELP_ROOT)

    # list
    p_list = subparsers.add_parser("list", help="Lista los instintos existentes.")
    p_list.add_argument("--root", type=Path, default=None, help=HELP_ROOT)

    # export
    p_exp = subparsers.add_parser("export", help="Exporta instintos en formato Markdown.")
    p_exp.add_argument("--root", type=Path, default=None, help=HELP_ROOT)

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)

    root = getattr(args, "root", None)
    repo_root = root.resolve() if root else Path(__file__).resolve().parent.parent.parent

    if args.subcommand == "save":
        save_instinct(
            repo_root=repo_root,
            instinct_id=args.id,
            trigger=args.trigger,
            learning=args.learning,
            domain=args.domain,
            confidence=args.confidence,
        )
        return 0

    if args.subcommand == "list" or not args.subcommand:
        instincts = list_instincts(repo_root)
        logger.info("=== INSTINTOS REGISTRADOS (%d) ===", len(instincts))
        for inst in instincts:
            logger.info("  • [%s] %s: %s", inst.domain, inst.instinct_id, inst.trigger)
        return 0

    if args.subcommand == "export":
        summary = export_instincts(repo_root)
        logger.info("%s", summary)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
