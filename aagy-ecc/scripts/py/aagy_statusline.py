#!/usr/bin/env python3
"""
Status line de aagy para Claude Code y estado en una línea para Antigravity
(aagy_statusline.py).

Claude Code ejecuta el comando de ``statusLine`` en cada refresco y le pasa un
JSON por ``stdin`` (modelo, carpeta, coste, ``context_window``, transcript). Este
script escribe una sola línea con los segmentos de ``ui.segments``:

- ``model``: nombre del modelo.
- ``branch``: rama git de la carpeta de trabajo.
- ``context``: tokens de contexto usados y %, con color según
  ``ui.context_warn_pct`` (60) y ``ui.context_crit_pct`` (80).
- ``cost``: coste de la sesión que da Claude Code.
- ``local``: modo pedido del modelo local (``auto/off/tool/only``), sin red.
- ``task``: tarea y épica reclamadas por el agente en el backlog compartido.
- ``usage``: coste de hoy según ``ccusage`` (solo con ``ui.ccusage=true``; caché
  de 5 min que se refresca en segundo plano, nunca bloquea).

Se apaga con ``ui.statusline=false`` (``AAGY_UI_STATUSLINE=false``): no escribe
nada. ``--plain`` da el estado sin JSON ni colores (Antigravity, skill aagy-ui);
con ``--agent agy`` el contexto es la estimación de session_token_monitor.

Uso: ``aagy_statusline.py`` (JSON por stdin) o ``--plain --agent agy``. La caché
de ccusage la lleva aagy_ccusage.py. Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import aagy_config  # noqa: E402

ENCODING = "utf-8"
SEG_CONTEXT = "context"
KEY_CONTEXT_WINDOW = "context_window"
AGENT_AGY = "agy"
KEY_WINDOW_SIZE = "context_window_size"
DEFAULT_SEGMENTS = ("model", "branch", SEG_CONTEXT, "cost", "local", "task", "usage")
PLAIN_SEGMENTS = ("branch", SEG_CONTEXT, "local", "task")
DEFAULT_WARN_PCT = 60
DEFAULT_CRIT_PCT = 80
DEFAULT_CONTEXT_SIZE = 200_000
GIT_TIMEOUT_S = 1.0
SEP = " | "
TAIL_BYTES = 256 * 1024

RESET = "\033[0m"
COLORS = {"dim": "\033[2m", "green": "\033[32m", "yellow": "\033[33m", "red": "\033[31m", "cyan": "\033[36m"}
_EPIC_NUM_RE = re.compile(r"-(\d+)$")
_TRUE, _FALSE = ("1", "true", "on", "yes", "si", "sí"), ("0", "false", "off", "no")


@dataclass(frozen=True)
class UiSettings:
    enabled: bool
    segments: Tuple[str, ...]
    warn_pct: int
    crit_pct: int
    ccusage: bool
    color: bool


def as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    text = "" if value is None else str(value).strip().lower()
    return True if text in _TRUE else False if text in _FALSE else default


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_ui(start: Optional[Path] = None, environ: Optional[Mapping[str, str]] = None) -> UiSettings:
    env = os.environ if environ is None else environ
    cfg = aagy_config.load(start, env)
    raw_segments = cfg.get("ui.segments", None)
    if isinstance(raw_segments, str):
        raw_segments = [s.strip() for s in raw_segments.split(",")]
    segments = tuple(s for s in (raw_segments or DEFAULT_SEGMENTS) if s in DEFAULT_SEGMENTS)
    return UiSettings(
        enabled=as_bool(cfg.get("ui.statusline", True), True),
        segments=segments,
        warn_pct=_as_int(cfg.get("ui.context_warn_pct", DEFAULT_WARN_PCT), DEFAULT_WARN_PCT),
        crit_pct=_as_int(cfg.get("ui.context_crit_pct", DEFAULT_CRIT_PCT), DEFAULT_CRIT_PCT),
        ccusage=as_bool(cfg.get("ui.ccusage", False), False),
        color=as_bool(cfg.get("ui.color", True), True) and not env.get("NO_COLOR"),
    )


def paint(text: str, color: str, enabled: bool) -> str:
    return f"{COLORS[color]}{text}{RESET}" if enabled and color in COLORS else text


# --------------------------------------------------------------------------- contexto

def _usage_tokens(usage: Mapping[str, Any]) -> int:
    keys = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens")
    return sum(_as_int(usage.get(k), 0) for k in keys)


def tail_entries(path: Optional[str]) -> List[Dict[str, Any]]:
    """Entradas JSON del final de un transcript .jsonl, de la más nueva a la más vieja."""
    try:
        with open(str(path), "rb") as handle:
            handle.seek(0, os.SEEK_END)
            handle.seek(max(0, handle.tell() - TAIL_BYTES))
            lines = handle.read().decode(ENCODING, errors="ignore").splitlines()
    except (OSError, TypeError):
        return []
    entries = []
    for line in reversed(lines):
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if isinstance(entry, dict):
            entries.append(entry)
    return entries


def transcript_tokens(path: Optional[str]) -> Optional[int]:
    """Tokens de contexto del último mensaje del asistente con ``usage`` en el transcript."""
    for entry in tail_entries(path) if path else []:
        usage = (entry.get("message") or {}).get("usage")
        if isinstance(usage, dict) and not entry.get("isSidechain"):
            return _usage_tokens(usage)
    return None


def context_usage(data: Mapping[str, Any]) -> Optional[Tuple[int, int, float]]:
    """(tokens usados, tamaño de la ventana, %) o None si no se sabe."""
    window = _section(data, KEY_CONTEXT_WINDOW)
    size = _as_int(window.get(KEY_WINDOW_SIZE), 0) or DEFAULT_CONTEXT_SIZE
    current = window.get("current_usage")
    used: Optional[int] = _usage_tokens(current) if isinstance(current, dict) else None
    if used is None:
        used = transcript_tokens(data.get("transcript_path"))
    pct_raw = window.get("used_percentage")
    if used is None and pct_raw is None:
        return None
    pct = float(pct_raw) if isinstance(pct_raw, (int, float)) else 100.0 * (used or 0) / size
    if used is None:
        used = int(size * pct / 100)
    return used, size, pct


def _kilo(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    return f"{n / 1000:.0f}k" if n >= 1000 else str(n)


def segment_context(data: Mapping[str, Any], ui: UiSettings) -> Optional[str]:
    found = context_usage(data)
    if found is None:
        return None
    used, size, pct = found
    color = "red" if pct >= ui.crit_pct else "yellow" if pct >= ui.warn_pct else "green"
    text = f"ctx {_kilo(used)}/{_kilo(size)} {pct:.0f}%"
    if pct >= ui.crit_pct:
        text += " /compact"
    return paint(text, color, ui.color)


# --------------------------------------------------------------------------- git y backlog

def git_info(cwd: Path) -> Tuple[Optional[str], Optional[Path]]:
    """(rama, git-common-dir) con una sola llamada a git."""
    try:
        out = subprocess.run(
            ["git", "-C", str(cwd), "rev-parse", "--abbrev-ref", "HEAD", "--git-common-dir"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT_S, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None, None
    lines = out.stdout.strip().splitlines()
    if out.returncode != 0 or len(lines) < 2:
        return None, None
    common = Path(lines[1])
    return lines[0], common if common.is_absolute() else (cwd / common).resolve()


def active_task(common_dir: Optional[Path], repo_root: Path, agent: str) -> Optional[str]:
    """``#<épica> <tarea>`` de la tarea en curso del agente, o None."""
    if common_dir is None:
        return None
    try:
        import backlog  # noqa: WPS433 (import perezoso: solo si hay repo git)
        state = json.loads((common_dir / backlog.STATE_DIR_NAME / backlog.STATE_FILE_NAME).read_text(encoding=ENCODING))
    except (ImportError, OSError, ValueError):
        return None
    tasks = state.get("tasks") if isinstance(state, dict) else None
    if not isinstance(tasks, dict):
        return None
    mine = [tid for tid, e in sorted(tasks.items())
            if isinstance(e, dict) and e.get("owner") == agent and e.get("status") in backlog.ACTIVE_STATES]
    if not mine:
        return None
    task_id = mine[0]
    epic = _task_epic(backlog, repo_root, task_id)
    label = f"{epic} {task_id}" if epic else task_id
    return label + (f" +{len(mine) - 1}" if len(mine) > 1 else "")


