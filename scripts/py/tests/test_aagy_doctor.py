#!/usr/bin/env python3
"""Pruebas de /aagy-doctor (aagy_doctor.py) con instalaciones falsas en tmp_path."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import aagy_doctor as doc  # noqa: E402
import doctor_core as core  # noqa: E402
import install_manifest as im  # noqa: E402

SKILL = "---\nname: {name}\ndescription: Skill {name}\n---\n# {name}\n"
AGENT = "---\nname: {name}\ndescription: Agent {name}\nmodel: inherit\n---\n"
HOOKS = {
    "aagy-safety-gate": {
        "PreToolUse": [{"matcher": "run_command", "hooks": [{"type": "command", "command": "python scripts/check.py"}]}]
    }
}


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    _write(root / "plugin.json", '{"name": "aagy", "version": "1.0.0"}')
    _write(root / "aagy-ecc" / ".claude-plugin" / "plugin.json", '{"name": "aagy-ecc", "version": "1.0.0"}')
    for name in ("s1", "aagy-doctor", "extra"):
        _write(root / "skills" / name / "SKILL.md", SKILL.format(name=name))
    _write(root / "agents" / "a1.md", AGENT.format(name="a1"))
    _write(root / "rules" / "AGENTS.md", "# Reglas Tier 1\n")
    _write(root / "hooks.json", json.dumps(HOOKS))
    _write(root / "scripts" / "sh" / "aagy-sync.sh", "case x in\n  generic)\n    SKILLS=(s1 aagy-doctor missing)\n    AGENTS=(a1.md)\n    ;;\nesac\n")
    return root


@pytest.fixture
def plugin(tmp_path: Path, repo: Path) -> Path:
    """Instalación sana de la fase generic, con su manifiesto y el script del hook dentro del plugin."""
    dest = tmp_path / "home" / ".gemini" / "config" / "plugins" / "aagy"
    for name in ("s1", "aagy-doctor"):
        shutil.copytree(repo / "skills" / name, dest / "skills" / name)
    _write(dest / "agents" / "a1.md", (repo / "agents" / "a1.md").read_text(encoding="utf-8"))
    for rel in ("rules/AGENTS.md", "plugin.json", "hooks.json"):
        _write(dest / rel, (repo / rel).read_text(encoding="utf-8"))
    _write(dest / "scripts" / "check.py", "print('ok')\n")
    (dest / ".data").mkdir()
    im.write_manifest(dest, im.InstallManifest("agy", "generic", "1.0.0", "abc1234def", "2026-11-20T00:00:00+00:00", str(repo)))
    return dest


def _ctx(tmp_path: Path, plugin_dir: Path, repo: Path = None, project: Path = None) -> doc.AgyContext:
    argv = ["--home", str(tmp_path / "home"), "--plugin-dir", str(plugin_dir), "--project", str(project or tmp_path)]
    if repo is not None:
        argv += ["--repo-root", str(repo)]
    return doc.build_context(doc.parse_args(argv))


def _run(ctx: doc.AgyContext, check_id: str) -> core.CheckResult:
    return doc.REGISTRY[check_id](ctx)


@pytest.fixture
def interpreters(monkeypatch):
    """Simula python ≥ 3.10 y pwsh 7 en el PATH."""
    monkeypatch.setattr(core, "which", lambda name: f"/usr/bin/{name}" if name in ("python", "python3", "pwsh") else None)
    monkeypatch.setattr(core, "interpreter_version", lambda binary, flag="--version": (7, 4, 0) if "pwsh" in binary else (3, 12, 1))


def test_registry_matches_catalog():
    core.validate_registry(doc.REGISTRY)
    assert tuple(doc.REGISTRY) == core.CATALOG_IDS


def test_healthy_install_has_no_fail(tmp_path: Path, repo: Path, plugin: Path, interpreters, monkeypatch):
    monkeypatch.setattr(doc, "git_hooks_installed", lambda root: True)
    monkeypatch.setattr("audit_plugin_parity.audit_parity", lambda root: type("R", (), {"discrepancies": ()})())
    ctx = _ctx(tmp_path, plugin, repo)
    results = {r.check_id: r for r in core.run_checks(doc.REGISTRY, ctx)}
    statuses = {cid: r.status for cid, r in results.items()}
    assert core.STATUS_FAIL not in statuses.values(), {cid: r.message for cid, r in results.items()}
    for cid in ("DOC-02", "DOC-03", "DOC-04", "DOC-05", "DOC-06", "DOC-07", "DOC-08", "DOC-09", "DOC-10", "DOC-12", "DOC-14"):
        assert statuses[cid] == core.STATUS_PASS, (cid, results[cid].message, results[cid].evidence)
    assert statuses["DOC-01"] == core.STATUS_SKIP  # 'antigravity' no está en el PATH simulado
    assert statuses["DOC-13"] == core.STATUS_SKIP
    assert "fase 'generic'" in results["DOC-06"].message


def test_missing_plugin_fails_and_skips_install_checks(tmp_path: Path, repo: Path):
    ctx = _ctx(tmp_path, tmp_path / "no-existe", repo)
    assert _run(ctx, "DOC-02").status == core.STATUS_FAIL
    assert _run(ctx, "DOC-02").fix is not None
    for cid in ("DOC-03", "DOC-04", "DOC-05", "DOC-06", "DOC-07", "DOC-08", "DOC-09"):
        assert _run(ctx, cid).status == core.STATUS_SKIP


def test_bad_manifest_and_missing_rules(tmp_path: Path, repo: Path, plugin: Path):
    (plugin / "plugin.json").write_text('{"name": "otro"}', encoding="utf-8")
    (plugin / "rules" / "AGENTS.md").write_text("", encoding="utf-8")
    ctx = _ctx(tmp_path, plugin, repo)
    assert _run(ctx, "DOC-03").status == core.STATUS_FAIL
    assert _run(ctx, "DOC-05").status == core.STATUS_FAIL
    (plugin / "plugin.json").write_text("{roto", encoding="utf-8")
    assert _run(ctx, "DOC-03").status == core.STATUS_FAIL


def test_rules_drift_and_version_mismatch_warn(tmp_path: Path, repo: Path, plugin: Path):
    (plugin / "rules" / "AGENTS.md").write_text("# Reglas antiguas\n", encoding="utf-8")
    (repo / "plugin.json").write_text('{"name": "aagy", "version": "2.0.0"}', encoding="utf-8")
    (plugin / im.MANIFEST_FILE).unlink()
    ctx = _ctx(tmp_path, plugin, repo)
    rules = _run(ctx, "DOC-05")
    assert rules.status == core.STATUS_WARN and rules.fix is not None
    version = _run(ctx, "DOC-04")
    assert version.status == core.STATUS_WARN
    assert any("2.0.0" in item for item in version.evidence + (version.message,))
    drift = _run(ctx, "DOC-07")
    assert drift.status == core.STATUS_WARN and "distinto rules/AGENTS.md" in drift.evidence


def test_catalog_detects_missing_phase_items_and_bad_frontmatter(tmp_path: Path, repo: Path, plugin: Path):
    shutil.rmtree(plugin / "skills" / "aagy-doctor")
    _write(plugin / "skills" / "rota" / "SKILL.md", "sin frontmatter")
    ctx = _ctx(tmp_path, plugin, repo)
    catalog = _run(ctx, "DOC-06")
    assert catalog.status == core.STATUS_WARN
    assert "aagy-doctor" in catalog.evidence[0]
    assert any("rota" in item for item in catalog.evidence)
    assert _run(ctx, "DOC-08").status == core.STATUS_WARN


def test_expected_catalog_for_all_and_unknown_phase(repo: Path):
    skills, agents = doc.expected_catalog(repo, "all")
    assert skills == ("aagy-doctor", "extra", "s1") and agents == ("a1.md",)
    assert doc.expected_catalog(repo, "kakebo") is None
    assert doc.expected_catalog(None, "generic") is None
    assert doc.expected_catalog(repo, "generic") == (("s1", "aagy-doctor"), ("a1.md",))


def test_hooks_with_relative_scripts_warn(tmp_path: Path, repo: Path, plugin: Path, interpreters):
    hooks = {"g": {"PreToolUse": [{"hooks": [
        {"command": "pwsh -File scripts/ps1/safety-check.ps1"},
        {"command": "pwsh -File scripts/ps1/safety-check.ps1"},
        {"command": "nope /abs/missing.py"},
    ]}]}}
    (plugin / "hooks.json").write_text(json.dumps(hooks), encoding="utf-8")
    result = _run(_ctx(tmp_path, plugin, repo), "DOC-09")
    assert result.status == core.STATUS_WARN
    assert len(result.evidence) == 3  # relativo (sin duplicar), intérprete ausente, ruta absoluta inexistente
    assert any("es relativo" in e for e in result.evidence)


def test_hooks_json_invalid_or_absent(tmp_path: Path, repo: Path, plugin: Path):
    (plugin / "hooks.json").write_text("{roto", encoding="utf-8")
    ctx = _ctx(tmp_path, plugin, repo)
    assert _run(ctx, "DOC-09").status == core.STATUS_FAIL
    (plugin / "hooks.json").unlink()
    assert _run(ctx, "DOC-09").status == core.STATUS_WARN


def test_split_command_and_iter_hooks():
    assert doc.split_command('pwsh -File "scripts/a b.ps1" -X') == ("pwsh", ["scripts/a b.ps1"])
    assert doc.split_command("") == ("", [])
    assert doc.iter_hook_commands({"g": {"Stop": [{"hooks": [{"command": "x"}, {"type": "command"}]}]}, "bad": 1}) == ["x"]


def test_interpreters_fail_without_pwsh(tmp_path: Path, plugin: Path, monkeypatch):
    monkeypatch.setattr(core, "which", lambda name: "/usr/bin/python3" if name == "python3" else None)
    monkeypatch.setattr(core, "interpreter_version", lambda binary, flag="--version": (3, 12, 0))
    result = _run(_ctx(tmp_path, plugin), "DOC-10")
    assert result.status == core.STATUS_FAIL and "PowerShell" in result.message


def test_interpreters_reject_old_python(tmp_path: Path, plugin: Path, monkeypatch):
    monkeypatch.setattr(core, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(core, "interpreter_version", lambda binary, flag="--version": (7, 4, 0) if "pwsh" in binary else (3, 8, 0))
    result = _run(_ctx(tmp_path, plugin), "DOC-10")
    assert result.status == core.STATUS_FAIL and "3.8.0" in result.message


def test_smoke_skips_without_pwsh_and_checks_output(tmp_path: Path, repo: Path, plugin: Path, monkeypatch):
    monkeypatch.setattr(core, "which", lambda name: None)
    assert _run(_ctx(tmp_path, plugin, repo), "DOC-11").status == core.STATUS_SKIP
    _write(repo / "scripts" / "ps1" / "safety-check.ps1", "# fake")
    monkeypatch.setattr(core, "which", lambda name: "/usr/bin/pwsh")
    outputs = iter([(0, '{"decision":"deny"}', ""), (0, '{"decision":"allow"}', "")])
    monkeypatch.setattr(core, "run_capture", lambda *a, **k: next(outputs))
    assert _run(_ctx(tmp_path, plugin, repo), "DOC-11").status == core.STATUS_PASS
    outputs = iter([(0, '{"decision":"allow"}', ""), (0, '{"decision":"allow"}', "")])
    assert _run(_ctx(tmp_path, plugin, repo), "DOC-11").status == core.STATUS_FAIL


def test_data_dir_missing_offers_fix_and_legacy_is_reported(tmp_path: Path, repo: Path, plugin: Path, monkeypatch):
    monkeypatch.delenv(doc.ENV_PLUGIN_DATA, raising=False)
    shutil.rmtree(plugin / ".data")
    (plugin.parent / "everything-claude-code").mkdir()
    _write(plugin / "agents" / "viejo.md", AGENT.format(name="viejo"))
    result = _run(_ctx(tmp_path, plugin, repo), "DOC-12")
    assert result.status == core.STATUS_WARN
    assert result.fix is not None and result.fix.func is not None
    assert any("everything-claude-code" in e for e in result.evidence)
    assert any("viejo.md" in e for e in result.evidence)
    result.fix.func()
    assert (plugin / ".data").is_dir()


def test_data_dir_from_env(tmp_path: Path, plugin: Path, monkeypatch):
    monkeypatch.setenv(doc.ENV_PLUGIN_DATA, str(tmp_path / "datos"))
    assert doc.data_dir(_ctx(tmp_path, plugin)) == tmp_path / "datos"


def test_project_agents_dir(tmp_path: Path, repo: Path, plugin: Path):
    project = tmp_path / "proyecto"
    _write(project / ".agents" / "skills" / "s1" / "SKILL.md", SKILL.format(name="s1"))
    _write(project / ".agents" / "rules" / "local.md", "")
    result = _run(_ctx(tmp_path, plugin, repo, project), "DOC-13")
    assert result.status == core.STATUS_WARN
    assert any("ocultan" in e for e in result.evidence)
    assert any("vacío" in e for e in result.evidence)
    (project / ".agents" / "rules" / "local.md").write_text("# ok\n", encoding="utf-8")
    shutil.rmtree(project / ".agents" / "skills" / "s1")
    assert _run(_ctx(tmp_path, plugin, repo, project), "DOC-13").status == core.STATUS_PASS


def test_repo_check_skips_without_repo_and_reports_parity(tmp_path: Path, repo: Path, plugin: Path, monkeypatch):
    monkeypatch.setattr(doc.core, "find_repo_root", lambda start: None)
    (plugin / im.MANIFEST_FILE).unlink()
    assert _run(_ctx(tmp_path, plugin), "DOC-14").status == core.STATUS_SKIP
    assert _run(_ctx(tmp_path, plugin), "DOC-07").status == core.STATUS_SKIP
    monkeypatch.setattr(doc, "git_hooks_installed", lambda root: False)
    result = _run(_ctx(tmp_path, plugin, repo), "DOC-14")
    assert result.status == core.STATUS_WARN  # el repo falso no tiene paridad real ni git hooks


def test_repo_root_from_manifest(tmp_path: Path, repo: Path, plugin: Path):
    ctx = _ctx(tmp_path, plugin)
    assert ctx.repo_root == repo.resolve()
    assert ctx.phase == "generic"


def test_sync_fix_prefers_pwsh(tmp_path: Path, repo: Path, plugin: Path, monkeypatch):
    monkeypatch.setattr(core, "which", lambda name: "/usr/bin/pwsh" if name == "pwsh" else None)
    fix = doc.sync_fix(_ctx(tmp_path, plugin, repo))
    assert fix.argv[0] == "/usr/bin/pwsh" and "-Phase" in fix.argv and "generic" in fix.argv
    monkeypatch.setattr(core, "which", lambda name: None)
    fix = doc.sync_fix(_ctx(tmp_path, plugin, repo))
    assert fix.argv[0] == "bash" and fix.argv[-1] == str(plugin)


def test_cli_json_and_list_checks(tmp_path: Path, repo: Path, plugin: Path, capsys):
    assert doc.main(["--list-checks"]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 15
    code = doc.main(["--json", "--home", str(tmp_path / "home"), "--repo-root", str(repo), "--only", "DOC-02,DOC-05"])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert [c["id"] for c in data["checks"]] == ["DOC-02", "DOC-05"]
    assert data["version"] == "1.0.0"


def test_read_only_without_fix(tmp_path: Path, repo: Path, plugin: Path, capsys):
    before = {p: p.stat().st_mtime_ns for p in plugin.rglob("*")}
    doc.main(["--home", str(tmp_path / "home"), "--repo-root", str(repo)])
    capsys.readouterr()
    assert before == {p: p.stat().st_mtime_ns for p in plugin.rglob("*")}


@pytest.mark.skipif(sys.platform == "win32" or shutil.which("bash") is None, reason="necesita bash POSIX")
def test_real_generic_install_from_this_repo(tmp_path: Path):
    """Integración: aagy-sync.sh instala la fase generic del repo real y el doctor la valida."""
    dest = tmp_path / "home" / ".gemini" / "config" / "plugins" / "aagy"
    subprocess.run(["bash", str(_REPO_ROOT / "scripts" / "sh" / "aagy-sync.sh"), "generic", str(dest)],
                   check=True, capture_output=True, timeout=120)
    manifest = im.read_manifest(dest)
    assert manifest is not None and manifest.profile == "generic" and manifest.source_repo == str(_REPO_ROOT)
    ctx = _ctx(tmp_path, dest)
    for cid in ("DOC-02", "DOC-03", "DOC-05", "DOC-06", "DOC-07", "DOC-08"):
        result = doc.REGISTRY[cid](ctx)
        assert result.status == core.STATUS_PASS, (cid, result.message, result.evidence)
