#!/usr/bin/env python3
"""
Guarda de ficheros privados (local_private_guard.py), hook PreToolUse.

Si el agente va a leer un fichero que casa con ``local_model.private_globs``
(``.governance/aagy.json``), avisa de que es privado y propone ``local_run`` con
``paths`` del servidor ``aagy-local``, para que el contenido no salga del equipo.

- Claude Code (``--format claude``): decisión ``ask``; el usuario confirma o no.
- Antigravity (``--format agy``): decisión ``force_ask``, que pregunta siempre aunque
  haya un "Always Allow" guardado (un fichero privado no debe pasar por un permiso viejo).

Sin ``private_globs`` no hace nada. Ante cualquier error deja pasar (fail-open).
Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, Optional, Sequence

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

FMT_CLAUDE = "claude"
FMT_AGY = "agy"
CONFIRM_SUFFIX = " ¿Lo lee el agente en la nube de todos modos?"
CLAUDE_READ_TOOLS = frozenset({"Read", "NotebookRead", "Edit", "MultiEdit", "Write"})
CLAUDE_PATH_KEYS = ("file_path", "notebook_path")
AGY_PATH_KEYS = ("AbsolutePath", "TargetFile", "Path", "FilePath")


def target_of(payload: Dict[str, Any], fmt: str) -> Optional[str]:
    if fmt == FMT_AGY:
        args = (payload.get("toolCall") or {}).get("args") or {}
        return next((str(args[k]) for k in AGY_PATH_KEYS if args.get(k)), None)
    if str(payload.get("tool_name") or "") not in CLAUDE_READ_TOOLS:
        return None
    tool_input = payload.get("tool_input") or {}
    return next((str(tool_input[k]) for k in CLAUDE_PATH_KEYS if tool_input.get(k)), None)


def reason_for(target: str, cwd: Path, environ: Optional[Dict[str, str]] = None) -> Optional[str]:
    import local_model as lm  # noqa: PLC0415 - carga perezosa: el hook no paga la importación si no hay payload

    settings = lm.load_settings(cwd, environ)
    if not lm.is_private(target, settings, cwd):
        return None
    status = lm.get_status(settings)
    local = ("usa local_run(task, paths=[...]) del servidor aagy-local para que el contenido no salga del equipo"
             if status.effective == lm.MODE_TOOL else "el modelo local no está disponible ahora")
    return f"[aagy-local] {target} es privado (local_model.private_globs): {local}."


def response(reason: Optional[str], fmt: str) -> Dict[str, Any]:
    if fmt == FMT_AGY:
        return {"decision": "force_ask", "reason": reason + CONFIRM_SUFFIX} if reason else {"decision": "allow"}
    if not reason:
        return {}
    return {"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "ask",
        "permissionDecisionReason": reason + CONFIRM_SUFFIX,
    }}


def handle(payload: Dict[str, Any], fmt: str) -> Dict[str, Any]:
    target = target_of(payload, fmt)
    if not target:
        return response(None, fmt)
    cwd = Path(str(payload.get("cwd") or os.getcwd()))
    return response(reason_for(target, cwd), fmt)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Guarda de ficheros privados (PreToolUse).")
    parser.add_argument("--format", choices=(FMT_CLAUDE, FMT_AGY), default=FMT_CLAUDE)
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        out = handle(payload if isinstance(payload, dict) else {}, args.format)
    except Exception:  # noqa: BLE001 - fail-open: un hook roto no puede bloquear al agente
        out = response(None, args.format)
    if out:
        print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
