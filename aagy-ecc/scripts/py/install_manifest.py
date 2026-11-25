#!/usr/bin/env python3
"""
Manifiesto de instalación de aagy / aagy-ecc (install_manifest.py).

Los instaladores (install.ps1, install.sh, aagy-sync.ps1, aagy-sync.sh)
escriben `.aagy-install.json` en el destino para que los doctors sepan qué
se instaló: harness, perfil, versión, commit, fecha, repo de origen y la lista
de ficheros instalados por perfil, con su hash SHA-256 (RF-16).

``apply`` es la sincronización: el instalador prepara una copia nueva en un
directorio temporal (``--stage``) y este motor la lleva al destino.

- Copia solo los ficheros de la copia nueva. Nunca toca lo que no está en la
  lista (``.data/``, ficheros propios del proyecto).
- Si un fichero de la lista se editó a mano (su hash no es el del manifiesto),
  avisa y no lo pisa, salvo con ``--force``.
- Con ``--hard`` borra los ficheros que el perfil ya no trae (huérfanos); sin
  ``--hard`` los conserva y los anota en ``orphans`` para que el doctor avise.
- ``--dry-run`` muestra qué cambiaría sin tocar nada.

Escribir el manifiesto nunca debe abortar una instalación: ante cualquier
error se avisa y se sale con 0.

Uso:
  python scripts/py/install_manifest.py write --dest <dir> --harness agy --profile generic
  python scripts/py/install_manifest.py apply --stage <tmp> --dest <dir> --profile generic [--hard] [--force] [--dry-run]
  python scripts/py/install_manifest.py show --dest <dir>
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

MANIFEST_FILE = ".aagy-install.json"
MANIFEST_SCHEMA = 2
HARNESS_AGY = "agy"
HARNESS_CLAUDE = "claude"
HARNESSES = (HARNESS_AGY, HARNESS_CLAUDE)
ENCODING = "utf-8"
GIT_TIMEOUT_S = 3
# En aagy-ecc los packs son plugins aparte: no forman parte de la copia instalada del núcleo.
CLAUDE_EXCLUDE_TOP = ("packs",)
# Nunca forman parte de lo instalado: datos de ejecución y cachés.
SKIP_PARTS = frozenset({".data", "__pycache__", ".pytest_cache", ".git", ".DS_Store", "Thumbs.db"})
HASH_CHUNK = 1 << 16

FileHashes = Dict[str, str]


@dataclass(frozen=True)
class InstallManifest:
    """Contenido de .aagy-install.json."""
    harness: str
    profile: str
    version: str
    commit: str
    installed_at: str
    source_repo: str
    schema: int = MANIFEST_SCHEMA
    # Perfil -> {ruta relativa POSIX: sha256}. Un fichero común (reglas, scripts) sale en varios perfiles.
    files: Dict[str, FileHashes] = field(default_factory=dict)
    # Huérfanos conservados (sin --hard): {ruta: sha256 cuando se instaló}.
    orphans: FileHashes = field(default_factory=dict)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


def default_repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def read_version(repo_root: Path, harness: str) -> str:
    """Versión del plugin según el harness (plugin.json raíz o el de aagy-ecc)."""
    if harness == HARNESS_CLAUDE:
        manifest = repo_root / "aagy-ecc" / ".claude-plugin" / "plugin.json"
    else:
        manifest = repo_root / "plugin.json"
    try:
        data = json.loads(manifest.read_text(encoding=ENCODING))
    except (OSError, ValueError):
        return ""
    return str(data.get("version", "")) if isinstance(data, dict) else ""


def read_commit(repo_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT_S, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def build_manifest(repo_root: Path, harness: str, profile: str, now: Optional[datetime] = None,
                   files: Optional[Dict[str, FileHashes]] = None, orphans: Optional[FileHashes] = None) -> InstallManifest:
    stamp = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    return InstallManifest(
        harness=harness,
        profile=profile,
        version=read_version(repo_root, harness),
        commit=read_commit(repo_root),
        installed_at=stamp,
        source_repo=str(repo_root.resolve()),
        files=dict(files or {}),
        orphans=dict(orphans or {}),
    )


# --------------------------------------------------------------------------- #
# Lista de ficheros con hash y sincronización (RF-16)
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(HASH_CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_hashes(root: Path, exclude_top: Sequence[str] = ()) -> FileHashes:
    """{ruta relativa POSIX: sha256} de los ficheros de ``root`` (sin ``SKIP_PARTS`` ni el manifiesto)."""
    hashes: FileHashes = {}
    if not root.is_dir():
        return hashes
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if rel.parts[0] in exclude_top:
            continue
        if path.is_file() and not SKIP_PARTS.intersection(rel.parts) and rel.as_posix() != MANIFEST_FILE:
            hashes[rel.as_posix()] = sha256_file(path)
    return hashes


def all_files(manifest: Optional[InstallManifest]) -> FileHashes:
    """Unión de los ficheros de todos los perfiles instalados."""
    merged: FileHashes = {}
    for entries in (manifest.files.values() if manifest else ()):
        merged.update(entries)
    return merged


@dataclass
class SyncPlan:
    copy: List[str] = field(default_factory=list)
    unchanged: List[str] = field(default_factory=list)
    modified: List[str] = field(default_factory=list)
    delete: List[str] = field(default_factory=list)
    kept_orphans: List[str] = field(default_factory=list)


def _hand_edited(dest_file: Path, recorded: Optional[str]) -> bool:
    return recorded is not None and sha256_file(dest_file) != recorded


def plan_sync(stage: Path, dest: Path, profile: str, old: Optional[InstallManifest],
              hard: bool = False, force: bool = False) -> Tuple[SyncPlan, FileHashes]:
    """Plan de la sincronización y los hashes nuevos de ``profile``."""
    new = tree_hashes(stage)
    recorded = {**(old.orphans if old else {}), **all_files(old)}
    plan = SyncPlan()
    for rel, digest in new.items():
        target = dest / rel
        if not target.is_file():
            plan.copy.append(rel)
        elif sha256_file(target) == digest:
            plan.unchanged.append(rel)
        elif _hand_edited(target, recorded.get(rel)) and not force:
            plan.modified.append(rel)
        else:
            plan.copy.append(rel)
    others = {rel for name, entries in (old.files.items() if old else ()) if name != profile for rel in entries}
    previous = set(old.files.get(profile, {})) | set(old.orphans) if old else set()
    for rel in sorted(previous - set(new) - others):
        target = dest / rel
        if not target.is_file():
            continue
        if hard and (force or not _hand_edited(target, recorded.get(rel))):
            plan.delete.append(rel)
        else:
            plan.kept_orphans.append(rel)
    # Un fichero que no se pisa conserva su hash anterior: el doctor lo seguirá viendo como modificado.
    hashes = {rel: (recorded[rel] if rel in plan.modified else digest) for rel, digest in new.items()}
    return plan, hashes


def _remove_empty_parents(path: Path, stop: Path) -> None:
    parent = path.parent
    while parent != stop and parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()
        parent = parent.parent


def apply_plan(plan: SyncPlan, stage: Path, dest: Path) -> None:
    for rel in plan.copy:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage / rel, target)
    for rel in plan.delete:
        target = dest / rel
        target.unlink()
        _remove_empty_parents(target, dest)


def next_manifest(base: InstallManifest, old: Optional[InstallManifest], profile: str,
                  hashes: FileHashes, plan: SyncPlan) -> InstallManifest:
    files = {name: dict(entries) for name, entries in (old.files.items() if old else ())}
    files[profile] = hashes
    gone = set(plan.delete)
    for entries in files.values():
        for rel in gone & set(entries):
            del entries[rel]
    recorded = {**(old.orphans if old else {}), **all_files(old)}
    installed = {rel for entries in files.values() for rel in entries}
    orphans = {rel: recorded[rel] for rel in plan.kept_orphans if rel in recorded and rel not in installed}
    return InstallManifest(**{**base.to_dict(), "files": files, "orphans": orphans})


def drift(dest: Path, manifest: Optional[InstallManifest]) -> Tuple[List[str], List[str], List[str]]:
    """(modificados a mano, que faltan, huérfanos que siguen en disco) respecto al manifiesto."""
    modified: List[str] = []
    missing: List[str] = []
    for rel, digest in sorted(all_files(manifest).items()):
        target = dest / rel
        if not target.is_file():
            missing.append(rel)
        elif sha256_file(target) != digest:
            modified.append(rel)
    orphans = sorted(rel for rel in (manifest.orphans if manifest else {}) if (dest / rel).is_file())
    return modified, missing, orphans


def drift_problems(dest: Path, manifest: Optional[InstallManifest], fix_hint: str) -> List[str]:
    """Avisos del doctor (DOC-04) sobre ficheros del plugin editados a mano, borrados o huérfanos."""
    modified, missing, orphans = drift(dest, manifest)
    problems: List[str] = []
    for label, items in (("modificados a mano", modified), ("borrados", missing), ("huérfanos", orphans)):
        if items:
            shown = ", ".join(items[:3]) + (" ..." if len(items) > 3 else "")
            problems.append(f"{len(items)} ficheros del plugin {label}: {shown}. {fix_hint}")
    return problems


def print_plan(plan: SyncPlan, dry_run: bool) -> None:
    prefix = "[dry-run] " if dry_run else ""
    for rel in plan.copy:
        print(f"{prefix}[+] {rel}")
    for rel in plan.delete:
        print(f"{prefix}[-] {rel} (el plugin ya no lo trae)")
    for rel in plan.modified:
        print(f"{prefix}[!] {rel}: editado a mano, no se pisa (usa --force)")
    for rel in plan.kept_orphans:
        print(f"{prefix}[?] {rel}: huérfano conservado (usa --hard para borrarlo)")
    print(f"{prefix}[=] {len(plan.unchanged)} sin cambios, {len(plan.copy)} a copiar, "
          f"{len(plan.delete)} a borrar, {len(plan.modified)} protegidos, {len(plan.kept_orphans)} huérfanos.")


def write_manifest(dest: Path, manifest: InstallManifest) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / MANIFEST_FILE
    target.write_text(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding=ENCODING)
    return target


def _files_field(raw: object) -> Dict[str, FileHashes]:
    if not isinstance(raw, Mapping):
        return {}
    return {
        str(profile): {str(k): str(v) for k, v in entries.items()}
        for profile, entries in raw.items() if isinstance(entries, Mapping)
    }


def read_manifest(dest: Path) -> Optional[InstallManifest]:
    """Manifiesto de un destino, o None si falta o está corrupto."""
    try:
        data = json.loads((dest / MANIFEST_FILE).read_text(encoding=ENCODING))
    except (OSError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    try:
        return InstallManifest(
            harness=str(data["harness"]),
            profile=str(data.get("profile", "")),
            version=str(data.get("version", "")),
            commit=str(data.get("commit", "")),
            installed_at=str(data.get("installed_at", "")),
            source_repo=str(data.get("source_repo", "")),
            schema=int(data.get("schema", 1)),
            files=_files_field(data.get("files")),
            orphans=_files_field({"o": data.get("orphans")}).get("o", {}),
        )
    except (KeyError, TypeError, ValueError):
        return None


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Escribe o muestra el manifiesto de instalación .aagy-install.json.")
    parser.add_argument("action", choices=("write", "apply", "show"))
    parser.add_argument("--dest", type=Path, required=True, help="Directorio de instalación.")
    parser.add_argument("--harness", choices=HARNESSES, default=HARNESS_AGY)
    parser.add_argument("--profile", default="generic", help="Perfil o fase instalada (generic, all, infra...).")
    parser.add_argument("--repo-root", type=Path, default=None, help="Raíz del repo aagy de origen.")
    parser.add_argument("--stage", type=Path, default=None, help="apply: copia nueva preparada por el instalador.")
    parser.add_argument("--hard", action="store_true", help="apply: borra los ficheros que el perfil ya no trae.")
    parser.add_argument("--force", action="store_true", help="apply: pisa también los ficheros editados a mano.")
    parser.add_argument("--dry-run", action="store_true", help="apply: muestra qué cambiaría sin tocar nada.")
    return parser.parse_args(args)


def run_apply(parsed: argparse.Namespace, dest: Path, repo_root: Path) -> int:
    if parsed.stage is None or not parsed.stage.is_dir():
        print("[!] apply necesita --stage con la copia nueva.", file=sys.stderr)
        return 2
    old = read_manifest(dest)
    plan, hashes = plan_sync(parsed.stage, dest, parsed.profile, old, parsed.hard, parsed.force)
    print_plan(plan, parsed.dry_run)
    if parsed.dry_run:
        return 0
    apply_plan(plan, parsed.stage, dest)
    base = build_manifest(repo_root, parsed.harness, parsed.profile)
    try:
        write_manifest(dest, next_manifest(base, old, parsed.profile, hashes, plan))
    except OSError as exc:
        print(f"[!] No se pudo escribir {MANIFEST_FILE} en {dest}: {exc}", file=sys.stderr)
    return 0


def main(args: Optional[Sequence[str]] = None) -> int:
    parsed = parse_args(args)
    dest = parsed.dest.expanduser()
    if parsed.action == "show":
        manifest = read_manifest(dest)
        print(json.dumps(manifest.to_dict() if manifest else None, indent=2, ensure_ascii=False))
        return 0 if manifest else 1
    repo_root = (parsed.repo_root or default_repo_root()).resolve()
    if parsed.action == "apply":
        return run_apply(parsed, dest, repo_root)
    old = read_manifest(dest)
    exclude = CLAUDE_EXCLUDE_TOP if parsed.harness == HARNESS_CLAUDE else ()
    files = {**(old.files if old else {}), parsed.profile: tree_hashes(dest, exclude)}
    try:
        target = write_manifest(dest, build_manifest(repo_root, parsed.harness, parsed.profile, files=files))
    except OSError as exc:
        print(f"[!] No se pudo escribir {MANIFEST_FILE} en {dest}: {exc}", file=sys.stderr)
        return 0
    print(f"[+] Manifiesto de instalación escrito en {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
