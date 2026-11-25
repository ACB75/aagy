#!/usr/bin/env python3
"""Suite de pruebas unitarias para el despliegue automatizado por etiquetas en git-flow-helper."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

# Asegurar import de modulos aagy
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_PS_SCRIPT = _REPO_ROOT / "scripts" / "ps1" / "git-flow-helper.ps1"
_SH_SCRIPT = _REPO_ROOT / "scripts" / "sh" / "git-flow-helper.sh"
_HOSTS = {"AAGY_HOSTS_SANDBOX": "host-sandbox", "AAGY_HOSTS_LIVE": "host-live"}


def _env(with_hosts: bool = True) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AAGY_HOSTS")}
    env.pop("AAGY_ENV_DIR", None)
    if with_hosts:
        env.update(_HOSTS)
    return env


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
        env=_env(),
    )
    assert proc.returncode == 0
    assert "[DRY-RUN]" in proc.stdout
    assert "sandbox" in proc.stdout.lower()
    assert "v9.9.9-sandbox" in proc.stdout
    assert "host-sandbox" in proc.stdout


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
        env=_env(),
    )
    assert proc.returncode == 0
    assert "[DRY-RUN]" in proc.stdout
    assert "live" in proc.stdout.lower()
    assert "host-live" in proc.stdout


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
        env=_env(),
    )
    assert proc.returncode != 0


def test_deploy_without_declared_host_stops_and_explains() -> None:
    """Sin hosts.sandbox en la configuración no hay valor por defecto: para y dice qué falta."""
    for cmd in (["pwsh", "-NoProfile", "-File", str(_PS_SCRIPT)], ["sh", str(_SH_SCRIPT)]):
        proc = subprocess.run([*cmd, "-Action", "promote", "-Tag", "v9.9.9-sandbox", "-Deploy", "-DryRun"],
                              capture_output=True, text=True, check=False, env=_env(with_hosts=False))
        assert proc.returncode != 0
        assert "hosts.sandbox" in proc.stdout + proc.stderr


def test_sh_dry_run_uses_declared_host() -> None:
    proc = subprocess.run(["sh", str(_SH_SCRIPT), "-Action", "promote", "-Tag", "v9.9.9", "-Deploy",
                           "-Environment", "live", "-DryRun"], capture_output=True, text=True, check=False, env=_env())
    assert proc.returncode == 0 and "host-live" in proc.stdout
