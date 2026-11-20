from __future__ import annotations

from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PWSH_DIR = REPO_ROOT / "scripts" / "pwsh"

EXPECTED_PWSH_SCRIPTS = [
    "archive-todo.ps1",
    "audit-pg-locks.ps1",
    "audit-plugin-parity.ps1",
    "audit-sdk-parity.ps1",
    "audit-workspace.ps1",
    "auto-evolve.ps1",
    "complete-task-pr.ps1",
    "disable-skill.ps1",
    "enable-skill.ps1",
    "format-commit.ps1",
    "gemini-deep-ops.ps1",
    "generate-postmortem.ps1",
    "git-flow-helper.ps1",
    "hook-post-write.ps1",
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


def test_pwsh_scripts_exist():
    assert PWSH_DIR.is_dir(), f"scripts/pwsh directory must exist at {PWSH_DIR}"
    for script_name in EXPECTED_PWSH_SCRIPTS:
        script_path = PWSH_DIR / script_name
        assert script_path.is_file(), f"Expected pwsh script missing: {script_name}"


def test_pwsh_scripts_valid_structure():
    for script_name in EXPECTED_PWSH_SCRIPTS:
        script_path = PWSH_DIR / script_name
        content = script_path.read_text(encoding="utf-8")
        assert len(content.strip()) > 0, f"Script {script_name} must not be empty"
        assert (
            "param(" in content.lower()
            or "[CmdletBinding()]" in content
            or "$ErrorActionPreference" in content
            or ".SYNOPSIS" in content
        ), f"Script {script_name} must contain PowerShell structure or documentation"
