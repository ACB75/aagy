#!/usr/bin/env python3
"""
Estado vivo, catálogo y telemetría de sesiones de aagy / aagy-ecc (live_status.py).

Genera y mantiene al día:
  1. `.agents/LIVE_TELEMETRY.md` (gitignored, refrescada en `SessionStart` y `Stop`
     dentro del worktree del agente sin ensuciar git ni bloquear `recycle`).
  2. `doc/STATUS.md` (versionada, actualizada con `live_status.py sync` y
     verificada con `live_status.py check`).

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import io
import json
import logging
import os
from pathlib import Path
import sys
import threading
from typing import Any, Dict, List, Mapping, Optional, Sequence

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import agent_worktree_base as awb  # noqa: E402
import consumer_refs  # noqa: E402
from docs_map import resolve_doc_path  # noqa: E402
import live_status_collect as col  # noqa: E402
from live_status_collect import (  # noqa: E402,F401
    AGENT_AGY,
    AGENT_CLAUDE,
    DIR_AAGY_ECC,
    ENCODING,
    collect_backlog,
    collect_catalog,
    git_branch_and_head,
    read_json,
    stm,
)
from live_status_render import (  # noqa: E402
    LiveSnapshot,
    MARKER_CATALOG_END,
    MARKER_CATALOG_START,
    MARKER_TELEMETRY_END,
    MARKER_TELEMETRY_START,
    ORIGIN_SESSION_ID,
    render_live_telemetry_page,
    update_status_markdown,
)

logger = logging.getLogger("live-status")

LIVE_DIR_NAME = ".agents"
LIVE_PAGE_NAME = "LIVE_TELEMETRY.md"
CACHE_FILE_NAME = "telemetry-cache.json"
PLUGIN_JSON = "plugin.json"
KEY_VERSION = "version"
EVENT_STOP = "stop"
EVENT_SESSION_START = "session_start"


@dataclass(frozen=True)
class SyncOutcome:
    snapshot: LiveSnapshot
    live_path: Path
    status_path: Path
    status_updated: bool


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(f"{path.suffix}.tmp{os.getpid()}")
    tmp.write_text(content, encoding=ENCODING)
    os.replace(tmp, path)


def _is_aagy_repo(root: Path) -> bool:
    return (root / DIR_AAGY_ECC).is_dir() and (root / PLUGIN_JSON).is_file()


def _load_cache(cache_file: Path) -> Dict[str, Any]:
    entries = read_json(cache_file).get("entries")
    return dict(entries) if isinstance(entries, dict) else {}


def _save_cache(cache_file: Path, entries: Mapping[str, Any]) -> None:
    try:
        _write_atomic(cache_file, json.dumps({KEY_VERSION: 1, "entries": entries}, indent=2) + "\n")
    except OSError as exc:
        logger.debug("No se pudo guardar caché %s: %s", cache_file, exc)


def collect_snapshot(repo_root: Path, home: Optional[Path] = None, cache_dir: Optional[Path] = None) -> LiveSnapshot:
    resolved_home = (home or Path.home()).expanduser()
    resolved_cache_dir = cache_dir or (repo_root / LIVE_DIR_NAME)
    cache_file = resolved_cache_dir / CACHE_FILE_NAME
    cache = _load_cache(cache_file)
    forbidden = consumer_refs.declared_terms(repo_root)
    version = str(read_json(repo_root / PLUGIN_JSON).get(KEY_VERSION) or "0.0.0")
    ecc_version = str(read_json(repo_root / DIR_AAGY_ECC / ".claude-plugin" / PLUGIN_JSON).get(KEY_VERSION) or "0.0.0")
    branch, head = git_branch_and_head(repo_root)
    layout = awb.find_layout(repo_root, use_git=False)
    snap = LiveSnapshot(
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        version=version,
        ecc_version=ecc_version,
        branch=branch,
        head=head,
        worktree_active=bool(layout and layout.active),
        catalog=collect_catalog(repo_root),
        backlog=collect_backlog(repo_root),
        antigravity=col.collect_antigravity(resolved_home, cache, monitor=stm),
        claude=col.collect_claude(resolved_home, cache, forbidden),
    )
    if cache_dir is not None or (repo_root / LIVE_DIR_NAME).is_dir():
        _save_cache(cache_file, cache)
    return snap


def sync_live_pages(
    repo_root: Path,
    home: Optional[Path] = None,
    write_status: bool = True,
    write_root: Optional[Path] = None,
) -> SyncOutcome:
    target_root = (write_root or repo_root).resolve()
    live_dir = target_root / LIVE_DIR_NAME
    snap = collect_snapshot(repo_root, home=home, cache_dir=live_dir)
    forbidden = consumer_refs.declared_terms(repo_root)

    live_path = live_dir / LIVE_PAGE_NAME
    _write_atomic(live_path, render_live_telemetry_page(snap, forbidden))

    status_path = resolve_doc_path(target_root, "status")
    status_updated = False
    if write_status:
        existing = status_path.read_text(encoding=ENCODING) if status_path.is_file() else ""
        updated = update_status_markdown(existing, snap, forbidden)
        if updated != existing:
            _write_atomic(status_path, updated)
            status_updated = True
    return SyncOutcome(snap, live_path, status_path, status_updated)


def check_status_doc(repo_root: Path) -> List[str]:
    status_path = resolve_doc_path(repo_root, "status")
    if not status_path.is_file():
        return [f"No existe {status_path}."]
    text = status_path.read_text(encoding=ENCODING)
    problems: List[str] = []
    for marker in (MARKER_CATALOG_START, MARKER_CATALOG_END, MARKER_TELEMETRY_START, MARKER_TELEMETRY_END):
        if marker not in text:
            problems.append(f"Falta marcador '{marker}' en {status_path.name}.")
    for token in ("ADR-0001", "ADR-0004", ORIGIN_SESSION_ID):
        if token not in text:
            problems.append(f"Falta trazabilidad '{token}' en {status_path.name}.")
    cat = collect_catalog(repo_root)
    version = str(read_json(repo_root / PLUGIN_JSON).get(KEY_VERSION) or "")
    if version and f"`{version}`" not in text:
        problems.append(f"Versión desfasada en {status_path.name}: se esperaba `{version}`.")
    if f"{cat.agy_skills} en `skills/`" not in text or f"{cat.agy_agents} en `agents/`" not in text:
        problems.append(f"Catálogo desfasado en {status_path.name}: repo tiene {cat.agy_skills} skills y {cat.agy_agents} agentes.")
    return problems


def _locate_aagy_checkout(start: Path) -> Optional[Path]:
    current = start if start.is_dir() else start.parent
    for candidate in (current, *current.parents):
        if _is_aagy_repo(candidate):
            return candidate.resolve()
        if (candidate / ".git").exists():
            break
    return None


def _extract_start_dir(payload: Mapping[str, Any], repo: Optional[Path]) -> Path:
    if repo is not None:
        return repo.resolve()
    if payload.get("cwd"):
        return Path(str(payload["cwd"])).expanduser()
    ws = payload.get("workspacePaths")
    if isinstance(ws, list) and ws:
        return Path(str(ws[0])).expanduser()
    return Path.cwd()


def run_hook(
    payload: Optional[Mapping[str, Any]] = None,
    agent: str = AGENT_AGY,
    event: str = EVENT_STOP,
    home: Optional[Path] = None,
    repo: Optional[Path] = None,
) -> int:
    """Ejecución fail-open (<150 ms) para hooks SessionStart / Stop: actualiza .agents/LIVE_TELEMETRY.md."""
    try:
        start = _extract_start_dir(payload or {}, repo)
        checkout = _locate_aagy_checkout(start)
        if checkout is None:
            return 0
        layout = awb.find_layout(checkout, use_git=False)
        target = checkout
        if layout is not None and layout.active:
            wt = layout.worktrees.get(agent)
            if wt is None or not wt.is_dir():
                return 0
            target = wt
        source = target if _is_aagy_repo(target) else checkout
        sync_live_pages(source, home=home, write_status=False, write_root=target)
    except Exception as exc:  # noqa: BLE001 - los hooks nunca deben romper la sesión
        logger.debug("live_status hook (%s/%s) omitido: %s", agent, event, exc)
    return 0


def _read_stdin_nonblocking(timeout_sec: float = 0.05) -> Dict[str, Any]:
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    if isinstance(sys.stdin, io.TextIOBase) and not hasattr(sys.stdin, "fileno"):
        raw = sys.stdin.read()
    else:
        buf: List[str] = []
        worker = threading.Thread(target=lambda: buf.append(sys.stdin.read()), daemon=True)
        worker.start()
        worker.join(timeout=timeout_sec)
        raw = buf[0] if buf else ""
    try:
        parsed = json.loads(raw) if raw.strip() else {}
        return parsed if isinstance(parsed, dict) else {}
    except ValueError:
        return {}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Estado vivo, catálogo y telemetría de sesiones de aagy.")
    parser.add_argument("action", nargs="?", choices=("status", "sync", "check"), default="status")
    parser.add_argument("--repo", type=Path, default=None, help="Raíz del repositorio aagy.")
    parser.add_argument("--home", type=Path, default=None, help="Directorio HOME con sesiones.")
    parser.add_argument("--hook", action="store_true", help="Modo hook pasivo (SessionStart / Stop).")
    parser.add_argument("--event", choices=(EVENT_SESSION_START, EVENT_STOP), default=EVENT_STOP)
    parser.add_argument("--agent", choices=(AGENT_AGY, AGENT_CLAUDE), default=AGENT_AGY)
    parser.add_argument("--json", action="store_true", help="Salida JSON estructurada.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.hook:
        return run_hook(_read_stdin_nonblocking(), agent=args.agent, event=args.event, home=args.home, repo=args.repo)
    repo_root = (args.repo or Path.cwd()).resolve()
    if args.action == "check":
        problems = check_status_doc(repo_root)
        for problem in problems:
            print(f"[FAIL] {problem}")
        if not problems:
            print("[live-status] OK: doc/STATUS.md al día.")
        return 1 if problems else 0
    if args.action == "sync":
        outcome = sync_live_pages(repo_root, home=args.home, write_status=True)
        if args.json:
            print(json.dumps(outcome.snapshot.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(f"[live-status] Sincronizado: {outcome.live_path} y {outcome.status_path}")
        return 0
    snap = collect_snapshot(repo_root, home=args.home)
    if args.json:
        print(json.dumps(snap.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(f"[live-status] aagy {snap.version} | {snap.catalog.agy_skills} skills, {snap.catalog.agy_agents} agentes | "
              f"agy={snap.antigravity.total_sessions} ({snap.antigravity.total_estimated_tokens:,}t) | "
              f"claude={snap.claude.total_sessions}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
