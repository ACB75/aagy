#!/usr/bin/env python3
"""
Backlog compartido entre agentes (Claude Code / aagy-ecc y Antigravity / aagy).

- Las tareas y épicas se definen en TODO.md (ruta resuelta con docs-map.json).
- El estado vivo (dueño, estado, rama, notas de relevo) vive en
  `$(git rev-parse --git-common-dir)/aagy-backlog/state.json`, común a todos los
  worktrees del repositorio y fuera del control de versiones.
- Un claim caduca tras AAGY_BACKLOG_TTL_HOURS (4 h por defecto) sin actualizar.

Ver doc/04-operations/runbooks/MANUAL_shared_backlog.md.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from docs_map import DOCS_MAP_REL, resolve_doc_path  # noqa: E402

logger = logging.getLogger("backlog")

AGENTS: Tuple[str, ...] = ("claude", "agy", "human")
ST_TODO = "todo"
ST_IN_PROGRESS = "in_progress"
ST_REVIEW = "review"
ST_HANDOFF = "handoff"
ST_BLOCKED = "blocked"
ST_DONE = "done"
ACTIVE_STATES = (ST_IN_PROGRESS, ST_REVIEW)
DEFAULT_TTL_HOURS = 4.0
LOCK_STALE_SECONDS = 60.0
LOCK_WAIT_SECONDS = 10.0
BRIEF_MAX_LINES = 15
HISTORY_MAX = 20
STATE_DIR_NAME = "aagy-backlog"
STATE_FILE_NAME = "state.json"
LOCK_FILE_NAME = "state.lock"
WORKTREE_SUFFIX = ".wt"
ENV_AGENT = "AAGY_AGENT"
ENV_TTL = "AAGY_BACKLOG_TTL_HOURS"
ENCODING = "utf-8"
K_UPDATED = "updated"
K_WORKTREE = "worktree"
GIT_REV_PARSE = "rev-parse"
OPT_FORCE = "--force"
CMD_GH_SYNC = "gh-sync"

ID_REGEX = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ID_MAX = 64
TASK_LINE = re.compile(r"^[-*]\s*\[(?P<mark>[ xX])\]\s*(?P<title>.+?)\s*$")
EPIC_HEADER = re.compile(r"^##\s+(?:Épica|Epica|Epic)\s*:\s*(?P<title>.+?)\s*$", re.IGNORECASE)
SECTION_HEADER = re.compile(r"^#{1,2}\s+")
META_COMMENT = re.compile(r"<!--\s*aagy-task:(?P<body>[^>]*)-->")
META_PAIR = re.compile(r"([a-z_]+)=([^\s]+)")
TITLE_PREFIX = re.compile(r"^(?:\*\*)?(?:Tarea\s*:\s*)?", re.IGNORECASE)
GH_ID_RE = re.compile(r"^gh-(\d+)(?:-|$)")
GH_REF_RE = re.compile(r"(?:GH\s*#|issues/)(\d+)", re.IGNORECASE)


class BacklogError(Exception):
    """Error de uso o de estado; el CLI lo muestra y sale con código 1."""


# --------------------------------------------------------------------------- utilidades


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None
    try:
        return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def ttl_hours() -> float:
    raw = os.environ.get(ENV_TTL, "")
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_TTL_HOURS
    return value if value > 0 else DEFAULT_TTL_HOURS


def slugify(text: str) -> str:
    clean = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    clean = re.sub(r"[*_`#]+", "", clean)
    clean = unicodedata.normalize("NFKD", clean).encode("ascii", "ignore").decode("ascii").lower()
    slug = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    slug = slug[:ID_MAX].rstrip("-")
    return slug or "tarea"


def validate_id(task_id: str) -> str:
    cleaned = (task_id or "").strip()
    if len(cleaned) > ID_MAX or not ID_REGEX.match(cleaned):
        raise BacklogError(f"Identificador no válido: {task_id!r} (usa minúsculas, dígitos y guiones, máx. {ID_MAX}).")
    return cleaned


def validate_agent(agent: Optional[str]) -> str:
    value = (agent or os.environ.get(ENV_AGENT, "")).strip().lower()
    if value not in AGENTS:
        raise BacklogError(f"Indica el agente con --agent ({'|'.join(AGENTS)}) o la variable {ENV_AGENT}.")
    return value


def run_git(cwd: Path, *args: str) -> Optional[str]:
    try:
        proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=False, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def run_gh(cwd: Path, *args: str) -> Optional[str]:
    try:
        proc = subprocess.run(["gh", *args], cwd=str(cwd), capture_output=True, text=True, check=False, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


# --------------------------------------------------------------------------- modelo


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str
    epic: Optional[str]
    done_mark: bool
    line_no: int
    issue: Optional[int] = None


@dataclass(frozen=True)
class Epic:
    epic_id: str
    title: str
    line_no: int


@dataclass(frozen=True)
class Backlog:
    tasks: Tuple[Task, ...]
    epics: Tuple[Epic, ...]

    def find(self, task_id: str) -> Task:
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        raise BacklogError(f"No existe la tarea '{task_id}' en TODO.md.")


def clean_title(raw: str) -> str:
    title = META_COMMENT.sub("", raw).strip()
    title = TITLE_PREFIX.sub("", title)
    return title.replace("**", "").strip()


def _meta_from(lines: Sequence[str], start: int) -> Dict[str, str]:
    """Lee el comentario aagy-task de la línea de tarea o de su cuerpo indentado."""
    meta: Dict[str, str] = {}
    idx = start
    while idx < len(lines):
        line = lines[idx]
        if idx > start and (not line.startswith((" ", "\t")) and line.strip()):
            break
        match = META_COMMENT.search(line)
        if match:
            meta.update(dict(META_PAIR.findall(match.group("body"))))
            break
        idx += 1
    return meta


def _extract_issue(meta: Dict[str, str], task_id: str, title: str) -> Optional[int]:
    raw = meta.get("issue", "")
    if raw.isdigit():
        return int(raw)
    m_id = GH_ID_RE.match(task_id)
    if m_id:
        return int(m_id.group(1))
    m_ref = GH_REF_RE.search(title)
    return int(m_ref.group(1)) if m_ref else None


def parse_backlog(text: str) -> Backlog:
    lines = text.splitlines()
    tasks: List[Task] = []
    epics: List[Epic] = []
    current_epic: Optional[str] = None
    seen: Dict[str, int] = {}
    for idx, line in enumerate(lines):
        epic_match = EPIC_HEADER.match(line)
        if epic_match:
            title = epic_match.group("title").strip()
            current_epic = slugify(title)
            epics.append(Epic(epic_id=current_epic, title=title, line_no=idx))
            continue
        if SECTION_HEADER.match(line):
            current_epic = None
            continue
        task_match = TASK_LINE.match(line)
        if not task_match:
            continue
        meta = _meta_from(lines, idx)
        title = clean_title(task_match.group("title"))
        base_id = meta.get("id") or slugify(title)
        count = seen.get(base_id, 0) + 1
        seen[base_id] = count
        task_id = base_id if count == 1 else f"{base_id}-{count}"
        tasks.append(
            Task(
                task_id=task_id,
                title=title,
                epic=meta.get("epic") or current_epic,
                done_mark=task_match.group("mark").lower() == "x",
                line_no=idx,
                issue=_extract_issue(meta, task_id, title),
            )
        )
    return Backlog(tasks=tuple(tasks), epics=tuple(epics))


# --------------------------------------------------------------------------- repositorio y estado


@dataclass(frozen=True)
class Repo:
    root: Path
    state_dir: Path
    is_git: bool

    @property
    def todo_path(self) -> Path:
        return resolve_doc_path(self.root, "todo")

    @property
    def quick_dir(self) -> Path:
        return resolve_doc_path(self.root, "quick")

    @property
    def done_dir(self) -> Path:
        return resolve_doc_path(self.root, "todo_done")


def locate_repo(start: Path) -> Repo:
    start = start.resolve()
    top = run_git(start, GIT_REV_PARSE, "--show-toplevel")
    if top is None:
        return Repo(root=start, state_dir=start / ".aagy-backlog", is_git=False)
    root = Path(top).resolve()
    common = run_git(root, GIT_REV_PARSE, "--git-common-dir") or ".git"
    common_path = Path(common)
    if not common_path.is_absolute():
        common_path = (root / common_path).resolve()
    return Repo(root=root, state_dir=common_path / STATE_DIR_NAME, is_git=True)


def load_state(repo: Repo) -> Dict[str, Any]:
    path = repo.state_dir / STATE_FILE_NAME
    try:
        data = json.loads(path.read_text(encoding=ENCODING))
    except (OSError, ValueError):
        return {"version": 1, "tasks": {}}
    if not isinstance(data, dict) or not isinstance(data.get("tasks"), dict):
        return {"version": 1, "tasks": {}}
    return data


def save_state(repo: Repo, state: Dict[str, Any]) -> None:
    repo.state_dir.mkdir(parents=True, exist_ok=True)
    path = repo.state_dir / STATE_FILE_NAME
    tmp = path.with_suffix(f".tmp{os.getpid()}")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding=ENCODING)
    os.replace(tmp, path)


@contextmanager
def state_lock(repo: Repo) -> Iterator[None]:
    """Lock exclusivo por fichero (O_EXCL), portable a Windows y Linux."""
    repo.state_dir.mkdir(parents=True, exist_ok=True)
    lock = repo.state_dir / LOCK_FILE_NAME
    deadline = time.monotonic() + LOCK_WAIT_SECONDS
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, f"{os.getpid()} {iso(utc_now())}".encode(ENCODING))
            os.close(fd)
            break
        except FileExistsError:
            _break_stale_lock(lock)
            if time.monotonic() > deadline:
                raise BacklogError(f"El backlog está bloqueado por otro proceso ({lock}).")
            time.sleep(0.05)
    try:
        yield
    finally:
        _remove_quietly(lock)


def _break_stale_lock(lock: Path) -> None:
    try:
        age = time.time() - lock.stat().st_mtime
    except OSError:
        return
    if age > LOCK_STALE_SECONDS:
        _remove_quietly(lock)


def _remove_quietly(path: Path) -> None:
    """Borra un fichero; si ya no existe o no se puede, lo registra y sigue (otro proceso pudo borrarlo)."""
    try:
        path.unlink()
    except OSError as exc:
        logger.debug("No se pudo borrar %s: %s", path, exc)


# --------------------------------------------------------------------------- reglas de estado


def entry_for(state: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    entry = state["tasks"].get(task_id)
    if not isinstance(entry, dict):
        entry = {"status": ST_TODO}
        state["tasks"][task_id] = entry
    return entry


def is_stale(entry: Dict[str, Any], now: Optional[datetime] = None) -> bool:
    if entry.get("status") not in ACTIVE_STATES:
        return False
    updated = parse_iso(entry.get(K_UPDATED))
    if updated is None:
        return True
    return (now or utc_now()) - updated > timedelta(hours=ttl_hours())


def effective_status(task: Task, state: Dict[str, Any]) -> str:
    if task.done_mark:
        return ST_DONE
    entry = state["tasks"].get(task.task_id) or {}
    return entry.get("status", ST_TODO)


def is_available(task: Task, state: Dict[str, Any], agent: str) -> bool:
    status = effective_status(task, state)
    entry = state["tasks"].get(task.task_id) or {}
    if status in (ST_TODO, ST_HANDOFF):
        return True
    if status in ACTIVE_STATES:
        return entry.get("owner") == agent or is_stale(entry)
    return False


def record(entry: Dict[str, Any], agent: str, action: str, note: Optional[str] = None) -> None:
    now = iso(utc_now())
    entry[K_UPDATED] = now
    history = entry.setdefault("history", [])
    item = {"at": now, "agent": agent, "action": action}
    if note:
        item["note"] = note
    history.append(item)
    del history[:-HISTORY_MAX]


def apply_snapshot(entry: Dict[str, Any], cwd: Path) -> None:
    """Guarda el estado git; si el agente trabaja en otra rama de tarea, esa pasa a ser la rama de la tarea."""
    snap = git_snapshot(cwd)
    entry.update(snap)
    current = snap.get("current_branch")
    if current and current not in ("main", "master", "HEAD"):
        entry["branch"] = current


def git_snapshot(cwd: Path) -> Dict[str, Any]:
    branch = run_git(cwd, GIT_REV_PARSE, "--abbrev-ref", "HEAD")
    head = run_git(cwd, "log", "-1", "--format=%h %s")
    porcelain = run_git(cwd, "status", "--porcelain") or ""
    dirty = [line[3:] for line in porcelain.splitlines() if len(line) > 3][:30]
    snap: Dict[str, Any] = {"dirty": dirty}
    if branch:
        snap["current_branch"] = branch
    if head:
        snap["head"] = head
    return snap


# --------------------------------------------------------------------------- operaciones


@dataclass
class Context:
    repo: Repo
    cwd: Path

    def backlog(self) -> Backlog:
        path = self.repo.todo_path
        if not path.is_file():
            raise BacklogError(f"No existe {path}. Ejecuta 'backlog.py init' primero.")
        return parse_backlog(path.read_text(encoding=ENCODING))


def op_init(ctx: Context) -> List[str]:
    root = ctx.repo.root
    created: List[str] = []
    docs_map = root / DOCS_MAP_REL
    legacy_todo = root / "doc" / "TODO.md"
    if not docs_map.exists() and not legacy_todo.exists():
        docs_map.parent.mkdir(parents=True, exist_ok=True)
        docs_map.write_text(json.dumps({"schema_version": 2}, indent=2) + "\n", encoding=ENCODING)
        created.append(DOCS_MAP_REL)
    for key in ("quick", "todo_done", "plans"):
        folder = resolve_doc_path(root, key)
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            created.append(str(folder.relative_to(root)))
    todo = ctx.repo.todo_path
    if not todo.exists():
        todo.parent.mkdir(parents=True, exist_ok=True)
        todo.write_text("# Backlog\n\n## 1. Backlog Activo\n", encoding=ENCODING)
        created.append(str(todo.relative_to(root)))
    return created or ["Nada que crear: el backlog ya existe."]


def _status_label(task: Task, state: Dict[str, Any]) -> str:
    status = effective_status(task, state)
    entry = state["tasks"].get(task.task_id) or {}
    owner = entry.get("owner")
    label = status
    if owner and status != ST_TODO:
        label += f" ({owner})"
    if is_stale(entry):
        label += " [caducada]"
    return label


def op_list(ctx: Context, epic: Optional[str], agent: Optional[str], include_done: bool) -> List[Dict[str, Any]]:
    backlog = ctx.backlog()
    state = load_state(ctx.repo)
    rows: List[Dict[str, Any]] = []
    for task in backlog.tasks:
        if epic and task.epic != epic:
            continue
        status = effective_status(task, state)
        if status == ST_DONE and not include_done:
            continue
        entry = state["tasks"].get(task.task_id) or {}
        if agent and entry.get("owner") != agent:
            continue
        rows.append(
            {
                "id": task.task_id,
                "title": task.title,
                "epic": task.epic,
                "issue": task.issue,
                "status": status,
                "label": _status_label(task, state),
                "owner": entry.get("owner"),
                "branch": entry.get("branch"),
                K_WORKTREE: entry.get(K_WORKTREE),
                K_UPDATED: entry.get(K_UPDATED),
                "note": entry.get("note"),
                "stale": is_stale(entry),
            }
        )
    return rows


def brief_lines(ctx: Context) -> List[str]:
    """Resumen corto (≤ 15 líneas) para hooks de arranque de sesión."""
    try:
        rows = op_list(ctx, epic=None, agent=None, include_done=False)
    except BacklogError:
        return []
    priority = {ST_HANDOFF: 0, ST_IN_PROGRESS: 1, ST_REVIEW: 2, ST_BLOCKED: 3}
    active = sorted((r for r in rows if r["status"] in priority), key=lambda r: priority[r["status"]])
    pending = sum(1 for r in rows if r["status"] == ST_TODO)
    if not active and not pending:
        return []
    lines = [f"Backlog compartido ({ctx.repo.todo_path.name}): {len(active)} activas, {pending} pendientes."]
    for row in active[: BRIEF_MAX_LINES - 2]:
        extra = f" rama {row['branch']}" if row.get("branch") else ""
        lines.append(f"- [{row['label']}] {row['id']}: {row['title'][:70]}{extra}")
    lines.append("Gestiona tareas con scripts/py/backlog.py (list, next, claim, checkpoint, handoff, done).")
    return lines[:BRIEF_MAX_LINES]


def op_next(ctx: Context, agent: str, epic: Optional[str]) -> Optional[Task]:
    backlog = ctx.backlog()
    state = load_state(ctx.repo)
    candidates = [t for t in backlog.tasks if (not epic or t.epic == epic) and is_available(t, state, agent)]
    handoffs = [t for t in candidates if effective_status(t, state) == ST_HANDOFF]
    ordered = handoffs + [t for t in candidates if t not in handoffs]
    return ordered[0] if ordered else None


def default_branch(repo: Repo, task_id: str) -> str:
    project = slugify(repo.root.name.split(WORKTREE_SUFFIX)[0]) or "repo"
    return f"feat/{project}/{task_id}"


def worktree_path(repo: Repo, task_id: str) -> Path:
    main_root = repo.state_dir.parent.parent if repo.state_dir.parent.name == ".git" else repo.root
    return main_root.parent / f"{main_root.name}{WORKTREE_SUFFIX}" / task_id


def _ensure_worktree(repo: Repo, task_id: str, branch: str) -> Path:
    if not repo.is_git:
        raise BacklogError("--worktree necesita un repositorio git.")
    path = worktree_path(repo, task_id)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = run_git(repo.root, GIT_REV_PARSE, "--verify", "--quiet", f"refs/heads/{branch}") is not None
    args = [K_WORKTREE, "add", str(path), branch] if exists else [K_WORKTREE, "add", "-b", branch, str(path)]
    if run_git(repo.root, *args) is None:
        raise BacklogError(f"No se pudo crear el worktree {path} en la rama {branch}.")
    return path


def op_claim(
    ctx: Context, task_id: str, agent: str, branch: Optional[str], worktree: bool, force: bool
) -> Dict[str, Any]:
    task = ctx.backlog().find(validate_id(task_id))
    with state_lock(ctx.repo):
        state = load_state(ctx.repo)
        entry = entry_for(state, task.task_id)
        status = effective_status(task, state)
        if status == ST_DONE:
            raise BacklogError(f"La tarea '{task.task_id}' ya está terminada.")
        if not force and not is_available(task, state, agent):
            owner = entry.get("owner", "?")
            raise BacklogError(
                f"La tarea '{task.task_id}' la tiene {owner} ({status}, actualizada {entry.get(K_UPDATED)}). "
                f"Caduca a las {ttl_hours():g} h sin actualizar."
            )
        previous = entry.get("owner")
        target_branch = branch or entry.get("branch") or default_branch(ctx.repo, task.task_id)
        if worktree:
            entry[K_WORKTREE] = str(_ensure_worktree(ctx.repo, task.task_id, target_branch))
        entry.update({"status": ST_IN_PROGRESS, "owner": agent, "branch": target_branch})
        note = f"relevo desde {previous}" if previous and previous != agent else None
        record(entry, agent, "claim", note)
        save_state(ctx.repo, state)
        return dict(entry, id=task.task_id, title=task.title, previous_owner=previous)


def _owned(state: Dict[str, Any], agent: str, task_id: Optional[str]) -> List[str]:
    if task_id:
        entry = state["tasks"].get(task_id) or {}
        if entry.get("owner") != agent or entry.get("status") not in ACTIVE_STATES + (ST_BLOCKED,):
            raise BacklogError(f"La tarea '{task_id}' no está en curso por {agent}.")
        return [task_id]
    return [
        tid for tid, entry in state["tasks"].items()
        if entry.get("owner") == agent and entry.get("status") in ACTIVE_STATES
    ]


def op_checkpoint(ctx: Context, agent: str, task_id: Optional[str], note: Optional[str]) -> List[str]:
    with state_lock(ctx.repo):
        state = load_state(ctx.repo)
        ids = _owned(state, agent, validate_id(task_id) if task_id else None)
        for tid in ids:
            entry = state["tasks"][tid]
            cwd = Path(entry[K_WORKTREE]) if entry.get(K_WORKTREE) and Path(entry[K_WORKTREE]).is_dir() else ctx.cwd
            apply_snapshot(entry, cwd)
            if note:
                entry["note"] = note
            entry[K_UPDATED] = iso(utc_now())
        if ids:
            save_state(ctx.repo, state)
        return ids


def _auto_note(entry: Dict[str, Any]) -> str:
    previous = entry.get("note") or "sin nota de progreso"
    return f"Relevo automático (fin de sesión). Última nota: {previous}"


def write_handoff_file(ctx: Context, task: Task, entry: Dict[str, Any], agent: str, note: str) -> Path:
    folder = ctx.repo.quick_dir
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"HANDOFF_{task.task_id}.md"
    dirty = entry.get("dirty") or []
    lines = [
        f"# Relevo: {task.title}",
        "",
        f"- **Tarea**: `{task.task_id}`" + (f" (épica `{task.epic}`)" if task.epic else ""),
        f"- **De**: `{agent}` | **Fecha**: `{entry.get(K_UPDATED)}`",
        f"- **Rama de la tarea**: `{entry.get('branch', '-')}` (rama activa al salir: `{entry.get('current_branch', '-')}`)",
        f"- **Último commit**: `{entry.get('head', '-')}`",
    ]
    if entry.get(K_WORKTREE):
        lines.append(f"- **Worktree**: `{entry[K_WORKTREE]}`")
    lines += ["", "## Estado y siguiente paso", "", note, ""]
    if dirty:
        lines += ["## Ficheros sin commit", ""] + [f"- `{item}`" for item in dirty] + [""]
    lines += [
        "## Para continuar",
        "",
        "```bash",
        f"python scripts/py/backlog.py claim {task.task_id} --agent <claude|agy>",
        "```",
        "",
    ]
    path.write_text("\n".join(lines), encoding=ENCODING)
    return path


def op_handoff(
    ctx: Context, agent: str, task_id: Optional[str], note: Optional[str], to: Optional[str]
) -> List[Tuple[str, Path]]:
    backlog = ctx.backlog()
    results: List[Tuple[str, Path]] = []
    with state_lock(ctx.repo):
        state = load_state(ctx.repo)
        ids = _owned(state, agent, validate_id(task_id) if task_id else None)
        for tid in ids:
            task = backlog.find(tid)
            entry = state["tasks"][tid]
            cwd = Path(entry[K_WORKTREE]) if entry.get(K_WORKTREE) and Path(entry[K_WORKTREE]).is_dir() else ctx.cwd
            apply_snapshot(entry, cwd)
            text = note or _auto_note(entry)
            entry.update({"status": ST_HANDOFF, "note": text})
            if to:
                entry["handoff_to"] = to
            record(entry, agent, ST_HANDOFF, text)
            results.append((tid, write_handoff_file(ctx, task, entry, agent, text)))
        if ids:
            save_state(ctx.repo, state)
    return results


def op_transition(ctx: Context, task_id: str, agent: str, status: str, note: Optional[str], force: bool) -> None:
    task = ctx.backlog().find(validate_id(task_id))
    with state_lock(ctx.repo):
        state = load_state(ctx.repo)
        entry = entry_for(state, task.task_id)
        owner = entry.get("owner")
        if owner and owner != agent and not force and not is_stale(entry):
            raise BacklogError(f"La tarea '{task.task_id}' es de {owner}; usa --force si eres Master.")
        entry["status"] = status
        if status == ST_TODO:
            entry.pop("owner", None)
        else:
            entry["owner"] = agent
        if note:
            entry["note"] = note
        record(entry, agent, status, note)
        save_state(ctx.repo, state)


def mark_done_in_todo(path: Path, task: Task) -> None:
    lines = path.read_text(encoding=ENCODING).splitlines()
    line = lines[task.line_no]
    lines[task.line_no] = re.sub(r"\[\s\]", "[x]", line, count=1)
    path.write_text("\n".join(lines) + "\n", encoding=ENCODING)


def op_done(ctx: Context, task_id: str, agent: str, note: Optional[str], archive: bool, force: bool) -> List[str]:
    task = ctx.backlog().find(validate_id(task_id))
    op_transition(ctx, task.task_id, agent, ST_DONE, note, force)
    messages: List[str] = []
    if not task.done_mark:
        mark_done_in_todo(ctx.repo.todo_path, task)
        messages.append(f"Marcada como [x] en {ctx.repo.todo_path.name}.")
    if archive:
        import archive_todo  # noqa: PLC0415 - import diferido: solo se necesita al archivar

        archive_todo.process_archive(
            ctx.repo.todo_path, done_dir=ctx.repo.done_dir, target_title=task.title, notes=note
        )
        messages.append(f"Archivada en {ctx.repo.done_dir}.")
    handoff = ctx.repo.quick_dir / f"HANDOFF_{task.task_id}.md"
    if handoff.exists():
        handoff.unlink()
    messages.extend(_cleanup_worktree(ctx, task.task_id))
    return messages


def _cleanup_worktree(ctx: Context, task_id: str) -> List[str]:
    entry = load_state(ctx.repo)["tasks"].get(task_id) or {}
    path = entry.get(K_WORKTREE)
    if not path or not Path(path).is_dir():
        return []
    if run_git(ctx.repo.root, K_WORKTREE, "remove", path) is None:
        return [f"El worktree {path} tiene cambios sin commit; no se ha borrado."]
    return [f"Worktree {path} eliminado."]


# --------------------------------------------------------------------------- épicas y alta de tareas


def _insert_after_section(text: str, block: str) -> str:
    match = re.search(r"^##\s*1\..*$", text, re.MULTILINE)
    if match:
        idx = match.end()
        return text[:idx] + "\n\n" + block.rstrip() + "\n" + text[idx:]
    return text.rstrip() + "\n\n" + block.rstrip() + "\n"


def task_block(
    title: str,
    task_id: str,
    epic: Optional[str],
    detail: Optional[str],
    issue: Optional[int] = None,
) -> str:
    meta = f"id={task_id}" + (f" epic={epic}" if epic else "") + (f" issue={issue}" if issue else "")
    lines = [f"- [ ] **{title}**", f"  <!-- aagy-task: {meta} -->"]
    if detail:
        lines.extend(f"  {line}" if line.strip() else "" for line in detail.splitlines())
    return "\n".join(lines)


def op_add(
    ctx: Context,
    title: str,
    epic: Optional[str],
    task_id: Optional[str],
    detail: Optional[str],
    issue: Optional[int] = None,
) -> str:
    path = ctx.repo.todo_path
    text = path.read_text(encoding=ENCODING) if path.exists() else "# Backlog\n\n## 1. Backlog Activo\n"
    backlog = parse_backlog(text)
    new_id = validate_id(task_id) if task_id else slugify(title)
    if any(t.task_id == new_id for t in backlog.tasks):
        raise BacklogError(f"Ya existe una tarea con id '{new_id}'.")
    block = task_block(title.strip(), new_id, epic, detail, issue=issue)
    if epic:
        text = _insert_in_epic(text, backlog, validate_id(epic), block)
    else:
        text = _insert_after_section(text, block)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding=ENCODING)
    return new_id


def link_task_issue(todo_path: Path, task: Task, issue_number: int) -> None:
    """Enlaza una tarea existente de TODO.md con un número de GitHub Issue (#N)."""
    lines = todo_path.read_text(encoding=ENCODING).splitlines()
    idx = task.line_no + 1
    while idx < len(lines):
        line = lines[idx]
        if not line.startswith((" ", "\t")) and line.strip():
            break
        match = META_COMMENT.search(line)
        if match:
            body = match.group("body").strip()
            updated = re.sub(r"\bissue=\d+", f"issue={issue_number}", body)
            if f"issue={issue_number}" not in updated:
                updated = f"{updated} issue={issue_number}"
            lines[idx] = f"  <!-- aagy-task: {updated} -->"
            todo_path.write_text("\n".join(lines) + "\n", encoding=ENCODING)
            return
        idx += 1
    meta = f"id={task.task_id}" + (f" epic={task.epic}" if task.epic else "") + f" issue={issue_number}"
    lines.insert(task.line_no + 1, f"  <!-- aagy-task: {meta} -->")
    todo_path.write_text("\n".join(lines) + "\n", encoding=ENCODING)


def sync_gh_claim(cwd: Path, issue_number: Optional[int], agent: str, branch: str) -> bool:
    """Actualiza la GitHub Issue vinculada al hacer claim en el backlog compartido."""
    if not issue_number:
        return False
    num_str = str(issue_number)
    run_gh(cwd, "issue", "edit", num_str, "--add-assignee", "@me")
    run_gh(
        cwd,
        "issue",
        "comment",
        num_str,
        "--body",
        f"Reclamada en backlog compartido (`TODO.md`) por `{agent}` en rama `{branch}`.",
    )
    return True


def sync_gh_done(cwd: Path, issue_number: Optional[int], agent: str, note: Optional[str]) -> bool:
    """Cierra y comenta la GitHub Issue vinculada al completar una tarea del backlog compartido."""
    if not issue_number:
        return False
    comment = f"Completada en backlog compartido (`TODO.md`) por `{agent}`."
    if note:
        comment += f" Nota: {note}"
    run_gh(cwd, "issue", "close", str(issue_number), "--comment", comment)
    return True


def _fetch_gh_issues(cwd: Path) -> List[Dict[str, Any]]:
    raw = run_gh(cwd, "issue", "list", "--state", "all", "--limit", "100", "--json", "number,title,state,url")
    if not raw:
        return []
    try:
        data = json.loads(raw)
    except ValueError:
        return []
    return data if isinstance(data, list) else []


def _create_gh_issue_for_task(ctx: Context, task: Task) -> Optional[int]:
    body = f"Tarea sincronizada desde `{ctx.repo.todo_path.name}` (id: `{task.task_id}`)."
    out = run_gh(ctx.cwd, "issue", "create", "--title", task.title, "--body", body, "--label", "enhancement,harness:both")
    if not out:
        return None
    match = re.search(r"/issues/(\d+)", out)
    if not match:
        return None
    issue_num = int(match.group(1))
    link_task_issue(ctx.repo.todo_path, task, issue_num)
    return issue_num


def _sync_close_done(ctx: Context, by_num: Dict[int, Dict[str, Any]]) -> List[int]:
    closed: List[int] = []
    state = load_state(ctx.repo)
    for task in ctx.backlog().tasks:
        if not task.issue:
            continue
        remote = by_num.get(task.issue)
        status = effective_status(task, state)
        if status == ST_DONE and (not remote or str(remote.get("state", "")).upper() == "OPEN"):
            run_gh(ctx.cwd, "issue", "close", str(task.issue), "--comment", "Cerrada automáticamente desde TODO.md.")
            closed.append(task.issue)
        elif remote and str(remote.get("state", "")).upper() == "CLOSED" and not task.done_mark:
            mark_done_in_todo(ctx.repo.todo_path, task)
            closed.append(task.issue)
    return closed


def _sync_create_missing(ctx: Context) -> List[int]:
    created: List[int] = []
    while True:
        unlinked = next((t for t in ctx.backlog().tasks if not t.done_mark and not t.issue), None)
        if unlinked is None:
            break
        issue_num = _create_gh_issue_for_task(ctx, unlinked)
        if issue_num is None:
            break
        created.append(issue_num)
    return created


def _sync_import_open(
    ctx: Context,
    gh_issues: Sequence[Dict[str, Any]],
    epic: Optional[str],
) -> List[str]:
    imported: List[str] = []
    existing_issues = {t.issue for t in ctx.backlog().tasks if t.issue}
    existing_ids = {t.task_id for t in ctx.backlog().tasks}
    for item in gh_issues:
        if str(item.get("state", "")).upper() != "OPEN":
            continue
        num = int(item.get("number") or 0)
        if num <= 0 or num in existing_issues:
            continue
        tid = f"gh-{num}"
        if tid in existing_ids:
            continue
        title = str(item.get("title") or f"GitHub Issue #{num}").strip()
        url = str(item.get("url") or "").strip()
        detail = f"GitHub Issue: <{url}>" if url else None
        op_add(ctx, title, epic, tid, detail, issue=num)
        imported.append(tid)
        existing_issues.add(num)
        existing_ids.add(tid)
    return imported


def op_gh_sync(
    ctx: Context,
    create_missing: bool = False,
    close_done: bool = False,
    import_open: bool = False,
    epic: Optional[str] = None,
) -> Dict[str, Any]:
    """Sincroniza bidireccionalmente tareas de TODO.md con GitHub Issues (#N)."""
    gh_issues = _fetch_gh_issues(ctx.cwd)
    by_num = {int(item["number"]): item for item in gh_issues if item.get("number")}
    closed = _sync_close_done(ctx, by_num) if close_done else []
    created = _sync_create_missing(ctx) if create_missing else []
    imported = _sync_import_open(ctx, gh_issues, epic) if import_open else []
    linked = [t.issue for t in ctx.backlog().tasks if t.issue]
    return {"linked": linked, "created": created, "closed": closed, "imported": imported}


def _insert_in_epic(text: str, backlog: Backlog, epic_id: str, block: str) -> str:
    epic = next((e for e in backlog.epics if e.epic_id == epic_id), None)
    if epic is None:
        raise BacklogError(f"No existe la épica '{epic_id}'. Créala con 'epic add'.")
    lines = text.splitlines()
    end = len(lines)
    for idx in range(epic.line_no + 1, len(lines)):
        if SECTION_HEADER.match(lines[idx]):
            end = idx
            break
    while end > epic.line_no + 1 and not lines[end - 1].strip():
        end -= 1
    new_lines = lines[:end] + [""] + block.splitlines() + [""] + lines[end:]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(new_lines)).rstrip() + "\n"


