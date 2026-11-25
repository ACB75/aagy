#!/usr/bin/env python3
"""Pruebas de ci_local.py (CI local y Actions opcionales) y del presupuesto 0 $."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import List, Sequence

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import aagy_config  # noqa: E402
import audit_plugin_parity as parity  # noqa: E402
import ci_local  # noqa: E402


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / ".git").mkdir(parents=True)
    return root


def test_run_steps_skips_missing_and_reports_failures(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / "ok.txt").write_text("x", encoding="utf-8")
    calls: List[Sequence[str]] = []

    def runner(argv: Sequence[str], _cwd: Path) -> int:
        calls.append(argv)
        return 1 if argv[0] == "bad" else 0

    steps = [ci_local.Step("good", ("good",), needs=("ok.txt",)), ci_local.Step("bad", ("bad",)),
             ci_local.Step("missing", ("x",), needs=("nope.txt",)), ci_local.Step("slow", ("slow",), fast=False)]
    results = {name: status for name, status, _ in ci_local.run_steps(steps, root, fast=True, runner=runner)}
    assert results["good"] == "OK" and results["bad"] == "FAIL" and results["missing"].startswith("SKIP")
    assert "slow" not in results and ("x",) not in calls


def test_project_steps_override_defaults(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / ".governance").mkdir()
    (root / ".governance" / "aagy.json").write_text(json.dumps({"ci": {"steps": ["make test", "make lint"]}}), encoding="utf-8")
    assert [s.argv for s in ci_local.configured_steps(root)] == [("make", "test"), ("make", "lint")]


def test_actions_on_off_never_touch_own_workflows(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    templates = root / "templates" / "github-actions"
    templates.mkdir(parents=True)
    (templates / "ci.yml").write_text("# aagy-template: ci\nname: x\n", encoding="utf-8")
    (templates / "own.yml").write_text("# aagy-template: own\n", encoding="utf-8")
    workflows = root / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "own.yml").write_text("name: propio\n", encoding="utf-8")
    assert [p.name for p in ci_local.actions_on(root)] == ["ci.yml"]
    assert [p.name for p in ci_local.active_templates(root)] == ["ci.yml"]
    assert [p.name for p in ci_local.actions_off(root)] == ["ci.yml"]
    assert (workflows / "own.yml").is_file() and not (workflows / "ci.yml").exists()


def test_repo_has_no_active_workflows_and_template_calls_ci_local() -> None:
    assert ci_local.active_templates(_REPO_ROOT) == []
    assert not list((_REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    discrepancies: List[str] = []
    parity._check_ci_template(_REPO_ROOT, discrepancies)
    assert discrepancies == []


def test_ci_template_with_extra_step_fails(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    target = root / parity.CI_TEMPLATE
    target.parent.mkdir(parents=True)
    target.write_text("steps:\n  - run: python scripts/py/ci_local.py run\n  - run: |\n      curl evil\n", encoding="utf-8")
    discrepancies: List[str] = []
    parity._check_ci_template(root, discrepancies)
    assert discrepancies and "curl evil" in discrepancies[0]


def test_budget_defaults_to_zero(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    assert aagy_config.paid_allowed(root, {}) is False
    assert aagy_config.paid_allowed(root, {"AAGY_BUDGET": "10"}) is True
    assert aagy_config.paid_allowed(root, {"AAGY_BUDGET": "abc"}) is False


def test_paid_skills_declared() -> None:
    assert {"exa-search", "deep-research"} <= set(aagy_config.paid_skills(_REPO_ROOT / "skills"))
    discrepancies: List[str] = []
    parity._check_paid_skills(_REPO_ROOT, discrepancies)
    assert discrepancies == []


def test_doctor_warns_private_repo_with_workflows(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    (root / ".governance").mkdir()
    (root / ".governance" / "aagy.json").write_text(json.dumps({"ci": {"private": True}}), encoding="utf-8")
    (root / ".github" / "workflows").mkdir(parents=True)
    (root / ".github" / "workflows" / "x.yml").write_text("name: x\n", encoding="utf-8")
    status, message, _ = aagy_config.doctor_findings(root, {})
    assert status == aagy_config.STATUS_WARN and "minutos de pago" in message


def test_toggle_gemini_refuses_without_budget(tmp_path: Path, monkeypatch) -> None:
    import toggle_gemini_mcp

    config = tmp_path / "mcp_config.json"
    config.write_text(json.dumps({"mcpServers": {"gemini-mcp": {"disabled": True}}}), encoding="utf-8")
    monkeypatch.delenv("AAGY_BUDGET", raising=False)
    monkeypatch.chdir(tmp_path)
    assert toggle_gemini_mcp.main(["--config", str(config), "--enable"]) == 2
    assert json.loads(config.read_text(encoding="utf-8"))["mcpServers"]["gemini-mcp"]["disabled"] is True
