#!/usr/bin/env python3
"""
Recolectores de catálogo, backlog y telemetría de sesiones para live_status.py.

Reutiliza `session_token_monitor`, `aagy_statusline`, `workspace_audit` y
`backlog`. Mantiene caché incremental por hash SHA-256 + mtime/size para que
los hooks `SessionStart` y `Stop` completen en < 150 ms sin filtrar rutas.

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import logging
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import aagy_statusline as sl  # noqa: E402
import backlog as bl  # noqa: E402
import live_status_render as rnd  # noqa: E402
from live_status_render import (  # noqa: E402
    AgySessionRow,
    AgyTelemetry,
    BacklogStats,
    CatalogStats,
    ClaudeSessionRow,
    ClaudeTelemetry,
)
import workspace_audit as wa  # noqa: E402

try:
    import session_token_monitor as stm  # noqa: E402
except ImportError:  # aagy-ecc no espeja session_token_monitor.py
    stm = None  # type: ignore[assignment]

logger = logging.getLogger("live-status")

ENCODING = "utf-8"
AGENT_AGY = "agy"
AGENT_CLAUDE = "claude"
DEFAULT_THRESHOLD = 45_000
CHARS_PER_TOKEN = 3.8
RECENT_SESSIONS_LIMIT = 8
MAX_CLAUDE_FILES = 60
DIR_AAGY_ECC = "aagy-ecc"
FILE_HOOKS = "hooks.json"
UNKNOWN_LABEL = "unknown"
DATE_FMT = "%Y-%m-%d %H:%M"


def read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding=ENCODING))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError) as exc:
        logger.debug("JSON ilegible en %s: %s", path, exc)
        return {}


def git_branch_and_head(root: Path) -> Tuple[str, str]:
    try:
        br = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2.0, check=False,
        )
        sha = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=2.0, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.debug("git rev-parse omitido en %s: %s", root, exc)
        return UNKNOWN_LABEL, "-"
    if br.returncode != 0 or sha.returncode != 0:
        return UNKNOWN_LABEL, "-"
    return (br.stdout.strip() or UNKNOWN_LABEL), (sha.stdout.strip() or "-")


def _hook_events_agy(hooks_path: Path) -> Tuple[str, ...]:
    events: set[str] = set()
    for group in read_json(hooks_path).values():
        if isinstance(group, dict):
            events.update(str(k) for k in group)
    return tuple(sorted(events))


def _hook_events_ecc(hooks_path: Path) -> Tuple[str, ...]:
    hooks_map = read_json(hooks_path).get("hooks")
    return tuple(sorted(str(k) for k in hooks_map)) if isinstance(hooks_map, dict) else ()


def _count_skills(skills_dir: Path) -> int:
    return sum(1 for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else 0


def _count_md(folder: Path, ignore_readme: bool = True) -> int:
    if not folder.is_dir():
        return 0
    return sum(1 for p in folder.glob("*.md") if p.is_file() and (not ignore_readme or p.name != "README.md"))


def collect_catalog(repo_root: Path) -> CatalogStats:
    agy_skills, _sc, _se = wa.audit_skills(repo_root / "skills")
    agy_agents, _ac, _ae = wa.audit_agents(repo_root / "agents")
    rules_chars, rules_tokens, _re = wa.audit_rules(repo_root, include_rules=True)
    ecc_dir = repo_root / DIR_AAGY_ECC
    packs_dir = ecc_dir / "packs"
    packs = tuple(sorted(p.name for p in packs_dir.iterdir() if p.is_dir())) if packs_dir.is_dir() else ()
    return CatalogStats(
        agy_skills=agy_skills,
        agy_agents=agy_agents,
        rules_bytes=rules_chars,
        rules_tokens=rules_tokens,
        ecc_skills=_count_skills(ecc_dir / "skills"),
        ecc_agents=_count_md(ecc_dir / "agents"),
        ecc_commands=_count_md(ecc_dir / "commands", ignore_readme=False),
        ecc_packs=packs,
        agy_hook_events=_hook_events_agy(repo_root / FILE_HOOKS),
        ecc_hook_events=_hook_events_ecc(ecc_dir / "hooks" / FILE_HOOKS),
    )


def collect_backlog(repo_root: Path) -> BacklogStats:
    try:
        repo = bl.locate_repo(repo_root)
        todo = repo.todo_path
        if not todo.is_file():
            return BacklogStats(0, 0, 0)
        parsed = bl.parse_backlog(todo.read_text(encoding=ENCODING))
        state = bl.load_state(repo)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Backlog no legible en %s: %s", repo_root, exc)
        return BacklogStats(0, 0, 0)
    done = sum(1 for t in parsed.tasks if t.done_mark)
    active = sum(
        1 for entry in (state.get("tasks") or {}).values()
        if isinstance(entry, dict) and entry.get("status") in bl.ACTIVE_STATES
    )
    return BacklogStats(open_tasks=len(parsed.tasks) - done, active_claims=active, done_tasks=done)


def _fallback_agy_metrics(path: Path) -> Tuple[int, int]:
    steps, chars = 0, 0
    try:
        for line in path.read_text(encoding=ENCODING, errors="replace").splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            steps += 1
            try:
                row = json.loads(stripped)
            except ValueError:
                chars += len(stripped)
                continue
            if isinstance(row, dict):
                chars += len(str(row.get("content") or "")) + len(str(row.get("thinking") or ""))
    except OSError as exc:
        logger.debug("Error leyendo transcript %s: %s", path, exc)
    return steps, math.ceil(chars / CHARS_PER_TOKEN)


def _find_agy_transcripts(home: Path, monitor: Any) -> List[Path]:
    if monitor is not None:
        return monitor.find_transcripts(home)
    brain = home / ".gemini" / "antigravity" / "brain"
    if not brain.is_dir():
        return []
    found = [p for p in brain.glob("*/.system_generated/logs/transcript.jsonl") if p.is_file()]
    found.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return found


def _cache_key(prefix: str, path: Path) -> str:
    digest = hashlib.sha256(str(path).encode(ENCODING)).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _analyze_agy_cached(path: Path, cache: Dict[str, Any], threshold: int, monitor: Any) -> Tuple[int, int, str]:
    stat = path.stat()
    sig = [stat.st_mtime_ns, stat.st_size]
    key = _cache_key(AGENT_AGY, path)
    entry = cache.get(key)
    if isinstance(entry, dict) and entry.get("sig") == sig:
        steps, tokens = int(entry.get("steps", 0)), int(entry.get("tokens", 0))
    elif monitor is not None:
        report = monitor.analyze_transcript(path, threshold=threshold)
        steps, tokens = report.steps, report.estimated_tokens
        cache[key] = {"sig": sig, "steps": steps, "tokens": tokens}
    else:
        steps, tokens = _fallback_agy_metrics(path)
        cache[key] = {"sig": sig, "steps": steps, "tokens": tokens}
    stamp = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime(DATE_FMT)
    return steps, tokens, stamp


def collect_antigravity(home: Path, cache: Dict[str, Any], monitor: Any = None) -> AgyTelemetry:
    active_mon = stm if monitor is None else monitor
    threshold = active_mon.DEFAULT_THRESHOLD if active_mon is not None else DEFAULT_THRESHOLD
    transcripts = _find_agy_transcripts(home, active_mon)
    rows: List[AgySessionRow] = []
    total_steps, total_tokens, over = 0, 0, 0
    for path in transcripts:
        try:
            steps, tokens, stamp = _analyze_agy_cached(path, cache, threshold, active_mon)
        except OSError as exc:
            logger.debug("Transcript omitido %s: %s", path, exc)
            continue
        compact = tokens > threshold
        total_steps += steps
        total_tokens += tokens
        over += 1 if compact else 0
        if len(rows) < RECENT_SESSIONS_LIMIT:
            rows.append(AgySessionRow(path.parents[2].name, stamp, steps, tokens, compact))
    return AgyTelemetry(len(transcripts), total_steps, total_tokens, over, threshold, tuple(rows))


def _parse_claude_entry(path: Path) -> Tuple[str, str, int, int]:
    session_id, model, ctx_tokens, out_tokens = path.stem, UNKNOWN_LABEL, 0, 0
    for entry in sl.tail_entries(str(path)):
        if entry.get("sessionId"):
            session_id = str(entry["sessionId"])
        msg = entry.get("message")
        usage = msg.get("usage") if isinstance(msg, dict) else None
        if isinstance(usage, dict) and not entry.get("isSidechain"):
            model = str(msg.get("model") or UNKNOWN_LABEL)
            ctx_tokens = sl._usage_tokens(usage)
            out_tokens = int(usage.get("output_tokens") or 0)
            break
    return session_id, model, ctx_tokens, out_tokens


def _claude_cached(path: Path, cache: Dict[str, Any]) -> Tuple[str, str, int, int, str]:
    stat = path.stat()
    sig = [stat.st_mtime_ns, stat.st_size]
    key = _cache_key(AGENT_CLAUDE, path)
    entry = cache.get(key)
    if isinstance(entry, dict) and entry.get("sig") == sig:
        sid = str(entry.get("sid", path.stem))
        model = str(entry.get("model", UNKNOWN_LABEL))
        ctx, out = int(entry.get("ctx", 0)), int(entry.get("out", 0))
    else:
        sid, model, ctx, out = _parse_claude_entry(path)
        cache[key] = {"sig": sig, "sid": sid, "model": model, "ctx": ctx, "out": out}
    stamp = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime(DATE_FMT)
    return sid, model, ctx, out, stamp


def collect_claude(home: Path, cache: Dict[str, Any], forbidden: Sequence[str]) -> ClaudeTelemetry:
    projects_dir = home / ".claude" / "projects"
    if not projects_dir.is_dir():
        return ClaudeTelemetry(0, 0, 0, ())
    files = sorted((p for p in projects_dir.glob("*/*.jsonl") if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    rows: List[ClaudeSessionRow] = []
    total_ctx, total_out = 0, 0
    for path in files[:MAX_CLAUDE_FILES]:
        try:
            sid, model, ctx, out, stamp = _claude_cached(path, cache)
        except OSError as exc:
            logger.debug("Sesión Claude omitida %s: %s", path, exc)
            continue
        total_ctx += ctx
        total_out += out
        if len(rows) < RECENT_SESSIONS_LIMIT:
            workspace = rnd.sanitize_workspace_label(path.parent.name, forbidden)
            rows.append(ClaudeSessionRow(sid, workspace, stamp, model, ctx, out))
    return ClaudeTelemetry(len(files), total_ctx, total_out, tuple(rows))