def op_epic_add(ctx: Context, title: str, objective: Optional[str]) -> str:
    path = ctx.repo.todo_path
    text = path.read_text(encoding=ENCODING) if path.exists() else "# Backlog\n\n## 1. Backlog Activo\n"
    epic_id = slugify(title)
    if any(e.epic_id == epic_id for e in parse_backlog(text).epics):
        raise BacklogError(f"Ya existe la épica '{epic_id}'.")
    block = f"## Épica: {title.strip()}\n"
    if objective:
        block += f"\n> {objective.strip()}\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n\n" + block, encoding=ENCODING)
    return epic_id


def op_epic_sync(ctx: Context, epic: Optional[str]) -> List[Dict[str, Any]]:
    backlog = ctx.backlog()
    state = load_state(ctx.repo)
    summary: List[Dict[str, Any]] = []
    for item in backlog.epics:
        if epic and item.epic_id != epic:
            continue
        tasks = [t for t in backlog.tasks if t.epic == item.epic_id]
        counts: Dict[str, int] = {}
        for task in tasks:
            status = effective_status(task, state)
            counts[status] = counts.get(status, 0) + 1
        summary.append(
            {
                "id": item.epic_id,
                "title": item.title,
                "total": len(tasks),
                "counts": counts,
                "tasks": [(t.task_id, _status_label(t, state)) for t in tasks],
            }
        )
    return summary


