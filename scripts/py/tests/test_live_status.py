#!/usr/bin/env python3
"""Tests unitarios y de integración para live_status.py (Opción B: estado, catálogo y telemetría viva)."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import consumer_refs  # noqa: E402
import live_status as ls  # noqa: E402

SKILL_TMPL = "---\nname: {name}\ndescription: Skill {name}\n---\n# {name}\n"
AGENT_TMPL = "---\nname: {name}\ndescription: Agent {name}\nmodel: inherit\n---\n"
STATUS_INITIAL = """# Estado de Salud | Demo

> **Versión**: `1.0.0` (`/doc` v2)

## 1. Métricas de calidad

| Paso | Estado |
| :--- | :---: |
| `pytest` | ✅ |
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    root = tmp_path / "aagy"
    _write(root / "plugin.json", json.dumps({"name": "aagy", "version": "5.2.0"}))
    _write(root / "rules" / "AGENTS.md", "# Rules\n\n- Regla base\n")
    _write(root / "hooks.json", json.dumps({"g": {"SessionStart": [], "Stop": []}}))
    for name in ("tdd-workflow", "aagy-doctor"):
        _write(root / "skills" / name / "SKILL.md", SKILL_TMPL.format(name=name))
    _write(root / "agents" / "planner.md", AGENT_TMPL.format(name="planner"))

    ecc = root / "aagy-ecc"
    _write(ecc / ".claude-plugin" / "plugin.json", json.dumps({"name": "aagy-ecc", "version": "5.2.0"}))
    _write(ecc / "hooks" / "hooks.json", json.dumps({"hooks": {"SessionStart": [], "Stop": []}}))
    _write(ecc / "skills" / "tdd-workflow" / "SKILL.md", SKILL_TMPL.format(name="tdd-workflow"))
    _write(ecc / "agents" / "planner.md", AGENT_TMPL.format(name="planner"))
    _write(ecc / "commands" / "aagy-ui.md", "---\ndescription: UI\n---\n")
    _write(ecc / "packs" / "go" / ".claude-plugin" / "plugin.json", json.dumps({"name": "aagy-ecc-go"}))

    _write(root / ".governance" / "docs-map.json", json.dumps({"schema_version": 2}))
    _write(root / ".governance" / "aagy.json", json.dumps({"consumer_refs": ["secret-client", "C:\\Workspace"]}))
    _write(root / "doc" / "STATUS.md", STATUS_INITIAL)
    _write(root / "doc" / "LOG.md", "# Log\n")
    _write(root / "doc" / "06-backlog" / "TODO.md", "# Backlog\n\n## 1. Backlog Activo\n\n- [ ] **Tarea demo**\n")
    _write(root / "doc" / "02-adr" / "ADR_aagy_0001_two_tier_global_plugin_and_project_scaffolding.md", "# ADR-0001\n")
    _write(root / "doc" / "02-adr" / "ADR_aagy_0004_stack_profiles_declared_by_consumer_repo.md", "# ADR-0004\n")
    _write(root / "doc" / "04-operations" / "runbooks" / "MANUAL_session_token_telemetry.md", "# Manual\n")
    _write(root / "doc" / "04-operations" / "runbooks" / "MANUAL_ui.md", "# UI\n")
    return root


