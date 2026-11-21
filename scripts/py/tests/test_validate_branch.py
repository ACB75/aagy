import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_branch import (
    validate_branch_name,
    is_fix_branch
)

@pytest.mark.parametrize("branch", [
    "fix/SEC-001",
    "fix/auth-leak",
    "fix/kakebo/issue-102",
    "fix/cluster/timeout-p99",
    "fix/login-redirect-302",
])
def test_valid_fix_branches(branch: str):
    valid, msg = validate_branch_name(branch)
    assert valid is True
    assert msg == "OK"
    assert is_fix_branch(branch) is True

@pytest.mark.parametrize("branch", [
    "feat/aagy/new-feature",
    "feat/cluster-portal",
    "refactor/kakebo/signals",
    "infra/cluster/traefik-v3",
    "chore/deps-update",
    "docs/adr-0012",
    "test/e2e-auth",
])
def test_valid_task_branches(branch: str):
    valid, msg = validate_branch_name(branch)
    assert valid is True
    assert msg == "OK"
    assert is_fix_branch(branch) is False

@pytest.mark.parametrize("branch", [
    "main",
    "master",
    "bugfix/broken",
    "hotfix/urgent",
    "patch/memory",
    "FEAT/UPPERCASE",
    "fix/has space in name",
    "invalid_no_slash",
    "feat//double-slash",
    "feat/trailing-slash/",
])
def test_invalid_task_branches(branch: str):
    valid, msg = validate_branch_name(branch)
    assert valid is False
    assert "no cumple la convención canónica" in msg or "no permitida" in msg


from validate_branch import branches_in_command, command_rejection, invalid_branches_in_command  # noqa: E402


def _current():
    return "claude/project-thread-x"


@pytest.mark.parametrize("command,expected", [
    ("git checkout -b claude/foo", ["claude/foo"]),
    ("git -C /repo switch --create=feat/a/b", ["feat/a/b"]),
    ("git branch worktree-abc", ["worktree-abc"]),
    ("git branch -m old feature/x", ["feature/x"]),
    ("git push -u origin HEAD:fix/aagy/x", ["fix/aagy/x"]),
    ("git push -u origin HEAD", ["claude/project-thread-x"]),
    ("git push", ["claude/project-thread-x"]),
    ("git add . && git commit -m 'x; y' && git push origin +refs/heads/chore/x", ["chore/x"]),
    ("git push origin --delete claude/x", []),
    ("git push origin :claude/x", []),
    ("git push origin v1.2.0-sandbox", []),
    ("git push origin refs/tags/v1", []),
    ("git branch -D claude/x", []),
    ("git branch --show-current", []),
    ("echo git checkout -b x", []),
])
def test_branches_in_command(command, expected):
    assert branches_in_command(command, _current) == expected


def test_invalid_branches_allows_main_and_canonical():
    assert invalid_branches_in_command("git push origin main", _current) == []
    assert invalid_branches_in_command("git push -u origin HEAD", _current) == ["claude/project-thread-x"]


def test_command_rejection_message():
    assert command_rejection("ls -la", _current) == ""
    assert "[BRANCH-GUARD]" in command_rejection("git checkout -b claude/foo", _current)


def test_cli_git_command_exit_codes():
    import subprocess
    script = Path(__file__).resolve().parent.parent / "validate_branch.py"
    bad = subprocess.run([sys.executable, str(script), "--git-command", "git switch -c claude/x"],
                         capture_output=True, text=True, check=False)
    good = subprocess.run([sys.executable, str(script), "--git-command", "git switch -c fix/aagy/x"],
                          capture_output=True, text=True, check=False)
    assert bad.returncode == 1 and "[BRANCH-GUARD]" in bad.stdout
    assert good.returncode == 0 and good.stdout == ""