def op_epic_close(ctx: Context, epic_id: str, agent: str) -> List[str]:
    epic_id = validate_id(epic_id)
    summary = op_epic_sync(ctx, epic_id)
    if not summary:
        raise BacklogError(f"No existe la épica '{epic_id}'.")
    pending = [tid for tid, label in summary[0]["tasks"] if not label.startswith(ST_DONE)]
    if pending:
        raise BacklogError(f"La épica '{epic_id}' tiene tareas sin terminar: {', '.join(pending)}.")
    backlog = ctx.backlog()
    path = ctx.repo.todo_path
    lines = path.read_text(encoding=ENCODING).splitlines()
    epic = next(e for e in backlog.epics if e.epic_id == epic_id)
    lines[epic.line_no] = f"{lines[epic.line_no]} (cerrada {utc_now().date().isoformat()} por {agent})"
    path.write_text("\n".join(lines) + "\n", encoding=ENCODING)
    return [f"Épica '{epic_id}' cerrada ({summary[0]['total']} tareas)."]


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backlog compartido entre Claude Code y Antigravity.")
    parser.add_argument("--repo", type=Path, default=Path("."), help="Carpeta del repositorio (por defecto, la actual).")
    parser.add_argument("--json", action="store_true", help="Salida JSON.")
    parser.add_argument("--quiet", action="store_true", help="Sin salida (para hooks).")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def with_agent(p: argparse.ArgumentParser) -> argparse.ArgumentParser:
        p.add_argument("--agent", choices=AGENTS, default=None, help=f"Agente ({ENV_AGENT} si falta).")
        return p

    sub.add_parser("init", help="Crea doc/06-backlog/ y docs-map.json si faltan.")
    p = with_agent(sub.add_parser("list", help="Lista tareas con estado y dueño."))
    p.add_argument("--epic")
    p.add_argument("--mine", action="store_true")
    p.add_argument("--all", action="store_true", help="Incluye terminadas.")
    p.add_argument("--brief", action="store_true", help="Resumen corto para arranque de sesión.")
    p = with_agent(sub.add_parser("next", help="Siguiente tarea libre (los relevos primero)."))
    p.add_argument("--epic")
    p.add_argument("--claim", action="store_true", help="Reclamarla directamente.")
    p.add_argument("--worktree", action="store_true")
    p = with_agent(sub.add_parser("claim", help="Reclama una tarea."))
    p.add_argument("id")
    p.add_argument("--branch")
    p.add_argument("--worktree", action="store_true", help="Crea un git worktree propio (modo simultáneo).")
    p.add_argument("--gh", action="store_true", help="Sincroniza asignación/comentario con la GitHub Issue vinculada.")
    p.add_argument(OPT_FORCE, action="store_true")
    p = with_agent(sub.add_parser("checkpoint", help="Guarda rama, commit, ficheros y nota de la tarea en curso."))
    p.add_argument("--id")
    p.add_argument("--note")
    p.add_argument("--auto", action="store_true", help="No falla si no hay backlog o tarea (hooks).")
    p = with_agent(sub.add_parser(ST_HANDOFF, help="Deja la tarea lista para que la continúe otro agente."))
    p.add_argument("id", nargs="?")
    p.add_argument("--note")
    p.add_argument("--to", choices=AGENTS)
    p.add_argument("--auto", action="store_true", help="No falla si no hay backlog o tarea (hooks).")
    for name, help_text in (("release", "Devuelve la tarea a pendiente."), ("review", "Pasa a revisión."), ("block", "Marca bloqueada.")):
        p = with_agent(sub.add_parser(name, help=help_text))
        p.add_argument("id")
        p.add_argument("--note", "--reason", dest="note")
        p.add_argument(OPT_FORCE, action="store_true")
    p = with_agent(sub.add_parser("done", help="Termina, marca [x] y archiva."))
    p.add_argument("id")
    p.add_argument("--note")
    p.add_argument("--no-archive", action="store_true")
    p.add_argument("--gh", action="store_true", help="Cierra y comenta la GitHub Issue vinculada.")
    p.add_argument(OPT_FORCE, action="store_true")
    p = sub.add_parser("add", help="Añade una tarea a TODO.md.")
    p.add_argument("title")
    p.add_argument("--epic")
    p.add_argument("--id")
    p.add_argument("--issue", type=int, default=None, help="Número de GitHub Issue vinculada.")
    p.add_argument("--detail", help="Texto (p. ej. 7 fases) bajo la tarea.")
    p = sub.add_parser(CMD_GH_SYNC, help="Sincroniza TODO.md con GitHub Issues (#N).")
    p.add_argument("--create-missing", action="store_true", help="Crea GitHub Issues para tareas pendientes sin issue.")
    p.add_argument("--close-done", action="store_true", help="Cierra issues completadas y marca [x] issues cerradas.")
    p.add_argument("--import-open", action="store_true", help="Importa GitHub Issues abiertas hacia TODO.md.")
    p.add_argument("--epic", default=None, help="Épica destino al importar issues abiertas.")

    epic = sub.add_parser("epic", help="Épicas: add, sync, close.")
    esub = epic.add_subparsers(dest="epic_cmd", required=True)
    p = esub.add_parser("add")
    p.add_argument("title")
    p.add_argument("--objective")
    p = esub.add_parser("sync")
    p.add_argument("id", nargs="?")
    p = with_agent(esub.add_parser("close"))
    p.add_argument("id")
    return parser