@pytest.fixture()
def sample_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    # Antigravity sessions
    agy1 = home / ".gemini" / "antigravity" / "brain" / "sess-agy-1" / ".system_generated" / "logs" / "transcript.jsonl"
    _write(agy1, json.dumps({"step_index": 0, "content": "x" * 3800}) + "\n")
    agy2 = home / ".gemini" / "antigravity" / "brain" / "sess-agy-2" / ".system_generated" / "logs" / "transcript.jsonl"
    _write(agy2, json.dumps({"step_index": 0, "content": "y" * 190000}) + "\n")

    # Claude Code sessions (incluye carpeta con consumer_ref para validar sanitización)
    c1 = home / ".claude" / "projects" / "C--Workspace-projects-aagy" / "claude-sess-1.jsonl"
    _write(
        c1,
        json.dumps(
            {
                "type": "assistant",
                "sessionId": "claude-sess-1",
                "timestamp": "2026-11-25T21:00:00Z",
                "message": {
                    "model": "claude-opus-5-5",
                    "usage": {
                        "input_tokens": 100,
                        "cache_creation_input_tokens": 1000,
                        "cache_read_input_tokens": 900,
                        "output_tokens": 250,
                    },
                },
            }
        )
        + "\n",
    )
    c2 = home / ".claude" / "projects" / "C--Workspace--secret-client" / "claude-sess-2.jsonl"
    _write(
        c2,
        json.dumps(
            {
                "type": "assistant",
                "sessionId": "claude-sess-2",
                "timestamp": "2026-11-25T20:00:00Z",
                "message": {
                    "model": "claude-sonnet-4-5",
                    "usage": {"input_tokens": 500, "output_tokens": 50},
                },
            }
        )
        + "\n",
    )
    return home


def test_collect_snapshot_catalog_and_telemetry(sample_repo: Path, sample_home: Path) -> None:
    snap = ls.collect_snapshot(sample_repo, home=sample_home)
    assert snap.version == "5.2.0"
    assert snap.catalog.agy_skills == 2
    assert snap.catalog.agy_agents == 1
    assert snap.catalog.ecc_skills == 1
    assert snap.catalog.ecc_agents == 1
    assert snap.catalog.ecc_commands == 1
    assert snap.catalog.ecc_packs == ("go",)
    assert snap.backlog.open_tasks == 1

    assert snap.antigravity.total_sessions == 2
    assert snap.antigravity.over_threshold == 1
    assert snap.antigravity.total_estimated_tokens >= 51000

    assert snap.claude.total_sessions == 2
    assert snap.claude.total_context_tokens == 2500
    assert snap.claude.total_output_tokens == 300
    workspaces = {s.workspace for s in snap.claude.recent}
    assert "aagy" in workspaces
    assert "external" in workspaces
    assert all("secret-client" not in s.workspace.lower() for s in snap.claude.recent)


def test_sync_updates_status_md_and_live_page_idempotently(sample_repo: Path, sample_home: Path) -> None:
    res = ls.sync_live_pages(sample_repo, home=sample_home, write_status=True)
    status_text = res.status_path.read_text(encoding="utf-8")
    live_text = res.live_path.read_text(encoding="utf-8")

    assert ls.MARKER_CATALOG_START in status_text and ls.MARKER_CATALOG_END in status_text
    assert ls.MARKER_TELEMETRY_START in status_text and ls.MARKER_TELEMETRY_END in status_text
    assert "ADR-0001" in status_text and "ADR-0004" in status_text
    assert "cc240ae0-bb1b-4e71-8287-891d6f5ee2a0" in status_text
    assert "sess-agy-2" in live_text and "claude-sess-1" in live_text

    # Cero fugas de consumer_refs ni rutas locales prohibidas
    terms, hits = consumer_refs.audit(sample_repo)
    assert terms
    assert hits == [], hits
    assert "secret-client" not in live_text.lower()
    assert "c:\\workspace" not in live_text.lower()

    # Check pasa en verde tras sync
    assert ls.check_status_doc(sample_repo) == []

    # Idempotencia al volver a sincronizar
    ls.sync_live_pages(sample_repo, home=sample_home, write_status=True)
    status_again = res.status_path.read_text(encoding="utf-8")
    assert status_again.count(ls.MARKER_TELEMETRY_START) == 1
    assert status_again.count(ls.MARKER_CATALOG_START) == 1


