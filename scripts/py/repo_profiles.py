#!/usr/bin/env python3
"""
Perfiles de stack por repositorio consumidor (repo_profiles.py).

El plugin aagy no conoce a sus consumidores: es cada repositorio el que declara
en `.governance/aagy-profiles.json` los perfiles de stack que necesita
(`{"profiles": ["java-spring", "go"]}`). Este script instala la unión de esos
perfiles (sin lo que ya aporta el perfil global `generic`) en `<repo>/.agents/`,
registra lo instalado en `.agents/.aagy-profiles.lock.json` y mantiene un bloque
gestionado en `.agents/.gitignore` para que las copias no se versionen.

Las listas de cada perfil se leen de `scripts/sh/aagy-sync.sh` (fuente única,
igual que /aagy-doctor). Solo toca los elementos que gestiona: las skills y
agentes propios del repositorio nunca se modifican.

Uso:
  python scripts/py/repo_profiles.py install --repo C:\\Ruta\\A\\MiRepo
  python scripts/py/repo_profiles.py status  --repo C:\\Ruta\\A\\MiRepo
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Set, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from aagy_doctor import expected_catalog  # noqa: E402

PROFILES_FILE = ".governance/aagy-profiles.json"
AGENTS_DIR = ".agents"
LOCK_FILE = ".aagy-profiles.lock.json"
GITIGNORE_FILE = ".gitignore"
GLOBAL_PROFILE = "generic"
FORBIDDEN_PROFILES = frozenset({GLOBAL_PROFILE, "all", "status"})
KEY_PROFILES = "profiles"
KEY_SKILLS = "skills"
KEY_AGENTS = "agents"
BLOCK_BEGIN = "# BEGIN aagy-profiles (gestionado por repo_profiles.py; no editar)"
BLOCK_END = "# END aagy-profiles"
DEFAULT_AAGY_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Selection:
    profiles: Tuple[str, ...]
    skills: Tuple[str, ...]
    agents: Tuple[str, ...]


def read_profiles(repo: Path) -> Tuple[str, ...]:
    """Lee y valida la lista de perfiles declarada por el repositorio consumidor."""
    cfg = repo / PROFILES_FILE
    if not cfg.is_file():
        raise ValueError(f"No existe '{cfg}': el repositorio debe declarar sus perfiles en {PROFILES_FILE}.")
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido en '{cfg}': {exc}") from exc
    profiles = data.get(KEY_PROFILES) if isinstance(data, dict) else None
    if not isinstance(profiles, list) or not all(isinstance(p, str) and p for p in profiles):
        raise ValueError(f"'{cfg}' debe contener {{\"{KEY_PROFILES}\": [\"perfil\", ...]}}.")
    bad = sorted(set(profiles) & FORBIDDEN_PROFILES)
    if bad:
        raise ValueError(f"Perfiles no permitidos en un repositorio: {', '.join(bad)} ('generic' ya es global).")
    return tuple(dict.fromkeys(profiles))


def resolve_selection(aagy_root: Path, profiles: Sequence[str]) -> Selection:
    """Unión de skills/agentes de los perfiles, menos lo que ya instala el perfil global."""
    base = expected_catalog(aagy_root, GLOBAL_PROFILE) or ((), ())
    skills: Dict[str, None] = {}
    agents: Dict[str, None] = {}
    for profile in profiles:
        catalog = expected_catalog(aagy_root, profile)
        if catalog is None:
            raise ValueError(f"Perfil desconocido: '{profile}' (ver scripts/sh/aagy-sync.sh).")
        skills.update(dict.fromkeys(s for s in catalog[0] if s not in base[0]))
        agents.update(dict.fromkeys(a for a in catalog[1] if a not in base[1]))
    return Selection(tuple(profiles), tuple(skills), tuple(agents))


def _read_lock(dest: Path) -> Dict[str, List[str]]:
    lock = dest / LOCK_FILE
    if not lock.is_file():
        return {KEY_SKILLS: [], KEY_AGENTS: []}
    data = json.loads(lock.read_text(encoding="utf-8"))
    return {KEY_SKILLS: list(data.get(KEY_SKILLS, [])), KEY_AGENTS: list(data.get(KEY_AGENTS, []))}


def _remove(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _install_items(src_dir: Path, dst_dir: Path, names: Sequence[str], managed: Set[str], warnings: List[str]) -> List[str]:
    installed: List[str] = []
    dst_dir.mkdir(parents=True, exist_ok=True)
    for name in names:
        src, dst = src_dir / name, dst_dir / name
        if dst.exists() and name not in managed:
            warnings.append(f"Se omite '{dst}': ya existe y es propio del repositorio.")
            continue
        _remove(dst)
        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
        installed.append(name)
    return installed


def _write_gitignore_block(dest: Path, skills: Sequence[str], agents: Sequence[str]) -> None:
    gitignore = dest / GITIGNORE_FILE
    text = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    if BLOCK_BEGIN in text and BLOCK_END in text:
        head, rest = text.split(BLOCK_BEGIN, 1)
        tail = rest.split(BLOCK_END, 1)[1]
        text = head.rstrip("\n") + ("\n" if head.strip() else "") + tail.lstrip("\n")
    lines = [BLOCK_BEGIN, f"/{LOCK_FILE}"]
    lines += [f"/{KEY_SKILLS}/{s}/" for s in skills] + [f"/{KEY_AGENTS}/{a}" for a in agents]
    lines.append(BLOCK_END)
    body = text.rstrip("\n")
    gitignore.write_text((body + "\n\n" if body else "") + "\n".join(lines) + "\n", encoding="utf-8")


def install(repo: Path, aagy_root: Path = DEFAULT_AAGY_ROOT) -> Tuple[Selection, List[str]]:
    """Instala/actualiza los perfiles del repositorio de forma idempotente."""
    selection = resolve_selection(aagy_root, read_profiles(repo))
    dest = repo / AGENTS_DIR
    previous = _read_lock(dest)
    for name in set(previous[KEY_SKILLS]) - set(selection.skills):
        _remove(dest / KEY_SKILLS / name)
    for name in set(previous[KEY_AGENTS]) - set(selection.agents):
        _remove(dest / KEY_AGENTS / name)
    warnings: List[str] = []
    skills = _install_items(aagy_root / KEY_SKILLS, dest / KEY_SKILLS, selection.skills, set(previous[KEY_SKILLS]), warnings)
    agents = _install_items(aagy_root / KEY_AGENTS, dest / KEY_AGENTS, selection.agents, set(previous[KEY_AGENTS]), warnings)
    lock = {KEY_PROFILES: list(selection.profiles), KEY_SKILLS: skills, KEY_AGENTS: agents}
    (dest / LOCK_FILE).write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")
    _write_gitignore_block(dest, skills, agents)
    return Selection(selection.profiles, tuple(skills), tuple(agents)), warnings


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Instala en <repo>/.agents/ los perfiles de stack que declara el repo.")
    parser.add_argument("action", choices=("install", "status"))
    parser.add_argument("--repo", type=Path, required=True, help="Raíz del repositorio consumidor.")
    parser.add_argument("--aagy-root", type=Path, default=DEFAULT_AAGY_ROOT, help="Raíz del repo aagy de origen.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    repo = args.repo.resolve()
    try:
        if args.action == "status":
            lock = _read_lock(repo / AGENTS_DIR)
            print(f"Perfiles declarados: {', '.join(read_profiles(repo))}")
            print(f"Skills gestionadas ({len(lock[KEY_SKILLS])}): {', '.join(lock[KEY_SKILLS])}")
            print(f"Agentes gestionados ({len(lock[KEY_AGENTS])}): {', '.join(lock[KEY_AGENTS])}")
            return 0
        selection, warnings = install(repo, args.aagy_root.resolve())
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    for warning in warnings:
        print(f"[!] {warning}")
    print(f"[OK] Perfiles {', '.join(selection.profiles)}: {len(selection.skills)} skills y "
          f"{len(selection.agents)} agentes en {repo / AGENTS_DIR}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