def _task_epic(backlog: Any, repo_root: Path, task_id: str) -> Optional[str]:
    try:
        todo = backlog.resolve_doc_path(repo_root, "todo")
        task = backlog.parse_backlog(todo.read_text(encoding=ENCODING)).find(task_id)
    except Exception:  # noqa: BLE001 (TODO ausente o roto: sin épica)
        return None
    if not task.epic:
        return None
    match = _EPIC_NUM_RE.search(task.epic)
    return f"#{match.group(1)}" if match else task.epic


def local_mode(start: Path) -> Optional[str]:
    try:
        import local_model  # noqa: WPS433
        return local_model.load_settings(start).mode
    except Exception:  # noqa: BLE001 (sin configuración legible: sin segmento)
        return None


# --------------------------------------------------------------------------- ccusage

def segment_usage(ui: UiSettings, path: Optional[Path] = None, spawn: bool = True) -> Optional[str]:
    if not ui.ccusage or shutil.which("ccusage") is None:
        return None
    import aagy_ccusage as cu  # noqa: WPS433 (solo con ui.ccusage)
    path = path or cu.cache_path()
    now = time.time()
    cost, stale = cu.read_cache(path, now)
    if stale and spawn:
        cu.spawn_refresh(path, now)
    return None if cost is None else paint(f"hoy ${cost:.2f}", "dim", ui.color)


