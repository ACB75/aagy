#!/usr/bin/env python3
"""Pruebas de aagy_config.py: capas de configuración externa y check DOC-17."""

from __future__ import annotations

import json
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import aagy_config as cfg  # noqa: E402


def _write_json(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def _project(tmp_path: Path, data: object) -> Path:
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    _write_json(repo / ".governance" / "aagy.json", data)
    return repo


def _env_dir(tmp_path: Path, data: object) -> Path:
    root = tmp_path / "@env"
    _write_json(root / "aagy" / "env.json", data)
    return root


def test_env_var_name():
    assert cfg.env_var_name("hosts.live.ip") == "AAGY_HOSTS_LIVE_IP"


def test_no_layers_returns_default(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    assert cfg.get("ingress.domain_suffix", "x", start=tmp_path, environ={}) == "x"
    assert cfg.get("ingress.domain_suffix", start=tmp_path, environ={}) is None


def test_priority_variable_then_project_then_env(tmp_path: Path):
    repo = _project(tmp_path, {"ingress": {"domain_suffix": "proj.lab"}})
    env_root = _env_dir(tmp_path, {"domains": {"ingress_suffix": "env.lab"}, "hosts": {"live": {"ip": "10.0.0.1"}}})
    environ = {cfg.ENV_DIR_VAR: str(env_root)}
    loaded = cfg.load(repo / "src", environ)
    assert loaded.lookup("ingress.domain_suffix") == ("proj.lab", cfg.LAYER_PROJECT)
    assert loaded.lookup("hosts.live.ip") == ("10.0.0.1", cfg.LAYER_ENV)
    environ["AAGY_HOSTS_LIVE_IP"] = "10.0.0.9"
    assert cfg.load(repo, environ).lookup("hosts.live.ip") == ("10.0.0.9", cfg.LAYER_VAR)


def test_variable_parses_json_lists(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    value = cfg.get("projects", start=tmp_path, environ={"AAGY_PROJECTS": '["a", "b"]'})
    assert value == ["a", "b"]


def test_project_search_stops_at_git_root(tmp_path: Path):
    _write_json(tmp_path / ".governance" / "aagy.json", {"projects": ["fuera"]})
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    assert cfg.find_project_file(repo) is None


def test_invalid_key_rejected(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    try:
        cfg.load(tmp_path, {}).lookup("Hosts Live")
    except cfg.ConfigError:
        return
    raise AssertionError("debía rechazar la clave")


def test_doctor_skip_without_config(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    status, message, _ = cfg.doctor_findings(tmp_path, {})
    assert status == cfg.STATUS_SKIP
    assert cfg.ENV_DIR_VAR in message


def test_doctor_pass_with_both_layers(tmp_path: Path):
    repo = _project(tmp_path, {"projects": ["api"]})
    env_root = _env_dir(tmp_path, {"hosts": {"live": {"name": "prod"}}, "secrets_env": {"github": "GH_TOKEN"}})
    status, _, evidence = cfg.doctor_findings(repo, {cfg.ENV_DIR_VAR: str(env_root)})
    assert status == cfg.STATUS_PASS
    assert any(str(env_root) in line for line in evidence)


def test_doctor_warns_on_broken_or_unknown(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / ".git").mkdir(parents=True)
    (repo / ".governance").mkdir()
    (repo / ".governance" / "aagy.json").write_text("{no json", encoding="utf-8")
    status, message, _ = cfg.doctor_findings(repo, {})
    assert status == cfg.STATUS_WARN and "JSON" in message
    _write_json(repo / ".governance" / "aagy.json", {"projetcs": []})
    status, message, _ = cfg.doctor_findings(repo, {})
    assert status == cfg.STATUS_WARN and "projetcs" in message


def test_doctor_warns_on_missing_env_dir(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    status, message, _ = cfg.doctor_findings(tmp_path, {cfg.ENV_DIR_VAR: str(tmp_path / "nada")})
    assert status == cfg.STATUS_WARN and "no existe" in message


def test_doctor_warns_on_secrets_and_workflows(tmp_path: Path):
    (tmp_path / ".git").mkdir()
    env_root = _env_dir(tmp_path, {"hosts": {"live": {"api_token": "abc"}}})
    status, message, _ = cfg.doctor_findings(tmp_path, {cfg.ENV_DIR_VAR: str(env_root)})
    assert status == cfg.STATUS_WARN and "hosts.live.api_token" in message
    _write_json(env_root / "aagy" / "env.json", {"hosts": {}})
    (env_root / ".github" / "workflows").mkdir(parents=True)
    (env_root / ".github" / "workflows" / "ci.yml").write_text("on: push\n", encoding="utf-8")
    status, message, _ = cfg.doctor_findings(tmp_path, {cfg.ENV_DIR_VAR: str(env_root)})
    assert status == cfg.STATUS_WARN and "Actions" in message


def test_cli_get_and_missing(tmp_path: Path, monkeypatch, capsys):
    repo = _project(tmp_path, {"sdk": {"dir": "my-sdk"}})
    monkeypatch.delenv(cfg.ENV_DIR_VAR, raising=False)
    assert cfg.main(["--start", str(repo), "get", "sdk.dir"]) == cfg.EXIT_OK
    assert capsys.readouterr().out.strip() == "my-sdk"
    assert cfg.main(["--start", str(repo), "get", "hosts.live.ip"]) == cfg.EXIT_MISSING
    assert cfg.main(["--start", str(repo), "get", "hosts.live.ip", "--default", "none"]) == cfg.EXIT_OK
    assert capsys.readouterr().out.strip() == "none"


def test_windows_user_env_dir_fallback(tmp_path: Path, monkeypatch):
    import local_model

    (tmp_path / ".git").mkdir()
    env_root = _env_dir(tmp_path, {"local_model": {"tool": "demo:1b"}, "hosts": {"live": {"name": "prod"}}})
    monkeypatch.delenv(cfg.ENV_DIR_VAR, raising=False)
    monkeypatch.setattr(cfg, "_user_env_dir", lambda: str(env_root))
    assert cfg.load(tmp_path).lookup("hosts.live.name") == ("prod", cfg.LAYER_ENV)
    assert local_model.load_settings(tmp_path).tool_model == "demo:1b"
