#!/usr/bin/env python3
"""
Interruptores de la UI de aagy (aagy_ui.py): status line, avisos, ccusage y
extensiones recomendadas de VS Code / Antigravity.

Uso::

    python aagy_ui.py status
    python aagy_ui.py statusline on|off [--scope user|project|local] [--force]
    python aagy_ui.py repair              # hook SessionStart: ruta nueva tras actualizar el plugin
    python aagy_ui.py notify auto|on|off  # ui.notify en .governance/aagy.json
    python aagy_ui.py ccusage on|off      # ui.ccusage en .governance/aagy.json
    python aagy_ui.py usage [daily|monthly|session|blocks]
    python aagy_ui.py vscode [--apply]    # extensiones recomendadas en .vscode/extensions.json

El plugin no puede fijar ``statusLine`` por sí mismo: este script lo escribe en el
``settings.json`` de Claude Code y solo toca la entrada que es suya.

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
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
import aagy_notify  # noqa: E402
import aagy_statusline  # noqa: E402

ENCODING = "utf-8"
PREFIX = "[aagy-ui]"
SCRIPT_NAME = "aagy_statusline.py"
KEY_STATUSLINE = "statusLine"
KEY_COMMAND = "command"
CCUSAGE = "ccusage"
SCOPES = ("user", "project", "local")
USAGE_REPORTS = ("daily", "monthly", "session", "blocks")
CCUSAGE_HINT = "ccusage no está en el PATH. Es gratuito (MIT): npm install -g ccusage (o bun/pnpm). aagy no lo descarga."
EXTENSIONS_REL = Path(".vscode") / "extensions.json"

# Extensiones gratuitas, publicadas en el Marketplace de VS Code y en Open VSX (Antigravity).
RECOMMENDED_EXTENSIONS: Tuple[Tuple[str, str], ...] = (
    ("anthropic.claude-code", "Claude Code en el editor (diffs, @-menciones, /ide)"),
    ("gruntfuggly.todo-tree", "panel de TODO/FIXME del código"),
    ("eamodio.gitlens", "estado Git, blame y ramas (las funciones Pro no hacen falta)"),
    ("mhutchie.git-graph", "grafo de ramas y commits"),
    ("davidanson.vscode-markdownlint", "el mismo markdownlint que usan los hooks"),
)


class UiError(RuntimeError):
    """Operación que no se puede hacer sin pisar algo ajeno."""


# --------------------------------------------------------------------------- settings.json de Claude Code

def repo_root(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for folder in (current, *current.parents):
        if (folder / ".git").exists():
            return folder
    return current


def settings_path(scope: str, start: Optional[Path] = None, environ: Optional[Mapping[str, str]] = None) -> Path:
    env = os.environ if environ is None else environ
    if scope == "user":
        base = env.get("CLAUDE_CONFIG_DIR") or str(Path.home() / ".claude")
        return Path(base).expanduser() / "settings.json"
    name = "settings.local.json" if scope == "local" else "settings.json"
    return repo_root(start) / ".claude" / name


def statusline_command(script: Optional[Path] = None) -> str:
    target = (script or _HERE / SCRIPT_NAME).resolve().as_posix()
    return f'P=$(command -v python || command -v python3); "$P" "{target}"'


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding=ENCODING) or "{}")
    if not isinstance(data, dict):
        raise UiError(f"{path} no es un objeto JSON.")
    return data


def _write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding=ENCODING)


def is_ours(entry: Any) -> bool:
    return isinstance(entry, dict) and SCRIPT_NAME in str(entry.get(KEY_COMMAND, ""))


def statusline_on(path: Path, force: bool = False, script: Optional[Path] = None) -> bool:
    """Escribe la status line de aagy. Devuelve True si cambió algo."""
    data = _read_json(path)
    current = data.get(KEY_STATUSLINE)
    if current and not is_ours(current) and not force:
        raise UiError(f"{path} ya tiene otra statusLine; usa --force para sustituirla.")
    wanted = {"type": KEY_COMMAND, KEY_COMMAND: statusline_command(script), "padding": 0}
    if current == wanted:
        return False
    data[KEY_STATUSLINE] = wanted
    _write_json(path, data)
    return True


def statusline_off(path: Path) -> bool:
    data = _read_json(path)
    current = data.get(KEY_STATUSLINE)
    if current is None:
        return False
    if not is_ours(current):
        raise UiError(f"La statusLine de {path} no es de aagy; no la toco.")
    del data[KEY_STATUSLINE]
    _write_json(path, data)
    return True


def _script_in(command: str) -> Optional[Path]:
    for chunk in command.split('"'):
        if chunk.endswith(SCRIPT_NAME):
            return Path(chunk)
    return None


def repair(paths: Sequence[Path], script: Optional[Path] = None) -> List[Path]:
    """Actualiza la ruta de las status lines de aagy que apuntan a un script que ya no existe."""
    fixed: List[Path] = []
    for path in paths:
        try:
            data = _read_json(path)
        except (OSError, ValueError, UiError):
            continue
        entry = data.get(KEY_STATUSLINE)
        if not is_ours(entry):
            continue
        old = _script_in(str(entry.get(KEY_COMMAND, "")))
        if old is not None and old.is_file():
            continue
        entry[KEY_COMMAND] = statusline_command(script)
        _write_json(path, data)
        fixed.append(path)
    return fixed


# --------------------------------------------------------------------------- .governance/aagy.json

def set_project_value(key: str, value: Any, start: Optional[Path] = None) -> Path:
    """Guarda ``key`` (con puntos) en .governance/aagy.json del repo (idempotente)."""
    path = aagy_config.find_project_file(start) or (repo_root(start) / aagy_config.PROJECT_FILE)
    data = _read_json(path)
    node = data
    *parents, leaf = key.split(".")
    for part in parents:
        node = node.setdefault(part, {})
    if node.get(leaf) != value:
        node[leaf] = value
        _write_json(path, data)
    return path


# --------------------------------------------------------------------------- VS Code / Antigravity

def merge_recommendations(path: Path, ids: Sequence[str]) -> Tuple[bool, List[str]]:
    """Añade ``ids`` a ``recommendations`` sin quitar nada. (cambió, añadidas)."""
    data: Dict[str, Any] = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding=ENCODING) or "{}")
        except ValueError as exc:
            raise UiError(f"{path} tiene comentarios o no es JSON; añade a mano el bloque de 'vscode'.") from exc
    recs = data.setdefault("recommendations", [])
    known = {str(r).lower() for r in recs}
    added = [ext for ext in ids if ext.lower() not in known]
    if added:
        recs.extend(added)
        _write_json(path, data)
    return bool(added), added


# --------------------------------------------------------------------------- comandos

def _scope_paths(start: Optional[Path] = None) -> List[Path]:
    return [settings_path(scope, start) for scope in SCOPES]


def cmd_status(_args: argparse.Namespace) -> int:
    ui = aagy_statusline.load_ui()
    cfg = aagy_config.load()
    installed = [scope for scope in SCOPES if is_ours(_safe_entry(settings_path(scope)))]
    print(f"{PREFIX} statusline: {'instalada en ' + ', '.join(installed) if installed else 'no instalada'}"
          f" · ui.statusline={ui.enabled} · segmentos={','.join(ui.segments)}")
    print(f"{PREFIX} contexto: aviso {ui.warn_pct}% · crítico {ui.crit_pct}%")
    print(f"{PREFIX} avisos: ui.notify={aagy_notify.notify_mode(cfg)} · activos aquí="
          f"{aagy_notify.enabled(cfg, os.environ, sys.platform)}")
    print(f"{PREFIX} ccusage: ui.ccusage={ui.ccusage} · en PATH={shutil.which(CCUSAGE) is not None}")
    return 0


def _safe_entry(path: Path) -> Any:
    try:
        return _read_json(path).get(KEY_STATUSLINE)
    except (OSError, ValueError, UiError):
        return None


def cmd_statusline(args: argparse.Namespace) -> int:
    path = settings_path(args.scope)
    changed = statusline_on(path, args.force) if args.state == "on" else statusline_off(path)
    verb = "instalada" if args.state == "on" else "quitada"
    print(f"{PREFIX} statusline {verb if changed else 'sin cambios'} en {path}. Se ve en la próxima respuesta.")
    return 0


def cmd_repair(args: argparse.Namespace) -> int:
    for path in repair(_scope_paths()):
        if not args.quiet:
            print(f"{PREFIX} statusline reparada en {path}")
    return 0


def cmd_set(key: str, value: Any) -> int:
    path = set_project_value(key, value)
    print(f"{PREFIX} {key}={json.dumps(value)} en {path}")
    return 0


def cmd_usage(args: argparse.Namespace) -> int:
    exe = shutil.which(CCUSAGE)
    if exe is None:
        print(f"{PREFIX} {CCUSAGE_HINT}")
        return 0
    return subprocess.run([exe, args.report, "--offline"], check=False).returncode  # noqa: S603


def cmd_vscode(args: argparse.Namespace) -> int:
    ids = [ext for ext, _why in RECOMMENDED_EXTENSIONS]
    for ext, why in RECOMMENDED_EXTENSIONS:
        print(f"  {ext:<34} {why}")
    if not args.apply:
        print(f"{PREFIX} Añádelas con --apply (fusiona en {EXTENSIONS_REL}, no borra nada).")
        return 0
    path = repo_root() / EXTENSIONS_REL
    _changed, added = merge_recommendations(path, ids)
    print(f"{PREFIX} {len(added)} añadidas en {path}" if added else f"{PREFIX} {path} ya las recomienda todas.")
    return 0


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="UI de aagy: status line, avisos, ccusage y extensiones.")
    parser.add_argument("--quiet", action="store_true")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("status")
    p_sl = sub.add_parser("statusline")
    p_sl.add_argument("state", choices=("on", "off"))
    p_sl.add_argument("--scope", choices=SCOPES, default="user")
    p_sl.add_argument("--force", action="store_true")
    sub.add_parser("repair")
    p_nt = sub.add_parser("notify")
    p_nt.add_argument("state", choices=(aagy_notify.NOTIFY_AUTO, aagy_notify.NOTIFY_ON, aagy_notify.NOTIFY_OFF))
    p_cu = sub.add_parser(CCUSAGE)
    p_cu.add_argument("state", choices=("on", "off"))
    p_us = sub.add_parser("usage")
    p_us.add_argument("report", nargs="?", choices=USAGE_REPORTS, default="daily")
    p_vs = sub.add_parser("vscode")
    p_vs.add_argument("--apply", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    handlers = {
        "statusline": cmd_statusline,
        "repair": cmd_repair,
        "notify": lambda a: cmd_set("ui.notify", a.state),
        CCUSAGE: lambda a: cmd_set("ui.ccusage", a.state == "on"),
        "usage": cmd_usage,
        "vscode": cmd_vscode,
    }
    try:
        return handlers.get(args.command or "status", cmd_status)(args)
    except (UiError, OSError, ValueError) as exc:
        if args.command == "repair":
            return 0
        print(f"{PREFIX} {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
