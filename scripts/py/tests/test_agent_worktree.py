"""Tests de los worktrees fijos por agente (agent_worktree.py)."""

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import agent_worktree as aw  # noqa: E402
import agent_worktree_guard as guard  # noqa: E402
import backlog  # noqa: E402

GH_STATE_FILE = "gh_state.json"


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True)
    return proc.stdout.strip()


@pytest.fixture()
def fake_gh(tmp_path, monkeypatch):
    """gh falso: devuelve el contenido de gh_state.json para 'gh pr list'."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    state = tmp_path / GH_STATE_FILE
    state.write_text("[]", encoding="utf-8")
    script = bin_dir / "gh"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import sys\n"
        f"print(open({str(state)!r}, encoding='utf-8').read())\n",
        encoding="utf-8",
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ['PATH']}")

    def set_pr(state_name: str, head: str = "", number: int = 7) -> None:
        state.write_text(json.dumps([{"state": state_name, "headRefOid": head, "number": number}]), encoding="utf-8")

    return set_pr


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    """Remoto bare + clon principal `home-lab` en main, con .gitignore y un .env sin versionar."""
    monkeypatch.chdir(tmp_path)
    remote = tmp_path / "remote.git"
    git(tmp_path, "init", "--bare", "-b", "main", str(remote))
    work = tmp_path / "projects"
    work.mkdir()
    main = work / "home-lab"
    git(work, "clone", str(remote), str(main))
    for key, value in (("user.email", "t@example.com"), ("user.name", "Test"), ("commit.gpgsign", "false")):
        git(main, "config", key, value)
    git(main, "checkout", "-b", "main")
    (main / ".gitignore").write_text(".env\n.env.*\nnode_modules/\n", encoding="utf-8")
    (main / "README.md").write_text("hola\n", encoding="utf-8")
    git(main, "add", ".")
    git(main, "commit", "-m", "inicio")
    git(main, "push", "-u", "origin", "main")
    (main / ".env").write_text("SECRET=1\n", encoding="utf-8")
    return main


def layout_of(main: Path) -> aw.Layout:
    layout = aw.find_layout(main)
    assert layout is not None
    return layout


def merge_on_remote(main: Path, branch_dir: Path, branch: str) -> str:
    """Simula un squash merge de la rama en GitHub: commit nuevo en origin/main; la rama remota se borra."""
    head = git(branch_dir, "rev-parse", "HEAD")
    tmp = main.parent / "merger"
    if not tmp.exists():
        git(main.parent, "clone", git(main, "remote", "get-url", "origin"), str(tmp))
        git(tmp, "config", "user.email", "m@example.com")
        git(tmp, "config", "user.name", "Merger")
    git(tmp, "fetch", "origin")
    git(tmp, "checkout", "-B", "main", "origin/main")
    git(tmp, "merge", "--squash", f"origin/{branch}")
    git(tmp, "commit", "-m", f"squash {branch}")
    git(tmp, "push", "origin", "main")
    git(tmp, "push", "origin", "--delete", branch)
    return head


def start_task(path: Path, branch: str, name: str = "x.txt") -> None:
    git(path, "switch", "-c", branch, "origin/main")
    git(path, "config", "user.email", "a@example.com")
    git(path, "config", "user.name", "Agente")
    (path / name).write_text("cambio\n", encoding="utf-8")
    git(path, "add", name)
    git(path, "commit", "-m", "tarea")
    git(path, "push", "-u", "origin", branch)


def test_init_creates_two_detached_worktrees(repo):
    layout = layout_of(repo)
    messages = aw.op_init(layout, install=False)
    for agent, suffix in (("agy", "-aagy"), ("claude", "-aagy-ecc")):
        path = repo.parent / f"home-lab{suffix}"
        assert path.is_dir()
        assert git(path, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"
        assert (path / ".env").read_text(encoding="utf-8") == "SECRET=1\n"
        assert layout.worktrees[agent] == path
    assert layout.active
    assert len(git(repo, "worktree", "list").splitlines()) == 3
    again = aw.op_init(layout, install=False)
    assert any("ya existe" in m for m in again)
    assert messages


def test_where_roles(repo, tmp_path):
    layout = layout_of(repo)
    aw.op_init(layout, install=False)
    from_wt = aw.find_layout(repo.parent / "home-lab-aagy-ecc")
    assert from_wt is not None and from_wt.main == layout.main
    assert from_wt.role(repo.parent / "home-lab-aagy-ecc" / "src") == "claude"
    assert from_wt.role(repo.parent / "home-lab-aagy") == "agy"
    assert from_wt.role(repo / "doc") == "main"
    assert from_wt.role(tmp_path) == "other"
    assert aw.find_layout(repo.parent / "home-lab-aagy", use_git=False).main == layout.main


def test_recycle_merged_clean(repo, fake_gh):
    layout = layout_of(repo)
    aw.op_init(layout, install=False)
    wt = layout.worktrees["claude"]
    start_task(wt, "feat/home-lab/t1")
    head = merge_on_remote(repo, wt, "feat/home-lab/t1")
    fake_gh("MERGED", head)
    messages = aw.op_recycle(layout, "claude", install=False)
    assert git(wt, "rev-parse", "HEAD") == git(repo, "rev-parse", "origin/main")
    assert git(wt, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"
    assert not git(repo, "branch", "--list", "feat/home-lab/t1")
    assert (wt / ".env").is_file()
    assert git(repo, "rev-parse", "HEAD") == git(repo, "rev-parse", "origin/main")
    assert any("principal actualizado" in m for m in messages)


def test_recycle_blocks_on_dirty(repo, fake_gh):
    layout = layout_of(repo)
    aw.op_init(layout, install=False)
    wt = layout.worktrees["agy"]
    start_task(wt, "fix/home-lab/t2")
    head = merge_on_remote(repo, wt, "fix/home-lab/t2")
    fake_gh("MERGED", head)
    (wt / "README.md").write_text("sin guardar\n", encoding="utf-8")
    with pytest.raises(aw.WorktreeError) as err:
        aw.op_recycle(layout, "agy", install=False)
    assert err.value.code == aw.EXIT_BLOCKED
    assert (wt / "README.md").read_text(encoding="utf-8") == "sin guardar\n"
    assert git(wt, "rev-parse", "--abbrev-ref", "HEAD") == "fix/home-lab/t2"


def test_recycle_blocks_on_commits_after_pr(repo, fake_gh):
    layout = layout_of(repo)
    aw.op_init(layout, install=False)
    wt = layout.worktrees["claude"]
    start_task(wt, "feat/home-lab/t3")
    head = merge_on_remote(repo, wt, "feat/home-lab/t3")
    (wt / "y.txt").write_text("más\n", encoding="utf-8")
    git(wt, "add", "y.txt")
    git(wt, "commit", "-m", "posterior")
    fake_gh("MERGED", head)
    with pytest.raises(aw.WorktreeError) as err:
        aw.op_recycle(layout, "claude", install=False)
    assert err.value.code == aw.EXIT_BLOCKED
    assert "posteriores" in str(err.value)


def test_recycle_not_merged(repo, fake_gh):
    layout = layout_of(repo)
    aw.op_init(layout, install=False)
    wt = layout.worktrees["claude"]
    start_task(wt, "feat/home-lab/t4")
    fake_gh("OPEN", git(wt, "rev-parse", "HEAD"))
    assert aw.op_recycle(layout, "claude", if_merged=True, install=False) == []
    with pytest.raises(aw.WorktreeError) as err:
        aw.op_recycle(layout, "claude", install=False)
    assert err.value.code == aw.EXIT_NOT_MERGED
    assert git(wt, "rev-parse", "--abbrev-ref", "HEAD") == "feat/home-lab/t4"


def test_recycle_hard_recreate(repo, fake_gh):
    layout = layout_of(repo)
    aw.op_init(layout, install=False)
    wt = layout.worktrees["agy"]
    (wt / "node_modules").mkdir()
    (wt / "node_modules" / "basura.js").write_text("x\n", encoding="utf-8")
    (wt / ".env").unlink()
    aw.op_recycle(layout, "agy", hard_recreate=True, install=False)
    assert not (wt / "node_modules").exists()
    assert (wt / ".env").is_file()


def test_recycle_keeps_dirty_main(repo, fake_gh):
    layout = layout_of(repo)
    aw.op_init(layout, install=False)
    wt = layout.worktrees["claude"]
    start_task(wt, "feat/home-lab/t5")
    head = merge_on_remote(repo, wt, "feat/home-lab/t5")
    fake_gh("MERGED", head)
    (repo / "README.md").write_text("de Master\n", encoding="utf-8")
    before = git(repo, "rev-parse", "HEAD")
    messages = aw.op_recycle(layout, "claude", install=False)
    assert git(repo, "rev-parse", "HEAD") == before
    assert (repo / "README.md").read_text(encoding="utf-8") == "de Master\n"
    assert any("cambios sin commit" in m for m in messages)


def test_install_plan_regenerates_only_what_main_has(repo):
    layout = layout_of(repo)
    (repo / "web").mkdir()
    (repo / "web" / "package.json").write_text("{}", encoding="utf-8")
    (repo / "web" / "package-lock.json").write_text("{}", encoding="utf-8")
    git(repo, "add", "web")
    git(repo, "commit", "-m", "web")
    (repo / "web" / "node_modules").mkdir()
    (repo / "web" / "node_modules" / "x.js").write_text("", encoding="utf-8")
    target = repo.parent / "copia"
    (target / "web").mkdir(parents=True)
    (target / "web" / "package-lock.json").write_text("{}", encoding="utf-8")
    plan = aw.install_plan(layout.main, target, aw.load_config(layout.main))
    assert plan == [(target / "web", ["npm", "ci"])]
    files = aw.config_files_to_copy(layout.main, aw.load_config(layout.main))
    assert files == [".env"]


# --------------------------------------------------------------------------- guarda


@pytest.fixture()
def active(repo):
    layout = layout_of(repo)
    aw.op_init(layout, install=False)
    return layout


def test_guard_file_paths(active):
    claude = active.worktrees["claude"]
    assert guard.guard_file("claude", claude, "src/a.py") is None
    assert guard.guard_file("claude", claude, str(active.main / "README.md"))
    assert guard.guard_file("claude", claude, "../home-lab/README.md")
    assert guard.guard_file("claude", claude, str(active.worktrees["agy"] / "x.md"))
    assert guard.guard_file("agy", active.worktrees["agy"], str(claude / "x.md"))


def test_guard_commands(active):
    claude, main = active.worktrees["claude"], active.main
    allowed = [
        "git status && git log -1",
        f'git -C "{main}" status',
        f"cat {main}/README.md",
        "git commit -m x",
        f"cd {main} && git log",
        f"python scripts/py/agent_worktree.py recycle --agent claude",
    ]
    for command in allowed:
        assert guard.guard_command("claude", claude, command) is None, command
    denied = [
        f'git -C "{main}" commit -m x',
        f"cd {main} && git commit -m x",
        f"rm -f {main}/README.md",
        f"echo hola > {active.worktrees['agy']}/x.txt",
        "git worktree add ../otro",
        "claude --worktree prueba",
    ]
    for command in denied:
        assert guard.guard_command("claude", claude, command), command
    assert guard.guard_command("claude", main, "npm install")
    assert guard.guard_command("claude", main, "git status") is None


def test_guard_inactive_without_marker(repo):
    assert guard.guard_file("claude", repo, "README.md") is None
    assert guard.guard_command("claude", repo, "git commit -m x") is None


def test_guard_payload_formats(active):
    main = active.main
    claude_payload = {"tool_name": "Write", "tool_input": {"file_path": str(main / "a.md")}, "cwd": str(active.worktrees["claude"])}
    response = guard.guard_response(guard.guard_payload("claude", claude_payload, "claude"), "claude")
    assert response["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert guard.guard_payload("claude", {"tool_name": "EnterWorktree", "tool_input": {}}, "claude")
    agy_payload = {"toolCall": {"name": "run_command", "args": {"CommandLine": "git commit -m x", "Cwd": str(main)}}}
    assert guard.guard_response(guard.guard_payload("agy", agy_payload, "agy"), "agy")["decision"] == "deny"
    ok_payload = {"toolCall": {"name": "write_file", "args": {"Path": str(active.worktrees["agy"] / "a.md")}}}
    assert guard.guard_response(guard.guard_payload("agy", ok_payload, "agy"), "agy") == {"decision": "allow"}


def test_session_notice(active):
    assert "AVISO" in guard.session_notice("claude", active.main)
    assert "Trabaja solo aquí" in guard.session_notice("claude", active.worktrees["claude"])


# --------------------------------------------------------------------------- backlog


TODO = "# Backlog\n\n## 1. Backlog Activo\n\n- [ ] **Tarea uno**\n  <!-- aagy-task: id=t-uno -->\n"


def test_backlog_claim_and_handoff_between_worktrees(repo):
    todo = repo / "doc" / "TODO.md"
    todo.parent.mkdir(parents=True)
    todo.write_text(TODO, encoding="utf-8")
    git(repo, "add", "doc")
    git(repo, "commit", "-m", "todo")
    git(repo, "push", "origin", "main")
    layout = layout_of(repo)
    aw.op_init(layout, install=False)
    claude, agy = layout.worktrees["claude"], layout.worktrees["agy"]
    ctx = backlog.Context(repo=backlog.locate_repo(claude), cwd=claude)
    entry = backlog.op_claim(ctx, "t-uno", "claude", None, False, False)
    assert entry["branch"] == "feat/home-lab/t-uno"
    assert git(claude, "rev-parse", "--abbrev-ref", "HEAD") == "feat/home-lab/t-uno"
    assert entry[backlog.K_AGENT_WORKTREE] == str(claude)
    backlog.op_handoff(ctx, "claude", "t-uno", "sigue tú", "agy")
    assert git(claude, "rev-parse", "--abbrev-ref", "HEAD") == "HEAD"
    ctx_agy = backlog.Context(repo=backlog.locate_repo(agy), cwd=agy)
    entry_agy = backlog.op_claim(ctx_agy, "t-uno", "agy", None, False, False)
    assert entry_agy["previous_owner"] == "claude"
    assert git(agy, "rev-parse", "--abbrev-ref", "HEAD") == "feat/home-lab/t-uno"
    assert entry_agy[backlog.K_AGENT_WORKTREE] == str(agy)


def test_npm_install_without_lockfile_does_not_create_one(tmp_path):
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")
    import agent_worktree_provision as prov

    assert prov.installer_for("node_modules", tmp_path) == [["npm", "install", "--no-package-lock"]]
