#!/usr/bin/env python3
"""
Un git worktree fijo por agente (Claude Code / aagy-ecc y Antigravity / aagy).

Para un clon principal `<padre>/<repo>` (el de Master) se mantienen dos worktrees
hermanos del mismo clon:

- `<padre>/<repo>-aagy`      → Antigravity (agy)
- `<padre>/<repo>-aagy-ecc`  → Claude Code (claude)

Comandos:

- `init`     crea los worktrees que falten, desacoplados en `origin/<base>`.
- `where`    dice si la carpeta actual es el principal, el worktree de un agente u otra.
- `status`   estado de los tres checkouts.
- `recycle`  tras fusionarse la PR: limpia el worktree en sitio (o lo recrea si no se
             puede), copia la configuración (.env) del principal, regenera las
             dependencias y actualiza el principal con --ff-only si está limpio en main.
             Nunca borra trabajo sin guardar: si lo hay, bloquea y avisa.
- `guard`    hook PreToolUse: impide que un agente escriba fuera de su worktree.

El marcador `$(git common dir)/aagy-worktrees.json` activa la guarda; sin él, el repo
sigue como siempre. Ver doc/04-operations/runbooks/MANUAL_agent_worktrees.md.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

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
GH_TIMEOUT = 20
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_BLOCKED = 3
EXIT_NOT_MERGED = 4
EXIT_NO_GH = 5

DEFAULT_CONFIG: Dict[str, Any] = {
    "base": DEFAULT_BASE,
    "copy": [".env", ".env.*"],
    "copy_exclude": ["node_modules", ".venv", "venv"],
    "install": "auto",
    "install_timeout_s": 900,
}
GENERATED_DIRS = ("node_modules", ".venv", "venv")
GUARD_TAG = "[WORKTREE-GUARD]"

# Comandos que se pueden ejecutar en una carpeta ajena porque solo leen.
READONLY_COMMANDS = frozenset(
    {
        "ls", "dir", "cat", "type", "head", "tail", "less", "more", "grep", "rg", "find", "wc",
        "pwd", "echo", "which", "where", "file", "stat", "tree", "du", "df", "diff", "sort", "uniq",
        "get-childitem", "gci", "get-content", "gc", "select-string", "sls", "get-location",
        "get-item", "test-path", "resolve-path", "write-output", "write-host", "measure-object",
        "cd", "set-location", "sl", "pushd", "popd", "chdir", "true", "exit",
    }
)
READONLY_GIT = frozenset(
    {
        "status", "log", "diff", "show", "fetch", "blame", "rev-parse", "ls-files", "ls-remote",
        "describe", "shortlog", "grep", "remote", "config", "for-each-ref", "cat-file", "rev-list",
        "merge-base", "reflog", "help", "version", "--version",
    }
)
WRITE_HINTS = re.compile(
    r"(>>?|\btee\b|\brm\b|\brmdir\b|\bdel\b|\bmv\b|\bcp\b|\bmkdir\b|\btouch\b|\bsed\s+-i|"
    r"remove-item|set-content|add-content|out-file|new-item|copy-item|move-item|rename-item|"
    r"\bri\b|\bni\b|\bcpi\b|\bmi\b)",
    re.IGNORECASE,
)
SEGMENT_SPLIT = re.compile(r"\s*(?:&&|\|\||;|\||\r?\n)\s*")
CD_TARGET = re.compile(r"^(?:cd|chdir|pushd|set-location|sl)\s+(?:-path\s+)?(?P<path>.+?)\s*$", re.IGNORECASE)
GIT_C_TARGET = re.compile(r"(?:^|\s)git(?:\.exe)?\s+(?:-C\s+|--work-tree[= ])(?P<path>\"[^\"]+\"|'[^']+'|\S+)")
WORKTREE_CMD = re.compile(r"(?:^|\s)git(?:\.exe)?\s+(?:-C\s+\S+\s+)?worktree\s+(?:add|remove|move)\b")
NATIVE_WORKTREE = re.compile(r"(?:^|\s)claude(?:\.exe|\.cmd)?\s+(?:[^|;&]*\s)?(?:--worktree|-w)\b")
SELF_SCRIPT = re.compile(r"agent[_-]worktree\.(?:py|ps1|sh)", re.IGNORECASE)


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


def _common_dir_from_fs(start: Path) -> Optional[Path]:
    """Busca el git common dir sin llamar a git (lo usa la guarda, que tiene que ser rápida)."""
    current = start if start.is_dir() else start.parent
    for candidate in [current, *current.parents]:
        dot_git = candidate / ".git"
        if dot_git.is_dir():
            return dot_git
        if dot_git.is_file():
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
            if commondir_file.is_file():
                rel = commondir_file.read_text(encoding=ENCODING).strip()
                common = Path(rel) if Path(rel).is_absolute() else (gitdir / rel)
                return common.resolve()
            return gitdir.parent.parent
    return None


def find_layout(start: Path, use_git: bool = True) -> Optional[Layout]:
    """Disposición del clon que contiene `start`, o None si no es un repo git con .git normal."""
    start = Path(os.path.abspath(str(start)))
    common: Optional[Path] = None
    if use_git:
        out = git_out(start if start.is_dir() else start.parent, "rev-parse", "--path-format=absolute", "--git-common-dir")
        if out:
            common = Path(out)
    if common is None:
        common = _common_dir_from_fs(start)
    if common is None or common.name != ".git":
        return None
    return layout_for_main(common.parent, common)


def load_config(main: Path) -> Dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    path = main / CONFIG_REL
    try:
        data = json.loads(path.read_text(encoding=ENCODING))
    except (OSError, ValueError):
        return config
    if isinstance(data, dict):
        config.update({k: v for k, v in data.items() if k in DEFAULT_CONFIG or k == "extra_install"})
    return config


def resolve_agent(value: Optional[str], layout: Optional[Layout] = None, cwd: Optional[Path] = None) -> str:
    agent = (value or os.environ.get(ENV_AGENT) or "").strip().lower()
    if not agent and layout is not None and cwd is not None:
        role = layout.role(cwd)
        if role in AGENT_SUFFIXES:
            agent = role
    if agent not in AGENT_SUFFIXES:
        raise WorktreeError(f"Agente desconocido '{agent or '-'}': usa --agent agy|claude.")
    return agent


@contextmanager
def worktree_lock(layout: Layout) -> Iterator[None]:
    lock = layout.common_dir / LOCK_NAME
    deadline = time.monotonic() + LOCK_WAIT_SECONDS
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()} {utc_iso()}".encode(ENCODING))
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > LOCK_STALE_SECONDS:
                    lock.unlink()
                    continue
            except OSError:
                pass
            if time.monotonic() > deadline:
                raise WorktreeError(f"Otro proceso está reciclando worktrees ({lock}).")
            time.sleep(0.2)
    try:
        yield
    finally:
        try:
            lock.unlink()
        except OSError:
            pass


def registered_worktrees(layout: Layout) -> Dict[str, Dict[str, str]]:
    """`git worktree list --porcelain` como {ruta normalizada: {head, branch, ...}}."""
    out = git_out(layout.main, "worktree", "list", "--porcelain") or ""
    entries: Dict[str, Dict[str, str]] = {}
    current: Dict[str, str] = {}
    for line in out.splitlines() + [""]:
        if not line.strip():
            if current.get("worktree"):
                entries[norm(Path(current["worktree"]))] = current
            current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value or "true"
    return entries


# --------------------------------------------------------------------------- configuración y dependencias


def _ignored_entries(main: Path) -> List[str]:
    out = git_out(main, "ls-files", "--others", "--ignored", "--exclude-standard", "--directory") or ""
    return [line.strip() for line in out.splitlines() if line.strip()]


def config_files_to_copy(main: Path, config: Dict[str, Any]) -> List[str]:
    patterns = [str(p) for p in config.get("copy") or []]
    excludes = {str(p) for p in config.get("copy_exclude") or []}
    found: List[str] = []
    for rel in _ignored_entries(main):
        if rel.endswith("/"):
            continue
        parts = rel.split("/")
        if any(part in excludes for part in parts):
            continue
        name = parts[-1]
        if any(fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat) for pat in patterns):
            found.append(rel)
    return found


def copy_config(main: Path, target: Path, config: Dict[str, Any]) -> List[str]:
    copied: List[str] = []
    for rel in config_files_to_copy(main, config):
        src, dst = main / rel, target / rel
        if not src.is_file():
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append(rel)
    return copied


def _venv_python(venv: Path) -> Path:
    win = venv / "Scripts" / "python.exe"
    return win if os.name == "nt" or win.exists() else venv / "bin" / "python"


def installer_for(generated: str, folder: Path) -> Optional[List[List[str]]]:
    """Comandos que regeneran `generated` (node_modules, .venv) en `folder`, según su lockfile."""
    if generated == "node_modules":
        if (folder / "pnpm-lock.yaml").exists():
            return [["pnpm", "install", "--frozen-lockfile"]]
        if (folder / "yarn.lock").exists():
            return [["yarn", "install", "--frozen-lockfile"]]
        if (folder / "bun.lockb").exists() or (folder / "bun.lock").exists():
            return [["bun", "install", "--frozen-lockfile"]]
        if (folder / "package-lock.json").exists():
            return [["npm", "ci"]]
        if (folder / "package.json").exists():
            return [["npm", "install"]]
        return None
    if generated in (".venv", "venv"):
        if (folder / "uv.lock").exists():
            return [["uv", "sync"]]
        if (folder / "poetry.lock").exists():
            return [["poetry", "install"]]
        if (folder / "requirements.txt").exists():
            py = sys.executable or "python"
            venv_py = str(_venv_python(folder / generated))
            return [[py, "-m", "venv", generated], [venv_py, "-m", "pip", "install", "-q", "-r", "requirements.txt"]]
        return None
    return None


def install_plan(main: Path, target: Path, config: Dict[str, Any]) -> List[Tuple[Path, List[str]]]:
    """Regenera solo lo que el principal tiene generado (node_modules, .venv…), más lo declarado."""
    plan: List[Tuple[Path, List[str]]] = []
    mode = config.get("install", "auto")
    if mode == "auto":
        for rel in _ignored_entries(main):
            parts = rel.rstrip("/").split("/")
            name = parts[-1]
            if not rel.endswith("/") or name not in GENERATED_DIRS:
                continue
            if any(part in GENERATED_DIRS for part in parts[:-1]):
                continue
            folder = target.joinpath(*parts[:-1]) if len(parts) > 1 else target
            for argv in installer_for(name, folder) or []:
                plan.append((folder, argv))
    elif isinstance(mode, list):
        plan.extend(_explicit_commands(target, mode))
    plan.extend(_explicit_commands(target, config.get("extra_install") or []))
    return plan


def _explicit_commands(target: Path, items: Sequence[Any]) -> List[Tuple[Path, List[str]]]:
    plan: List[Tuple[Path, List[str]]] = []
    for item in items:
        if isinstance(item, dict) and item.get("argv"):
            argv = item["argv"]
            argv = shlex.split(argv) if isinstance(argv, str) else [str(a) for a in argv]
            plan.append((target / str(item.get("cwd") or "."), argv))
    return plan


def run_installs(main: Path, target: Path, config: Dict[str, Any]) -> List[str]:
    messages: List[str] = []
    timeout = int(config.get("install_timeout_s") or DEFAULT_CONFIG["install_timeout_s"])
    for folder, argv in install_plan(main, target, config):
        exe = argv[0]
        if not Path(exe).is_absolute() and shutil.which(exe) is None:
            messages.append(f"AVISO: no está {exe}; no se regenera {folder}.")
            continue
        if Path(exe).is_absolute():
            resolved = exe
        else:
            resolved = shutil.which(exe) or exe
        res = run([resolved, *argv[1:]], folder, timeout)
        rel = os.path.relpath(folder, target)
        label = " ".join(argv[:3])
        if res.ok:
            messages.append(f"Regenerado: {label} en {rel}.")
        else:
            messages.append(f"AVISO: falló {label} en {rel}: {(res.err or res.out)[-300:]}")
    return messages


def provision(layout: Layout, target: Path, config: Dict[str, Any], install: bool) -> List[str]:
    messages: List[str] = []
    copied = copy_config(layout.main, target, config)
    if copied:
        messages.append("Configuración copiada del principal: " + ", ".join(copied) + ".")
    if install:
        messages.extend(run_installs(layout.main, target, config))
    return messages


# --------------------------------------------------------------------------- init / status


def _fetch(layout: Layout, base: str) -> None:
    res = git(layout.main, "fetch", "--prune", REMOTE, base)
    if not res.ok:
        raise WorktreeError(f"git fetch {REMOTE} {base} falló: {res.err}")


def write_marker(layout: Layout, base: str) -> None:
    data = {"version": 1, "base": base, "updated": utc_iso(), **layout.to_dict()}
    data.pop("active", None)
    layout.marker.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding=ENCODING)


def op_init(layout: Layout, install: bool = True, fetch: bool = True) -> List[str]:
    config = load_config(layout.main)
    base = str(config.get("base") or DEFAULT_BASE)
    messages: List[str] = []
    with worktree_lock(layout):
        if fetch:
            _fetch(layout, base)
        registered = registered_worktrees(layout)
        for agent, path in layout.worktrees.items():
            label = AGENT_LABELS[agent]
            if norm(path) in registered:
                messages.append(f"{label}: {path} ya existe.")
                continue
            if path.exists():
                raise WorktreeError(f"{path} existe pero no es un worktree de {layout.main}. Muévelo o bórralo.")
            res = git(layout.main, "worktree", "add", "--detach", str(path), f"{REMOTE}/{base}")
            if not res.ok:
                raise WorktreeError(f"No se pudo crear {path}: {res.err}")
            messages.append(f"{label}: creado {path} en {REMOTE}/{base}.")
            messages.extend(provision(layout, path, config, install))
        write_marker(layout, base)
    messages.append(f"Activado. El checkout principal {layout.main} queda para Master.")
    return messages


def worktree_state(path: Path) -> Dict[str, Any]:
    if not path.is_dir():
        return {"exists": False}
    branch = git_out(path, "symbolic-ref", "--quiet", "--short", "HEAD")
    head = git_out(path, "rev-parse", "--short", "HEAD")
    dirty = git_out(path, "status", "--porcelain") or ""
    return {"exists": True, "branch": branch, "head": head, "dirty": len(dirty.splitlines())}


def op_status(layout: Layout) -> Dict[str, Any]:
    data: Dict[str, Any] = {"active": layout.active, "main": {"path": str(layout.main), **worktree_state(layout.main)}}
    for agent, path in layout.worktrees.items():
        data[agent] = {"path": str(path), **worktree_state(path)}
    return data


# --------------------------------------------------------------------------- recycle


@dataclass
class PrInfo:
    state: str
    head_oid: Optional[str]
    number: Optional[int]


def pr_info(cwd: Path, branch: str) -> Optional[PrInfo]:
    """PR más reciente de la rama, o None si no hay gh o no hay PR."""
    if shutil.which("gh") is None:
        raise WorktreeError("Falta gh (GitHub CLI): sin él no se puede saber si la PR está fusionada.", EXIT_NO_GH)
    res = run(
        ["gh", "pr", "list", "--head", branch, "--state", "all", "--limit", "1",
         "--json", "state,headRefOid,number"],
        cwd, GH_TIMEOUT,
    )
    if not res.ok:
        raise WorktreeError(f"gh no pudo consultar la PR de {branch}: {res.err}", EXIT_NO_GH)
    try:
        items = json.loads(res.out or "[]")
    except ValueError:
        items = []
    if not items:
        return None
    item = items[0]
    return PrInfo(state=str(item.get("state") or "").upper(), head_oid=item.get("headRefOid"), number=item.get("number"))


def unsaved_work(path: Path, branch: Optional[str], pr: Optional[PrInfo], base: str) -> List[str]:
    """Lista legible de lo que se perdería al reciclar. Vacía = seguro."""
    problems: List[str] = []
    status = git_out(path, "status", "--porcelain") or ""
    if status:
        lines = status.splitlines()
        problems.append(f"{len(lines)} fichero(s) sin commit: " + ", ".join(l[3:] for l in lines[:5]))
    if branch:
        stashes = git_out(path, "stash", "list") or ""
        mine = [s for s in stashes.splitlines() if f"on {branch}:" in s.lower() or f"On {branch}:" in s]
        if mine:
            problems.append(f"{len(mine)} stash(es) de la rama {branch}.")
        problems.extend(_unpushed(path, branch, pr, base))
    else:
        contained = git(path, "merge-base", "--is-ancestor", "HEAD", f"{REMOTE}/{base}")
        if not contained.ok:
            remote_has = git_out(path, "branch", "-r", "--contains", "HEAD") or ""
            if not remote_has:
                problems.append("HEAD desacoplado con commits que no están en ninguna rama remota.")
    return problems


def _unpushed(path: Path, branch: str, pr: Optional[PrInfo], base: str) -> List[str]:
    if pr is not None and pr.state == "MERGED":
        if not pr.head_oid or git(path, "cat-file", "-e", f"{pr.head_oid}^{{commit}}").code != 0:
            return [f"No encuentro en local el último commit de la PR #{pr.number}; no puedo asegurar que no haya trabajo nuevo."]
        count = git_out(path, "rev-list", "--count", f"{pr.head_oid}..HEAD") or "0"
        return [f"{count} commit(s) posteriores a la PR #{pr.number} sin publicar."] if count != "0" else []
    upstream = git_out(path, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    ref = "@{u}" if upstream else f"{REMOTE}/{base}"
    count = git_out(path, "rev-list", "--count", f"{ref}..HEAD") or "0"
    return [f"{count} commit(s) sin push en {branch}."] if count != "0" else []


def _clean_in_place(path: Path, base: str) -> Tuple[bool, str]:
    for args in (("switch", "--detach", f"{REMOTE}/{base}"), ("reset", "--hard", f"{REMOTE}/{base}")):
        res = git(path, *args)
        if not res.ok:
            return False, res.err
    res = git(path, "clean", "-ffdx")
    failed = [l for l in (res.err + "\n" + res.out).splitlines() if "failed to remove" in l.lower()]
    if not res.ok or failed:
        return False, "\n".join(failed) or res.err
    return True, ""


def _recreate(layout: Layout, path: Path, base: str) -> None:
    git(layout.main, "worktree", "remove", "--force", str(path))
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        raise WorktreeError(
            f"No se puede borrar {path}: algún programa (IDE, terminal, servidor de desarrollo) lo tiene abierto. "
            "Ciérralo y repite el reciclado."
        )
    git(layout.main, "worktree", "prune")
    res = git(layout.main, "worktree", "add", "--detach", str(path), f"{REMOTE}/{base}")
    if not res.ok:
        raise WorktreeError(f"No se pudo recrear {path}: {res.err}")


def update_main(layout: Layout, base: str) -> str:
    branch = git_out(layout.main, "symbolic-ref", "--quiet", "--short", "HEAD")
    if branch != base:
        return f"AVISO: tu checkout principal está en '{branch or 'HEAD desacoplado'}', no en {base}; no lo toco."
    dirty = git_out(layout.main, "status", "--porcelain", "--untracked-files=no")
    if dirty:
        return f"AVISO: tu checkout principal tiene cambios sin commit; no lo actualizo. Haz git pull cuando quieras."
    res = git(layout.main, "merge", "--ff-only", f"{REMOTE}/{base}")
    if not res.ok:
        return f"AVISO: tu checkout principal no avanza en fast-forward ({res.err.splitlines()[-1] if res.err else '?'}); no lo toco."
    head = git_out(layout.main, "rev-parse", "--short", "HEAD") or "?"
    return f"Checkout principal actualizado a {REMOTE}/{base} ({head})."


def _release_backlog(layout: Layout, path: Path, branch: Optional[str], agent: str) -> Optional[str]:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import backlog  # noqa: PLC0415 - dependencia opcional del mismo directorio
    except ImportError:
        return None
    repo = backlog.locate_repo(layout.main)
    try:
        with backlog.state_lock(repo):
            state = backlog.load_state(repo)
            touched = []
            for tid, entry in state.get("tasks", {}).items():
                same_wt = entry.get(backlog.K_AGENT_WORKTREE) and is_within(Path(entry[backlog.K_AGENT_WORKTREE]), path)
                if same_wt or (branch and entry.get("branch") == branch and entry.get("owner") == agent):
                    entry.pop(backlog.K_AGENT_WORKTREE, None)
                    backlog.record(entry, agent, "recycle", "worktree reciclado tras el merge")
                    touched.append(tid)
            if touched:
                backlog.save_state(repo, state)
    except Exception as exc:  # noqa: BLE001 - el backlog no debe impedir el reciclado
        return f"AVISO: no se pudo actualizar el backlog: {exc}"
    return f"Backlog: liberado el worktree de {', '.join(touched)}." if touched else None


def wait_for_merge(cwd: Path, branch: str, seconds: int) -> Optional[PrInfo]:
    deadline = time.monotonic() + max(0, seconds)
    pr = pr_info(cwd, branch)
    while pr is not None and pr.state == "OPEN" and time.monotonic() < deadline:
        time.sleep(5)
        pr = pr_info(cwd, branch)
    return pr


def op_recycle(
    layout: Layout,
    agent: str,
    if_merged: bool = False,
    hard_recreate: bool = False,
    install: bool = True,
    wait_s: int = 0,
) -> List[str]:
    config = load_config(layout.main)
    base = str(config.get("base") or DEFAULT_BASE)
    path = layout.worktrees[agent]
    if norm(path) not in registered_worktrees(layout):
        raise WorktreeError(f"{path} no es un worktree de {layout.main}. Ejecuta init.")
    messages: List[str] = []
    branch = git_out(path, "symbolic-ref", "--quiet", "--short", "HEAD")
    pr: Optional[PrInfo] = None
    if branch:
        pr = wait_for_merge(path, branch, wait_s) if wait_s else pr_info(path, branch)
        if pr is None or pr.state != "MERGED":
            state = "sin PR" if pr is None else f"PR #{pr.number} {pr.state.lower()}"
            if if_merged:
                return [] if not wait_s else [f"La rama {branch} aún no está fusionada ({state}); se reciclará en el próximo claim o inicio de sesión."]
            raise WorktreeError(f"La rama {branch} no está fusionada ({state}). No se recicla.", EXIT_NOT_MERGED)
    with worktree_lock(layout):
        os.chdir(str(layout.main))  # en Windows no se puede borrar la carpeta en la que está el proceso
        _fetch(layout, base)
        problems = unsaved_work(path, branch, pr, base)
        if problems:
            raise WorktreeError(
                f"No reciclo {path}: hay trabajo sin guardar.\n- " + "\n- ".join(problems)
                + "\nHaz commit y push (o descártalo tú) y repite.",
                EXIT_BLOCKED,
            )
        head = git_out(path, "rev-parse", "HEAD")
        at_base = head is not None and head == git_out(path, "rev-parse", f"{REMOTE}/{base}")
        if branch is None and at_base and not hard_recreate:
            messages.append(f"{path} ya está limpio en {REMOTE}/{base}.")
        else:
            ok, detail = (False, "--hard-recreate") if hard_recreate else _clean_in_place(path, base)
            if not ok:
                if not hard_recreate:
                    messages.append(f"La limpieza en sitio no fue posible ({detail.splitlines()[0] if detail else '?'}); recreo el worktree.")
                _recreate(layout, path, base)
            messages.append(f"{path} limpio en {REMOTE}/{base}.")
            if branch:
                git(layout.main, "branch", "-D", branch)
                messages.append(f"Rama local {branch} borrada.")
            git(layout.main, "worktree", "prune")
            messages.extend(provision(layout, path, config, install))
        note = _release_backlog(layout, path, branch, agent)
        if note:
            messages.append(note)
        messages.append(update_main(layout, base))
    return messages


# --------------------------------------------------------------------------- guarda


def _strip_quotes(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def _resolve(raw: str, cwd: Path) -> Path:
    expanded = os.path.expanduser(os.path.expandvars(_strip_quotes(raw)))
    path = Path(expanded)
    return Path(os.path.normpath(str(path if path.is_absolute() else cwd / path)))


def _first_word(segment: str) -> str:
    try:
        words = shlex.split(segment, posix=False)
    except ValueError:
        words = segment.split()
    if not words:
        return ""
    word = _strip_quotes(words[0]).lower().replace("\\", "/").rsplit("/", 1)[-1]
    return word[:-4] if word.endswith(".exe") else word


def _git_subcommand(segment: str) -> Optional[str]:
    try:
        words = [_strip_quotes(w) for w in shlex.split(segment, posix=False)]
    except ValueError:
        words = segment.split()
    i = 1
    while i < len(words):
        word = words[i]
        if word in ("-C", "-c", "--git-dir", "--work-tree"):
            i += 2
            continue
        if word.startswith("-") and word not in ("--version",):
            i += 1
            continue
        return word.lower()
    return None


def _is_readonly(segment: str) -> bool:
    word = _first_word(segment)
    if not word:
        return True
    if WRITE_HINTS.search(segment) and word not in ("cd", "set-location", "sl", "pushd", "chdir"):
        return False
    if word == "git":
        sub = _git_subcommand(segment)
        if sub == "branch":
            return bool(re.search(r"\s(--list|-l|-a|-r|-v|-vv|--show-current|--contains)\b", segment)) or segment.strip().endswith("branch")
        if sub == "stash":
            return bool(re.search(r"\sstash\s+(list|show)\b", segment))
        return sub in READONLY_GIT
    return word in READONLY_COMMANDS


def _paths_in(segment: str, cwd: Path) -> List[Path]:
    paths: List[Path] = []
    try:
        words = shlex.split(segment, posix=False)
    except ValueError:
        words = segment.split()
    for word in words[1:]:
        token = _strip_quotes(word)
        for piece in re.split(r"[=,]", token):
            if re.match(r"^([A-Za-z]:[\\/]|/|~|\.\.?[\\/])", piece):
                paths.append(_resolve(piece, cwd))
    return paths


def _deny_reason(agent: str, layout: Layout, target: Path) -> str:
    own = layout.worktrees[agent]
    whose = "el checkout principal de Master" if layout.role(target) == ROLE_MAIN else (
        f"el worktree de {AGENT_LABELS.get(layout.role(target), '?')}"
    )
    return (
        f"{GUARD_TAG} {AGENT_LABELS[agent]} trabaja solo en {own}. {target} es {whose}: no puedes escribir ahí. "
        f"Cambia a tu worktree (cd \"{own}\"); para leer usa Read/Grep. "
        "Gestiona los worktrees solo con agent_worktree.py."
    )


def guard_file(agent: str, cwd: Path, target_raw: str) -> Optional[str]:
    if not target_raw:
        return None
    target = _resolve(target_raw, cwd)
    layout = find_layout(target if target.exists() else target.parent, use_git=False) or find_layout(cwd, use_git=False)
    if layout is None or not layout.active:
        return None
    if any(is_within(target, p) for p in layout.protected_for(agent)):
        return _deny_reason(agent, layout, target)
    return None


def guard_command(agent: str, cwd: Path, command: str) -> Optional[str]:
    if not command.strip():
        return None
    if NATIVE_WORKTREE.search(command):
        return f"{GUARD_TAG} No uses el worktree nativo de Claude Code (--worktree/-w): cada agente tiene su worktree fijo (agent_worktree.py)."
    layout = find_layout(cwd, use_git=False)
    if layout is None or not layout.active:
        return None
    if SELF_SCRIPT.search(command):
        return None
    if WORKTREE_CMD.search(command):
        return f"{GUARD_TAG} No crees ni borres worktrees a mano: usa agent_worktree.py init|recycle."
    protected = layout.protected_for(agent)
    current = cwd
    for segment in SEGMENT_SPLIT.split(command):
        if not segment.strip():
            continue
        cd = CD_TARGET.match(segment.strip())
        if cd:
            current = _resolve(cd.group("path"), current)
            continue
        if _is_readonly(segment):
            continue
        targets = [current]
        match = GIT_C_TARGET.search(segment)
        if match:
            targets = [_resolve(match.group("path"), current)]
        targets += _paths_in(segment, current)
        for target in targets:
            if any(is_within(target, p) for p in protected):
                return _deny_reason(agent, layout, target)
    return None


def guard_payload(agent: str, payload: Dict[str, Any], fmt: str) -> Optional[str]:
    """Interpreta el payload PreToolUse de Claude Code (`claude`) o de Antigravity (`agy`)."""
    if fmt == "agy":
        call = payload.get("toolCall") or {}
        name = str(call.get("name") or payload.get("toolName") or "").lower()
        args = call.get("args") or {}
        cwd = Path(str(args.get("Cwd") or payload.get("cwd") or os.getcwd()))
        command = args.get("CommandLine")
        if command:
            return guard_command(agent, cwd, str(command))
        target = args.get("TargetFile") or args.get("Path") or args.get("AbsolutePath") or args.get("FilePath")
        if target or "write" in name or "edit" in name or "replace" in name:
            return guard_file(agent, cwd, str(target or ""))
        return None
    name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    cwd = Path(str(payload.get("cwd") or os.getcwd()))
    if name == "EnterWorktree":
        return f"{GUARD_TAG} No uses EnterWorktree: trabaja en tu worktree fijo (agent_worktree.py where)."
    if name in ("Bash", "PowerShell"):
        return guard_command(agent, cwd, str(tool_input.get("command") or ""))
    target = tool_input.get("file_path") or tool_input.get("notebook_path") or tool_input.get("path")
    if name in ("Write", "Edit", "MultiEdit", "NotebookEdit") and target:
        return guard_file(agent, cwd, str(target))
    return None


def guard_response(reason: Optional[str], fmt: str) -> Dict[str, Any]:
    if fmt == "agy":
        return {"decision": "deny", "reason": reason} if reason else {"decision": "allow"}
    if not reason:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def session_notice(agent: str, cwd: Path) -> str:
    """Aviso de arranque si la sesión no está en el worktree del agente (vacío si todo está bien)."""
    layout = find_layout(cwd, use_git=False)
    if layout is None or not layout.active:
        return ""
    own = layout.worktrees[agent]
    if layout.role(cwd) == agent:
        return f"Worktree de {AGENT_LABELS[agent]}: {own}. Trabaja solo aquí; el checkout principal {layout.main} es de Master."
    return (
        f"AVISO: esta sesión está en {cwd}, pero {AGENT_LABELS[agent]} solo puede escribir en su worktree {own}. "
        f"Pide a Master que abra la sesión allí o trabaja con cd \"{own}\"."
    )


# --------------------------------------------------------------------------- doctor (DOC-15)


def doctor_findings(start: Path) -> Tuple[str, str, List[str]]:
    """Estado (PASS/WARN/SKIP), mensaje y evidencias del check DOC-15 de los dos doctors."""
    layout = find_layout(start)
    if layout is None:
        return "SKIP", f"{start} no es un repositorio git con checkout principal.", []
    if not layout.active:
        return "SKIP", "Worktrees por agente no activados en este repo (agent_worktree.py init).", []
    base = str(load_config(layout.main).get("base") or DEFAULT_BASE)
    registered = registered_worktrees(layout)
    problems: List[str] = []
    for agent, path in layout.worktrees.items():
        entry = registered.get(norm(path))
        if entry is None:
            problems.append(f"Falta el worktree de {AGENT_LABELS[agent]}: {path}.")
        elif entry.get("branch") == f"refs/heads/{base}":
            problems.append(f"El worktree de {AGENT_LABELS[agent]} tiene {base} en checkout; debe estar desacoplado o en una rama de tarea.")
    main_entry = registered.get(norm(layout.main), {})
    if main_entry.get("detached"):
        problems.append(f"El checkout principal {layout.main} está desacoplado.")
    legacy = layout.main.parent / f"{layout.main.name}.wt"
    if legacy.is_dir():
        problems.append(f"Quedan worktrees por tarea en {legacy} (backlog.py --worktree).")
    if problems:
        return "WARN", problems[0], problems[1:6]
    return "PASS", f"Worktrees de agente correctos: {', '.join(str(p) for p in layout.worktrees.values())}.", []


def init_argv(start: Path) -> Tuple[str, ...]:
    return (sys.executable or "python", str(Path(__file__).resolve()), "--repo", str(start), "init")


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Un git worktree fijo por agente (aagy / aagy-ecc).")
    parser.add_argument("--repo", default=".", help="Cualquier carpeta del repositorio (por defecto, la actual).")
    parser.add_argument("--quiet", action="store_true", help="No imprime nada si no hay nada que hacer.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init", help="Crea los worktrees de los agentes.")
    p.add_argument("--no-install", action="store_true")
    p.add_argument("--no-fetch", action="store_true")
    p = sub.add_parser("where", help="Rol de la carpeta actual.")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("status", help="Estado de los tres checkouts.")
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("recycle", help="Recicla el worktree del agente tras el merge.")
    p.add_argument("--agent", choices=sorted(AGENT_SUFFIXES))
    p.add_argument("--if-merged", action="store_true", help="Sale sin error si la PR aún no está fusionada.")
    p.add_argument("--hard-recreate", action="store_true", help="Borra y recrea el worktree en vez de limpiarlo.")
    p.add_argument("--no-install", action="store_true")
    p.add_argument("--wait", type=int, default=0, help="Segundos a esperar a que la PR se fusione.")
    p = sub.add_parser("guard", help="Hook PreToolUse: lee el payload por stdin.")
    p.add_argument("--agent", required=True, choices=sorted(AGENT_SUFFIXES))
    p.add_argument("--format", choices=("claude", "agy"), default="claude")
    p = sub.add_parser("notice", help="Aviso de arranque de sesión.")
    p.add_argument("--agent", required=True, choices=sorted(AGENT_SUFFIXES))
    return parser


def _read_stdin_json() -> Dict[str, Any]:
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _require_layout(start: Path) -> Layout:
    layout = find_layout(start)
    if layout is None:
        raise WorktreeError(f"{start} no está en un repositorio git con checkout principal normal.")
    return layout


def _cmd_guard(args: argparse.Namespace) -> int:
    try:
        reason = guard_payload(args.agent, _read_stdin_json(), args.format)
    except Exception:  # noqa: BLE001 - una guarda rota no debe bloquear el trabajo (fail-open)
        reason = None
    response = guard_response(reason, args.format)
    if response:
        print(json.dumps(response, ensure_ascii=False))
    return EXIT_OK


def _emit(lines: Sequence[str], quiet: bool) -> None:
    if lines or not quiet:
        for line in lines:
            print(line)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "guard":
        return _cmd_guard(args)
    start = Path(args.repo).resolve()
    try:
        if args.command == "notice":
            payload = _read_stdin_json()
            text = session_notice(args.agent, Path(str(payload.get("cwd") or start)))
            _emit([text] if text else [], True)
            return EXIT_OK
        layout = find_layout(start)
        if layout is None and args.quiet:
            return EXIT_OK
        layout = layout or _require_layout(start)
        if args.command == "recycle" and args.quiet and not layout.active:
            return EXIT_OK  # hooks: repos que no usan worktrees por agente
        if args.command == "init":
            _emit(op_init(layout, install=not args.no_install, fetch=not args.no_fetch), args.quiet)
        elif args.command == "where":
            data = layout.to_dict(start)
            print(json.dumps(data, ensure_ascii=False) if args.json else data["role"])
        elif args.command == "status":
            data = op_status(layout)
            if args.json:
                print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                for key in (ROLE_MAIN, *AGENT_SUFFIXES):
                    item = data[key]
                    state = "no existe" if not item.get("exists") else (
                        f"{item.get('branch') or 'desacoplado'} @ {item.get('head')}, {item.get('dirty')} cambio(s)"
                    )
                    print(f"{key:7} {item['path']}: {state}")
                print("Guarda activa." if data["active"] else "Guarda inactiva (ejecuta init).")
        elif args.command == "recycle":
            agent = resolve_agent(args.agent, layout, start)
            lines = op_recycle(
                layout, agent, if_merged=args.if_merged, hard_recreate=args.hard_recreate,
                install=not args.no_install, wait_s=args.wait,
            )
            _emit(lines, args.quiet)
    except WorktreeError as exc:
        if not (args.quiet and exc.code == EXIT_NO_GH):
            print(f"[agent-worktree] {exc}", file=sys.stderr)
        return exc.code
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