def test_check_detects_missing_or_stale_status(sample_repo: Path) -> None:
    problems = ls.check_status_doc(sample_repo)
    assert problems
    ls.sync_live_pages(sample_repo, write_status=True)
    assert ls.check_status_doc(sample_repo) == []
    # Simular deriva manual en conteo de skills
    status_path = sample_repo / "doc" / "STATUS.md"
    status_path.write_text(status_path.read_text(encoding="utf-8").replace("2 en `skills/`", "999 en `skills/`"), encoding="utf-8")
    assert any("Catálogo" in p or "skills" in p for p in ls.check_status_doc(sample_repo))


def test_telemetry_cache_reuses_unchanged_transcripts(sample_repo: Path, sample_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0
    orig = ls.stm.analyze_transcript

    def tracked(path, threshold=ls.stm.DEFAULT_THRESHOLD):
        nonlocal calls
        calls += 1
        return orig(path, threshold)

    monkeypatch.setattr(ls.stm, "analyze_transcript", tracked)
    ls.sync_live_pages(sample_repo, home=sample_home, write_status=False)
    assert calls == 2
    # Segunda corrida sin cambios usa la caché
    ls.sync_live_pages(sample_repo, home=sample_home, write_status=False)
    assert calls == 2


def test_hook_mode_respects_agent_worktree_and_keeps_git_clean(sample_repo: Path, sample_home: Path) -> None:
    def git(cwd: Path, *args: str) -> str:
        return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()

    remote = sample_repo.parent / "remote.git"
    git(sample_repo.parent, "init", "--bare", "-b", "main", str(remote))
    git(sample_repo, "init", "-q", "-b", "main")
    git(sample_repo, "config", "user.email", "t@example.com")
    git(sample_repo, "config", "user.name", "Test")
    _write(sample_repo / ".gitignore", ".agents/\n")
    git(sample_repo, "remote", "add", "origin", str(remote))
    git(sample_repo, "add", ".")
    git(sample_repo, "commit", "-qm", "init")
    git(sample_repo, "push", "-qu", "origin", "main")

    import agent_worktree as aw

    layout = aw.find_layout(sample_repo)
    assert layout is not None
    aw.op_init(layout, install=False, fetch=False)
    wt_agy = layout.worktrees["agy"]

    exit_code = ls.run_hook(
        payload={"cwd": str(sample_repo), "conversationId": "conv-1"},
        agent="agy",
        event="stop",
        home=sample_home,
    )
    assert exit_code == 0
    assert (wt_agy / ".agents" / "LIVE_TELEMETRY.md").is_file()
    assert not (sample_repo / ".agents" / "LIVE_TELEMETRY.md").exists()
    # Ningún fichero tracked queda sucio en main ni en el worktree
    assert git(sample_repo, "status", "--porcelain") == ""
    assert git(wt_agy, "status", "--porcelain") == ""


def test_hook_mode_noop_outside_aagy_and_fail_open_on_bad_stdin(tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    assert ls.run_hook(payload={"cwd": str(other)}, agent="agy", event="session_start", home=tmp_path) == 0
    assert not (other / ".agents" / "LIVE_TELEMETRY.md").exists()

    proc = subprocess.run(
        [sys.executable, str(_SCRIPTS_DIR / "live_status.py"), "--hook", "--agent", "agy", "--event", "stop"],
        input="{not-json",
        cwd=str(other),
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0


def test_cli_json_and_real_repo_parity(sample_repo: Path, sample_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ls.main(["status", "--repo", str(sample_repo), "--home", str(sample_home), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["version"] == "5.2.0"
    assert data["catalog"]["agy_skills"] == 2
    assert data["antigravity"]["total_sessions"] == 2

    # Paridad real en /aagy
    import sync_aagy_ecc
    import audit_plugin_parity as parity

    assert "live_status.py" in sync_aagy_ecc.MIRRORED_PY_MODULES
    agy_hooks, ecc_hooks = parity.hook_coverage(_REPO_ROOT)
    assert "live_status.py" in agy_hooks.get("SessionStart", set())
    assert "live_status.py" in agy_hooks.get("Stop", set())
    assert "live_status.py" in ecc_hooks.get("SessionStart", set())
    assert "live_status.py" in ecc_hooks.get("Stop", set())
