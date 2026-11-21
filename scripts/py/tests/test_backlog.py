"""Tests del backlog compartido entre agentes (backlog.py)."""

import json
import subprocess
import sys
import threading
from datetime import timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backlog  # noqa: E402
from backlog import (  # noqa: E402
    BacklogError,
    Context,
    brief_lines,
    iso,
    load_state,
    locate_repo,
    main,
    op_add,
    op_checkpoint,
    op_claim,
    op_done,
    op_epic_add,
    op_epic_close,
    op_epic_sync,
    op_handoff,
    op_init,
    op_list,
    op_next,
    op_transition,
    parse_backlog,
    save_state,
    slugify,
    utc_now,
    validate_id,
)

TODO_SAMPLE = """# Backlog

## 1. Backlog Activo

* [ ] **Tarea: Configurar TLS en el proxy**
  * **01 - ROLE:** SRE.

- [ ] **Migrar logs**
  <!-- aagy-task: id=logs epic=observabilidad -->

- [x] **Tarea vieja**

## Épica: Observabilidad

- [ ] **Exportar métricas**
"""


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "proyecto"
    root.mkdir()
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "t@example.com")
    git(root, "config", "user.name", "t")
    (root / ".governance").mkdir()
    (root / ".governance" / "docs-map.json").write_text(json.dumps({"schema_version": 2}), encoding="utf-8")
    todo = root / "doc" / "06-backlog" / "TODO.md"
    todo.parent.mkdir(parents=True)
    todo.write_text(TODO_SAMPLE, encoding="utf-8")
    git(root, "add", ".")
    git(root, "commit", "-qm", "init")
    return root


def ctx_for(path: Path) -> Context:
    return Context(repo=locate_repo(path), cwd=path)


# ----------------------------------------------------------------- parser


def test_parse_backlog_ids_epics_and_done():
    parsed = parse_backlog(TODO_SAMPLE)
    ids = [t.task_id for t in parsed.tasks]
    assert ids == ["configurar-tls-en-el-proxy", "logs", "tarea-vieja", "exportar-metricas"]
    by_id = {t.task_id: t for t in parsed.tasks}
    assert by_id["logs"].epic == "observabilidad"
    assert by_id["exportar-metricas"].epic == "observabilidad"
    assert by_id["configurar-tls-en-el-proxy"].epic is None
    assert by_id["tarea-vieja"].done_mark is True
    assert [e.epic_id for e in parsed.epics] == ["observabilidad"]


def test_parse_duplicate_titles_get_suffix():
    parsed = parse_backlog("- [ ] **A**\n- [ ] **A**\n")
    assert [t.task_id for t in parsed.tasks] == ["a", "a-2"]


def test_slugify_and_validate_id():
    assert slugify("Tarea: Añadir Épica ÚNICA!") == "tarea-anadir-epica-unica"
    assert slugify("") == "tarea"
    assert validate_id("ok-1") == "ok-1"
    for bad in ("../x", "A", "a b", "a/b", "", "x" * 65):
        with pytest.raises(BacklogError):
            validate_id(bad)


# ----------------------------------------------------------------- estado compartido


def test_state_lives_in_git_common_dir(repo: Path):
    info = locate_repo(repo)
    assert info.is_git
    assert info.state_dir == (repo / ".git" / "aagy-backlog").resolve()


def test_claim_blocks_other_agent_and_next_skips(repo: Path):
    ctx = ctx_for(repo)
    entry = op_claim(ctx, "logs", "claude", None, False, False)
    assert entry["owner"] == "claude"
    assert entry["branch"] == "feat/proyecto/logs"
    with pytest.raises(BacklogError, match="la tiene claude"):
        op_claim(ctx, "logs", "agy", None, False, False)
    nxt = op_next(ctx, "agy", None)
    assert nxt is not None and nxt.task_id == "configurar-tls-en-el-proxy"
    rows = {r["id"]: r for r in op_list(ctx, None, None, False)}
    assert rows["logs"]["owner"] == "claude"
    assert "tarea-vieja" not in rows