def _print(args: argparse.Namespace, payload: Any, lines: Sequence[str]) -> None:
    if args.quiet:
        return
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    else:
        for line in lines:
            print(line)


def _render_rows(rows: Sequence[Dict[str, Any]]) -> List[str]:
    if not rows:
        return ["No hay tareas que mostrar."]
    out = []
    for row in rows:
        epic = f" <{row['epic']}>" if row.get("epic") else ""
        branch = f" · {row['branch']}" if row.get("branch") else ""
        out.append(f"[{row['label']}] {row['id']}{epic}: {row['title']}{branch}")
        if row.get("note") and row["status"] in (ST_HANDOFF, ST_BLOCKED):
            out.append(f"    nota: {row['note']}")
    return out


def _dispatch_simple(args: argparse.Namespace, ctx: Context) -> Tuple[Any, List[str]]:
    cmd = args.cmd
    if cmd == "init":
        created = op_init(ctx)
        return created, created
    if cmd == "add":
        new_id = op_add(ctx, args.title, args.epic, args.id, args.detail, issue=getattr(args, "issue", None))
        return {"id": new_id}, [f"Tarea añadida: {new_id}"]
    if cmd == "list":
        if args.brief:
            lines = brief_lines(ctx)
            return lines, lines
        agent = validate_agent(args.agent) if args.mine else None
        rows = op_list(ctx, args.epic, agent, args.all)
        return rows, _render_rows(rows)
    if cmd == CMD_GH_SYNC:
        res = op_gh_sync(ctx, args.create_missing, args.close_done, args.import_open, args.epic)
        msg = (
            f"GH Sync: vinculadas={len(res['linked'])}, creadas={len(res['created'])}, "
            f"cerradas={len(res['closed'])}, importadas={len(res['imported'])}"
        )
        return res, [msg]
    if cmd == "epic":
        return _dispatch_epic(args, ctx)
    raise KeyError(cmd)


