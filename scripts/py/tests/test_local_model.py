#!/usr/bin/env python3
"""Pruebas de local_model.py y local_model_mcp.py con un Ollama simulado."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, HTTPServer
import io
import json
from pathlib import Path
import sys
import threading
from typing import Any, Dict, Iterator, List

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import local_model as lm  # noqa: E402
import local_model_mcp as mcp  # noqa: E402

MODEL = "fake-model:1b"


class _FakeOllama(BaseHTTPRequestHandler):
    requests: List[Dict[str, Any]] = []

    def log_message(self, *_args: Any) -> None:  # silencio
        return

    def _send(self, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        self._send({"models": [{"name": MODEL}]})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length))
        _FakeOllama.requests.append(payload)
        user = payload["messages"][1]["content"]
        self._send({"message": {"content": f"OK:{len(user)}"}})


@pytest.fixture()
def ollama() -> Iterator[str]:
    _FakeOllama.requests = []
    server = HTTPServer(("127.0.0.1", 0), _FakeOllama)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    return root


def _env(url: str, **extra: str) -> Dict[str, str]:
    env = {"AAGY_OLLAMA_URL": url, "AAGY_LOCAL_MODEL_NAME": MODEL}
    env.update(extra)
    return env


def _dead_url() -> str:
    return "http://127.0.0.1:9"


def test_defaults_without_config(repo: Path) -> None:
    settings = lm.load_settings(repo, {})
    assert settings.mode == lm.MODE_AUTO
    assert settings.url == lm.DEFAULT_URL
    assert settings.tool_model == ""
    assert set(settings.tasks) == set(lm.DEFAULT_TASKS)


def test_project_layer_and_aliases(repo: Path) -> None:
    gov = repo / ".governance"
    gov.mkdir()
    (gov / "aagy.json").write_text(json.dumps({"local_model": {
        "mode": "tool", "tool": "from-file", "private_globs": ["secrets/**"],
        "tasks": {"translate": None, "tag": {"instruction": "Etiqueta: {x}", "params": ["x"]}},
    }}), encoding="utf-8")
    settings = lm.load_settings(repo, {"AAGY_LOCAL_MODEL_NAME": "from-var"})
    assert settings.mode == lm.MODE_TOOL
    assert settings.tool_model == "from-var"
    assert "translate" not in settings.tasks and "tag" in settings.tasks
    assert lm.is_private("secrets/a.txt", settings, repo)
    assert not lm.is_private("src/a.py", settings, repo)


def test_status_auto_without_ollama(repo: Path) -> None:
    status = lm.get_status(lm.load_settings(repo, _env(_dead_url())))
    assert status.effective == lm.MODE_OFF and not status.reachable


def test_status_off_does_not_probe(repo: Path) -> None:
    status = lm.get_status(lm.load_settings(repo, _env(_dead_url(), AAGY_LOCAL_MODEL="off")))
    assert status.effective == lm.MODE_OFF and status.reason == "Modo off."


def test_status_auto_with_ollama(repo: Path, ollama: str) -> None:
    status = lm.get_status(lm.load_settings(repo, _env(ollama)))
    assert status.reachable and status.tool_model_present and status.effective == lm.MODE_TOOL


def test_status_missing_model(repo: Path, ollama: str) -> None:
    status = lm.get_status(lm.load_settings(repo, _env(ollama, AAGY_LOCAL_MODEL_NAME="other")))
    assert status.effective == lm.MODE_OFF and "ollama pull other" in status.reason


def test_run_with_paths_reads_file_and_hides_content(repo: Path, ollama: str) -> None:
    (repo / "log.txt").write_text("secreto " * 10, encoding="utf-8")
    result = lm.run_task(lm.load_settings(repo, _env(ollama)), {"task": "summarize", "paths": ["log.txt"]}, repo)
    assert result["result"].startswith("OK:") and "secreto" not in json.dumps(result)
    assert result["model"] == MODEL and result["truncated"] is False and "duration_ms" in result


def test_run_rejects_paths_outside_repo(repo: Path, ollama: str, tmp_path: Path) -> None:
    outside = tmp_path / "x.txt"
    outside.write_text("x", encoding="utf-8")
    result = lm.run_task(lm.load_settings(repo, _env(ollama)), {"task": "summarize", "paths": [str(outside)]}, repo)
    assert "fuera del proyecto" in result["error"]


def test_run_requires_params_and_json_format(repo: Path, ollama: str) -> None:
    settings = lm.load_settings(repo, _env(ollama))
    assert "labels" in lm.run_task(settings, {"task": "classify", "text": "a"}, repo)["error"]
    ok = lm.run_task(settings, {"task": "extract", "text": "a", "params": {"fields": ["x", "y"]}}, repo)
    assert "error" not in ok and _FakeOllama.requests[-1]["format"] == "json"


def test_run_truncates(repo: Path, ollama: str) -> None:
    result = lm.run_task(lm.load_settings(repo, _env(ollama)), {"task": "complete", "text": "a" * 9000}, repo)
    assert result["truncated"] is True


def test_run_with_dead_ollama_is_structured(repo: Path) -> None:
    result = lm.run_task(lm.load_settings(repo, _env(_dead_url())), {"task": "complete", "text": "a"}, repo)
    assert "Ollama no responde" in result["error"]


def test_run_unknown_task_and_both_sources(repo: Path, ollama: str) -> None:
    settings = lm.load_settings(repo, _env(ollama))
    assert "desconocida" in lm.run_task(settings, {"task": "chat", "text": "a"}, repo)["error"]
    assert "uno de los dos" in lm.run_task(settings, {"task": "complete"}, repo)["error"]


def test_set_mode_is_idempotent(repo: Path) -> None:
    settings = lm.load_settings(repo, {})
    path = lm.set_mode("off", settings, repo)
    first = path.stat().st_mtime_ns
    lm.set_mode("off", lm.load_settings(repo, {}), repo)
    assert json.loads(path.read_text(encoding="utf-8"))["local_model"]["mode"] == "off"
    assert path.stat().st_mtime_ns == first
    with pytest.raises(lm.LocalModelError):
        lm.set_mode("x", settings, repo)


def test_register_agy(tmp_path: Path) -> None:
    config = tmp_path / "mcp_config.json"
    config.write_text(json.dumps({"mcpServers": {"other": {"command": "x"}}}), encoding="utf-8")
    assert lm.register_agy(config) is True
    assert lm.register_agy(config) is False
    data = json.loads(config.read_text(encoding="utf-8"))
    assert "other" in data["mcpServers"] and data["mcpServers"]["aagy-local"]["args"][0].endswith("local_model_mcp.py")


def _rpc(server: mcp.Server, *messages: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = io.StringIO()
    mcp.serve(io.StringIO("\n".join(json.dumps(m) for m in messages) + "\n"), out, server)
    return [json.loads(line) for line in out.getvalue().splitlines()]


def test_mcp_empty_tools_without_ollama(repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _env(_dead_url()).items():
        monkeypatch.setenv(key, value)
    replies = _rpc(mcp.Server(repo),
                   {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05"}},
                   {"jsonrpc": "2.0", "method": "notifications/initialized"},
                   {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert replies[0]["result"]["serverInfo"]["name"] == "aagy-local"
    assert replies[1]["result"]["tools"] == []


def test_mcp_tools_and_call(repo: Path, ollama: str, monkeypatch: pytest.MonkeyPatch) -> None:
    for key, value in _env(ollama).items():
        monkeypatch.setenv(key, value)
    replies = _rpc(mcp.Server(repo),
                   {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
                   {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                    "params": {"name": "local_run", "arguments": {"task": "complete", "text": "hola"}}},
                   {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "nope"}},
                   {"jsonrpc": "2.0", "id": 4, "method": "nope"})
    assert [t["name"] for t in replies[0]["result"]["tools"]] == ["local_status", "local_run"]
    payload = json.loads(replies[1]["result"]["content"][0]["text"])
    assert payload["result"] == "OK:4" and replies[1]["result"]["isError"] is False
    assert replies[2]["error"]["code"] == mcp.ERR_PARAMS
    assert replies[3]["error"]["code"] == mcp.ERR_METHOD
