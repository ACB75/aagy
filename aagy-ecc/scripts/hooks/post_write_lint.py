#!/usr/bin/env python3
"""
Hook PostToolUse (Write / Edit / MultiEdit) de aagy-ecc para Claude Code.

Equivalente a scripts/ps1/hook-post-write.ps1 del plugin aagy (Antigravity):
si el archivo escrito es Markdown, busca el .markdownlint.json más cercano
(subiendo desde el archivo) y ejecuta `markdownlint --fix` cuando el CLI está
instalado. Si falta el CLI o la configuración, no hace nada. Nunca bloquea.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Optional

CONFIG_NAME = ".markdownlint.json"
LINT_TIMEOUT_SEC = 20


def find_config(start: Path) -> Optional[Path]:
    """Busca .markdownlint.json desde el directorio del archivo hacia arriba."""
    for directory in (start, *start.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def _extract_path(raw: str) -> Optional[Path]:
    try:
        payload = json.loads(raw) if raw and raw.strip() else {}
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    tool_input = payload.get("tool_input") or {}
    file_path = str(tool_input.get("file_path") or "") if isinstance(tool_input, dict) else ""
    if not file_path:
        return None
    path = Path(file_path)
    if not path.is_absolute() and payload.get("cwd"):
        path = Path(str(payload["cwd"])) / path
    return path


def lint_markdown(path: Path) -> bool:
    """Formatea el archivo con markdownlint si procede. Devuelve True si se ejecutó."""
    if path.suffix.lower() != ".md" or not path.is_file():
        return False
    config = find_config(path.resolve().parent)
    linter = shutil.which("markdownlint")
    if config is None or linter is None:
        return False
    try:
        subprocess.run(
            [linter, "--config", str(config), "--fix", str(path)],
            capture_output=True,
            timeout=LINT_TIMEOUT_SEC,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return True


def main() -> int:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    path = _extract_path(raw)
    if path is not None:
        lint_markdown(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
