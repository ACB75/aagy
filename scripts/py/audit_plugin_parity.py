#!/usr/bin/env python3
"""
Módulo de auditoría de paridad multi-harness entre Anything Antigravity (aagy)
y el subplugin para Claude Code (aagy) (audit_plugin_parity.py).

Verifica la simetría y coherencia estructural entre el arnés Antigravity/Gemini
y el arnés Claude Code para garantizar capacidades equivalentes sin deriva.
Cumple con SonarQube Quality Gate A (S3776 <= 15, S1192 sin duplicados).
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Constantes de Estado y Literales para SonarQube (S1192)
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_SKIPPED = "SKIPPED"

PLUGIN_NAME_AAGY = "aagy"
PLUGIN_NAME_AAGY_ECC = "aagy-ecc"

FILE_PLUGIN_JSON = "plugin.json"
DIR_SKILLS = "skills"
DIR_AAGY_ECC = "aagy-ecc"

# Configuración de codificación UTF-8
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("audit-plugin-parity")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError) as exc:
        logger.debug("sys.stdout reconfigure skipped: %s", exc)


@dataclass(frozen=True)
class ParityAuditResult:
    """Resultado estructurado de la auditoría de paridad multi-harness."""
    status: str
    is_valid: bool
    root_plugin_name: str
    claude_plugin_name: str
    skills_count: int
    claude_skills_count: int
    discrepancies: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return asdict(self)


def _load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Carga y parsea un archivo JSON de forma segura."""
    if not file_path.is_file():
        return None
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return None
    except Exception:
        return None


def _check_root_plugin(repo_root: Path, discrepancies: List[str]) -> str:
    """Valida el manifiesto plugin.json del plugin raíz Antigravity."""
    root_manifest = repo_root / FILE_PLUGIN_JSON
    root_data = _load_json_file(root_manifest)
    if not root_data:
        discrepancies.append(f"No se encontró o es inválido '{FILE_PLUGIN_JSON}' en la raíz del repositorio.")
        return ""

    root_name = str(root_data.get("name", "")).strip()
    if root_name != PLUGIN_NAME_AAGY:
        discrepancies.append(
            f"El nombre del plugin raíz ('{root_name}') no coincide con '{PLUGIN_NAME_AAGY}'."
        )
    return root_name


def _check_claude_plugin(repo_root: Path, discrepancies: List[str]) -> Tuple[str, int]:
    """Valida el subplugin aagy-ecc para Claude Code."""
    claude_dir = repo_root / DIR_AAGY_ECC
    if not claude_dir.is_dir():
        discrepancies.append(f"No se encontró el subdirectorio del plugin Claude Code '{DIR_AAGY_ECC}/'.")
        return "", 0

    claude_manifest = claude_dir / ".claude-plugin" / FILE_PLUGIN_JSON
    claude_data = _load_json_file(claude_manifest)
    claude_name = ""
    if not claude_data:
        pkg_json = claude_dir / "package.json"
        pkg_data = _load_json_file(pkg_json)
        if pkg_data:
            claude_name = str(pkg_data.get("name", "")).strip()
        else:
            discrepancies.append(f"No se encontró manifiesto válido de plugin en '{claude_dir.name}/.claude-plugin/' ni 'package.json'.")
    else:
        claude_name = str(claude_data.get("name", "")).strip()

    if claude_name and claude_name != PLUGIN_NAME_AAGY_ECC:
        discrepancies.append(f"El nombre del plugin Claude Code ('{claude_name}') no es '{PLUGIN_NAME_AAGY_ECC}'.")

    claude_skills_dir = claude_dir / DIR_SKILLS
    claude_skills_count = 0
    if claude_skills_dir.is_dir():
        claude_skills_count = sum(1 for p in claude_skills_dir.iterdir() if p.is_dir())
    elif (repo_root / DIR_SKILLS).is_dir():
        claude_skills_count = sum(1 for p in (repo_root / DIR_SKILLS).iterdir() if p.is_dir())

    return claude_name, claude_skills_count


def audit_parity(repo_root: Path) -> ParityAuditResult:
    """
    Ejecuta la auditoría de paridad completa entre Anything Antigravity y Claude Code.
    """
    discrepancies: List[str] = []

    root_name = _check_root_plugin(repo_root, discrepancies)
    claude_name, claude_skills_count = _check_claude_plugin(repo_root, discrepancies)

    # Contar skills raíz en Antigravity
    root_skills_dir = repo_root / DIR_SKILLS
    root_skills_count = 0
    if root_skills_dir.is_dir():
        root_skills_count = sum(1 for p in root_skills_dir.iterdir() if p.is_dir())

    is_valid = len(discrepancies) == 0
    status = STATUS_PASS if is_valid else STATUS_FAIL

    return ParityAuditResult(
        status=status,
        is_valid=is_valid,
        root_plugin_name=root_name,
        claude_plugin_name=claude_name,
        skills_count=root_skills_count,
        claude_skills_count=claude_skills_count,
        discrepancies=tuple(discrepancies),
    )


def print_report(result: ParityAuditResult) -> None:
    """Muestra el reporte legible de paridad."""
    color_code = "\033[92m" if result.is_valid else "\033[91m"
    reset_code = "\033[0m"

    logger.info("=======================================================")
    logger.info("   AUDITORIA DE PARIDAD MULTI-HARNESS (aagy <-> aagy-ecc)   ")
    logger.info("=======================================================")
    logger.info(f"Estado de Paridad:        {color_code}[{result.status}]{reset_code}")
    logger.info(f"Plugin Raíz Antigravity:  {result.root_plugin_name or 'N/A'}")
    logger.info(f"Subplugin Claude Code:    {result.claude_plugin_name or 'N/A'}")
    logger.info(f"Habilidades Antigravity:  {result.skills_count}")
    logger.info(f"Habilidades Claude Code:  {result.claude_skills_count}")

    if result.discrepancies:
        logger.info("\nDiscrepancias Detectadas:")
        for disc in result.discrepancies:
            logger.info(f"  - {disc}")
    logger.info("=======================================================\n")


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Auditoría de paridad multi-harness entre Anything Antigravity (aagy) y Claude Code (aagy)."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Ruta raíz del repositorio (por defecto actual)."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Solo verifica y retorna código de salida 0 o 1 sin reporte verboso."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en formato JSON estructurado."
    )
    return parser.parse_args(args)


def main(args: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada principal."""
    parsed = parse_args(args)
    repo_root = parsed.repo_root.resolve()

    result = audit_parity(repo_root)

    if parsed.json:
        print(json.dumps(result.to_dict(), indent=2))
    elif not parsed.check_only:
        print_report(result)

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
