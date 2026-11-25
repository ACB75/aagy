#!/usr/bin/env python3
"""
Caché de ``ccusage`` para la status line de aagy (aagy_ccusage.py).

``ccusage`` (gratuito, MIT) lee los transcripts locales de Claude Code. Es
opcional: solo se usa con ``ui.ccusage=true`` y si está en el ``PATH``; aagy
nunca lo instala ni lo descarga. El coste de hoy se guarda en
``<tmp>/aagy-ccusage-<fecha>.json`` y se refresca en segundo plano cada 5 min,
así la status line no espera nunca a ``ccusage``.

Uso::

    python aagy_ccusage.py --refresh   # lo lanza la status line, sin esperar

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Optional, Sequence, Tuple

ENCODING = "utf-8"
EXE = "ccusage"
TTL_S = 300
LOCK_TTL_S = 60
TIMEOUT_S = 20


def cache_path() -> Path:
    return Path(tempfile.gettempdir()) / f"aagy-ccusage-{date.today():%Y%m%d}.json"


def read_cache(path: Path, now: float) -> Tuple[Optional[float], bool]:
    """(coste de hoy, caducada)."""
    try:
        data = json.loads(path.read_text(encoding=ENCODING))
        return float(data["cost"]), now - float(data["at"]) > TTL_S
    except (OSError, ValueError, KeyError, TypeError):
        return None, True


def refresh(path: Path) -> bool:
    """Ejecuta ccusage (si está en el PATH) y guarda el coste de hoy."""
    exe = shutil.which(EXE)
    if exe is None:
        return False
    cmd = [exe, "daily", "--json", "--offline", "--since", f"{date.today():%Y%m%d}"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT_S, check=False)  # noqa: S603
        cost = float(json.loads(out.stdout).get("totals", {}).get("totalCost", 0.0))
    except (OSError, subprocess.SubprocessError, ValueError, TypeError, AttributeError):
        return False
    path.write_text(json.dumps({"cost": cost, "at": time.time()}), encoding=ENCODING)
    return True


def spawn_refresh(path: Path, now: float) -> None:
    """Lanza ``--refresh`` sin esperar, como mucho una vez por minuto."""
    lock = path.with_suffix(".lock")
    try:
        if lock.exists() and now - lock.stat().st_mtime < LOCK_TTL_S:
            return
        lock.write_text(str(now), encoding=ENCODING)
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
        subprocess.Popen(  # noqa: S603 (comando fijo: este script)
            [sys.executable, str(Path(__file__).resolve()), "--refresh"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=flags, start_new_session=os.name != "nt",
        )
    except OSError:
        return


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Caché de ccusage para la status line de aagy.")
    parser.add_argument("--refresh", action="store_true", help="Refresca la caché y sale.")
    args = parser.parse_args(argv)
    if args.refresh:
        refresh(cache_path())
    return 0


if __name__ == "__main__":
    sys.exit(main())
