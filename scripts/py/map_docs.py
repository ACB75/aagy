#!/usr/bin/env python3
"""
Módulo de auditoría, mapeo y validación de enlaces relativos en documentación Markdown (map_docs.py).
Detecta enlaces rotos en /doc (v2 o clásico), valida `.governance/docs-map.json` y genera un informe estructurado.
Cumple con SonarQube Quality Gate A (S3776 <= 15, S1192 sin duplicados, S107 <= 7).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import List, Optional, Sequence, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from docs_map import DOCS_MAP_REL, resolve_doc_path, validate_docs_map_targets

# Regex para extraer enlaces Markdown: [texto](destino)
MD_LINK_REGEX = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
INLINE_CODE_REGEX = re.compile(r"`([^`]*)`")
IGNORED_SCHEMES = ("http://", "https://", "mailto:", "ftp://", "file://")


@dataclass(frozen=True)
class DocLink:
    """Representa un enlace extraído de un archivo Markdown."""

    source_file: Path
    line_no: int
    link_text: str
    target_path: str
    is_valid: bool


def _is_relative_doc_link(raw_target: str) -> bool:
    """Verifica si el enlace es una referencia relativa interna a archivo."""
    trimmed = raw_target.strip()
    if not trimmed or trimmed.startswith("#"):
        return False
    if "<" in trimmed or ">" in trimmed:
        return False
    return not any(trimmed.startswith(scheme) for scheme in IGNORED_SCHEMES)


def _sanitize_inline_code(line: str) -> str:
    """Preserva etiquetas con backticks [`texto`](url) e ignora ejemplos sintácticos `[a](b)`."""
    def _replace(match: re.Match[str]) -> str:
        inner = match.group(1)
        return "" if "](" in inner else inner

    return INLINE_CODE_REGEX.sub(_replace, line)


def extract_links_from_markdown(file_path: Path, content: str) -> List[DocLink]:
    """Extrae enlaces relativos de un archivo Markdown, ignorando bloques y fragmentos de código."""
    links: List[DocLink] = []
    in_fence = False
    for line_idx, line in enumerate(content.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        sanitized_line = _sanitize_inline_code(line)
        for match in MD_LINK_REGEX.finditer(sanitized_line):
            text = match.group(1).strip()
            target = match.group(2).strip()
            if _is_relative_doc_link(target):
                links.append(
                    DocLink(
                        source_file=file_path,
                        line_no=line_idx,
                        link_text=text,
                        target_path=target,
                        is_valid=False,
                    )
                )
    return links


def _resolve_link_target(source_file: Path, target_path: str) -> bool:
    """Comprueba la existencia del archivo de destino en disco."""
    clean_target = target_path.split("#", 1)[0].strip()
    if not clean_target:
        return True
    resolved = (source_file.parent / clean_target).resolve()
    return resolved.exists()


def validate_links(doc_root: Path) -> List[DocLink]:
    """Escanea y valida todos los enlaces relativos bajo doc_root."""
    results: List[DocLink] = []
    if not doc_root.exists():
        return results

    md_files = [doc_root] if doc_root.is_file() else sorted(doc_root.rglob("*.md"))
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for link in extract_links_from_markdown(md_file, content):
            valid = _resolve_link_target(link.source_file, link.target_path)
            results.append(
                DocLink(
                    source_file=link.source_file,
                    line_no=link.line_no,
                    link_text=link.link_text,
                    target_path=link.target_path,
                    is_valid=valid,
                )
            )
    return results


def generate_report(
    links: List[DocLink],
    docs_map_issues: Optional[Sequence[str]] = None,
) -> Tuple[int, str]:
    """Genera un reporte textual estructurado de los enlaces auditados."""
    total = len(links)
    broken = [lnk for lnk in links if not lnk.is_valid]
    map_issues = list(docs_map_issues or [])
    valid_count = total - len(broken)
    total_failures = len(broken) + len(map_issues)

    report_lines = [
        "==================================================================",
        "          INFORME DE SALUD Y MAPEO DOCUMENTAL (MAP-DOCS)          ",
        "==================================================================",
        f"Total de enlaces relativos auditados: {total}",
        f"Enlaces válidos: {valid_count}",
        f"Enlaces rotos detectados: {len(broken)}",
    ]

    if docs_map_issues is not None:
        report_lines.append(f"Incidencias en .governance/docs-map.json: {len(map_issues)}")

    if broken:
        report_lines.append("\n=== ENLACES ROTOS DETECTADOS ===")
        for item in broken:
            clean_path = str(item.source_file).replace("\\", "/")
            report_lines.append(f"  [BROKEN] {clean_path}:{item.line_no} -> '{item.target_path}' ({item.link_text})")

    if map_issues:
        report_lines.append("\n=== INCIDENCIAS EN DOCS-MAP ===")
        for issue in map_issues:
            report_lines.append(f"  [DOCS-MAP] {issue}")

    if total_failures == 0:
        report_lines.append("\n[PASS] Todos los enlaces relativos y referencias documentales son válidos.")

    report_lines.append("==================================================================")
    return total_failures, "\n".join(report_lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Auditoría y validación de enlaces documentales relativos.")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Raíz del repositorio.")
    parser.add_argument(
        "--doc-root",
        type=Path,
        default=None,
        help="Directorio raíz de documentación a auditar (opcional, lee docs-map.json).",
    )
    parser.add_argument(
        "--check-docs-map",
        action="store_true",
        help="Valida integridad y destinos de .governance/docs-map.json.",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada principal."""
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()
    doc_root = args.doc_root if args.doc_root is not None else resolve_doc_path(repo_root, "doc_root")

    links = validate_links(doc_root)
    docs_map_issues: Optional[List[str]] = None
    should_check_map = args.check_docs_map or (args.doc_root is None and (repo_root / DOCS_MAP_REL).is_file())
    if should_check_map:
        docs_map_issues = validate_docs_map_targets(repo_root)

    failure_count, report_text = generate_report(links, docs_map_issues=docs_map_issues)
    print(report_text)
    return 1 if failure_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
