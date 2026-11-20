#!/usr/bin/env python3
"""Pruebas unitarias para sync_aagy_ecc.py y los hooks Python de aagy-ecc."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
_HOOKS_DIR = _REPO_ROOT / "aagy-ecc" / "scripts" / "hooks"
for _p in (_SCRIPTS_DIR, _HOOKS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from sync_aagy_ecc import compare, main, sync  # noqa: E402
import post_write_lint  # noqa: E402
import safety_check  # noqa: E402


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / "skills" / "tdd-workflow").mkdir(parents=True)
    (tmp_path / "skills" / "tdd-workflow" / "SKILL.md").write_text("# TDD\n", encoding="utf-8")
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "planner.md").write_text("# planner\n", encoding="utf-8")
    (tmp_path / "rules").mkdir()
    (tmp_path / "rules" / "AGENTS.md").write_text("# rules\n", encoding="utf-8")
    (tmp_path / "scripts" / "py").mkdir(parents=True)
    (tmp_path / "scripts" / "py" / "self_improve.py").write_text("print('x')\n", encoding="utf-8")
    (tmp_path / "aagy-ecc").mkdir()
    return tmp_path


def test_compare_reports_missing_before_sync(repo: Path):
    report = compare(repo)
    assert not report.in_sync
    assert "skills/tdd-workflow/SKILL.md" in report.missing
    assert "agents/planner.md" in report.missing
    assert "rules/AGENTS.md" in report.missing
    assert "scripts/py/self_improve.py" in report.missing


def test_sync_copies_and_then_in_sync(repo: Path):
    sync(repo)
    assert (repo / "aagy-ecc" / "skills" / "tdd-workflow" / "SKILL.md").is_file()
    assert compare(repo).in_sync


def test_sync_removes_stale_mirrored_files(repo: Path):
    sync(repo)
    stale = repo / "aagy-ecc" / "skills" / "old-skill" / "SKILL.md"
    stale.parent.mkdir(parents=True)
    stale.write_text("# old", encoding="utf-8")
    assert "skills/old-skill/SKILL.md" in compare(repo).extra
    sync(repo)
    assert not stale.parent.exists()
    assert compare(repo).in_sync


def test_compare_ignores_crlf_only_differences(repo: Path):
    sync(repo)
    (repo / "aagy-ecc" / "agents" / "planner.md").write_bytes(b"# planner\r\n")
    assert compare(repo).in_sync


def test_check_mode_exit_codes(repo: Path):
    assert main(["--repo-root", str(repo), "--check"]) == 1
    assert main(["--repo-root", str(repo)]) == 0
    assert main(["--repo-root", str(repo), "--check"]) == 0


def test_real_repository_mirror_is_in_sync():
    """El espejo versionado de aagy-ecc/ debe coincidir con la raíz (ejecuta sync-aagy-ecc si falla)."""
    report = compare(_REPO_ROOT)
    assert report.in_sync, report.to_dict()


@pytest.mark.parametrize("command", [
    "rm -rf /",
    "sudo rm -rf / --no-preserve-root",
    "mkfs.ext4 /dev/sda1",
    "psql -c 'DROP DATABASE prod'",
    "dd if=/dev/zero of=/dev/sda",
])
def test_safety_check_denies_dangerous(command: str):
    out = safety_check.build_response(command)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("command", ["ls -la", "rm -rf ./build", "git status", ""])
def test_safety_check_allows_safe(command: str):
    assert safety_check.build_response(command) == {}


def test_safety_check_cli_contract():
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "rm -rf /"}})
    proc = subprocess.run([sys.executable, str(_HOOKS_DIR / "safety_check.py")], input=payload,
                          capture_output=True, text=True, check=False)
    assert proc.returncode == 0
    assert json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_post_write_lint_skips_non_markdown(tmp_path: Path):
    target = tmp_path / "a.py"
    target.write_text("x = 1\n", encoding="utf-8")
    assert post_write_lint.lint_markdown(target) is False


def test_post_write_lint_finds_nearest_config(tmp_path: Path):
    (tmp_path / ".markdownlint.json").write_text("{}", encoding="utf-8")
    nested = tmp_path / "doc" / "sub"
    nested.mkdir(parents=True)
    assert post_write_lint.find_config(nested) == tmp_path / ".markdownlint.json"


def test_post_write_lint_cli_never_fails():
    payload = json.dumps({"tool_name": "Write", "tool_input": {"file_path": "/no/existe.md"}})
    proc = subprocess.run([sys.executable, str(_HOOKS_DIR / "post_write_lint.py")], input=payload,
                          capture_output=True, text=True, check=False)
    assert proc.returncode == 0


def test_session_start_injects_rules(tmp_path: Path):
    import session_start_rules
    rules = tmp_path / "AGENTS.md"
    rules.write_text("# Reglas\n- regla 1\n", encoding="utf-8")
    out = session_start_rules.build_response(rules)
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "regla 1" in out["hookSpecificOutput"]["additionalContext"]


def test_session_start_missing_rules_is_noop(tmp_path: Path):
    import session_start_rules
    assert session_start_rules.build_response(tmp_path / "nope.md") == {}


def test_session_start_real_plugin_rules_present():
    import session_start_rules
    assert session_start_rules.build_response() != {}
