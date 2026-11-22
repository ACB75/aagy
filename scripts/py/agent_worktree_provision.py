#!/usr/bin/env python3
"""
Preparación de un worktree de agente tras crearlo o reciclarlo (agent_worktree.py):

- **Configuración**: los ficheros ignorados por git que casan con `copy` (por defecto
  `.env` y `.env.*`) se copian del checkout principal.
- **Generados**: `node_modules` y `.venv` no se copian; se regeneran con el instalador
  de su lockfile, y solo si el principal los tiene. Maven, Gradle y Go usan cachés
  globales del usuario, así que no hay nada que regenerar por worktree.

Configurable en `.governance/agent-worktrees.json` (ver MANUAL_agent_worktrees.md).
"""

from __future__ import annotations

import fnmatch
import os
import shlex
import shutil
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from agent_worktree_base import (
    DEFAULT_CONFIG,
    GENERATED_DIRS,
    K_COPY,
    K_COPY_EXCLUDE,
    K_EXTRA_INSTALL,
    K_INSTALL,
    K_INSTALL_TIMEOUT,
    NODE_MODULES,
    VENV_DIRS,
    git_out,
    run,
)

FROZEN = "--frozen-lockfile"
INSTALL = "install"
Step = Tuple[Path, List[str]]

# (lockfile, comando) en orden de preferencia para node_modules.
NODE_INSTALLERS: Tuple[Tuple[Tuple[str, ...], List[str]], ...] = (
    (("pnpm-lock.yaml",), ["pnpm", INSTALL, FROZEN]),
    (("yarn.lock",), ["yarn", INSTALL, FROZEN]),
    (("bun.lockb", "bun.lock"), ["bun", INSTALL, FROZEN]),
    (("package-lock.json",), ["npm", "ci"]),
    (("package.json",), ["npm", INSTALL]),
)


def ignored_entries(main: Path) -> List[str]:
    out = git_out(main, "ls-files", "--others", "--ignored", "--exclude-standard", "--directory") or ""
    return [line.strip() for line in out.splitlines() if line.strip()]


def config_files_to_copy(main: Path, config: Dict[str, Any]) -> List[str]:
    patterns = [str(p) for p in config.get(K_COPY) or []]
    excludes = {str(p) for p in config.get(K_COPY_EXCLUDE) or []}
    found: List[str] = []
    for rel in ignored_entries(main):
        parts = rel.split("/")
        if rel.endswith("/") or any(part in excludes for part in parts):
            continue
        if any(fnmatch.fnmatch(parts[-1], pat) or fnmatch.fnmatch(rel, pat) for pat in patterns):
            found.append(rel)
    return found


def copy_config(main: Path, target: Path, config: Dict[str, Any]) -> List[str]:
    copied: List[str] = []
    for rel in config_files_to_copy(main, config):
        src, dst = main / rel, target / rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied.append(rel)
    return copied


def _venv_python(venv: Path) -> Path:
    win = venv / "Scripts" / "python.exe"
    return win if os.name == "nt" or win.exists() else venv / "bin" / "python"


def _node_installer(folder: Path) -> Optional[List[List[str]]]:
    for lockfiles, argv in NODE_INSTALLERS:
        if any((folder / name).exists() for name in lockfiles):
            return [list(argv)]
    return None


def _venv_installer(folder: Path, venv_name: str) -> Optional[List[List[str]]]:
    if (folder / "uv.lock").exists():
        return [["uv", "sync"]]
    if (folder / "poetry.lock").exists():
        return [["poetry", INSTALL]]
    if (folder / "requirements.txt").exists():
        venv_py = str(_venv_python(folder / venv_name))
        return [[sys.executable or "python", "-m", "venv", venv_name], [venv_py, "-m", "pip", INSTALL, "-q", "-r", "requirements.txt"]]
    return None


def installer_for(generated: str, folder: Path) -> Optional[List[List[str]]]:
    """Comandos que regeneran `generated` (node_modules, .venv) en `folder`, según su lockfile."""
    if generated == NODE_MODULES:
        return _node_installer(folder)
    if generated in VENV_DIRS:
        return _venv_installer(folder, generated)
    return None


def _explicit_commands(target: Path, items: Sequence[Any]) -> List[Step]:
    plan: List[Step] = []
    for item in items:
        if isinstance(item, dict) and item.get("argv"):
            argv = item["argv"]
            argv = shlex.split(argv) if isinstance(argv, str) else [str(a) for a in argv]
            plan.append((target / str(item.get("cwd") or "."), argv))
    return plan


def _auto_plan(main: Path, target: Path) -> List[Step]:
    plan: List[Step] = []
    for rel in ignored_entries(main):
        parts = rel.rstrip("/").split("/")
        if not rel.endswith("/") or parts[-1] not in GENERATED_DIRS:
            continue
        if any(part in GENERATED_DIRS for part in parts[:-1]):
            continue
        folder = target.joinpath(*parts[:-1]) if len(parts) > 1 else target
        plan.extend((folder, argv) for argv in installer_for(parts[-1], folder) or [])
    return plan


def install_plan(main: Path, target: Path, config: Dict[str, Any]) -> List[Step]:
    """Regenera solo lo que el principal tiene generado (node_modules, .venv…), más lo declarado."""
    mode = config.get(K_INSTALL, "auto")
    plan: List[Step] = []
    if mode == "auto":
        plan = _auto_plan(main, target)
    elif isinstance(mode, list):
        plan = _explicit_commands(target, mode)
    return plan + _explicit_commands(target, config.get(K_EXTRA_INSTALL) or [])


def run_installs(
    main: Path, target: Path, config: Dict[str, Any], which: Callable[[str], Optional[str]] = shutil.which
) -> List[str]:
    messages: List[str] = []
    timeout = int(config.get(K_INSTALL_TIMEOUT) or DEFAULT_CONFIG[K_INSTALL_TIMEOUT])
    for folder, argv in install_plan(main, target, config):
        exe = argv[0] if Path(argv[0]).is_absolute() else which(argv[0])
        label = " ".join(argv[:3])
        rel = os.path.relpath(folder, target)
        if exe is None:
            messages.append(f"AVISO: no está {argv[0]}; no se regenera {rel}.")
            continue
        res = run([exe, *argv[1:]], folder, timeout)
        if res.ok:
            messages.append(f"Regenerado: {label} en {rel}.")
        else:
            messages.append(f"AVISO: falló {label} en {rel}: {(res.err or res.out)[-300:]}")
    return messages


def provision(main: Path, target: Path, config: Dict[str, Any], install: bool) -> List[str]:
    messages: List[str] = []
    copied = copy_config(main, target, config)
    if copied:
        messages.append("Configuración copiada del principal: " + ", ".join(copied) + ".")
    if install:
        messages.extend(run_installs(main, target, config))
    return messages
