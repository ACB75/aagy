#!/usr/bin/env python3
"""
Referencias a proyectos consumidores (consumer_refs.py, RF-14).

El plugin no nombra a ningún proyecto, máquina ni usuario que lo use. Este check
falla si reaparece una referencia. La lista de términos no vive en el código:
se declara en ``consumer_refs`` de la capa de proyecto (``.governance/aagy.json``)
o de la capa de entorno (``<AAGY_ENV_DIR>/aagy/env.json``), y se unen las dos.
Sin términos declarados, el check se salta y lo dice.

Se buscan como texto literal, sin distinguir mayúsculas, en los ficheros
versionados del repo. Se excluye solo el fichero que declara la lista.

Uso::

    python consumer_refs.py [--repo <raíz>] [--json]

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import subprocess
import sys
from typing import Iterable, Iterator, List, Optional, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))

import aagy_config  # noqa: E402

ENCODING = "utf-8"
KEY = "consumer_refs"
SKIP_DIRS = frozenset({".git", "node_modules", ".pytest_cache", "__pycache__", ".venv"})
MAX_BYTES = 2_000_000


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    term: str


def declared_terms(repo_root: Path) -> Tuple[str, ...]:
    """Unión de ``consumer_refs`` de las capas de proyecto y de entorno, sin vacíos ni duplicados."""
    cfg = aagy_config.load(repo_root)
    terms: List[str] = []
    for layer in (cfg.project, cfg.env):
        value = layer.data.get(KEY)
        if isinstance(value, list):
            terms.extend(str(t).strip() for t in value if str(t).strip())
    return tuple(dict.fromkeys(terms))


def _git_files(repo_root: Path) -> Optional[List[Path]]:
    try:
        out = subprocess.run(["git", "ls-files", "-z"], cwd=repo_root, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [repo_root / p for p in out.stdout.decode(ENCODING, "replace").split("\0") if p]


def _walk(repo_root: Path) -> Iterator[Path]:
    for path in repo_root.rglob("*"):
        if path.is_file() and not SKIP_DIRS.intersection(path.relative_to(repo_root).parts):
            yield path


def candidate_files(repo_root: Path) -> Iterable[Path]:
    tracked = _git_files(repo_root)
    return tracked if tracked is not None else _walk(repo_root)


def scan(repo_root: Path, terms: Sequence[str], exclude: Sequence[Path] = ()) -> List[Hit]:
    """Apariciones de ``terms`` en los ficheros de texto del repo."""
    lowered = [(t, t.lower()) for t in terms]
    skipped = {p.resolve() for p in exclude}
    hits: List[Hit] = []
    for path in candidate_files(repo_root):
        if path.resolve() in skipped or not path.is_file() or path.stat().st_size > MAX_BYTES:
            continue
        data = path.read_bytes()
        if b"\0" in data[:4096]:
            continue
        rel = path.relative_to(repo_root).as_posix()
        for number, line in enumerate(data.decode(ENCODING, "replace").lower().splitlines(), 1):
            hits.extend(Hit(rel, number, term) for term, low in lowered if low in line)
    return hits


def audit(repo_root: Path) -> Tuple[Tuple[str, ...], List[Hit]]:
    """(términos, apariciones). Sin términos devuelve una lista vacía de apariciones."""
    terms = declared_terms(repo_root)
    if not terms:
        return terms, []
    declaring = aagy_config.find_project_file(repo_root)
    return terms, scan(repo_root, terms, [declaring] if declaring else [])


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Falla si el repo nombra a un proyecto consumidor.")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    terms, hits = audit(args.repo.resolve())
    if args.json:
        print(json.dumps([h.__dict__ for h in hits], ensure_ascii=False, indent=2))
    elif not terms:
        print(f"[consumer-refs] SKIP: sin '{KEY}' en {aagy_config.PROJECT_FILE.as_posix()} ni en la capa de entorno.")
    else:
        for hit in hits[:50]:
            print(f"[FAIL] {hit.path}:{hit.line}: '{hit.term}'")
        print(f"[consumer-refs] {len(terms)} términos, {len(hits)} apariciones")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
