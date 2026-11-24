#!/usr/bin/env python3
"""
Sincronizador de la distribución hermana aagy-ecc (Claude Code) (sync_aagy_ecc.py).

Claude Code solo carga los archivos que viven dentro de la carpeta del plugin,
así que aagy-ecc/ necesita su propia copia de las skills, subagentes, reglas y
motores Python que usan sus hooks. Este script la genera desde la raíz del
repositorio (fuente única de verdad) y, con --check, detecta deriva sin escribir.

Para no cargar el catálogo completo en cada sesión, el reparto sigue los perfiles
de stack de scripts/sh/aagy-sync.sh (ADR-0004): el plugin núcleo aagy-ecc lleva el
perfil global `generic`; cada perfil de stack se publica como paquete opcional
aagy-ecc/packs/<perfil>/ (plugin `aagy-ecc-<perfil>`) y lo que no está en ningún
perfil va al paquete `extras`. Cada usuario o repo habilita solo los paquetes que
necesita. Sin aagy-sync.sh todo va al núcleo.

Uso:
  python scripts/py/sync_aagy_ecc.py            # regenera los espejos
  python scripts/py/sync_aagy_ecc.py --check    # solo verifica (exit 0 / 1)
  python scripts/py/sync_aagy_ecc.py --json     # informe estructurado
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import re
import shutil
import sys
from typing import Dict, List, Optional, Sequence, Set, Tuple, Union

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("sync-aagy-ecc")

DIR_AAGY_ECC = "aagy-ecc"
STATUS_IN_SYNC = "IN_SYNC"
STATUS_DRIFT = "DRIFT"
STATUS_SYNCED = "SYNCED"

# Motores Python que necesitan los hooks y comandos de aagy-ecc (con sus dependencias).
MIRRORED_PY_MODULES: Tuple[str, ...] = (
    "self_improve.py",
    "aagy_config.py",
    "local_model.py",
    "local_model_mcp.py",
    "local_model_ops.py",
    "local_private_guard.py",
    "instinct_manager.py",
    "security_audit.py",
    "workspace_audit.py",
    "docs_map.py",
    "doctor_core.py",
    "install_manifest.py",
    "backlog.py",
    "archive_todo.py",
    "sync_ideas_todo.py",
    "new_lifecycle_task.py",
    "validate_branch.py",
    "agent_worktree.py",
    "agent_worktree_base.py",
    "agent_worktree_guard.py",
    "agent_worktree_provision.py",
)

# Entradas propias de Antigravity que no deben llegar a Claude Code (relativas al directorio espejo).
# skills/aagy-doctor y skills/aagy-local son de Antigravity; Claude Code usa /aagy-ecc-doctor y /aagy-local.
MIRROR_EXCLUDED: Dict[str, Tuple[str, ...]] = {
    "skills": ("aagy-doctor", "aagy-local"),
}

MIRRORED_FILES: Tuple[Tuple[str, str], ...] = tuple(
    (f"scripts/py/{name}", f"scripts/py/{name}") for name in MIRRORED_PY_MODULES
) + (
    ("rules/AGENTS.md", "rules/AGENTS.md"),
    ("CLAUDE.md", "project-template/CLAUDE.md"),
)

CORE_PROFILE = "generic"
PACK_EXTRAS = "extras"
DIR_PACKS = "packs"
DIR_SKILLS = "skills"
DIR_AGENTS = "agents"
PACK_PREFIX = "aagy-ecc-"
FILE_PLUGIN_MANIFEST = ".claude-plugin/plugin.json"
FILE_MARKETPLACE = ".claude-plugin/marketplace.json"
PROFILES_SCRIPT = Path("scripts", "sh", "aagy-sync.sh")
_PROFILE_BLOCK = re.compile(r"^\s*([a-z0-9-]+)\)\s*\n\s*SKILLS=\(([^)]*)\)\s*\n\s*AGENTS=\(([^)]*)\)", re.MULTILINE)
MANIFEST_SHARED_KEYS = ("author", "homepage", "repository", "license")

Source = Union[Path, bytes]
Catalog = Tuple[Set[str], Set[str]]

IGNORED_NAMES = frozenset({"__pycache__", ".pytest_cache", ".DS_Store", "Thumbs.db"})
IGNORED_SUFFIXES = (".pyc", ".pyo")


@dataclass(frozen=True)
class SyncReport:
    """Resultado de comparar (o sincronizar) los espejos de aagy-ecc."""
    status: str
    missing: Tuple[str, ...]
    changed: Tuple[str, ...]
    extra: Tuple[str, ...]

    @property
    def in_sync(self) -> bool:
        return not (self.missing or self.changed or self.extra)

    def to_dict(self) -> Dict[str, object]:
        data = asdict(self)
        data["in_sync"] = self.in_sync
        return data


def _is_ignored(path: Path) -> bool:
    return any(part in IGNORED_NAMES for part in path.parts) or path.suffix in IGNORED_SUFFIXES


def _list_files(base: Path) -> Dict[str, Path]:
    if not base.is_dir():
        return {}
    files: Dict[str, Path] = {}
    for path in sorted(base.rglob("*")):
        rel = path.relative_to(base)
        if path.is_file() and not _is_ignored(rel):
            files[rel.as_posix()] = path
    return files


def _normalized_bytes(path: Path) -> bytes:
    """Contenido con CRLF normalizado a LF, para no marcar deriva por finales de línea de Windows."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def read_profiles(repo_root: Path) -> Dict[str, Catalog]:
    """Perfiles {nombre: (skills, agentes .md)} en el orden de aagy-sync.sh; {} si no existe."""
    script = repo_root / PROFILES_SCRIPT
    if not script.is_file():
        return {}
    text = script.read_text(encoding="utf-8")
    return {m.group(1): (set(m.group(2).split()), set(m.group(3).split())) for m in _PROFILE_BLOCK.finditer(text)}