def test_claim_same_agent_is_idempotent(repo: Path):
    ctx = ctx_for(repo)
    op_claim(ctx, "logs", "claude", None, False, False)
    assert op_claim(ctx, "logs", "claude", None, False, False)["owner"] == "claude"


def test_claim_done_task_fails(repo: Path):
    with pytest.raises(BacklogError, match="terminada"):
        op_claim(ctx_for(repo), "tarea-vieja", "claude", None, False, False)


def test_stale_claim_can_be_taken(repo: Path, monkeypatch: pytest.MonkeyPatch):
    ctx = ctx_for(repo)
    op_claim(ctx, "logs", "claude", None, False, False)
    state = load_state(ctx.repo)
    state["tasks"]["logs"]["updated"] = iso(utc_now() - timedelta(hours=5))
    save_state(ctx.repo, state)
    entry = op_claim(ctx, "logs", "agy", None, False, False)
    assert entry["owner"] == "agy"
    assert entry["previous_owner"] == "claude"
    monkeypatch.setenv("AAGY_BACKLOG_TTL_HOURS", "10")
    state = load_state(ctx.repo)
    state["tasks"]["logs"]["updated"] = iso(utc_now() - timedelta(hours=5))
    save_state(ctx.repo, state)
    with pytest.raises(BacklogError):
        op_claim(ctx, "logs", "claude", None, False, False)


def test_concurrent_claims_have_single_winner(repo: Path):
    winners = []
    errors = []

    def attempt(agent: str) -> None:
        try:
            op_claim(ctx_for(repo), "configurar-tls-en-el-proxy", agent, None, False, False)
            winners.append(agent)
        except BacklogError as exc:
            errors.append(str(exc))

    threads = [threading.Thread(target=attempt, args=(a,)) for a in ("claude", "agy") * 4]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    owner = load_state(locate_repo(repo))["tasks"]["configurar-tls-en-el-proxy"]["owner"]
    assert set(winners) == {owner}
    assert errors


def test_worktree_shares_state(repo: Path):
    ctx = ctx_for(repo)
    entry = op_claim(ctx, "logs", "claude", None, True, False)
    wt = Path(entry["worktree"])
    assert wt.is_dir()
    assert wt == repo.parent / "proyecto.wt" / "logs"
    assert git(wt, "rev-parse", "--abbrev-ref", "HEAD").strip() == "feat/proyecto/logs"
    wt_ctx = ctx_for(wt)
    assert wt_ctx.repo.state_dir == ctx.repo.state_dir
    with pytest.raises(BacklogError):
        op_claim(wt_ctx, "logs", "agy", None, False, False)


# ----------------------------------------------------------------- checkpoint y relevo


def test_checkpoint_records_git_snapshot(repo: Path):
    ctx = ctx_for(repo)
    op_claim(ctx, "logs", "claude", None, False, False)
    (repo / "nuevo.txt").write_text("x", encoding="utf-8")
    assert op_checkpoint(ctx, "claude", None, "paso 1 hecho") == ["logs"]
    entry = load_state(ctx.repo)["tasks"]["logs"]
    assert entry["note"] == "paso 1 hecho"
    assert entry["current_branch"] == "main"
    assert entry["branch"] == "feat/proyecto/logs"
    assert "init" in entry["head"]
    assert "nuevo.txt" in entry["dirty"]


def test_checkpoint_adopts_real_task_branch(repo: Path):
    ctx = ctx_for(repo)
    op_claim(ctx, "logs", "claude", None, False, False)
    git(repo, "switch", "-q", "-c", "fix/proyecto/logs-rotacion")
    op_checkpoint(ctx, "claude", None, None)
    assert load_state(ctx.repo)["tasks"]["logs"]["branch"] == "fix/proyecto/logs-rotacion"


def test_checkpoint_without_tasks_is_noop(repo: Path):
    assert op_checkpoint(ctx_for(repo), "agy", None, None) == []


