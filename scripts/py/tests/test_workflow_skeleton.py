"""Esqueleto común de workflows y su check (#94, CA-04)."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import audit_plugin_parity as parity  # noqa: E402
import workflow_skeleton as ws  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]
GOOD = """---
name: x
---

# x

## Cuándo usarlo

a

## Uso

b

## Qué hacer

c

## Reglas

d

## Paridad

Claude Code: comando `/x`.

## Extra

e
"""


def test_own_workflows_follow_skeleton():
    fails = [f for f in ws.audit(REPO_ROOT) if f.level == ws.LEVEL_FAIL]
    assert fails == []


def test_every_own_workflow_exists():
    keys = {key for key, _ in ws.workflow_files(REPO_ROOT)}
    assert ws.OWN_WORKFLOWS <= keys


def test_good_skeleton_passes():
    assert ws.check_text(GOOD, own=True) == []


def test_order_and_extra_sections_before_common_fail():
    swapped = GOOD.replace("## Uso\n", "## TMP\n").replace("## Qué hacer\n", "## Uso\n").replace("## TMP\n", "## Qué hacer\n")
    assert any("orden" in p for p in ws.check_text(swapped, own=True))
    extra_first = GOOD.replace("# x\n", "# x\n\n## Intro\n\nz\n")
    assert ws.check_text(extra_first, own=True)


def test_parity_must_name_equivalent_or_asymmetry():
    vague = GOOD.replace("Claude Code: comando `/x`.", "Igual.")
    assert any("Paridad" in p for p in ws.check_text(vague, own=True))
    asym = GOOD.replace("Claude Code: comando `/x`.", "Asimetría: Antigravity no tiene este evento.")
    assert ws.check_text(asym, own=True) == []


def test_inherited_accept_english_aliases():
    inherited = "## When to Use\n## Usage\n## Process\n## Rules\n## Parity\n"
    assert ws.check_text(inherited, own=False) == []
    assert ws.check_text(inherited, own=True)
    assert ws.check_text("## Notes\n", own=False)


def test_headings_ignore_code_blocks():
    assert ws.headings("## A\n```\n## B\n```\n## 2. C\n") == ["A", "C"]


def test_parity_audit_flags_broken_own_workflow(tmp_path):
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "todo-archiver.md").write_text("# roto\n", encoding="utf-8")
    discrepancies = []
    parity._check_workflow_skeleton(tmp_path, discrepancies)
    assert discrepancies and "agents/todo-archiver" in discrepancies[0]


def test_inherited_without_skeleton_fails(tmp_path):
    (tmp_path / "agents").mkdir()
    (tmp_path / "agents" / "heredado.md").write_text("# x\n\n## Notes\n", encoding="utf-8")
    findings = ws.audit(tmp_path)
    assert [f.level for f in findings] == [ws.LEVEL_FAIL]
    assert ws.main(["--repo", str(tmp_path)]) == 1


def test_cli_exit_codes(capsys):
    assert ws.main(["--repo", str(REPO_ROOT)]) == 0
    assert "sin esqueleto común: 0" in capsys.readouterr().out