def _dispatch_epic(args: argparse.Namespace, ctx: Context) -> Tuple[Any, List[str]]:
    if args.epic_cmd == "add":
        epic_id = op_epic_add(ctx, args.title, args.objective)
        return {"id": epic_id}, [f"Épica creada: {epic_id}"]
    if args.epic_cmd == "sync":
        summary = op_epic_sync(ctx, args.id)
        lines: List[str] = []
        for item in summary:
            counts = ", ".join(f"{k}={v}" for k, v in sorted(item["counts"].items())) or "sin tareas"
            lines.append(f"Épica {item['id']}: {item['title']} ({item['total']} tareas: {counts})")
            lines.extend(f"  [{label}] {tid}" for tid, label in item["tasks"])
        return summary, lines or ["No hay épicas."]
    messages = op_epic_close(ctx, args.id, validate_agent(args.agent))
    return messages, messages


def _dispatch_agent(args: argparse.Namespace, ctx: Context) -> Tuple[Any, List[str]]:
    agent = validate_agent(args.agent)
    cmd = args.cmd
    if cmd == "next":
        task = op_next(ctx, agent, args.epic)
        if task is None:
            return None, ["No hay tareas libres."]
        if args.claim:
            entry = op_claim(ctx, task.task_id, agent, None, args.worktree, False)
            return entry, _claim_lines(entry)
        return {"id": task.task_id, "title": task.title}, [f"Siguiente: {task.task_id}: {task.title}"]
    if cmd == "claim":
        task = ctx.backlog().find(validate_id(args.id))
        entry = op_claim(ctx, args.id, agent, args.branch, args.worktree, args.force)
        if getattr(args, "gh", False) and task.issue:
            sync_gh_claim(ctx.cwd, task.issue, agent, str(entry.get("branch", "")))
        return entry, _claim_lines(entry)
    if cmd == "checkpoint":
        ids = op_checkpoint(ctx, agent, args.id, args.note)
        return ids, [f"Checkpoint: {', '.join(ids)}" if ids else "Sin tareas en curso."]
    if cmd == ST_HANDOFF:
        results = op_handoff(ctx, agent, args.id, args.note, args.to)
        lines = [f"Relevo listo: {tid} -> {path}" for tid, path in results] or ["Sin tareas en curso."]
        return [{"id": tid, "file": str(path)} for tid, path in results], lines
    if cmd == "done":
        task = ctx.backlog().find(validate_id(args.id))
        messages = op_done(ctx, args.id, agent, args.note, not args.no_archive, args.force)
        if getattr(args, "gh", False) and task.issue:
            sync_gh_done(ctx.cwd, task.issue, agent, args.note)
        return messages, [f"Tarea {args.id} terminada."] + messages
    status = {"release": ST_TODO, "review": ST_REVIEW, "block": ST_BLOCKED}[cmd]
    op_transition(ctx, args.id, agent, status, args.note, args.force)
    return {"id": args.id, "status": status}, [f"{args.id}: {status}"]


def _claim_lines(entry: Dict[str, Any]) -> List[str]:
    lines = [f"Reclamada: {entry['id']} ({entry['title']}) en la rama {entry['branch']}."]
    if entry.get("previous_owner") and entry["previous_owner"] != entry.get("owner"):
        lines.append(f"Viene de {entry['previous_owner']}. Nota: {entry.get('note') or '-'}")
    if entry.get(K_WORKTREE):
        lines.append(f"Trabaja en el worktree: {entry[K_WORKTREE]}")
    elif entry.get("branch"):
        lines.append(f"Cambia a la rama con: git switch {entry['branch']} (o git switch -c si no existe).")
    return lines


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    cwd = args.repo.resolve()
    ctx = Context(repo=locate_repo(cwd), cwd=cwd)
    auto = getattr(args, "auto", False)
    try:
        if auto and not ctx.repo.todo_path.is_file():
            return 0
        if args.cmd in ("init", "add", "list", CMD_GH_SYNC, "epic"):
            payload, lines = _dispatch_simple(args, ctx)
        else:
            payload, lines = _dispatch_agent(args, ctx)
    except (BacklogError, ValueError, KeyError) as exc:
        if auto:
            return 0
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    _print(args, payload, lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