def test_handoff_writes_note_and_other_agent_continues(repo: Path):
    ctx = ctx_for(repo)
    op_claim(ctx, "logs", "claude", None, False, False)
    op_checkpoint(ctx, "claude", None, "falta el test de rotación")
    results = op_handoff(ctx, "claude", None, None, "agy")
    assert [tid for tid, _ in results] == ["logs"]
    note_file = results[0][1]
    content = note_file.read_text(encoding="utf-8")
    assert "falta el test de rotación" in content
    assert "backlog.py claim logs" in content
    assert op_next(ctx, "agy", None).task_id == "logs"
    entry = op_claim(ctx, "logs", "agy", None, False, False)
    assert entry["previous_owner"] == "claude"
    assert entry["branch"] == "feat/proyecto/logs"


def test_brief_lists_handoff_first(repo: Path):
    ctx = ctx_for(repo)
    op_claim(ctx, "configurar-tls-en-el-proxy", "agy", None, False, False)
    op_claim(ctx, "logs", "claude", None, False, False)
    op_handoff(ctx, "claude", "logs", "seguir", None)
    lines = brief_lines(ctx)
    assert len(lines) <= 15
    assert lines[1].startswith("- [handoff (claude)] logs")
    assert any("in_progress (agy)" in line for line in lines)


def test_brief_empty_without_backlog(tmp_path: Path):
    assert brief_lines(ctx_for(tmp_path)) == []


# ----------------------------------------------------------------- transiciones y cierre


def test_transition_protects_owner(repo: Path):
    ctx = ctx_for(repo)
    op_claim(ctx, "logs", "claude", None, False, False)
    with pytest.raises(BacklogError, match="es de claude"):
        op_transition(ctx, "logs", "agy", "blocked", "x", False)
    op_transition(ctx, "logs", "human", "todo", None, True)
    assert "owner" not in load_state(ctx.repo)["tasks"]["logs"]


def test_done_marks_and_archives(repo: Path):
    ctx = ctx_for(repo)
    op_claim(ctx, "logs", "claude", None, False, False)
    op_handoff(ctx, "claude", "logs", "x", None)
    op_claim(ctx, "logs", "agy", None, False, False)
    messages = op_done(ctx, "logs", "agy", "verificado", True, False)
    todo = ctx.repo.todo_path.read_text(encoding="utf-8")
    assert "Migrar logs" not in todo
    assert "Configurar TLS" in todo
    archived = list(ctx.repo.done_dir.glob("TODO_Migrar_logs_*.md"))
    assert archived
    assert not (ctx.repo.quick_dir / "HANDOFF_logs.md").exists()
    assert any("Archivada" in m for m in messages)


def test_done_without_archive_keeps_checked_task(repo: Path):
    ctx = ctx_for(repo)
    op_done(ctx, "logs", "claude", None, False, False)
    assert "- [x] **Migrar logs**" in ctx.repo.todo_path.read_text(encoding="utf-8")


# ----------------------------------------------------------------- épicas y alta


def test_epic_add_task_sync_and_close(repo: Path):
    ctx = ctx_for(repo)
    epic_id = op_epic_add(ctx, "Backup nocturno", "Copias diarias verificadas")
    assert epic_id == "backup-nocturno"
    op_add(ctx, "Script de backup", epic_id, None, "**01 - ROLE:** SRE.")
    op_add(ctx, "Restaurar prueba", epic_id, "restaurar", None)
    parsed = parse_backlog(ctx.repo.todo_path.read_text(encoding="utf-8"))
    by_id = {t.task_id: t for t in parsed.tasks}
    assert by_id["script-de-backup"].epic == epic_id
    assert by_id["restaurar"].epic == epic_id
    summary = op_epic_sync(ctx, epic_id)
    assert summary[0]["total"] == 2 and summary[0]["counts"] == {"todo": 2}
    with pytest.raises(BacklogError, match="sin terminar"):
        op_epic_close(ctx, epic_id, "claude")
    assert op_next(ctx, "agy", epic_id).task_id == "script-de-backup"
    op_done(ctx, "script-de-backup", "agy", None, False, False)
    op_done(ctx, "restaurar", "agy", None, False, False)
    assert "cerrada" in op_epic_close(ctx, epic_id, "claude")[0]


