#!/usr/bin/env python3
"""
Sincronizador de la distribución hermana aagy-ecc (Claude Code) (sync_aagy_ecc.py).

Claude Code solo carga los archivos que viven dentro de la carpeta del plugin,
así que aagy-ecc/ necesita su propia copia de las skills, subagentes, reglas y
motores Python que usan sus hooks. Este script la genera desde la raíz del
repositorio (fuente única de verdad) y, con --check, detecta deriva sin escribir.

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
import shutil
import sys
from typing import Dict, List, Optional, Sequence, Tuple

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("sync-aagy-ecc")

DIR_AAGY_ECC = "aagy-ecc"
STATUS_IN_SYNC = "IN_SYNC"
STATUS_DRIFT = "DRIFT"
STATUS_SYNCED = "SYNCED"

# (origen relativo a la raíz, destino relativo a aagy-ecc/)
MIRRORED_DIRS: Tuple[Tuple[str, str], ...] = (
    ("skills", "skills"),
    ("agents", "agents"),
)

# Motores Python que necesitan los hooks y comandos de aagy-ecc (con sus dependencias).
MIRRORED_PY_MODULES: Tuple[str, ...] = (
    "self_improve.py",
    "instinct_manager.py",
    "security_audit.py",
    "workspace_audit.py",
    "docs_map.py",
)

MIRRORED_FILES: Tuple[Tuple[str, str], ...] = tuple(
    (f"scripts/py/{name}", f"scripts/py/{name}") for name in MIRRORED_PY_MODULES
) + (
    ("rules/AGENTS.md", "rules/AGENTS.md"),
)

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


def build_mapping(repo_root: Path) -> Tuple[Dict[str, Path], List[str]]:
    """
    Devuelve el mapa {ruta destino relativa a aagy-ecc: archivo origen} y la lista
    de directorios espejo (relativos a aagy-ecc) gestionados por completo.
    """
    mapping: Dict[str, Path] = {}
    managed_dirs: List[str] = []
    for src_rel, dst_rel in MIRRORED_DIRS:
        managed_dirs.append(dst_rel)
        for rel, src in _list_files(repo_root / src_rel).items():
            mapping[f"{dst_rel}/{rel}"] = src
    for src_rel, dst_rel in MIRRORED_FILES:
        src = repo_root / src_rel
        if src.is_file():
            mapping[dst_rel] = src
    return mapping, managed_dirs


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
        elif _normalized_bytes(dst) != _normalized_bytes(src):
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
        shutil.copyfile(mapping[dst_rel], dst)
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
