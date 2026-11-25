#!/usr/bin/env python3
"""Pruebas de la UI de aagy: aagy_statusline.py, aagy_notify.py y aagy_ui.py."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Dict

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import aagy_ccusage as cu  # noqa: E402
import aagy_config  # noqa: E402
import aagy_notify as nt  # noqa: E402
import aagy_statusline as sl  # noqa: E402
import aagy_ui as ui  # noqa: E402

TODO = """# Backlog

## 1. Backlog Activo

## Épica: UI (#116)

- [ ] **Status line**
  <!-- aagy-task: id=ui-statusline epic=ui-de-claude-code-y-agy-116 issue=116 -->
"""


def _ui(**kw: Any) -> sl.UiSettings:
    base = dict(enabled=True, segments=sl.DEFAULT_SEGMENTS, warn_pct=60, crit_pct=80, ccusage=False, color=False)
    base.update(kw)
    return sl.UiSettings(**base)


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "feat/aagy/demo", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q",
                    "--allow-empty", "-m", "init"], check=True)
    return root


def _claim(root: Path, agent: str = "claude") -> None:
    (root / "doc").mkdir()
    (root / "doc" / "TODO.md").write_text(TODO, encoding="utf-8")  # ruta sin docs-map.json
    state = root / ".git" / "aagy-backlog"
    state.mkdir()
    (state / "state.json").write_text(json.dumps(
        {"version": 1, "tasks": {"ui-statusline": {"status": "in_progress", "owner": agent}}}), encoding="utf-8")


# --------------------------------------------------------------------------- status line

def test_render_full_json(repo: Path) -> None:
    _claim(repo)
    data = {
        "model": {"display_name": "Opus"},
        "workspace": {"current_dir": str(repo)},
        "cost": {"total_cost_usd": 0.4242},
        "context_window": {"context_window_size": 200000,
                           "current_usage": {"input_tokens": 1000, "cache_read_input_tokens": 49000}},
    }
    line = sl.render(data, _ui())
    assert line.split(sl.SEP) == ["Opus", "feat/aagy/demo", "ctx 50k/200k 25%", "$0.42", "local:auto", "#116 ui-statusline"]


def test_context_from_transcript(tmp_path: Path) -> None:
    transcript = tmp_path / "t.jsonl"
    rows = [{"type": "assistant", "message": {"usage": {"input_tokens": 10}}},
            {"type": "assistant", "message": {"usage": {"input_tokens": 130000, "cache_read_input_tokens": 0}}},
            {"type": "user", "message": {"content": "hola"}}]
    transcript.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    assert sl.context_usage({"transcript_path": str(transcript)}) == (130000, 200000, 65.0)


def test_context_colors_and_compact_hint() -> None:
    def seg(pct: float) -> str:
        return sl.segment_context({"context_window": {"used_percentage": pct}}, _ui(color=True)) or ""
    assert sl.COLORS["green"] in seg(10)
    assert sl.COLORS["yellow"] in seg(65)
    crit = seg(85)
    assert sl.COLORS["red"] in crit and "/compact" in crit


def test_context_unknown_is_omitted() -> None:
    assert sl.segment_context({}, _ui()) is None


def test_disabled_prints_nothing(repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.chdir(repo)
    monkeypatch.setenv("AAGY_UI_STATUSLINE", "false")
    monkeypatch.setattr(sl, "read_stdin", lambda: {"model": {"display_name": "Opus"}})
    assert sl.main([]) == 0
    assert capsys.readouterr().out == ""


def test_segments_from_config(repo: Path) -> None:
    (repo / ".governance").mkdir()
    (repo / ".governance" / "aagy.json").write_text(json.dumps({"ui": {"segments": ["model", "bogus"]}}), encoding="utf-8")
    settings = sl.load_ui(repo, {})
    assert settings.segments == ("model",)
    assert sl.load_ui(repo, {"NO_COLOR": "1"}).color is False


def test_plain_mode_for_agy(repo: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    _claim(repo, agent="agy")
    monkeypatch.chdir(repo)
    assert sl.main(["--plain", "--agent", "agy"]) == 0
    out = capsys.readouterr().out.strip()
    assert out == "feat/aagy/demo | local:auto | #116 ui-statusline"
    assert "\033[" not in out


def test_no_git_no_branch(tmp_path: Path) -> None:
    line = sl.render({"workspace": {"current_dir": str(tmp_path)}}, _ui(segments=("branch", "task")))
    assert line == ""


def test_usage_from_cache_without_blocking(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache = tmp_path / "usage.json"
    cache.write_text(json.dumps({"cost": 1.5, "at": time.time()}), encoding="utf-8")
    monkeypatch.setattr(sl.shutil, "which", lambda _name: "/bin/ccusage")
    assert sl.segment_usage(_ui(ccusage=True), cache, spawn=False) == "hoy $1.50"
    assert sl.segment_usage(_ui(ccusage=False), cache, spawn=False) is None
    monkeypatch.setattr(sl.shutil, "which", lambda _name: None)
    assert sl.segment_usage(_ui(ccusage=True), cache, spawn=False) is None


def test_stale_usage_cache(tmp_path: Path) -> None:
    cache = tmp_path / "usage.json"
    cache.write_text(json.dumps({"cost": 2, "at": time.time() - 3600}), encoding="utf-8")
    assert cu.read_cache(cache, time.time()) == (2.0, True)
    assert cu.read_cache(tmp_path / "missing.json", time.time()) == (None, True)


# --------------------------------------------------------------------------- avisos

def _cfg(tmp_path: Path, env: Dict[str, str]) -> aagy_config.Config:
    return aagy_config.load(tmp_path, env)


def test_notify_modes(tmp_path: Path) -> None:
    desktop = {"DISPLAY": ":0"}
    assert nt.enabled(_cfg(tmp_path, {}), desktop, "linux")
    assert not nt.enabled(_cfg(tmp_path, {}), {}, "linux")
    assert not nt.enabled(_cfg(tmp_path, {}), {"CI": "true", "DISPLAY": ":0"}, "linux")
    assert not nt.enabled(_cfg(tmp_path, {}), {"CLAUDE_CODE_REMOTE": "true"}, "win32")
    assert nt.enabled(_cfg(tmp_path, {"AAGY_UI_NOTIFY": "on"}), {}, "linux")
    assert not nt.enabled(_cfg(tmp_path, {"AAGY_UI_NOTIFY": "off"}), desktop, "linux")
    assert nt.enabled(_cfg(tmp_path, {}), {}, "win32")


def _transcript(tmp_path: Path, seconds_ago: float) -> str:
    start = datetime.now(timezone.utc) - timedelta(seconds=seconds_ago)
    rows = [
        {"type": "user", "message": {"content": "haz algo"}, "timestamp": start.isoformat()},
        {"type": "user", "message": {"content": [{"type": "tool_result", "content": "x"}]},
         "timestamp": datetime.now(timezone.utc).isoformat()},
    ]
    path = tmp_path / "t.jsonl"
    path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
    return str(path)


def test_stop_needs_long_turn(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, {"AAGY_UI_NOTIFY": "on"})
    assert not nt.should_notify("stop", {"transcript_path": _transcript(tmp_path, 5)}, cfg, {}, "linux")
    assert nt.should_notify("stop", {"transcript_path": _transcript(tmp_path, 120)}, cfg, {}, "linux")
    assert nt.should_notify("stop", {}, cfg, {}, "linux")  # Antigravity: sin transcript
    assert not nt.should_notify("stop", {"stop_hook_active": True}, cfg, {}, "linux")
    assert nt.should_notify("notification", {"message": "permiso"}, cfg, {}, "linux")


def test_commands_keep_text_out_of_code() -> None:
    evil = "\"; rm -rf / #'$(x)"
    which = lambda name: f"/usr/bin/{name}"  # noqa: E731
    argv, env = nt.build_command("aagy", evil, "win32", which)
    assert evil not in " ".join(argv) and env["AAGY_NOTIFY_BODY"] == evil
    argv, env = nt.build_command("aagy", evil, "darwin", which)
    assert argv[-1] == evil and evil not in " ".join(argv[:-1]) and env == {}
    argv, _env = nt.build_command("aagy", evil, "linux", which)
    assert argv[-1] == evil and "--" in argv
    assert nt.build_command("aagy", "x", "linux", lambda _n: None) is None


def test_message_for_events() -> None:
    assert nt.message_for("notification", {"cwd": "/x/proj", "message": "Pide permiso"}) == ("aagy · proj", "Pide permiso")
    assert nt.message_for("stop", {"cwd": "/x/proj"})[1] == "Turno terminado."


def test_notify_main_never_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(nt, "read_stdin", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert nt.main(["--event", "stop"]) == 0


# --------------------------------------------------------------------------- aagy_ui

def test_statusline_on_off_idempotent(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
    assert ui.statusline_on(path) is True
    assert ui.statusline_on(path) is False
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["theme"] == "dark" and ui.SCRIPT_NAME in data["statusLine"]["command"]
    assert ui.statusline_off(path) is True
    assert "statusLine" not in json.loads(path.read_text(encoding="utf-8"))
    assert ui.statusline_off(path) is False


def test_statusline_keeps_foreign(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"statusLine": {"type": "command", "command": "mine.sh"}}), encoding="utf-8")
    with pytest.raises(ui.UiError):
        ui.statusline_on(path)
    with pytest.raises(ui.UiError):
        ui.statusline_off(path)
    assert ui.statusline_on(path, force=True) is True


def test_repair_old_plugin_path(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"statusLine": {"type": "command",
                                               "command": ui.statusline_command(tmp_path / "old" / ui.SCRIPT_NAME)}}),
                    encoding="utf-8")
    assert ui.repair([path, tmp_path / "missing.json"]) == [path]
    assert ui.repair([path]) == []
    assert str((Path(ui.__file__).parent / ui.SCRIPT_NAME).resolve().as_posix()) in path.read_text(encoding="utf-8")


def test_settings_path_scopes(tmp_path: Path, repo: Path) -> None:
    assert ui.settings_path("user", environ={"CLAUDE_CONFIG_DIR": str(tmp_path)}) == tmp_path / "settings.json"
    assert ui.settings_path("local", repo) == repo / ".claude" / "settings.local.json"


def test_set_project_value(repo: Path) -> None:
    path = ui.set_project_value("ui.notify", "off", repo)
    assert path == repo / ".governance" / "aagy.json"
    ui.set_project_value("ui.ccusage", True, repo)
    assert json.loads(path.read_text(encoding="utf-8")) == {"ui": {"notify": "off", "ccusage": True}}
    assert aagy_config.load(repo, {}).get("ui.notify") == "off"


def test_merge_recommendations(tmp_path: Path) -> None:
    path = tmp_path / ".vscode" / "extensions.json"
    path.parent.mkdir()
    path.write_text(json.dumps({"recommendations": ["Eamodio.GitLens", "foo.bar"]}), encoding="utf-8")
    changed, added = ui.merge_recommendations(path, ["eamodio.gitlens", "gruntfuggly.todo-tree"])
    assert changed and added == ["gruntfuggly.todo-tree"]
    assert json.loads(path.read_text(encoding="utf-8"))["recommendations"][1] == "foo.bar"
    assert ui.merge_recommendations(path, ["gruntfuggly.todo-tree"]) == (False, [])
    path.write_text("// comentario\n{}", encoding="utf-8")
    with pytest.raises(ui.UiError):
        ui.merge_recommendations(path, ["x.y"])


def test_usage_without_ccusage(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
    monkeypatch.setattr(ui.shutil, "which", lambda _name: None)
    assert ui.main(["usage"]) == 0
    assert "npm install -g ccusage" in capsys.readouterr().out


def test_plain_agy_context_from_monitor(monkeypatch: pytest.MonkeyPatch) -> None:
    import session_token_monitor as stm
    report = stm.SessionTokenReport("t", 3, 1000, 40000, 45000, False)
    monkeypatch.setattr(stm, "analyze_transcript", lambda _path=None: report)
    assert sl.segment_context(sl.agy_context(), _ui()) == "ctx 40k/45k 89% /compact"


def test_status_per_harness(capsys: pytest.CaptureFixture) -> None:
    assert ui.main(["status", "--harness", "agy"]) == 0
    out = capsys.readouterr().out
    assert "statusline (CLI de Antigravity)" in out and "ccusage: no aplica" in out


# --------------------------------------------------------------------------- usage en Antigravity (#123)

def _agy_transcript(home: Path, session: str, text: str, mtime: float) -> Path:
    path = home / ".gemini" / "antigravity" / "brain" / session / ".system_generated" / "logs" / "transcript.jsonl"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"content": text}) + "\n", encoding="utf-8")
    os.utime(path, (mtime, mtime))
    return path


def test_agy_usage_groups_by_day_and_session(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    day1 = datetime(2026, 11, 24, 12).timestamp()
    day2 = datetime(2026, 11, 25, 12).timestamp()
    _agy_transcript(tmp_path, "s1", "x" * 380, day1)
    _agy_transcript(tmp_path, "s2", "x" * 38, day2)
    _agy_transcript(tmp_path, "s3", "x" * 38, day2)
    transcripts = ui._token_monitor().find_transcripts(tmp_path)
    assert ui.agy_usage_rows("daily", transcripts) == [("2026-11-25", 2, 20), ("2026-11-24", 1, 100)]
    assert ui.agy_usage_rows("monthly", transcripts) == [("2026-11", 3, 120)]
    sessions = ui.agy_usage_rows("session", transcripts)
    assert sorted(sessions) == [("s1", 1, 100), ("s2", 1, 10), ("s3", 1, 10)] and sessions[-1][0] == "s1"
    assert ui.cmd_usage_agy("daily", tmp_path) == 0
    assert "120 tokens estimados" in capsys.readouterr().out


def test_agy_usage_without_transcripts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ui.cmd_usage_agy("daily", tmp_path) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and "No hay transcripts" in out[0]


def test_agy_usage_blocks_not_applicable(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert ui.cmd_usage_agy("blocks", tmp_path) == 0
    assert "no aplica" in capsys.readouterr().out


# --------------------------------------------------------------------------- asimetrías de Antigravity (#124)

def test_agy_statusline_command_and_settings(tmp_path: Path) -> None:
    path = ui.agy_settings_path(tmp_path)
    assert path == tmp_path / ".gemini" / "antigravity-cli" / "settings.json"
    assert ui.statusline_on(path, harness="agy")
    command = json.loads(path.read_text(encoding="utf-8"))["statusLine"]["command"]
    assert command.endswith("aagy_statusline.py --agent agy") and "$(" not in command
    assert not ui.statusline_on(path, harness="agy")
    assert ui.statusline_off(path)


def test_agy_observe_marks_turn_start_and_confirmation(tmp_path: Path) -> None:
    base = {"conversation_id": "c-1"}
    assert nt.agy_observe({**base, "agent_state": "idle"}, now=100.0, tmp=tmp_path) is None
    assert nt.agy_observe({**base, "agent_state": "working"}, now=110.0, tmp=tmp_path) is None
    assert nt.agy_observe({**base, "agent_state": "tool_use"}, now=120.0, tmp=tmp_path) is None
    pending = {**base, "agent_state": "tool_use", "tool_confirmation_pending": True}
    assert nt.agy_observe(pending, now=125.0, tmp=tmp_path) == nt.EVENT_NOTIFICATION
    assert nt.agy_observe(pending, now=126.0, tmp=tmp_path) is None
    now = datetime.fromtimestamp(150.0, tz=timezone.utc)
    assert nt.agy_turn_seconds({"conversationId": "c-1"}, now, tmp=tmp_path) == 40.0
    assert nt.agy_turn_seconds({"conversationId": "otra"}, now, tmp=tmp_path) is None
    assert nt.agy_state_path("", tmp_path) is None


def test_agy_statusline_cost_and_estimated_context(tmp_path: Path) -> None:
    transcript = tmp_path / "transcript.jsonl"
    transcript.write_text(json.dumps({"content": "x" * 3800}) + "\n", encoding="utf-8")
    data = sl.agy_cli_data({"transcript_path": str(transcript), "cost": {"total_usd": 0.5}})
    assert sl.context_usage(data)[0] == 1000
    line = sl.render(data, _ui(segments=("cost", "context")), agent="agy", cwd=tmp_path)
    assert line.startswith("$0.50")