def test_add_rejects_duplicates_and_unknown_epic(repo: Path):
    ctx = ctx_for(repo)
    with pytest.raises(BacklogError, match="Ya existe"):
        op_add(ctx, "Otra", None, "logs", None)
    with pytest.raises(BacklogError, match="No existe la épica"):
        op_add(ctx, "Otra", "inexistente", None, None)
    new_id = op_add(ctx, "Tarea suelta", None, None, None)
    text = ctx.repo.todo_path.read_text(encoding="utf-8")
    assert text.index("Tarea suelta") < text.index("Configurar TLS")
    assert new_id == "tarea-suelta"


# ----------------------------------------------------------------- init y CLI


def test_init_creates_structure_in_empty_repo(tmp_path: Path):
    root = tmp_path / "homelab-app"
    root.mkdir()
    git(root, "init", "-q")
    ctx = ctx_for(root)
    created = op_init(ctx)
    assert ".governance/docs-map.json" in created
    assert ctx.repo.todo_path.is_file()
    assert (root / "doc" / "06-backlog" / "quick").is_dir()
    assert op_list(ctx, None, None, False) == []
    assert op_init(ctx) == ["Nada que crear: el backlog ya existe."]


def test_init_respects_legacy_layout(tmp_path: Path):
    (tmp_path / "doc").mkdir()
    (tmp_path / "doc" / "TODO.md").write_text("- [ ] **X**\n", encoding="utf-8")
    ctx = ctx_for(tmp_path)
    op_init(ctx)
    assert not (tmp_path / ".governance").exists()
    assert [t.task_id for t in ctx.backlog().tasks] == ["x"]


def test_cli_auto_is_silent_and_never_fails(tmp_path: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["--repo", str(tmp_path), "--quiet", "checkpoint", "--auto"]) == 0
    assert main(["--repo", str(tmp_path), "handoff", "--auto", "--agent", "claude"]) == 0
    assert capsys.readouterr().out == ""


def test_cli_flow_and_errors(repo: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch):
    base = ["--repo", str(repo)]
    assert main(base + ["claim", "logs", "--agent", "claude"]) == 0
    assert "Reclamada: logs" in capsys.readouterr().out
    assert main(base + ["claim", "logs", "--agent", "agy"]) == 1
    assert "la tiene claude" in capsys.readouterr().err
    monkeypatch.setenv("AAGY_AGENT", "claude")
    assert main(base + ["handoff", "--note", "seguir con tests"]) == 0
    capsys.readouterr()
    assert main(base + ["list", "--brief"]) == 0
    out = capsys.readouterr().out
    assert "handoff (claude)" in out
    assert main(base + ["epic", "sync"]) == 0
    assert "Épica observabilidad" in capsys.readouterr().out
    monkeypatch.delenv("AAGY_AGENT")
    assert main(base + ["next"]) == 1
    assert "--agent" in capsys.readouterr().err


def test_cli_json_output(repo: Path, capsys: pytest.CaptureFixture[str]):
    assert main(["--repo", str(repo), "--json", "list", "--all"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert {r["id"] for r in rows} >= {"logs", "tarea-vieja"}


def test_lock_breaks_when_stale(repo: Path):
    ctx = ctx_for(repo)
    ctx.repo.state_dir.mkdir(parents=True, exist_ok=True)
    lock = ctx.repo.state_dir / backlog.LOCK_FILE_NAME
    lock.write_text("999 viejo", encoding="utf-8")
    import os
    import time

    old = time.time() - 120
    os.utime(lock, (old, old))
    assert op_claim(ctx, "logs", "claude", None, False, False)["owner"] == "claude"
    assert not lock.exists()
