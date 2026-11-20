#!/usr/bin/env python3
"""Suite de pruebas unitarias para el despliegue automatizado por etiquetas en git-flow-helper."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

# Asegurar import de modulos aagy
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_PS_SCRIPT = _REPO_ROOT / "scripts" / "pwsh" / "git-flow-helper.ps1"
_SH_SCRIPT = _REPO_ROOT / "scripts" / "sh" / "git-flow-helper.sh"


def test_dry_run_sandbox_promotion() -> None:
    """Verifica ejecucion en modo -DryRun para promocion a entorno sandbox."""
    proc = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(_PS_SCRIPT),
            "-Action",
            "promote",
            "-Tag",
            "v9.9.9-sandbox",
            "-Deploy",
            "-DryRun",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "[DRY-RUN]" in proc.stdout
    assert "sandbox" in proc.stdout.lower()
    assert "v9.9.9-sandbox" in proc.stdout


def test_dry_run_live_promotion() -> None:
    """Verifica ejecucion en modo -DryRun para promocion a entorno live."""
    proc = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(_PS_SCRIPT),
            "-Action",
            "promote",
            "-Tag",
            "v9.9.9",
            "-Deploy",
            "-Environment",
            "live",
            "-DryRun",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    assert "[DRY-RUN]" in proc.stdout
    assert "live" in proc.stdout.lower()
    assert "NEO" in proc.stdout or "live" in proc.stdout.lower()


def test_deploy_without_tag_throws() -> None:
    """Verifica que la promocion con -Deploy sin -Tag arroje error."""
    proc = subprocess.run(
        [
            "pwsh",
            "-NoProfile",
            "-File",
            str(_PS_SCRIPT),
            "-Action",
            "promote",
            "-Deploy",
            "-DryRun",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
