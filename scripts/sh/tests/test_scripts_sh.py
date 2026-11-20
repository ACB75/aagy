from __future__ import annotations

from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SH_DIR = REPO_ROOT / "scripts" / "sh"

EXPECTED_SH_SCRIPTS = [
    "archive-todo.sh",
    "audit-pg-locks.sh",
    "audit-plugin-parity.sh",
    "audit-sdk-parity.sh",
    "audit-workspace.sh",
    "auto-evolve.sh",
    "complete-task-pr.sh",
    "disable-skill.sh",
    "aagy-sync.sh",
    "enable-skill.sh",
    "format-commit.sh",
    "gemini-deep-ops.sh",
    "generate-postmortem.sh",
    "git-flow-helper.sh",
    "hook-post-write.sh",
    "hook-stop-capture.sh",
    "install-git-hooks.sh",
    "lint-markdown.sh",
    "manage-instincts.sh",
    "map-docs.sh",
    "new-lifecycle-task.sh",
    "safety-check.sh",
    "security-audit.sh",
    "session-token-monitor.sh",
    "sonar-audit.sh",
    "sync-ideas-todo.sh",
    "toggle-gemini-mcp.sh",
    "validate-ingress-routes.sh",
]


def test_sh_scripts_exist():
    assert SH_DIR.is_dir(), f"scripts/sh directory must exist at {SH_DIR}"
    for script_name in EXPECTED_SH_SCRIPTS:
        script_path = SH_DIR / script_name
        assert script_path.is_file(), f"Expected sh script missing: {script_name}"


def test_sh_scripts_have_shebang_and_lf():
    for script_name in EXPECTED_SH_SCRIPTS:
        script_path = SH_DIR / script_name
        raw = script_path.read_bytes()
        assert len(raw) > 0, f"Script {script_name} must not be empty"
        assert raw.startswith(b"#!/"), f"Script {script_name} must begin with shebang #!/"
        assert b"\r\n" not in raw, f"Script {script_name} must use strict LF line endings"


def test_auto_evolve_sh_is_agnostic():
    content = (SH_DIR / "auto-evolve.sh").read_text(encoding="utf-8")
    assert "home-lab" not in content.lower()
    assert "self_improve.py" in content
