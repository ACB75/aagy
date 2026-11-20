#!/usr/bin/env python3
"""
scripts/py/skill_promotion.py - Gestor de Promoción On-Demand de Skills Tier 2 a Tier 1

Permite promover temporalmente una skill especializada de Tier 2 (skills/<name>)
hacia el plugin activo de Antigravity (~/.gemini/config/plugins/ecc-agy/skills/),
validando los límites de frontmatter (<= 140c) y registrándola en .active_promotions.json
para su posterior retirada limpia (disable-skill).
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import shutil
import sys
from typing import Optional, Sequence, Tuple

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger: logging.Logger = logging.getLogger("skill-promotion")

REGISTRY_FILE = ".active_promotions.json"
SKILL_DOC = "SKILL.md"
MAX_SKILL_DESC_CHARS = 140
PLUGIN_NAME_ECC_AGY = "aagy"


def _default_repo_skills_dir() -> Path:
    repo_root = Path(__file__).resolve().parent.parent.parent
    return repo_root / "skills"


def _default_plugin_dir() -> Path:
    return Path.home() / ".gemini" / "config" / "plugins" / PLUGIN_NAME_ECC_AGY


def _load_registry(plugin_dir: Path) -> dict[str, str]:
    reg_file = plugin_dir / REGISTRY_FILE
    if not reg_file.is_file():
        return {}
    try:
        data = json.loads(reg_file.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_registry(plugin_dir: Path, registry: dict[str, str]) -> None:
    reg_file = plugin_dir / REGISTRY_FILE
    reg_file.write_text(json.dumps(registry, indent=2), encoding="utf-8")


def _read_description_length(skill_md: Path) -> Tuple[int, Optional[str]]:
    try:
        content = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0, None

    if not content.startswith("---"):
        return 0, None

    parts = content.split("---", 2)
    if len(parts) < 3:
        return 0, None

    frontmatter = parts[1]
    for line in frontmatter.splitlines():
        line_clean = line.strip()
        if line_clean.startswith("description:"):
            desc = line_clean.split(":", 1)[1].strip().strip('"').strip("'")
            return len(desc), desc
    return 0, None


def promote_skill(
    name: str,
    repo_skills_dir: Optional[Path] = None,
    plugin_dir: Optional[Path] = None,
) -> Tuple[int, str]:
    """Promueve una skill de Tier 2 a la carpeta de skills activas del plugin."""
    src_dir = (repo_skills_dir or _default_repo_skills_dir()) / name
    dst_base = plugin_dir or _default_plugin_dir()
    dst_dir = dst_base / "skills" / name

    registry = _load_registry(dst_base)

    # Si ya existe en destino pero no está en registry, es una skill Core permanente
    if dst_dir.is_dir() and name not in registry:
        return 1, f"La skill '{name}' ya es una skill Core activa en Tier 1."

    if not src_dir.is_dir() or not (src_dir / SKILL_DOC).is_file():
        return 1, f"Skill '{name}' no encontrada en el repositorio origen ({src_dir})."

    desc_len, _ = _read_description_length(src_dir / SKILL_DOC)
    if desc_len > MAX_SKILL_DESC_CHARS:
        return 1, f"Frontmatter de skill '{name}' excede {MAX_SKILL_DESC_CHARS} caracteres ({desc_len}c)."

    try:
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        shutil.copytree(src_dir, dst_dir)
        registry[name] = datetime.now(timezone.utc).isoformat()
        _save_registry(dst_base, registry)
    except OSError as err:
        return 1, f"Error copiando skill '{name}' al plugin: {err}"

    return 0, f"Skill '{name}' promovida exitosamente a Tier 1 en {dst_dir}."


def demote_skill(
    name: str,
    plugin_dir: Optional[Path] = None,
) -> Tuple[int, str]:
    """Retira una skill promovida previamente del plugin activo."""
    dst_base = plugin_dir or _default_plugin_dir()
    dst_dir = dst_base / "skills" / name
    registry = _load_registry(dst_base)

    if name not in registry:
        return 1, f"La skill '{name}' no es una skill promovida o es una skill Core protegida."

    try:
        if dst_dir.exists():
            shutil.rmtree(dst_dir)
        del registry[name]
        _save_registry(dst_base, registry)
    except OSError as err:
        return 1, f"Error retirando skill '{name}' del plugin: {err}"

    return 0, f"Skill '{name}' retirada exitosamente del plugin activo."


def list_promotions(plugin_dir: Optional[Path] = None) -> list[str]:
    """Retorna las skills actualmente promovidas de forma temporal."""
    dst_base = plugin_dir or _default_plugin_dir()
    registry = _load_registry(dst_base)
    return sorted(registry.keys())


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gestor de promoción y despromoción on-demand de skills Tier 2 a Tier 1."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--promote", "-p", type=str, help="Nombre de la skill a promover.")
    group.add_argument("--demote", "-d", type=str, help="Nombre de la skill promovida a retirar.")
    group.add_argument("--list", "-l", action="store_true", help="Listar skills promovidas.")

    parser.add_argument("--repo-skills", type=Path, help="Ruta a skills/ del repositorio.")
    parser.add_argument("--plugin-dir", type=Path, help="Ruta a la carpeta del plugin.")
    parser.add_argument("--json", action="store_true", help="Salida en JSON.")

    args = parser.parse_args(argv)

    if args.list:
        promotions = list_promotions(plugin_dir=args.plugin_dir)
        if args.json:
            print(json.dumps({"promotions": promotions}))
        else:
            logger.info("Skills promovidas activas (%d):", len(promotions))
            for item in promotions:
                logger.info("  • %s", item)
        return 0

    if args.promote:
        code, msg = promote_skill(args.promote, repo_skills_dir=args.repo_skills, plugin_dir=args.plugin_dir)
        if code == 0:
            logger.info("[OK] %s", msg)
        else:
            logger.error("[FAIL] %s", msg)
        return code

    if args.demote:
        code, msg = demote_skill(args.demote, plugin_dir=args.plugin_dir)
        if code == 0:
            logger.info("[OK] %s", msg)
        else:
            logger.error("[FAIL] %s", msg)
        return code

    return 0


if __name__ == "__main__":
    sys.exit(main())
