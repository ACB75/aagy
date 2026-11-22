#!/usr/bin/env python3
"""
Base común de los worktrees por agente (agent_worktree.py, agent_worktree_guard.py,
agent_worktree_provision.py): constantes, ejecución de git, disposición del clon
(principal + `<repo>-aagy` + `<repo>-aagy-ecc`), configuración y bloqueo.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence

logger = logging.getLogger("agent-worktree")

AGENT_SUFFIXES: Dict[str, str] = {"agy": "-aagy", "claude": "-aagy-ecc"}
AGENT_LABELS: Dict[str, str] = {"agy": "Antigravity", "claude": "Claude Code"}
ROLE_MAIN = "main"
ROLE_OTHER = "other"
MARKER_NAME = "aagy-worktrees.json"
LOCK_NAME = "aagy-worktrees.lock"
CONFIG_REL = Path(".governance") / "agent-worktrees.json"
ENCODING = "utf-8"
ENV_AGENT = "AAGY_AGENT"
REMOTE = "origin"
DEFAULT_BASE = "main"
LOCK_STALE_SECONDS = 3600.0
LOCK_WAIT_SECONDS = 30.0
GIT_TIMEOUT = 120
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BLOCKED = 3
EXIT_NOT_MERGED = 4
EXIT_NO_GH = 5

# Argumentos de git repetidos (evita literales duplicados, S1192).
G_REV_PARSE = "rev-parse"
G_REV_LIST = "rev-list"
G_WORKTREE = "worktree"
G_PORCELAIN = "--porcelain"
G_DETACH = "--detach"

K_BASE = "base"
K_COPY = "copy"
K_COPY_EXCLUDE = "copy_exclude"
K_INSTALL = "install"
K_INSTALL_TIMEOUT = "install_timeout_s"
K_EXTRA_INSTALL = "extra_install"
NODE_MODULES = "node_modules"
VENV_DIRS = (".venv", "venv")
GENERATED_DIRS = (NODE_MODULES, *VENV_DIRS)

DEFAULT_CONFIG: Dict[str, Any] = {
    K_BASE: DEFAULT_BASE,
    K_COPY: [".env", ".env.*"],
    K_COPY_EXCLUDE: list(GENERATED_DIRS),
    K_INSTALL: "auto",
    K_INSTALL_TIMEOUT: 900,
}


class WorktreeError(Exception):
    """Error de uso o de estado; el CLI lo muestra y sale con el código indicado."""

    def __init__(self, message: str, code: int = EXIT_ERROR) -> None:
        super().__init__(message)
        self.code = code


# --------------------------------------------------------------------------- utilidades


def utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def norm(path: Path) -> str:
    """Clave de comparación de rutas: absoluta, normalizada y sin distinguir mayúsculas en Windows."""
    return os.path.normcase(os.path.normpath(os.path.abspath(str(path))))


def is_within(path: Path, root: Path) -> bool:
    p, r = norm(path), norm(root)
    return p == r or p.startswith(r.rstrip(os.sep) + os.sep)


@dataclass
class Result:
    code: int
    out: str
    err: str

    @property
    def ok(self) -> bool:
        return self.code == 0


def run(argv: Sequence[str], cwd: Path, timeout: int = GIT_TIMEOUT) -> Result:
    try:
        proc = subprocess.run(
            list(argv), cwd=str(cwd), capture_output=True, text=True, check=False, timeout=timeout,
            encoding=ENCODING, errors="replace",
        )
    except FileNotFoundError:
        return Result(127, "", f"No se encuentra {argv[0]}.")
    except (OSError, subprocess.SubprocessError) as exc:
        return Result(1, "", str(exc))
    return Result(proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip())


def git(cwd: Path, *args: str, timeout: int = GIT_TIMEOUT) -> Result:
    return run(["git", *args], cwd, timeout)


def git_out(cwd: Path, *args: str) -> Optional[str]:
    res = git(cwd, *args)
    return res.out if res.ok else None


def current_branch(path: Path) -> Optional[str]:
    """Rama en checkout, o None si HEAD está desacoplado."""
    return git_out(path, "symbolic-ref", "--quiet", "--short", "HEAD")


def short_head(path: Path) -> Optional[str]:
    return git_out(path, G_REV_PARSE, "--short", "HEAD")


def status_lines(path: Path, *extra: str) -> List[str]:
    return (git_out(path, "status", G_PORCELAIN, *extra) or "").splitlines()


# --------------------------------------------------------------------------- disposición


@dataclass
class Layout:
    main: Path
    common_dir: Path
    worktrees: Dict[str, Path] = field(default_factory=dict)

    @property
    def marker(self) -> Path:
        return self.common_dir / MARKER_NAME

    @property
    def active(self) -> bool:
        return self.marker.is_file()

    def role(self, path: Path) -> str:
        for agent, root in self.worktrees.items():
            if is_within(path, root):
                return agent
        if is_within(path, self.main):
            return ROLE_MAIN
        return ROLE_OTHER

    def protected_for(self, agent: str) -> List[Path]:
        return [self.main] + [p for a, p in self.worktrees.items() if a != agent]

    def to_dict(self, path: Optional[Path] = None) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "main": str(self.main),
            "active": self.active,
            **{agent: str(p) for agent, p in self.worktrees.items()},
        }
        if path is not None:
            data["role"] = self.role(path)
        return data


def layout_for_main(main: Path, common_dir: Path) -> Layout:
    worktrees = {agent: main.parent / f"{main.name}{suffix}" for agent, suffix in AGENT_SUFFIXES.items()}
    return Layout(main=main, common_dir=common_dir, worktrees=worktrees)


def _common_dir_of_gitfile(candidate: Path, dot_git: Path) -> Optional[Path]:
    """Resuelve el `.git` fichero de un worktree (`gitdir: ...`) hasta el common dir."""
    try:
        text = dot_git.read_text(encoding=ENCODING).strip()
    except OSError:
        return None
    if not text.startswith("gitdir:"):
        return None
    gitdir = Path(text.split(":", 1)[1].strip())
    if not gitdir.is_absolute():
        gitdir = (candidate / gitdir).resolve()
    commondir_file = gitdir / "commondir"
    if not commondir_file.is_file():
        return gitdir.parent.parent
    rel = Path(commondir_file.read_text(encoding=ENCODING).strip())
    return (rel if rel.is_absolute() else gitdir / rel).resolve()


def _common_dir_from_fs(start: Path) -> Optional[Path]:
    """Busca el git common dir sin llamar a git (lo usa la guarda, que tiene que ser rápida)."""
    current = start if start.is_dir() else start.parent
    for candidate in [current, *current.parents]:
        dot_git = candidate / ".git"
        if dot_git.is_dir():
            return dot_git
        if dot_git.is_file():
            return _common_dir_of_gitfile(candidate, dot_git)
    return None


def find_layout(start: Path, use_git: bool = True) -> Optional[Layout]:
    """Disposición del clon que contiene `start`, o None si no es un repo git con .git normal."""
    start = Path(os.path.abspath(str(start)))
    common: Optional[Path] = None
    if use_git:
        folder = start if start.is_dir() else start.parent
        out = git_out(folder, G_REV_PARSE, "--path-format=absolute", "--git-common-dir")
        common = Path(out) if out else None
    if common is None:
        common = _common_dir_from_fs(start)
    if common is None or common.name != ".git":
        return None
    return layout_for_main(common.parent, common)


def load_config(main: Path) -> Dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    try:
        data = json.loads((main / CONFIG_REL).read_text(encoding=ENCODING))
    except (OSError, ValueError):
        return config
    if isinstance(data, dict):
        config.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG or k == K_EXTRA_INSTALL})
    return config


def base_branch(main: Path) -> str:
    return str(load_config(main).get(K_BASE) or DEFAULT_BASE)


def resolve_agent(value: Optional[str], layout: Optional[Layout] = None, cwd: Optional[Path] = None) -> str:
    agent = (value or os.environ.get(ENV_AGENT) or "").strip().lower()
    if not agent and layout is not None and cwd is not None and layout.role(cwd) in AGENT_SUFFIXES:
        agent = layout.role(cwd)
    if agent not in AGENT_SUFFIXES:
        raise WorktreeError(f"Agente desconocido '{agent or '-'}': usa --agent agy|claude.")
    return agent


def _unlink(path: Path) -> None:
    try:
        path.unlink()
    except OSError as exc:
        logger.debug("No se pudo borrar %s: %s", path, exc)


def _lock_is_stale(lock: Path) -> bool:
    try:
        return time.time() - lock.stat().st_mtime > LOCK_STALE_SECONDS
    except OSError as exc:
        logger.debug("Lock %s desaparecido: %s", lock, exc)
        return False


@contextmanager
def worktree_lock(layout: Layout) -> Iterator[None]:
    """Lock exclusivo por fichero (O_EXCL) en el common dir; caduca a la hora."""
    lock = layout.common_dir / LOCK_NAME
    deadline = time.monotonic() + LOCK_WAIT_SECONDS
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()} {utc_iso()}".encode(ENCODING))
            os.close(fd)
            break
        except FileExistsError:
            if _lock_is_stale(lock):
                _unlink(lock)
                continue
            if time.monotonic() > deadline:
                raise WorktreeError(f"Otro proceso está reciclando worktrees ({lock}).")
            time.sleep(0.2)
    try:
        yield
    finally:
        _unlink(lock)


def registered_worktrees(layout: Layout) -> Dict[str, Dict[str, str]]:
    """`git worktree list --porcelain` como {ruta normalizada: {head, branch, ...}}."""
    out = git_out(layout.main, G_WORKTREE, "list", G_PORCELAIN) or ""
    entries: Dict[str, Dict[str, str]] = {}
    current: Dict[str, str] = {}
    for line in out.splitlines() + [""]:
        if not line.strip():
            if current.get(G_WORKTREE):
                entries[norm(Path(current[G_WORKTREE]))] = current
            current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value or "true"
    return entries