# --------------------------------------------------------------------------- render

@dataclass(frozen=True)
class _Ctx:
    data: Mapping[str, Any]
    ui: UiSettings
    agent: str
    folder: Path
    branch: Optional[str]
    common: Optional[Path]


def _section(data: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = data.get(key)
    return value if isinstance(value, dict) else {}


def _seg_model(ctx: _Ctx) -> Optional[str]:
    model = _section(ctx.data, "model")
    text = model.get("display_name") or model.get("id")
    return paint(text, "cyan", ctx.ui.color) if text else None


def _seg_cost(ctx: _Ctx) -> Optional[str]:
    section = _section(ctx.data, "cost")
    cost = section.get("total_cost_usd", section.get("total_usd"))  # Claude Code / CLI de Antigravity
    return f"${float(cost):.2f}" if isinstance(cost, (int, float)) and cost > 0 else None


def _seg_local(ctx: _Ctx) -> Optional[str]:
    mode = local_mode(ctx.folder)
    return f"local:{mode}" if mode else None


SEGMENTS = {
    "model": _seg_model,
    "branch": lambda ctx: ctx.branch,
    SEG_CONTEXT: lambda ctx: segment_context(ctx.data, ctx.ui),
    "cost": _seg_cost,
    "local": _seg_local,
    "task": lambda ctx: active_task(ctx.common, ctx.folder, ctx.agent),
    "usage": lambda ctx: segment_usage(ctx.ui),
}


def render(data: Mapping[str, Any], ui: UiSettings, agent: str = "claude", cwd: Optional[Path] = None) -> str:
    if not ui.enabled:
        return ""
    workspace = _section(data, "workspace")
    folder = Path(workspace.get("current_dir") or data.get("cwd") or cwd or Path.cwd())
    branch, common = git_info(folder) if {"branch", "task"} & set(ui.segments) else (None, None)
    ctx = _Ctx(data, ui, agent, folder, branch, common)
    parts = [SEGMENTS[name](ctx) for name in ui.segments]
    return SEP.join(part for part in parts if part)


def agy_context(transcript: Optional[str] = None) -> Dict[str, Any]:
    """Contexto de Antigravity estimado por session_token_monitor (tokens frente a su umbral de /compact)."""
    try:
        import session_token_monitor as stm  # noqa: WPS433 (solo existe en aagy)
        report = stm.analyze_transcript(Path(transcript) if transcript else None)
    except Exception:  # noqa: BLE001 (sin transcript ni monitor: sin segmento)
        return {}
    if not report.steps:
        return {}
    return {KEY_CONTEXT_WINDOW: {"current_usage": {"input_tokens": report.estimated_tokens},
                               KEY_WINDOW_SIZE: report.threshold}}


def agy_cli_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Status line del CLI de Antigravity: avisos por cambio de estado y contexto estimado si falta."""
    import aagy_notify  # noqa: WPS433 (importa este módulo; aquí no hay ciclo)

    aagy_notify.agy_status_changed(data)
    if context_usage(data) is None:
        data = {**data, **agy_context(data.get("transcript_path"))}
    return data


def read_stdin() -> Dict[str, Any]:
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Status line de aagy (Claude Code) y estado en una línea (Antigravity).")
    parser.add_argument("--plain", action="store_true", help="Sin JSON por stdin ni colores (Antigravity).")
    parser.add_argument("--agent", default="claude", help="Agente del backlog (claude o agy).")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        ui = load_ui()
        data = read_stdin() if not args.plain else agy_context() if args.agent == AGENT_AGY else {}
        if args.agent == AGENT_AGY and not args.plain:
            data = agy_cli_data(data)
        if args.plain:
            ui = UiSettings(True, tuple(s for s in ui.segments if s in PLAIN_SEGMENTS),
                            ui.warn_pct, ui.crit_pct, False, False)
        line = render(data, ui, args.agent)
    except Exception as exc:  # noqa: BLE001 (la status line nunca debe romper la sesión)
        line = f"aagy: {type(exc).__name__}"
    if line:
        sys.stdout.write(line + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
