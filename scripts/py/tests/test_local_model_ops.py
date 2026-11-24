#!/usr/bin/env python3
"""Pruebas de DOC-16, bench, registro de uso y guarda de ficheros privados del modelo local."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
for folder in (_SCRIPTS_DIR, Path(__file__).resolve().parent):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

import local_model as lm  # noqa: E402
import local_model_ops as ops  # noqa: E402
import local_private_guard as guard  # noqa: E402
from test_local_model import MODEL, _dead_url, _env, ollama, repo  # noqa: E402,F401


def _private_repo(repo_dir: Path) -> Path:
    gov = repo_dir / ".governance"
    gov.mkdir(exist_ok=True)
    (gov / "aagy.json").write_text(json.dumps({"local_model": {"private_globs": ["secrets/**"]}}), encoding="utf-8")
    return repo_dir


def test_doctor_skip_when_off_or_auto_without_ollama(repo: Path) -> None:
    assert ops.doctor_findings(repo, None, _env(_dead_url(), AAGY_LOCAL_MODEL="off"))[0] == ops.STATUS_SKIP
    assert ops.doctor_findings(repo, None, _env(_dead_url()))[0] == ops.STATUS_SKIP


def test_doctor_fail_when_forced_without_ollama(repo: Path) -> None:
    assert ops.doctor_findings(repo, None, _env(_dead_url(), AAGY_LOCAL_MODEL="tool"))[0] == ops.STATUS_FAIL


def test_doctor_warns_missing_model_and_registration(repo: Path, ollama: str) -> None:
    status, message, _evidence, missing = ops.doctor_findings(repo, False, _env(ollama, AAGY_LOCAL_MODEL_NAME="other"))
    assert status == ops.STATUS_WARN and missing == ["other"] and "sin descargar" in message
    assert ops.pull_argv("other") == ["ollama", "pull", "other"]


def test_doctor_warns_unmeasured_then_passes(repo: Path, ollama: str) -> None:
    status, message, _e, _m = ops.doctor_findings(repo, True, _env(ollama))
    assert status == ops.STATUS_WARN and "sin medir" in message
    (repo / "a.py").write_text("print('x')\n", encoding="utf-8")
    settings = lm.load_settings(repo, _env(ollama))
    ops.save_bench([ops.bench_model(settings, MODEL, repo)], ops.bench_path(settings, repo))
    assert ops.doctor_findings(repo, True, _env(ollama))[0] == ops.STATUS_PASS


def test_bench_file_shape(repo: Path, ollama: str) -> None:
    (repo / "b.md").write_text("# t\n", encoding="utf-8")
    row = ops.bench_model(lm.load_settings(repo, _env(ollama)), MODEL, repo)
    assert row["model"] == MODEL and row["samples"] == 1 and 0.0 <= row["accuracy"] <= 1.0


def test_usage_log_has_no_content(repo: Path, ollama: str) -> None:
    lm.run_task(lm.load_settings(repo, _env(ollama)), {"task": "complete", "text": "texto secreto"}, repo)
    log = lm.usage_log_path(repo)
    assert log is not None and log.is_file()
    row = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
    assert row["task"] == "complete" and row["ok"] is True and "secreto" not in log.read_text(encoding="utf-8")
    assert lm.usage_summary(repo)["calls"] == 1


def _claude(path: str, cwd: Path, tool: str = "Read") -> Dict[str, Any]:
    return {"tool_name": tool, "tool_input": {"file_path": path}, "cwd": str(cwd)}


def test_guard_asks_in_claude_for_private(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AAGY_OLLAMA_URL", _dead_url())
    _private_repo(repo)
    out = guard.handle(_claude("secrets/a.txt", repo), guard.FMT_CLAUDE)
    assert out["hookSpecificOutput"]["permissionDecision"] == "ask"
    assert guard.handle(_claude("src/a.py", repo), guard.FMT_CLAUDE) == {}
    assert guard.handle(_claude("secrets/a.txt", repo, "Bash"), guard.FMT_CLAUDE) == {}


def test_guard_denies_in_agy_for_private(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AAGY_OLLAMA_URL", _dead_url())
    _private_repo(repo)
    payload = {"toolCall": {"args": {"AbsolutePath": str(repo / "secrets" / "a.txt")}}, "cwd": str(repo)}
    assert guard.handle(payload, guard.FMT_AGY)["decision"] == "deny"
    payload["toolCall"]["args"]["AbsolutePath"] = str(repo / "README.md")
    assert guard.handle(payload, guard.FMT_AGY) == {"decision": "allow"}


def test_guard_noop_without_globs(repo: Path) -> None:
    assert guard.handle(_claude("secrets/a.txt", repo), guard.FMT_CLAUDE) == {}