def _available(repo_root: Path) -> Catalog:
    excluded = set(MIRROR_EXCLUDED.get(DIR_SKILLS, ()))
    skills_dir, agents_dir = repo_root / DIR_SKILLS, repo_root / DIR_AGENTS
    skills = {p.name for p in skills_dir.iterdir() if p.is_dir() and p.name not in excluded} if skills_dir.is_dir() else set()
    agents = {p.name for p in agents_dir.glob("*.md")} if agents_dir.is_dir() else set()
    return skills, agents


def plan_packs(repo_root: Path) -> Dict[str, Catalog]:
    """
    Reparto {paquete: (skills, agentes)}; la clave "" es el núcleo aagy-ecc.
    Un paquete de stack repite lo que comparte con otro stack (cada uno es autónomo),
    pero nunca lo que ya trae el núcleo. Lo que no está en ningún perfil va a extras.
    """
    skills, agents = _available(repo_root)
    profiles = read_profiles(repo_root)
    if CORE_PROFILE not in profiles:
        return {"": (skills, agents)}
    core_skills = profiles[CORE_PROFILE][0] & skills
    core_agents = profiles[CORE_PROFILE][1] & agents
    packs: Dict[str, Catalog] = {"": (core_skills, core_agents)}
    used_skills, used_agents = set(core_skills), set(core_agents)
    for name, (p_skills, p_agents) in profiles.items():
        if name == CORE_PROFILE:
            continue
        pack = ((p_skills & skills) - core_skills, (p_agents & agents) - core_agents)
        if pack[0] or pack[1]:
            packs[name] = pack
            used_skills |= pack[0]
            used_agents |= pack[1]
    extras = (skills - used_skills, agents - used_agents)
    if extras[0] or extras[1]:
        packs[PACK_EXTRAS] = extras
    return packs


def pack_root(pack: str) -> str:
    """Ruta del paquete relativa a aagy-ecc/ ("" para el núcleo)."""
    return f"{DIR_PACKS}/{pack}/" if pack else ""


def _load_json(path: Path) -> Dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _json_bytes(data: object) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def pack_manifest(core: Dict[str, object], pack: str) -> Dict[str, object]:
    """plugin.json de un paquete: nombre propio, misma versión y autoría que el núcleo."""
    manifest: Dict[str, object] = {
        "name": f"{PACK_PREFIX}{pack}",
        "version": core.get("version", "0.0.0"),
        "description": f"Paquete opcional de aagy-ecc con las skills y subagentes del perfil '{pack}'. Requiere aagy-ecc.",
    }
    manifest.update({k: core[k] for k in MANIFEST_SHARED_KEYS if k in core})
    return manifest


def marketplace_with_packs(market: Dict[str, object], core: Dict[str, object], packs: Sequence[str]) -> Dict[str, object]:
    """Conserva las entradas escritas a mano (núcleo) y regenera las de los paquetes."""
    entries = market.get("plugins", [])
    plugins = [p for p in entries if isinstance(p, dict) and not str(p.get("name", "")).startswith(PACK_PREFIX)]
    for pack in packs:
        entry = pack_manifest(core, pack)
        entry.update({"source": f"./{DIR_PACKS}/{pack}", "category": "workflow", "strict": False})
        plugins.append(entry)
    return {**market, "plugins": plugins}


def build_mapping(repo_root: Path) -> Tuple[Dict[str, Source], List[str]]:
    """
    Devuelve el mapa {ruta destino relativa a aagy-ecc: archivo origen o contenido generado}
    y la lista de directorios espejo (relativos a aagy-ecc) gestionados por completo.
    """
    mapping: Dict[str, Source] = {}
    managed_dirs: List[str] = []
    packs = plan_packs(repo_root)
    for pack, catalog in packs.items():
        root = pack_root(pack)
        for kind, names in zip((DIR_SKILLS, DIR_AGENTS), catalog):
            managed_dirs.append(f"{root}{kind}")
            for rel, src in _list_files(repo_root / kind).items():
                if rel.split("/", 1)[0] in names:
                    mapping[f"{root}{kind}/{rel}"] = src
    for src_rel, dst_rel in MIRRORED_FILES:
        src = repo_root / src_rel
        if src.is_file():
            mapping[dst_rel] = src
    _add_pack_manifests(repo_root, [p for p in packs if p], mapping)
    return mapping, managed_dirs


