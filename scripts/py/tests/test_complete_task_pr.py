"""Fase 4 con motor Python único (complete_task_pr.py, #95)."""

import json
from pathlib import Path
import subprocess
import sys
from typing import List, Sequence, Tuple

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import complete_task_pr as ctp  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
TITLE = "[feat]-[aagy]: algo nuevo"


class FakeRunner:
    """Simula git y gh: responde por prefijo de comando y guarda las llamadas."""

    def __init__(self, branch: str = "feat/aagy/gh-42-algo", dirty: str = "", pr: str = "", fail: Sequence[str] = ()):
        self.calls: List[List[str]] = []
        self.branch, self.dirty, self.pr, self.fail = branch, dirty, pr, tuple(fail)
        self.created = False

    def __call__(self, argv: Sequence[str], cwd: Path) -> Tuple[int, str]:
        argv = list(argv)
        self.calls.append(argv)
        joined = " ".join(argv)
        if any(f in joined for f in self.fail):
            return 1, ""
        if argv[:3] == ["git", "branch", "--show-current"]:
            return 0, self.branch
        if argv[:2] == ["git", "status"]:
            return 0, self.dirty
        if argv[:3] == ["gh", "pr", "create"]:
            self.created = True
            return 0, "https://github.com/o/r/pull/7"
        if argv[:3] == ["gh", "pr", "list"]:
            return 0, self.pr or ("7" if self.created else "")
        if argv[:3] == ["gh", "issue", "view"]:
            return 0, json.dumps({"labels": [{"name": "bug"}], "milestone": {"title": "M1"}, "projectItems": []})
        if argv[-1:] == ["where"]:
            return 0, "main"
        return 0, ""

    def ran(self, *prefix: str) -> bool:
        return any(c[: len(prefix)] == list(prefix) for c in self.calls)


def _args(tmp_path: Path, *extra: str):
    return ctp.parse_args(["--repo", str(tmp_path), "--title", TITLE, "--yes", *extra])


def test_issue_detection_order(tmp_path):
    assert ctp.detect_issue("feat/x/y", tmp_path, 5) == 5
    assert ctp.detect_issue("feat/aagy/gh-42-algo", tmp_path) == 42
    (tmp_path / ".governance").mkdir()
    (tmp_path / ctp.ACTIVE_ISSUE_REL).write_text('{"issue": 9}', encoding="utf-8")
    assert ctp.detect_issue("feat/aagy/algo", tmp_path) == 9


def test_with_closes_injects_once():
    body = ctp.default_body("feat/x/y", "main")
    once = ctp.with_closes(body, 61)
    assert once.count("Closes #61") == 1
    assert ctp.with_closes(once, 61) == once
    assert "Closes #3" in ctp.with_closes("texto", 3)


def test_rejects_invalid_branch_and_detached_head(tmp_path):
    with pytest.raises(ctp.PhaseError, match="Gobernanza"):
        ctp.build_plan(tmp_path, FakeRunner(branch="main"), TITLE)
    with pytest.raises(ctp.PhaseError, match="desacoplado"):
        ctp.build_plan(tmp_path, FakeRunner(branch=""), TITLE)


def test_requires_typed_title(tmp_path):
    with pytest.raises(ctp.PhaseError, match="title"):
        ctp.build_plan(tmp_path, FakeRunner(), "")


def test_review_only_changes_nothing(tmp_path, capsys):
    run = FakeRunner()
    assert ctp.run_phase(ctp.parse_args(["--repo", str(tmp_path), "--title", TITLE, "--review-only"]), run, run) == 0
    out = capsys.readouterr().out
    assert "AVISO DE" in out and "Closes #42" in out and "--review-only" in out
    assert not run.ran("git", "push") and not run.ran("gh", "pr", "create")


def test_full_flow_opens_pr_without_merging(tmp_path, capsys):
    run = FakeRunner(dirty=" M a.py")
    assert ctp.run_phase(_args(tmp_path), run, run) == 0
    assert run.ran(ctp.PY, ctp._script("ci_local.py"))
    assert run.ran("git", "commit", "-m", TITLE)
    create = next(c for c in run.calls if c[:3] == ["gh", "pr", "create"])
    assert "--assignee" in create and "--label" in create and "--milestone" in create
    assert not run.ran("gh", "pr", "merge")
    assert "Sin auto-merge" in capsys.readouterr().out


def test_merge_only_when_asked(tmp_path):
    run = FakeRunner(pr="7")
    assert ctp.run_phase(_args(tmp_path, "--merge"), run, run) == 0
    assert run.ran("gh", "pr", "merge", "7", "--squash", "--delete-branch")
    assert run.ran("git", "checkout", "main")


def test_gate_failure_stops_before_commit(tmp_path):
    run = FakeRunner(dirty=" M a.py", fail=("ci_local.py",))
    with pytest.raises(ctp.PhaseError, match="gate"):
        ctp.run_phase(_args(tmp_path), run, run)
    assert not run.ran("git", "commit")


def test_declared_checks_run_after_ci_local(tmp_path):
    (tmp_path / ".governance").mkdir()
    (tmp_path / ctp.DOCS_MAP_REL).write_text(json.dumps({"checks": ["python check_sdk.py --strict"]}), encoding="utf-8")
    run = FakeRunner()
    ctp.quality_gate(tmp_path, run)
    assert run.calls[-1] == ["python", "check_sdk.py", "--strict"]


def test_fix_branch_generates_postmortem(tmp_path):
    run = FakeRunner(branch="fix/aagy/roto")
    ctp.run_phase(_args(tmp_path, "--skip-gate"), run, run)
    assert any("generate_postmortem.py" in " ".join(c) for c in run.calls)


def test_launchers_are_thin_and_generic():
    for rel in ("scripts/ps1/aagy.ps1", "scripts/sh/aagy.sh"):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "complete_task_pr" not in text and "gh pr" not in text and len(text.splitlines()) < 60
    assert b"\r\n" not in (REPO_ROOT / "scripts/sh/aagy.sh").read_bytes()


def test_engine_is_mirrored_in_aagy_ecc():
    for name in ("complete_task_pr.py", "generate_postmortem.py", "ci_local.py", "archive_todo.py", "validate_branch.py"):
        assert (REPO_ROOT / "aagy-ecc" / "scripts" / "py" / name).is_file(), name


def test_sh_wrapper_review_only_runs_engine():
    branch = subprocess.run(["git", "branch", "--show-current"], capture_output=True, text=True, cwd=REPO_ROOT).stdout.strip()
    res = subprocess.run(["bash", str(REPO_ROOT / "scripts/sh/aagy.sh"), "complete-task-pr", "--review-only", "--title", TITLE],
                         capture_output=True, text=True, cwd=REPO_ROOT)
    if ctp.validate_branch_name(branch)[0]:
        assert res.returncode == 0 and "AVISO DE" in res.stdout
    else:
        assert res.returncode != 0
