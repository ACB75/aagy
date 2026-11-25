#!/usr/bin/env python3
"""
Linter Markdown tras escribir (hook_post_write.py), PostToolUse de los dos plugins.

Si el fichero escrito es Markdown, busca el ``.markdownlint.json`` más cercano y
ejecuta ``markdownlint --fix`` cuando el CLI está instalado. Si falta el CLI o la
configuración, no hace nada. Nunca bloquea.

- ``--format claude``: ``tool_input.file_path``.
- ``--format agy``: ``toolCall.args`` (``TargetFile``, ``AbsolutePath``, ``Path``, ``FilePath``); responde ``{}``.

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, Optional, Sequence

FMT_CLAUDE = "claude"
FMT_AGY = "agy"
CONFIG_NAME = ".markdownlint.json"
LINT_TIMEOUT_SEC = 20
AGY_PATH_KEYS = ("TargetFile", "AbsolutePath", "Path", "FilePath")


def find_config(start: Path) -> Optional[Path]:
    """Busca .markdownlint.json desde la carpeta del fichero hacia arriba."""
    return next((d / CONFIG_NAME for d in (start, *start.parents) if (d / CONFIG_NAME).is_file()), None)


def extract_path(payload: Any, fmt: str) -> Optional[Path]:
    if not isinstance(payload, dict):
        return None
    if fmt == FMT_AGY:
        args = (payload.get("toolCall") or {}).get("args") or {}
        raw = next((str(args[k]) for k in AGY_PATH_KEYS if isinstance(args, dict) and args.get(k)), "")
    else:
        tool_input = payload.get("tool_input") or {}
        raw = str(tool_input.get("file_path") or "") if isinstance(tool_input, dict) else ""
    if not raw:
        return None
    path = Path(raw)
    if not path.is_absolute() and payload.get("cwd"):
        path = Path(str(payload["cwd"])) / path
    return path


def lint_markdown(path: Path) -> bool:
    """Formatea el fichero con markdownlint si procede. True si se ejecutó."""
    if path.suffix.lower() != ".md" or not path.is_file():
        return False
    config = find_config(path.resolve().parent)
    linter = shutil.which("markdownlint")
    if config is None or linter is None:
        return False
    try:
        subprocess.run([linter, "--config", str(config), "--fix", str(path)],  # noqa: S603
                       capture_output=True, timeout=LINT_TIMEOUT_SEC, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Linter Markdown PostToolUse (Claude Code y Antigravity).")
    parser.add_argument("--format", choices=(FMT_CLAUDE, FMT_AGY), default=FMT_CLAUDE)
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        path = extract_path(json.loads(raw) if raw.strip() else {}, args.format)
        if path is not None:
            lint_markdown(path)
    except Exception as exc:  # noqa: BLE001 - nunca bloquea
        print(f"[aagy-lint] hook omitido: {exc}", file=sys.stderr)
    if args.format == FMT_AGY:
        print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
