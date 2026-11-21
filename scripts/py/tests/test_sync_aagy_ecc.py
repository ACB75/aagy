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


_PROFILES_SH = """case "$PHASE" in
  generic)
    SKILLS=(tdd-workflow)
    AGENTS=(planner.md)
    ;;
  go)
    SKILLS=(golang-patterns tdd-workflow)
    AGENTS=(go-reviewer.md)
    ;;
esac
"""


@pytest.fixture
def profiled_repo(repo: Path) -> Path:
    for name in ("golang-patterns", "healthcare"):
        (repo / "skills" / name).mkdir()
        (repo / "skills" / name / "SKILL.md").write_text(f"# {name}\n", encoding="utf-8")
    (repo / "agents" / "go-reviewer.md").write_text("# go\n", encoding="utf-8")
    (repo / "scripts" / "sh").mkdir(parents=True)
    (repo / "scripts" / "sh" / "aagy-sync.sh").write_text(_PROFILES_SH, encoding="utf-8")
    manifest_dir = repo / "aagy-ecc" / ".claude-plugin"
    manifest_dir.mkdir(parents=True)
    (manifest_dir / "plugin.json").write_text(json.dumps({"name": "aagy-ecc", "version": "9.9.9", "license": "MIT"}),
                                              encoding="utf-8")
    (manifest_dir / "marketplace.json").write_text(json.dumps({"name": "aagy-ecc", "plugins": [
        {"name": "aagy-ecc", "source": "./"}, {"name": "aagy-ecc-old", "source": "./packs/old"}]}), encoding="utf-8")
    return repo


def test_plan_packs_core_is_generic_and_rest_goes_to_packs(profiled_repo: Path):
    from sync_aagy_ecc import plan_packs
    packs = plan_packs(profiled_repo)
    assert packs[""] == ({"tdd-workflow"}, {"planner.md"})
    assert packs["go"] == ({"golang-patterns"}, {"go-reviewer.md"})
    assert packs["extras"] == ({"healthcare"}, set())


def test_plan_packs_without_profiles_keeps_everything_in_core(repo: Path):
    from sync_aagy_ecc import plan_packs
    assert plan_packs(repo) == {"": ({"tdd-workflow"}, {"planner.md"})}


def test_sync_writes_packs_manifests_and_marketplace(profiled_repo: Path):
    sync(profiled_repo)
    ecc = profiled_repo / "aagy-ecc"
    assert (ecc / "skills" / "tdd-workflow" / "SKILL.md").is_file()
    assert not (ecc / "skills" / "golang-patterns").exists()
    assert (ecc / "packs" / "go" / "skills" / "golang-patterns" / "SKILL.md").is_file()
    assert (ecc / "packs" / "extras" / "skills" / "healthcare" / "SKILL.md").is_file()
    go_manifest = json.loads((ecc / "packs" / "go" / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert go_manifest["name"] == "aagy-ecc-go" and go_manifest["version"] == "9.9.9"
    market = json.loads((ecc / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert [p["name"] for p in market["plugins"]] == ["aagy-ecc", "aagy-ecc-go", "aagy-ecc-extras"]
    assert compare(profiled_repo).in_sync


def test_real_marketplace_lists_every_pack():
    market = json.loads((_REPO_ROOT / "aagy-ecc" / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    sources = {p["source"] for p in market["plugins"]}
    for pack in (_REPO_ROOT / "aagy-ecc" / "packs").iterdir():
        assert f"./packs/{pack.name}" in sources
        assert (pack / ".claude-plugin" / "plugin.json").is_file()


def test_session_start_condenses_long_rules(tmp_path: Path):
    import session_start_rules
    rules = tmp_path / "AGENTS.md"
    filler = "x" * 3000
    rules.write_text(f"# Reglas\n## 1. Core\n- **Workflow** (`tdd` skill): {filler}\n  1. *detalle*: {filler}\n",
                     encoding="utf-8")
    context = session_start_rules.build_response(rules)["hookSpecificOutput"]["additionalContext"]
    assert "## 1. Core" in context and "- Workflow (`tdd` skill)" in context
    assert filler not in context and str(rules) in context


def test_session_start_real_rules_fit_budget():
    import session_start_rules
    context = session_start_rules.build_response()["hookSpecificOutput"]["additionalContext"]
    assert len(context) < 3000


def test_session_start_appends_shared_backlog(tmp_path: Path):
    import subprocess
    import session_start_rules
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".governance").mkdir()
    (tmp_path / ".governance" / "docs-map.json").write_text('{"schema_version": 2}', encoding="utf-8")
    todo = tmp_path / "doc" / "06-backlog" / "TODO.md"
    todo.parent.mkdir(parents=True)
    todo.write_text("# B\n\n## 1. Backlog Activo\n\n- [ ] **Tarea pendiente**\n", encoding="utf-8")
    brief = session_start_rules.backlog_brief(str(tmp_path))
    assert "Backlog compartido" in brief and "1 pendientes" in brief
    context = session_start_rules.build_response(tmp_path / "nope.md", extra=brief)
    assert "Backlog compartido" in context["hookSpecificOutput"]["additionalContext"]


def test_session_start_backlog_brief_empty_outside_backlog(tmp_path: Path):
    import session_start_rules
    assert session_start_rules.backlog_brief(str(tmp_path)) == ""


@pytest.mark.parametrize("command", [
    "git checkout -b claude/project-thread-x",
    "git switch -c worktree-abc",
    "git push -u origin claude/project-thread-x",
    "git branch -m feature/login",
])
def test_safety_check_denies_non_canonical_branches(command: str):
    out = safety_check.build_response(command)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "[BRANCH-GUARD]" in out["hookSpecificOutput"]["permissionDecisionReason"]


@pytest.mark.parametrize("command", [
    "git switch -c fix/aagy-ecc/branch-naming",
    "git push -u origin HEAD:feat/aagy/doctor",
    "git push origin --delete claude/project-thread-x",
    "git branch -D claude/project-thread-x",
])
def test_safety_check_allows_canonical_branches(command: str):
    assert safety_check.build_response(command) == {}


def test_session_start_keeps_branch_rule_in_full():
    import session_start_rules
    context = session_start_rules.build_response()["hookSpecificOutput"]["additionalContext"]
    assert "`fix/<id>` or `fix/<project>/<id>`" in context
    assert "git push -u origin HEAD:<tipo>/<proyecto>/<nombre>" in context
