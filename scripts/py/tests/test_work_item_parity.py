"""Issues, PR y TODO con las mismas secciones y check de paridad issues ↔ TODO (#93)."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import backlog  # noqa: E402
import doc_templates as dt  # noqa: E402
from new_lifecycle_task import scaffold_lifecycle_task  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[3]

TODO = """# Backlog

## 1. Backlog Activo

## Épica: Algo grande (#10)

- [ ] **Tarea abierta**
  <!-- aagy-task: id=abierta issue=11 -->

- [ ] **Tarea con issue cerrada**
  <!-- aagy-task: id=cerrada issue=12 -->

- [x] **Tarea hecha**
  <!-- aagy-task: id=hecha issue=13 -->

- [ ] **Sin issue**
  <!-- aagy-task: id=sin-issue -->
"""


def _issues(**states):
    return [{"number": int(k[1:]), "state": v} for k, v in states.items()]


def test_parity_diff_reports_every_mismatch():
    epic_text = "## Épica: Algo grande (#10)"
    issues = _issues(n10="OPEN", n11="OPEN", n12="CLOSED", n13="OPEN", n14="OPEN")
    diff = backlog.parity_diff(backlog.parse_backlog(TODO), issues, epic_text)
    assert diff == {
        "issue_without_task": ["#14"],
        "task_on_closed_issue": ["cerrada (#12)"],
        "done_task_open_issue": ["hecha (#13)"],
    }


def test_parity_diff_clean_when_aligned():
    issues = _issues(n10="OPEN", n11="OPEN", n12="OPEN", n13="CLOSED")
    diff = backlog.parity_diff(backlog.parse_backlog(TODO), issues, "(#10)")
    assert not any(diff.values())


def test_gh_sync_check_exit_codes(tmp_path, monkeypatch, capsys):
    (tmp_path / ".git").mkdir()
    todo = backlog.locate_repo(tmp_path).todo_path
    todo.parent.mkdir(parents=True, exist_ok=True)
    todo.write_text(TODO, encoding="utf-8")
    monkeypatch.setattr(backlog, "_fetch_gh_issues", lambda _cwd: _issues(n10="OPEN", n11="OPEN", n12="OPEN", n13="CLOSED"))
    assert backlog.main(["--repo", str(tmp_path), "gh-sync", "--check"]) == 0
    monkeypatch.setattr(backlog, "_fetch_gh_issues", lambda _cwd: _issues(n11="OPEN", n12="CLOSED", n15="OPEN"))
    assert backlog.main(["--repo", str(tmp_path), "gh-sync", "--check"]) == 1
    err = capsys.readouterr().err
    assert "#15" in err and "cerrada (#12)" in err


def test_github_templates_share_work_item_sections():
    assert dt.check_github(REPO_ROOT) == {}


def test_check_work_item_detects_missing_and_order():
    assert dt.check_work_item("## 1. Motivación\n## 2. Criterios de aceptación\n## 3. Paridad\n## 4. Artefactos") == []
    assert dt.check_work_item("## Motivación\n## Paridad") != []
    assert dt.check_work_item("## Artefactos\n## Motivación\n## Criterios de aceptación\n## Paridad") != []


def test_issue_body_and_quick_note_share_sections(tmp_path):
    task = backlog.parse_backlog(TODO).tasks[0]
    assert dt.check_work_item(backlog.issue_body_for(task, "TODO.md")) == []
    created = scaffold_lifecycle_task("feat/demo/rapida", tmp_path, phase="TODO")
    quick = next(p for p in created if p.name.startswith("QUICK_"))
    assert dt.check_work_item(quick.read_text(encoding="utf-8")) == []
