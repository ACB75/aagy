#!/usr/bin/env python3
"""
Manifiesto de instalación de aagy / aagy-ecc (install_manifest.py).

Los instaladores (install.ps1, install.sh, aagy-sync.ps1, aagy-sync.sh)
escriben `.aagy-install.json` en el destino para que los doctors sepan qué
se instaló: harness, perfil, versión, commit, fecha y repo de origen.

Escribir el manifiesto nunca debe abortar una instalación: ante cualquier
error se avisa y se sale con 0.

Uso:
  python scripts/py/install_manifest.py write --dest <dir> --harness agy --profile generic
  python scripts/py/install_manifest.py show --dest <dir>
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
from typing import Dict, Optional, Sequence

MANIFEST_FILE = ".aagy-install.json"
MANIFEST_SCHEMA = 1
HARNESS_AGY = "agy"
HARNESS_CLAUDE = "claude"
HARNESSES = (HARNESS_AGY, HARNESS_CLAUDE)
ENCODING = "utf-8"
GIT_TIMEOUT_S = 3


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


def build_manifest(repo_root: Path, harness: str, profile: str, now: Optional[datetime] = None) -> InstallManifest:
    stamp = (now or datetime.now(timezone.utc)).replace(microsecond=0).isoformat()
    return InstallManifest(
        harness=harness,
        profile=profile,
        version=read_version(repo_root, harness),
        commit=read_commit(repo_root),
        installed_at=stamp,
        source_repo=str(repo_root.resolve()),
    )


def write_manifest(dest: Path, manifest: InstallManifest) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / MANIFEST_FILE
    target.write_text(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding=ENCODING)
    return target


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
            schema=int(data.get("schema", MANIFEST_SCHEMA)),
        )
    except (KeyError, TypeError, ValueError):
        return None


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Escribe o muestra el manifiesto de instalación .aagy-install.json.")
    parser.add_argument("action", choices=("write", "show"))
    parser.add_argument("--dest", type=Path, required=True, help="Directorio de instalación.")
    parser.add_argument("--harness", choices=HARNESSES, default=HARNESS_AGY)
    parser.add_argument("--profile", default="generic", help="Perfil o fase instalada (generic, all, infra...).")
    parser.add_argument("--repo-root", type=Path, default=None, help="Raíz del repo aagy de origen.")
    return parser.parse_args(args)


def main(args: Optional[Sequence[str]] = None) -> int:
    parsed = parse_args(args)
    dest = parsed.dest.expanduser()
    if parsed.action == "show":
        manifest = read_manifest(dest)
        print(json.dumps(manifest.to_dict() if manifest else None, indent=2, ensure_ascii=False))
        return 0 if manifest else 1
    repo_root = (parsed.repo_root or default_repo_root()).resolve()
    try:
        target = write_manifest(dest, build_manifest(repo_root, parsed.harness, parsed.profile))
    except OSError as exc:
        print(f"[!] No se pudo escribir {MANIFEST_FILE} en {dest}: {exc}", file=sys.stderr)
        return 0
    print(f"[+] Manifiesto de instalación escrito en {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
