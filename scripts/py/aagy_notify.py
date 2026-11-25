#!/usr/bin/env python3
"""
Avisos de escritorio de aagy (aagy_notify.py).

Hook de Claude Code (``Stop`` y ``Notification``) y de Antigravity (``Stop``).
Avisa cuando el agente termina un turno largo o pide permiso, para no tener que
vigilar la terminal.

- ``ui.notify`` (``AAGY_UI_NOTIFY``): ``auto`` (por defecto), ``on`` u ``off``.
  ``auto`` se apaga en CI, en sesiones remotas de Claude Code y por SSH sin
  escritorio.
- ``ui.notify_min_s`` (30): en ``Stop`` solo avisa si el turno duró al menos eso
  (se mide desde el último mensaje del usuario en el transcript; si no hay
  transcript, avisa).

Backends: Windows ``powershell.exe`` (toast WinRT), macOS ``osascript``, Linux
``notify-send``. El título y el texto van como variables de entorno o
argumentos, nunca dentro del código del script. Sin backend sale con 0.
El proceso del aviso se lanza sin esperar: el hook vuelve al momento.

Uso::

    python aagy_notify.py --event stop|notification [--dry-run]

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import aagy_config  # noqa: E402
from aagy_statusline import as_bool, read_stdin, tail_entries  # noqa: E402

ENCODING = "utf-8"
EVENT_STOP = "stop"
EVENT_NOTIFICATION = "notification"
DEFAULT_MIN_S = 30
TITLE = "aagy"
TEXT_MAX = 180
NOTIFY_AUTO, NOTIFY_ON, NOTIFY_OFF = "auto", "on", "off"
REMOTE_VARS = ("CI", "CLAUDE_CODE_REMOTE", "GITHUB_ACTIONS")

# Toast WinRT de Windows PowerShell 5.1 (está en todo Windows 10/11). Lee el texto
# de variables de entorno y lo escapa como XML: nada del usuario entra en el código.
# Va como -EncodedCommand (UTF-16LE en base64) para no depender del entrecomillado.
PS_TOAST = (
    "$ErrorActionPreference='SilentlyContinue';"
    "[void][Windows.UI.Notifications.ToastNotificationManager,Windows.UI.Notifications,ContentType=WindowsRuntime];"
    "[void][Windows.Data.Xml.Dom.XmlDocument,Windows.Data.Xml.Dom.XmlDocument,ContentType=WindowsRuntime];"
    "$t=[Security.SecurityElement]::Escape($env:AAGY_NOTIFY_TITLE);"
    "$b=[Security.SecurityElement]::Escape($env:AAGY_NOTIFY_BODY);"
    "$x=New-Object Windows.Data.Xml.Dom.XmlDocument;"
    "$x.LoadXml(\"<toast><visual><binding template='ToastGeneric'><text>$t</text><text>$b</text></binding></visual></toast>\");"
    "$id='{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\\WindowsPowerShell\\v1.0\\powershell.exe';"
    "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($id)"
    ".Show([Windows.UI.Notifications.ToastNotification]::new($x))"
)
OSA_SCRIPT = ("-e", "on run argv", "-e", "display notification (item 2 of argv) with title (item 1 of argv)", "-e", "end run")


def notify_mode(cfg: aagy_config.Config) -> str:
    raw = cfg.get("ui.notify", NOTIFY_AUTO)
    if isinstance(raw, bool):
        return NOTIFY_ON if raw else NOTIFY_OFF
    text = str(raw).strip().lower()
    if text in (NOTIFY_ON, NOTIFY_OFF, NOTIFY_AUTO):
        return text
    return NOTIFY_ON if as_bool(text, True) else NOTIFY_OFF


def has_desktop(environ: Mapping[str, str], platform: str) -> bool:
    if any(as_bool(environ.get(var), False) for var in REMOTE_VARS):
        return False
    if platform.startswith("linux"):
        return bool(environ.get("DISPLAY") or environ.get("WAYLAND_DISPLAY"))
    if environ.get("SSH_CONNECTION") and not platform.startswith("win"):
        return False
    return True


def enabled(cfg: aagy_config.Config, environ: Mapping[str, str], platform: str) -> bool:
    mode = notify_mode(cfg)
    if mode == NOTIFY_OFF:
        return False
    return mode == NOTIFY_ON or has_desktop(environ, platform)


def _parse_ts(text: Any) -> Optional[datetime]:
    if not isinstance(text, str):
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _is_user_prompt(entry: Mapping[str, Any]) -> bool:
    """Mensaje escrito por la persona (no un tool_result que también llega como ``user``)."""
    if entry.get("type") != "user" or entry.get("isSidechain") or entry.get("isMeta"):
        return False
    content = (entry.get("message") or {}).get("content")
    if isinstance(content, str):
        return True
    return isinstance(content, list) and not any(
        isinstance(block, dict) and block.get("type") == "tool_result" for block in content
    )


def turn_seconds(transcript: Optional[str], now: Optional[datetime] = None) -> Optional[float]:
    """Segundos desde el último mensaje del usuario, o None si no se sabe."""
    for entry in tail_entries(transcript) if transcript else []:
        if _is_user_prompt(entry):
            started = _parse_ts(entry.get("timestamp"))
            if started is None:
                return None
            return ((now or datetime.now(timezone.utc)) - started).total_seconds()
    return None


def message_for(event: str, data: Mapping[str, Any]) -> Tuple[str, str]:
    folder = Path(str(data.get("cwd") or Path.cwd())).name
    title = f"{TITLE} · {folder}" if folder else TITLE
    if event == EVENT_NOTIFICATION:
        body = str(data.get("message") or "El agente necesita tu atención.")
    else:
        body = "Turno terminado."
    return title, body[:TEXT_MAX]


def should_notify(event: str, data: Mapping[str, Any], cfg: aagy_config.Config,
                  environ: Mapping[str, str], platform: str, now: Optional[datetime] = None) -> bool:
    if not enabled(cfg, environ, platform):
        return False
    if event != EVENT_STOP:
        return True
    if data.get("stop_hook_active"):
        return False
    try:
        min_s = float(cfg.get("ui.notify_min_s", DEFAULT_MIN_S))
    except (TypeError, ValueError):
        min_s = DEFAULT_MIN_S
    elapsed = turn_seconds(data.get("transcript_path"), now)
    return elapsed is None or elapsed >= min_s


def build_command(title: str, body: str, platform: str,
                  which: Any = shutil.which) -> Optional[Tuple[List[str], Dict[str, str]]]:
    """(argv, variables extra) del backend del SO, o None si no hay ninguno."""
    if platform.startswith("win"):
        exe = which("powershell.exe") or which("powershell")
        if exe:
            encoded = base64.b64encode(PS_TOAST.encode("utf-16-le")).decode("ascii")
            return [exe, "-NoProfile", "-NonInteractive", "-WindowStyle", "Hidden", "-EncodedCommand", encoded], {
                "AAGY_NOTIFY_TITLE": title, "AAGY_NOTIFY_BODY": body}
        return None
    if platform == "darwin":
        exe = which("osascript")
        return ([exe, *OSA_SCRIPT, title, body], {}) if exe else None
    exe = which("notify-send")
    return ([exe, "--app-name=aagy", "--", title, body], {}) if exe else None


def launch(argv: List[str], extra_env: Mapping[str, str]) -> None:
    env = dict(os.environ, **extra_env)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen(  # noqa: S603 (argv fijo; el texto va como dato)
            argv, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, creationflags=flags, start_new_session=os.name != "nt",
        )
    except OSError:
        return


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Avisos de escritorio de aagy (hooks Stop y Notification).")
    parser.add_argument("--event", choices=(EVENT_STOP, EVENT_NOTIFICATION), help="Evento (si no, hook_event_name).")
    parser.add_argument("--format", default="claude", help="Harness que llama (claude o agy); solo informativo.")
    parser.add_argument("--dry-run", action="store_true", help="Imprime el comando en vez de lanzarlo.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        data = read_stdin()
        event = args.event or str(data.get("hook_event_name", EVENT_STOP)).lower()
        cfg = aagy_config.load(Path(str(data.get("cwd") or Path.cwd())))
        if not should_notify(event, data, cfg, os.environ, sys.platform):
            return 0
        title, body = message_for(event, data)
        found = build_command(title, body, sys.platform)
        if found is None:
            return 0
        if args.dry_run:
            print(json.dumps({"argv": found[0], "env": found[1]}, ensure_ascii=False))
        else:
            launch(*found)
    except Exception:  # noqa: BLE001 (un aviso nunca debe romper el hook)
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
