#!/usr/bin/env python3
"""Pruebas de /aagy-ecc-doctor (aagy-ecc/scripts/py/aagy_ecc_doctor.py) con un ~/.claude falso en tmp_path."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
_ECC = _REPO_ROOT / "aagy-ecc"
for _p in (_SCRIPTS_DIR, _ECC / "scripts" / "py"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import aagy_ecc_doctor as doc  # noqa: E402
import aagy_doctor  # noqa: E402
import doctor_core as core  # noqa: E402
import install_manifest as im  # noqa: E402

REAL_DATA_DIR = doc.data_dir
SKILL = "---\nname: s1\ndescription: Skill s1\n---\n"
AGENT = "---\nname: a1\ndescription: Agent a1\nmodel: inherit\n---\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_plugin(root: Path, version: str = "1.0.0") -> Path:
    """Plugin aagy-ecc mínimo con los hooks y el comando reales del repo."""
    _write(root / ".claude-plugin" / "plugin.json", json.dumps({"name": "aagy-ecc", "version": version}))
    _write(root / ".claude-plugin" / "marketplace.json", json.dumps({"plugins": [{"name": "aagy-ecc", "version": version}]}))
    _write(root / "rules" / "AGENTS.md", "# Reglas Tier 1\n")
    _write(root / "skills" / "s1" / "SKILL.md", SKILL)
    _write(root / "agents" / "a1.md", AGENT)
    shutil.copytree(_ECC / "hooks", root / "hooks")
    shutil.copytree(_ECC / "scripts" / "hooks", root / "scripts" / "hooks", ignore=shutil.ignore_patterns("__pycache__"))
    _write(root / "commands" / "aagy-ecc-doctor.md", (_ECC / "commands" / "aagy-ecc-doctor.md").read_text(encoding="utf-8"))
    _write(root / "commands" / "plan.md", "---\ndescription: Plan\n---\n")
    _write(root / "project-template" / "CLAUDE.md", "# Plantilla\n")
    _write(root / "scripts" / "py" / "self_improve.py", "print('stop')\n")
    _write(root / "scripts" / "py" / "backlog.py", "print('backlog')\n")
    _write(root / "scripts" / "py" / "agent_worktree.py", "print('worktree')\n")
    _write(root / "scripts" / "py" / "local_private_guard.py", "print('{}')\n")
    for engine in ("hook_safety.py", "hook_post_write.py", "validate_branch.py"):
        shutil.copy2(_ECC / "scripts" / "py" / engine, root / "scripts" / "py" / engine)
    return root


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(root / "plugin.json", '{"name": "aagy", "version": "1.0.0"}')
    _write(root / "rules" / "AGENTS.md", "# Reglas Tier 1\n")
    _make_plugin(root / "aagy-ecc")
    return root


@pytest.fixture
def claude_home(tmp_path: Path, repo: Path) -> Path:
    """~/.claude con aagy-ecc instalado (formato v2 de installed_plugins.json) y copia en caché."""
    home = tmp_path / "home" / ".claude"
    install = home / "plugins" / "cache" / "aagy-ecc" / "aagy-ecc" / "1.0.0"
    shutil.copytree(repo / "aagy-ecc", install)
    im.write_manifest(install, im.InstallManifest("claude", "full", "1.0.0", "abc1234", "2026-11-20T00:00:00+00:00", str(repo)))
    _write(home / "plugins" / "installed_plugins.json", json.dumps({
        "version": 2,
        "plugins": {"aagy-ecc@aagy-ecc": [{"scope": "user", "installPath": str(install), "version": "1.0.0"}]},
    }))
    _write(home / "plugins" / "known_marketplaces.json", json.dumps({"aagy-ecc": {"source": {"source": "directory"}}}))
    _write(home / "settings.json", json.dumps({"enabledPlugins": {"aagy-ecc@aagy-ecc": True}}))
    return home


def _install(claude_home: Path) -> Path:
    return claude_home / "plugins" / "cache" / "aagy-ecc" / "aagy-ecc" / "1.0.0"


def _ctx(tmp_path: Path, claude_home: Path, repo: Path = None, project: Path = None, plugin_dir: Path = None) -> doc.EccContext:
    argv = ["--home", str(tmp_path / "home"), "--claude-home", str(claude_home), "--project", str(project or tmp_path)]
    if repo is not None:
        argv += ["--repo-root", str(repo)]
    if plugin_dir is not None:
        argv += ["--plugin-dir", str(plugin_dir)]
    return doc.build_context(doc.parse_args(argv))


def _run(ctx: doc.EccContext, check_id: str) -> core.CheckResult:
    return doc.REGISTRY[check_id](ctx)


@pytest.fixture(autouse=True)
def data_dir(tmp_path: Path, monkeypatch):
    target = tmp_path / "datos"
    target.mkdir()
    monkeypatch.setattr(doc, "data_dir", lambda: target)
    return target


def test_registry_matches_catalog_and_sibling_doctor():
    core.validate_registry(doc.REGISTRY)
    assert tuple(doc.REGISTRY) == tuple(aagy_doctor.REGISTRY) == core.CATALOG_IDS


def test_plugin_entries_supports_v1_and_v2():
    v1 = {"plugins": {"a@m": {"installPath": "/x"}}}
    v2 = {"plugins": {"a@m": [{"installPath": "/x"}, "basura"]}}
    assert doc.plugin_entries(v1) == doc.plugin_entries(v2) == {"a@m": [{"installPath": "/x"}]}
    assert doc.plugin_entries(None) == {}
    assert doc.plugin_entries({"plugins": []}) == {}


def test_healthy_install_has_no_fail(tmp_path: Path, repo: Path, claude_home: Path, monkeypatch):
    monkeypatch.setattr(doc, "check_repo", lambda ctx: core.result("DOC-14", core.STATUS_PASS, "ok"))
    registry = dict(doc.REGISTRY, **{"DOC-14": doc.check_repo})
    ctx = _ctx(tmp_path, claude_home, repo)
    assert ctx.install_path == _install(claude_home)
    results = {r.check_id: r for r in core.run_checks(registry, ctx)}
    for cid in ("DOC-02", "DOC-03", "DOC-04", "DOC-05", "DOC-06", "DOC-07", "DOC-08", "DOC-09", "DOC-11", "DOC-12"):
        assert results[cid].status == core.STATUS_PASS, (cid, results[cid].message, results[cid].evidence)
    assert results["DOC-13"].status == core.STATUS_SKIP


def test_not_installed(tmp_path: Path, repo: Path, monkeypatch):
    monkeypatch.setattr(doc, "find_install_path", lambda home, entries: None)
    ctx = _ctx(tmp_path, tmp_path / "vacio", repo)
    assert _run(ctx, "DOC-02").status == core.STATUS_FAIL
    for cid in ("DOC-03", "DOC-04", "DOC-05", "DOC-06", "DOC-07", "DOC-08", "DOC-09", "DOC-11"):
        assert _run(ctx, cid).status == core.STATUS_SKIP, cid


def test_unknown_state_with_copy_only_warns(tmp_path: Path, repo: Path):
    ctx = _ctx(tmp_path, tmp_path / "vacio", repo, plugin_dir=repo / "aagy-ecc")
    assert _run(ctx, "DOC-02").status == core.STATUS_WARN
    assert _run(ctx, "DOC-07").message.startswith("Claude Code usa directamente")


def test_disabled_or_unregistered_plugin_fails(tmp_path: Path, repo: Path, claude_home: Path, monkeypatch):
    (claude_home / "settings.json").write_text(json.dumps({"enabledPlugins": {"aagy-ecc@aagy-ecc": False}}), encoding="utf-8")
    (claude_home / "plugins" / "known_marketplaces.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(core, "which", lambda name: "/usr/bin/claude" if name == "claude" else None)
    result = _run(_ctx(tmp_path, claude_home, repo), "DOC-02")
    assert result.status == core.STATUS_FAIL
    assert any("deshabilitado" in e for e in result.evidence)
    assert "marketplace add" in result.fix.description


def test_find_install_path_fallbacks(tmp_path: Path, claude_home: Path):
    assert doc.find_install_path(claude_home, [{"installPath": "/no/existe"}]) == _install(claude_home)
    assert doc.find_install_path(tmp_path / "nada", []) == _ECC  # la propia carpeta del script es un plugin aagy-ecc


def test_manifest_problems(tmp_path: Path, repo: Path, claude_home: Path):
    meta = _install(claude_home) / ".claude-plugin"
    (meta / "marketplace.json").write_text(json.dumps({"plugins": [{"name": "aagy-ecc", "version": "0.9"}]}), encoding="utf-8")
    ctx = _ctx(tmp_path, claude_home, repo)
    assert _run(ctx, "DOC-03").status == core.STATUS_WARN
    (meta / "marketplace.json").write_text(json.dumps({"plugins": [{"name": "otro"}]}), encoding="utf-8")
    assert _run(ctx, "DOC-03").status == core.STATUS_FAIL
    (meta / "marketplace.json").write_text("{roto", encoding="utf-8")
    assert _run(ctx, "DOC-03").status == core.STATUS_WARN
    (meta / "plugin.json").write_text('{"name": "otro"}', encoding="utf-8")
    assert _run(ctx, "DOC-03").status == core.STATUS_FAIL


def test_stale_install_is_detected(tmp_path: Path, repo: Path, claude_home: Path):
    (repo / "aagy-ecc" / ".claude-plugin" / "plugin.json").write_text('{"name": "aagy-ecc", "version": "1.1.0"}', encoding="utf-8")
    _write(repo / "aagy-ecc" / "skills" / "s2" / "SKILL.md", SKILL.replace("s1", "s2"))
    (repo / "rules" / "AGENTS.md").write_text("# Reglas nuevas\n", encoding="utf-8")
    (_install(claude_home) / im.MANIFEST_FILE).unlink()
    ctx = _ctx(tmp_path, claude_home, repo)
    assert _run(ctx, "DOC-04").status == core.STATUS_WARN
    assert _run(ctx, "DOC-05").status == core.STATUS_WARN
    assert _run(ctx, "DOC-06").status == core.STATUS_WARN
    drift = _run(ctx, "DOC-07")
    assert drift.status == core.STATUS_WARN and "falta skills/s2/SKILL.md" in drift.evidence


def test_rules_missing_fails(tmp_path: Path, repo: Path, claude_home: Path):
    (_install(claude_home) / "rules" / "AGENTS.md").unlink()
    assert _run(_ctx(tmp_path, claude_home, repo), "DOC-05").status == core.STATUS_FAIL


def test_commands_checks(tmp_path: Path, repo: Path, claude_home: Path):
    install = _install(claude_home)
    (install / "commands" / "aagy-ecc-doctor.md").unlink()
    _write(install / "commands" / "sin-desc.md", "# nada\n")
    other = tmp_path / "otro-plugin"
    _write(other / "commands" / "plan.md", "---\ndescription: x\n---\n")
    data = json.loads((claude_home / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
    data["plugins"]["otro@m"] = [{"installPath": str(other)}]
    (claude_home / "plugins" / "installed_plugins.json").write_text(json.dumps(data), encoding="utf-8")
    result = _run(_ctx(tmp_path, claude_home, repo), "DOC-08")
    assert result.status == core.STATUS_WARN
    text = " ".join(result.evidence)
    assert "/aagy-ecc-doctor" in text and "sin-desc" in text and "otro@m" in text


def test_hook_targets(tmp_path: Path, repo: Path, claude_home: Path):
    install = _install(claude_home)
    (install / "scripts" / "py" / "hook_safety.py").unlink()
    result = _run(_ctx(tmp_path, claude_home, repo), "DOC-09")
    assert result.status == core.STATUS_FAIL and "scripts/py/hook_safety.py" in result.evidence
    (install / "hooks" / "hooks.json").write_text("{roto", encoding="utf-8")
    assert _run(_ctx(tmp_path, claude_home, repo), "DOC-09").status == core.STATUS_FAIL


def test_smoke_test_detects_broken_hook(tmp_path: Path, repo: Path, claude_home: Path):
    (_install(claude_home) / "scripts" / "py" / "hook_safety.py").write_text("print('{}')\n", encoding="utf-8")
    result = _run(_ctx(tmp_path, claude_home, repo), "DOC-11")
    assert result.status == core.STATUS_FAIL and "hook_safety.py" in result.message


def test_interpreters(tmp_path: Path, claude_home: Path, monkeypatch):
    ctx = _ctx(tmp_path, claude_home)
    monkeypatch.setattr(core, "which", lambda name: None)
    assert "bash" in _run(ctx, "DOC-10").message
    store = r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\python.exe"
    monkeypatch.setattr(core, "which", lambda name: store if name == "python" else "/bin/bash")
    assert _run(ctx, "DOC-10").status == core.STATUS_FAIL
    assert _run(ctx, "DOC-11").status == core.STATUS_SKIP
    monkeypatch.setattr(core, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(core, "interpreter_version", lambda binary, flag="--version": (3, 9, 0))
    assert _run(ctx, "DOC-10").status == core.STATUS_FAIL
    monkeypatch.setattr(core, "interpreter_version", lambda binary, flag="--version": (3, 12, 0))
    assert _run(ctx, "DOC-10").status == core.STATUS_PASS


def test_runtime(tmp_path: Path, claude_home: Path, monkeypatch):
    ctx = _ctx(tmp_path, claude_home)
    monkeypatch.setattr(core, "which", lambda name: None)
    assert _run(ctx, "DOC-01").status == core.STATUS_FAIL
    monkeypatch.setattr(core, "which", lambda name: "/usr/bin/claude")
    monkeypatch.setattr(core, "run_capture", lambda *a, **k: (0, "2.1.30 (Claude Code)", ""))
    assert "2.1.30" in _run(ctx, "DOC-01").message


def test_data_dir_and_legacy(tmp_path: Path, repo: Path, claude_home: Path, data_dir: Path, monkeypatch):
    data = json.loads((claude_home / "plugins" / "installed_plugins.json").read_text(encoding="utf-8"))
    data["plugins"]["everything-claude-code@ecc"] = [{"installPath": "/x"}]
    (claude_home / "plugins" / "installed_plugins.json").write_text(json.dumps(data), encoding="utf-8")
    missing = tmp_path / "datos-nuevos"
    monkeypatch.setattr(doc, "data_dir", lambda: missing)
    result = _run(_ctx(tmp_path, claude_home, repo), "DOC-12")
    assert result.status == core.STATUS_WARN
    assert any("everything-claude-code@ecc" in e for e in result.evidence)
    result.fix.func()
    assert missing.is_dir()


def test_real_data_dir_resolution(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("AGY_PLUGIN_DATA", str(tmp_path / "pd"))
    assert REAL_DATA_DIR() == (tmp_path / "pd").resolve()


def test_project_template(tmp_path: Path, repo: Path, claude_home: Path):
    project = tmp_path / "proyecto"
    project.mkdir()
    ctx = _ctx(tmp_path, claude_home, repo, project)
    assert _run(ctx, "DOC-13").status == core.STATUS_SKIP
    _write(project / "CLAUDE.md", "# Plantilla\n")
    assert _run(ctx, "DOC-13").status == core.STATUS_PASS
    _write(project / "CLAUDE.md", "# Plantilla vieja\n")
    assert _run(ctx, "DOC-13").status == core.STATUS_WARN


def test_repo_check_with_real_repo(tmp_path: Path, claude_home: Path, monkeypatch):
    monkeypatch.setattr(doc.core, "find_repo_root", lambda start: None)
    (_install(claude_home) / im.MANIFEST_FILE).unlink()
    assert _run(_ctx(tmp_path, claude_home), "DOC-14").status == core.STATUS_SKIP
    result = _run(_ctx(tmp_path, claude_home, _REPO_ROOT), "DOC-14")
    assert result.status == core.STATUS_PASS, (result.message, result.evidence)


def test_repo_check_reports_drift(tmp_path: Path, claude_home: Path):
    fake = tmp_path / "repo-con-deriva"
    _write(fake / "plugin.json", '{"name": "aagy", "version": "1.0.0"}')
    _write(fake / "skills" / "nueva" / "SKILL.md", SKILL)
    (fake / "aagy-ecc").mkdir()
    result = _run(_ctx(tmp_path, claude_home, fake), "DOC-14")
    assert result.status == core.STATUS_WARN and result.fix is not None
    assert result.fix.argv[1].endswith("sync_aagy_ecc.py")


def test_cli(tmp_path: Path, repo: Path, claude_home: Path, capsys):
    assert doc.main(["--list-checks"]) == 0
    assert [c["id"] for c in json.loads(capsys.readouterr().out)] == list(core.CATALOG_IDS)
    code = doc.main(["--json", "--home", str(tmp_path / "home"), "--claude-home", str(claude_home),
                     "--repo-root", str(repo), "--only", "DOC-02,DOC-09"])
    data = json.loads(capsys.readouterr().out)
    assert code == 0 and data["summary"]["PASS"] == 2 and data["version"] == "1.0.0"


def test_doc14_skips_outside_aagy_repo(tmp_path: Path, claude_home: Path):
    other = tmp_path / "consumer"
    (other / ".git").mkdir(parents=True)
    result = doc.check_repo(_ctx(tmp_path, claude_home, repo=other))
    assert result.status == core.STATUS_SKIP
    assert "no es el repo aagy" in result.message
