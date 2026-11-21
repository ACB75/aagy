#!/usr/bin/env python3
"""Pruebas del núcleo común de los doctors (doctor_core.py) y del manifiesto de instalación."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import doctor_core as core  # noqa: E402
import install_manifest as im  # noqa: E402


def _ok(check_id: str):
    return lambda ctx: core.result(check_id, core.STATUS_PASS, "ok")


def _registry(**overrides):
    registry = {cid: _ok(cid) for cid in core.CATALOG_IDS}
    registry.update(overrides)
    return registry


# --------------------------------------------------------------------------- #
# Catálogo y registro
# --------------------------------------------------------------------------- #
def test_catalog_has_fourteen_unique_ids():
    assert core.CATALOG_IDS == tuple(f"DOC-{n:02d}" for n in range(1, 15))
    assert json.loads(core.catalog_json())[0] == {"id": "DOC-01", "name": "Runtime del harness", "scope": core.SCOPE_INSTALL}


def test_validate_registry_rejects_missing_and_extra_ids():
    registry = _registry()
    del registry["DOC-07"]
    with pytest.raises(ValueError, match="DOC-07"):
        core.validate_registry(registry)
    with pytest.raises(ValueError, match="DOC-99"):
        core.validate_registry(_registry(**{"DOC-99": _ok("DOC-99")}))


def test_select_ids_keeps_catalog_order():
    assert core.select_ids(["doc-05", "DOC-01"]) == ("DOC-01", "DOC-05")
    assert "DOC-14" not in core.select_ids(skip=["DOC-14"])
    assert core.split_ids("DOC-01, ,DOC-02") == ["DOC-01", "DOC-02"]


# --------------------------------------------------------------------------- #
# Runner
# --------------------------------------------------------------------------- #
def test_run_checks_converts_exceptions_and_timeouts_into_fail():
    def boom(ctx):
        raise RuntimeError("roto")

    def slow(ctx):
        time.sleep(1)
        return core.result("DOC-02", core.STATUS_PASS, "tarde")

    results = core.run_checks(_registry(**{"DOC-01": boom, "DOC-02": slow}), None, ["DOC-01", "DOC-02", "DOC-03"], timeout_s=0.2)
    assert [r.status for r in results] == [core.STATUS_FAIL, core.STATUS_FAIL, core.STATUS_PASS]
    assert "roto" in results[0].message
    assert "Timeout" in results[1].message


def test_run_checks_rejects_results_with_wrong_id_or_status():
    bad_id = lambda ctx: core.result("DOC-09", core.STATUS_PASS, "x")  # noqa: E731
    bad_status = lambda ctx: core.CheckResult("DOC-02", "MAYBE", "x")  # noqa: E731
    results = core.run_checks(_registry(**{"DOC-01": bad_id, "DOC-02": bad_status}), None, ["DOC-01", "DOC-02"])
    assert all(r.status == core.STATUS_FAIL for r in results)


def test_exit_code_and_strict():
    warn = core.Report("t", "", "", (core.result("DOC-01", core.STATUS_WARN, "w"),))
    fail = core.Report("t", "", "", (core.result("DOC-01", core.STATUS_FAIL, "f"),))
    assert core.exit_code(warn) == core.EXIT_OK
    assert core.exit_code(warn, strict=True) == core.EXIT_FAILED
    assert core.exit_code(fail) == core.EXIT_FAILED


# --------------------------------------------------------------------------- #
# Salida
# --------------------------------------------------------------------------- #
def _sample_report() -> core.Report:
    fix = core.FixAction("Re-sincronizar", ("bash", "aagy sync.sh"))
    return core.Report(
        "aagy (Antigravity)",
        "/p",
        "4.1.0",
        (
            core.result("DOC-01", core.STATUS_PASS, "bien", "detalle oculto"),
            core.result("DOC-05", core.STATUS_FAIL, "mal", "evidencia", fix=fix),
            core.result("DOC-13", core.STATUS_SKIP, "no aplica"),
        ),
    )


def test_render_text_shows_fix_and_summary_without_color():
    text = core.render_text(_sample_report())
    assert "[FAIL] DOC-05 Reglas Tier 1: mal" in text
    assert '→ Arreglo: bash "aagy sync.sh"' in text
    assert "detalle oculto" not in text
    assert "1 PASS · 0 WARN · 1 FAIL · 1 SKIP  (3 checks)" in text
    assert "\033[" not in text
    assert "detalle oculto" in core.render_text(_sample_report(), color=True, verbose=True)


def test_render_json_matches_schema():
    data = json.loads(core.render_json(_sample_report()))
    assert set(data) == {"target", "plugin_dir", "version", "summary", "checks"}
    assert data["summary"] == {"PASS": 1, "WARN": 0, "FAIL": 1, "SKIP": 1}
    assert data["checks"][1] == {
        "id": "DOC-05", "name": "Reglas Tier 1", "scope": core.SCOPE_INSTALL, "status": "FAIL",
        "message": "mal", "evidence": ["evidencia"], "fix": 'bash "aagy sync.sh"',
    }


# --------------------------------------------------------------------------- #
# Arreglos
# --------------------------------------------------------------------------- #
def test_collect_fixes_dedupes_and_ignores_pass():
    fix = core.FixAction("A", ("x",))
    results = [
        core.result("DOC-01", core.STATUS_WARN, "w", fix=fix),
        core.result("DOC-02", core.STATUS_FAIL, "f", fix=core.FixAction("A", ("x",))),
        core.result("DOC-03", core.STATUS_PASS, "p", fix=core.FixAction("B", ("y",))),
    ]
    assert [f.description for f in core.collect_fixes(results)] == ["A"]


def test_apply_fixes_without_tty_or_yes_changes_nothing(tmp_path: Path, monkeypatch):
    target = tmp_path / "nuevo"
    monkeypatch.setattr(sys, "stdin", None)
    lines = []
    fixes = [core.FixAction("Crear", func=lambda: target.mkdir())]
    assert core.apply_fixes(fixes, assume_yes=False, out=lines.append) == 0
    assert not target.exists()
    assert any("--fix --yes" in line for line in lines)


def test_apply_fixes_with_yes_runs_func_and_argv(tmp_path: Path):
    target = tmp_path / "nuevo"
    fixes = [
        core.FixAction("Crear", func=lambda: target.mkdir()),
        core.FixAction("Python", (sys.executable, "-c", "print('ok')")),
        core.FixAction("Roto", (sys.executable, "-c", "import sys; sys.exit(3)")),
        core.FixAction("Vacío"),
    ]
    lines = []
    assert core.apply_fixes(fixes, assume_yes=True, out=lines.append) == 2
    assert target.is_dir()
    assert core.apply_fixes([], assume_yes=True, out=lines.append) == 0


def test_apply_fixes_asks_each_action(tmp_path: Path, monkeypatch):
    class FakeTty:
        def isatty(self):
            return True

    monkeypatch.setattr(sys, "stdin", FakeTty())
    created = []
    fixes = [core.FixAction("Uno", func=lambda: created.append(1)), core.FixAction("Dos", func=lambda: created.append(2))]
    answers = iter(["s", "n"])
    core.apply_fixes(fixes, assume_yes=False, ask=lambda prompt: next(answers), out=lambda line: None)
    assert created == [1]


def test_finish_routes_fix_output_to_stderr_in_json(capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", None)
    args = core.build_parser("t").parse_args(["--json", "--fix"])
    assert core.finish(_sample_report(), args) == core.EXIT_FAILED
    captured = capsys.readouterr()
    assert json.loads(captured.out)["summary"]["FAIL"] == 1
    assert "Plan de arreglos" in captured.err


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def test_compare_trees_normalizes_crlf(tmp_path: Path):
    a, b = tmp_path / "a", tmp_path / "b"
    for base in (a, b):
        (base / "x").mkdir(parents=True)
    (a / "x" / "same.md").write_bytes(b"hola\n")
    (b / "x" / "same.md").write_bytes(b"hola\r\n")
    (a / "x" / "changed.md").write_text("1", encoding="utf-8")
    (b / "x" / "changed.md").write_text("2", encoding="utf-8")
    (a / "only-a.md").write_text("a", encoding="utf-8")
    (b / "only-b.md").write_text("b", encoding="utf-8")
    (b / core.MANIFEST_FILE).write_text("{}", encoding="utf-8")
    (b / "__pycache__").mkdir()
    (b / "__pycache__" / "m.pyc").write_bytes(b"\0")
    diff = core.compare_trees(core.list_tree(a), core.list_tree(b))
    assert diff.missing == ("only-a.md",)
    assert diff.changed == ("x/changed.md",)
    assert diff.extra == ("only-b.md",)
    assert not diff.clean
    assert diff.summary() == "1 faltan, 1 distintos, 1 sobrantes"
    assert diff.sample(2) == ("falta only-a.md", "distinto x/changed.md")


def test_frontmatter_and_budget_helpers(tmp_path: Path):
    skills, agents = tmp_path / "skills", tmp_path / "agents"
    (skills / "good").mkdir(parents=True)
    (skills / "good" / "SKILL.md").write_text("---\nname: good\ndescription: \"corta\"\n---\n", encoding="utf-8")
    (skills / "long").mkdir()
    (skills / "long" / "SKILL.md").write_text(f"---\ndescription: {'x' * 141}\n---\n", encoding="utf-8")
    (skills / "empty").mkdir()
    agents.mkdir()
    (agents / "README.md").write_text("# no es agente", encoding="utf-8")
    (agents / "a.md").write_text("---\nname: a\n---\n", encoding="utf-8")
    (agents / "b.md").write_text(f"---\ndescription: {'y' * 121}\n---\n", encoding="utf-8")
    problems = core.frontmatter_problems(skills, agents)
    assert len(problems) == 4
    assert core.frontmatter_value("sin frontmatter", "description") is None

    rules = tmp_path / "AGENTS.md"
    assert core.rules_budget_problems(rules) == ["'AGENTS.md' falta o está vacío."]
    rules.write_text("x" * 70_000, encoding="utf-8")
    assert len(core.rules_budget_problems(rules)) == 2
    rules.write_text("# reglas\n", encoding="utf-8")
    assert core.rules_budget_problems(rules) == []


def test_misc_helpers(tmp_path: Path):
    assert core.parse_version("Python 3.12.4") == (3, 12, 4)
    assert core.parse_version("v2.1") == (2, 1, 0)
    assert core.parse_version("nada") is None
    assert core.is_windows_store_alias(r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\python.exe")
    assert not core.is_windows_store_alias("/usr/bin/python3")
    assert core.writable_dir(tmp_path / "a" / "b")
    assert core.run_capture(["/no/existe/bin"])[0] == -1
    code, out, _ = core.run_capture([sys.executable, "-c", "import sys; print(sys.stdin.read())"], stdin="eco")
    assert (code, out.strip()) == (0, "eco")
    assert core.interpreter_version(sys.executable) == tuple(sys.version_info[:3])
    ok, message = core.required_interpreter(("no-existe-python",), (3, 10, 0), "Python")
    assert not ok and "no está en el PATH" in message
    assert core.load_json(tmp_path / "nada.json") is None
    (tmp_path / "lista.json").write_text("[1]", encoding="utf-8")
    assert core.load_json_dict(tmp_path / "lista.json") is None


def test_find_repo_root(tmp_path: Path):
    (tmp_path / "aagy-ecc").mkdir()
    (tmp_path / "plugin.json").write_text('{"name": "aagy"}', encoding="utf-8")
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert core.find_repo_root(nested) == tmp_path
    assert core.find_repo_root(Path("/")) is None


# --------------------------------------------------------------------------- #
# Manifiesto de instalación
# --------------------------------------------------------------------------- #
def _fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "aagy-ecc" / ".claude-plugin").mkdir(parents=True)
    (repo / "plugin.json").write_text('{"name": "aagy", "version": "4.1.0"}', encoding="utf-8")
    (repo / "aagy-ecc" / ".claude-plugin" / "plugin.json").write_text('{"name": "aagy-ecc", "version": "4.2.0"}', encoding="utf-8")
    return repo


def test_manifest_roundtrip(tmp_path: Path):
    repo = _fake_repo(tmp_path)
    now = datetime(2026, 11, 20, 23, 0, 0, 123, tzinfo=timezone.utc)
    manifest = im.build_manifest(repo, im.HARNESS_CLAUDE, "full", now=now)
    assert manifest.version == "4.2.0"
    assert manifest.installed_at == "2026-11-20T23:00:00+00:00"
    assert manifest.commit == ""  # no es un repo git
    im.write_manifest(tmp_path / "dest", manifest)
    assert im.read_manifest(tmp_path / "dest") == manifest
    assert im.build_manifest(repo, im.HARNESS_AGY, "generic").version == "4.1.0"


def test_read_manifest_tolerates_missing_or_corrupt(tmp_path: Path):
    assert im.read_manifest(tmp_path) is None
    (tmp_path / im.MANIFEST_FILE).write_text("{no json", encoding="utf-8")
    assert im.read_manifest(tmp_path) is None
    (tmp_path / im.MANIFEST_FILE).write_text('{"profile": "x"}', encoding="utf-8")
    assert im.read_manifest(tmp_path) is None
    (tmp_path / im.MANIFEST_FILE).write_text("[]", encoding="utf-8")
    assert im.read_manifest(tmp_path) is None
    assert im.read_version(tmp_path, im.HARNESS_AGY) == ""


def test_manifest_cli_write_show_and_never_abort(tmp_path: Path, capsys):
    repo = _fake_repo(tmp_path)
    dest = tmp_path / "plugin"
    assert im.main(["show", "--dest", str(dest)]) == 1
    assert im.main(["write", "--dest", str(dest), "--harness", "agy", "--profile", "all", "--repo-root", str(repo)]) == 0
    assert im.main(["show", "--dest", str(dest)]) == 0
    assert '"profile": "all"' in capsys.readouterr().out
    blocker = tmp_path / "fichero"
    blocker.write_text("x", encoding="utf-8")
    assert im.main(["write", "--dest", str(blocker / "sub"), "--repo-root", str(repo)]) == 0
    assert "No se pudo escribir" in capsys.readouterr().err
