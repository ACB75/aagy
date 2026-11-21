from __future__ import annotations

from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PS1_DIR = REPO_ROOT / "scripts" / "ps1"

EXPECTED_PS1_SCRIPTS = [
    "archive-todo.ps1",
    "audit-pg-locks.ps1",
    "backlog.ps1",
    "audit-plugin-parity.ps1",
    "sync-aagy-ecc.ps1",
    "audit-sdk-parity.ps1",
    "audit-workspace.ps1",
    "auto-evolve.ps1",
    "complete-task-pr.ps1",
    "disable-skill.ps1",
    "aagy-sync.ps1",
    "aagy-doctor.ps1",
    "aagy-ecc-doctor.ps1",
    "enable-skill.ps1",
    "format-commit.ps1",
    "gemini-deep-ops.ps1",
    "generate-postmortem.ps1",
    "git-flow-helper.ps1",
    "hook-post-write.ps1",
    "hook-stop-capture.ps1",
    "install-git-hooks.ps1",
    "lint-markdown.ps1",
    "manage-instincts.ps1",
    "map-docs.ps1",
    "new-lifecycle-task.ps1",
    "safety-check.ps1",
    "security-audit.ps1",
    "session-token-monitor.ps1",
    "sonar-audit.ps1",
    "sync-ideas-todo.ps1",
    "toggle-gemini-mcp.ps1",
    "validate-ingress-routes.ps1",
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


def test_auto_evolve_ps1_is_agnostic():
    content = (PS1_DIR / "auto-evolve.ps1").read_text(encoding="utf-8")
    assert "home-lab" not in content.lower()
    assert "self_improve.py" in content
