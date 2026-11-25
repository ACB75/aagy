from __future__ import annotations

from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PS1_DIR = REPO_ROOT / "scripts" / "ps1"

EXPECTED_PS1_SCRIPTS = [
    "aagy.ps1",
    "aagy-sync.ps1",
    "git-flow-helper.ps1",
    "install-git-hooks.ps1",
    "lint-markdown.ps1",
]


def test_ps1_scripts_exist():
    assert PS1_DIR.is_dir(), f"scripts/ps1 directory must exist at {PS1_DIR}"
    for script_name in EXPECTED_PS1_SCRIPTS:
        script_path = PS1_DIR / script_name
        assert script_path.is_file(), f"Expected pwsh script missing: {script_name}"


def test_ps1_scripts_valid_structure():
    for script_name in EXPECTED_PS1_SCRIPTS:
        script_path = PS1_DIR / script_name
        content = script_path.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"Script {script_name} must not be empty"
        assert (
            "param(" in content.lower()
            or "[CmdletBinding()]" in content
            or "$ErrorActionPreference" in content
            or ".SYNOPSIS" in content
        ), f"Script {script_name} must contain PowerShell structure or documentation"


def test_launcher_is_agnostic_and_forwards_to_python():
    import subprocess
    launcher = PS1_DIR / "aagy.ps1"
    content = launcher.read_text(encoding="utf-8")
    assert not [w for w in _consumer_terms() if w in content.lower()]
    assert "../py" in content
    cmd = ['pwsh', '-NoProfile', '-File'] + [str(launcher)]
    listed = subprocess.run(cmd + ["help"], capture_output=True, text=True, check=False)
    assert listed.returncode == 0 and "complete-task-pr" in listed.stdout
    ran = subprocess.run(cmd + ["validate-branch", "--branch", "feat/app/x"], capture_output=True, text=True, check=False)
    assert ran.returncode == 0 and "PASS" in ran.stdout
    unknown = subprocess.run(cmd + ["no-existe"], capture_output=True, text=True, check=False)
    assert unknown.returncode == 2


def _consumer_terms():
    """Términos de consumer_refs del repo (.governance/aagy.json): el plugin no los conoce."""
    import json
    cfg = Path(__file__).resolve().parents[3] / ".governance" / "aagy.json"
    data = json.loads(cfg.read_text(encoding="utf-8")) if cfg.is_file() else {}
    return [str(t).lower() for t in data.get("consumer_refs", [])]