def _add_pack_manifests(repo_root: Path, stacks: Sequence[str], mapping: Dict[str, Source]) -> None:
    if not stacks:
        return
    ecc_root = repo_root / DIR_AAGY_ECC
    core = _load_json(ecc_root / FILE_PLUGIN_MANIFEST)
    for pack in stacks:
        mapping[f"{pack_root(pack)}{FILE_PLUGIN_MANIFEST}"] = _json_bytes(pack_manifest(core, pack))
    market = _load_json(ecc_root / FILE_MARKETPLACE)
    if market:
        mapping[FILE_MARKETPLACE] = _json_bytes(marketplace_with_packs(market, core, stacks))


def _source_bytes(src: Source) -> bytes:
    return src if isinstance(src, bytes) else _normalized_bytes(src)


def compare(repo_root: Path) -> SyncReport:
    """Compara los espejos de aagy-ecc con la raíz sin modificar nada."""
    ecc_root = repo_root / DIR_AAGY_ECC
    mapping, managed_dirs = build_mapping(repo_root)
    missing: List[str] = []
    changed: List[str] = []
    for dst_rel, src in sorted(mapping.items()):
        dst = ecc_root / dst_rel
        if not dst.is_file():
            missing.append(dst_rel)
        elif _normalized_bytes(dst) != _source_bytes(src):
            changed.append(dst_rel)
    extra: List[str] = []
    for managed in managed_dirs:
        for rel in _list_files(ecc_root / managed):
            dst_rel = f"{managed}/{rel}"
            if dst_rel not in mapping:
                extra.append(dst_rel)
    report = SyncReport(STATUS_IN_SYNC, tuple(missing), tuple(changed), tuple(sorted(extra)))
    if report.in_sync:
        return report
    return SyncReport(STATUS_DRIFT, report.missing, report.changed, report.extra)


def _prune_empty_dirs(base: Path) -> None:
    if not base.is_dir():
        return
    for path in sorted(base.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and not any(path.iterdir()):
            path.rmdir()


def sync(repo_root: Path) -> SyncReport:
    """Regenera los espejos de aagy-ecc y devuelve qué se ha corregido."""
    before = compare(repo_root)
    ecc_root = repo_root / DIR_AAGY_ECC
    mapping, managed_dirs = build_mapping(repo_root)
    for dst_rel in before.missing + before.changed:
        dst = ecc_root / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        src = mapping[dst_rel]
        if isinstance(src, bytes):
            dst.write_bytes(src)
        else:
            shutil.copyfile(src, dst)
    for dst_rel in before.extra:
        (ecc_root / dst_rel).unlink()
    for managed in managed_dirs:
        _prune_empty_dirs(ecc_root / managed)
    status = STATUS_IN_SYNC if before.in_sync else STATUS_SYNCED
    return SyncReport(status, before.missing, before.changed, before.extra)


def print_report(report: SyncReport, checking: bool) -> None:
    verb = "Faltan" if checking else "Copiados"
    logger.info("Estado aagy-ecc: [%s]", report.status)
    for label, items in ((verb, report.missing), ("Distintos" if checking else "Actualizados", report.changed),
                         ("Sobrantes" if checking else "Eliminados", report.extra)):
        if items:
            logger.info("  %s: %d", label, len(items))
            for item in items[:20]:
                logger.info("    - %s", item)
            if len(items) > 20:
                logger.info("    ... y %d más", len(items) - 20)


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sincroniza skills, agentes, reglas y motores Python en aagy-ecc/.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parent.parent.parent,
                        help="Raíz del repositorio aagy (por defecto, la de este script).")
    parser.add_argument("--check", action="store_true", help="Solo verifica la deriva (exit 1 si la hay).")
    parser.add_argument("--json", action="store_true", help="Salida JSON estructurada.")
    return parser.parse_args(args)


def main(args: Optional[Sequence[str]] = None) -> int:
    parsed = parse_args(args)
    repo_root = parsed.repo_root.resolve()
    if not (repo_root / DIR_AAGY_ECC).is_dir():
        logger.error("No se encontró '%s/' en %s", DIR_AAGY_ECC, repo_root)
        return 1
    report = compare(repo_root) if parsed.check else sync(repo_root)
    if parsed.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print_report(report, parsed.check)
    return 0 if (report.in_sync or not parsed.check) else 1


if __name__ == "__main__":
    sys.exit(main())
