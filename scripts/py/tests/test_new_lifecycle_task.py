"""Tests para el instanciador del ciclo de vida de ingeniería (4 fases y entradas flexibles)."""

import json
import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from new_lifecycle_task import (
    attach_lifecycle_artifacts,
    bind_github_issue,
    create_sub_issue,
    format_lifecycle_artifacts_comment,
    main,
    parse_issue_metadata,
    render_template_content,
    scaffold_lifecycle_task,
    slugify_task_id,
)
from validate_branch import validate_branch_name

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

ALL_TEMPLATE_FILENAMES = [
    "01_TOMA_REQUISITOS_E_IMPACTO.md",
    "02_PLAN_ACCION_ARQUITECTURA.md",
    "03_DOCUMENTACION_Y_RELEASE_NOTES.md",
    "04_PROPUESTA_COMMITS_PR.md",
]


def _seed_v2_repo(tmp_path: Path) -> None:
    gov_dir = tmp_path / ".governance"
    gov_dir.mkdir(parents=True, exist_ok=True)
    tmpl_dir = tmp_path / "doc" / "00-governance" / "templates"
    tmpl_dir.mkdir(parents=True, exist_ok=True)
    for filename in ALL_TEMPLATE_FILENAMES:
        (tmpl_dir / filename).write_text(f"Template {filename} for <id_tarea> (YYYY-MM-DD)", encoding="utf-8")
    (gov_dir / "docs-map.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "paths": {
                    "templates": "doc/00-governance/templates",
                    "plans": "doc/06-backlog/plans",
                    "ideas": "doc/06-backlog/IDEAS.md",
                    "todo": "doc/06-backlog/TODO.md",
                    "quick": "doc/06-backlog/quick",
                },
            }
        ),
        encoding="utf-8",
    )


def test_slugify_task_id():
    """Verifica que el generador de slugs limpie prefijos de rama y caracteres especiales."""
    assert slugify_task_id("feat/kakebo/export-csv") == "kakebo_export_csv"
    assert slugify_task_id("fix/cluster/oom-timeout") == "cluster_oom_timeout"
    assert slugify_task_id("refactor/whoiam/signals-upgrade") == "whoiam_signals_upgrade"
    assert slugify_task_id("simple-task") == "simple_task"
    assert slugify_task_id("") == "task"


def test_render_template_content():
    """Verifica la sustitución de marcadores de posición."""
    raw = "ID: <id_tarea> | Fecha: YYYY-MM-DD | Doc: REQ_<id_tarea>.md"
    rendered = render_template_content(raw, "feat/kakebo/test", "2026-11-20")
    assert "ID: feat/kakebo/test" in rendered
    assert "Fecha: 2026-11-20" in rendered
    assert "Doc: REQ_feat/kakebo/test.md" in rendered


def test_scaffold_lifecycle_task_dry_run(tmp_path: Path):
    """Verifica que el modo dry-run no altere el disco."""
    tmpl_dir = tmp_path / "doc" / "templates"
    tmpl_dir.mkdir(parents=True)
    out_dir = tmp_path / "doc" / "plan"

    for _, filename in [
        ("REQ", "01_TOMA_REQUISITOS_E_IMPACTO.md"),
        ("PLAN", "02_PLAN_ACCION_ARQUITECTURA.md"),
        ("DOCS", "03_DOCUMENTACION_Y_RELEASE_NOTES.md"),
        ("REVIEW", "04_PROPUESTA_COMMITS_PR.md"),
    ]:
        (tmpl_dir / filename).write_text(f"Content for {filename}", encoding="utf-8")

    files = scaffold_lifecycle_task(
        task_id="feat/kakebo/test",
        repo_root=tmp_path,
        templates_rel="doc/templates",
        output_rel="doc/plan",
        dry_run=True,
    )
    assert len(files) == 4
    assert not out_dir.exists()


def test_scaffold_lifecycle_task_creates_files(tmp_path: Path):
    """Verifica la creación real de los 4 archivos."""
    tmpl_dir = tmp_path / "doc" / "templates"
    tmpl_dir.mkdir(parents=True)
    out_dir = tmp_path / "doc" / "plan"

    for _, filename in [
        ("REQ", "01_TOMA_REQUISITOS_E_IMPACTO.md"),
        ("PLAN", "02_PLAN_ACCION_ARQUITECTURA.md"),
        ("DOCS", "03_DOCUMENTACION_Y_RELEASE_NOTES.md"),
        ("REVIEW", "04_PROPUESTA_COMMITS_PR.md"),
    ]:
        (tmpl_dir / filename).write_text(f"Template for <id_tarea>", encoding="utf-8")

    files = scaffold_lifecycle_task(
        task_id="feat/kakebo/export-csv",
        repo_root=tmp_path,
        templates_rel="doc/templates",
        output_rel="doc/plan",
    )
    assert len(files) == 4
    assert (out_dir / "REQ_kakebo_export_csv.md").exists()
    assert (out_dir / "PLAN_kakebo_export_csv.md").exists()
    assert (out_dir / "DOCS_kakebo_export_csv.md").exists()
    assert (out_dir / "REVIEW_kakebo_export_csv.md").exists()

    content = (out_dir / "REQ_kakebo_export_csv.md").read_text(encoding="utf-8")
    assert "feat/kakebo/export-csv" in content


def test_scaffold_lifecycle_task_prevents_overwrite_without_force(tmp_path: Path):
    """Verifica que no sobrescriba archivos existentes a menos que se use force."""
    tmpl_dir = tmp_path / "doc" / "templates"
    tmpl_dir.mkdir(parents=True)
    out_dir = tmp_path / "doc" / "plan"
    out_dir.mkdir(parents=True)

    for _, filename in [
        ("REQ", "01_TOMA_REQUISITOS_E_IMPACTO.md"),
        ("PLAN", "02_PLAN_ACCION_ARQUITECTURA.md"),
        ("DOCS", "03_DOCUMENTACION_Y_RELEASE_NOTES.md"),
        ("REVIEW", "04_PROPUESTA_COMMITS_PR.md"),
    ]:
        (tmpl_dir / filename).write_text("New template content", encoding="utf-8")

    req_file = out_dir / "REQ_kakebo_existing.md"
    req_file.write_text("Existing custom content", encoding="utf-8")

    scaffold_lifecycle_task(
        task_id="feat/kakebo/existing",
        repo_root=tmp_path,
        templates_rel="doc/templates",
        output_rel="doc/plan",
        force=False,
    )
    assert req_file.read_text(encoding="utf-8") == "Existing custom content"

    # Con force=True debe sobrescribir
    scaffold_lifecycle_task(
        task_id="feat/kakebo/existing",
        repo_root=tmp_path,
        templates_rel="doc/templates",
        output_rel="doc/plan",
        force=True,
    )
    assert "New template content" in req_file.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("phase", "expected_prefixes", "absent_prefixes"),
    [
        ("REQ", ["REQ", "PLAN", "DOCS", "REVIEW"], []),
        ("PLAN", ["PLAN", "DOCS", "REVIEW"], ["REQ"]),
        ("DOCS", ["DOCS", "REVIEW"], ["REQ", "PLAN"]),
        ("REVIEW", ["REVIEW"], ["REQ", "PLAN", "DOCS"]),
        ("ALL", ["REQ", "PLAN", "DOCS", "REVIEW"], []),
    ],
)
def test_flexible_phase_template_slices_with_v2_docs_map(
    tmp_path: Path,
    phase: str,
    expected_prefixes: list[str],
    absent_prefixes: list[str],
) -> None:
    """Verifica puntos de entrada REQ, PLAN, DOCS, REVIEW, ALL resolviendo v2 desde docs-map.json."""
    _seed_v2_repo(tmp_path)
    plans_dir = tmp_path / "doc" / "06-backlog" / "plans"

    created = scaffold_lifecycle_task(task_id="feat/aagy/test-phase", repo_root=tmp_path, phase=phase)
    assert len(created) == len(expected_prefixes)
    for prefix in expected_prefixes:
        assert (plans_dir / f"{prefix}_aagy_test_phase.md").is_file()
    for prefix in absent_prefixes:
        assert not (plans_dir / f"{prefix}_aagy_test_phase.md").exists()


def test_flexible_entry_ideas_and_todo_with_v2_docs_map(tmp_path: Path) -> None:
    """Verifica puntos de entrada IDEAS y TODO bajo esquema v2."""
    _seed_v2_repo(tmp_path)

    idea_files = scaffold_lifecycle_task(task_id="feat/aagy/fast-sync", repo_root=tmp_path, phase="IDEAS")
    ideas_path = tmp_path / "doc" / "06-backlog" / "IDEAS.md"
    assert ideas_path in idea_files
    assert "feat/aagy/fast-sync" in ideas_path.read_text(encoding="utf-8")

    # Idempotente si ya existe la idea
    assert scaffold_lifecycle_task(task_id="feat/aagy/fast-sync", repo_root=tmp_path, phase="IDEAS") == []

    todo_files = scaffold_lifecycle_task(task_id="feat/aagy/quick-fix", repo_root=tmp_path, phase="TODO")
    todo_path = tmp_path / "doc" / "06-backlog" / "TODO.md"
    quick_path = tmp_path / "doc" / "06-backlog" / "quick" / "QUICK_aagy_quick_fix.md"
    assert todo_path in todo_files
    assert quick_path in todo_files
    assert "**Tarea: feat/aagy/quick-fix**" in todo_path.read_text(encoding="utf-8")
    assert quick_path.is_file()


def test_legacy_fallback_resolution_without_docs_map(tmp_path: Path) -> None:
    """Sin .governance/docs-map.json usa doc/templates y doc/plan automáticamente."""
    tmpl_dir = tmp_path / "doc" / "templates"
    tmpl_dir.mkdir(parents=True)
    for filename in ALL_TEMPLATE_FILENAMES:
        (tmpl_dir / filename).write_text("Legacy <id_tarea>", encoding="utf-8")

    created = scaffold_lifecycle_task(task_id="feat/homelab/compat", repo_root=tmp_path, phase="PLAN")
    assert len(created) == 3
    assert (tmp_path / "doc" / "plan" / "PLAN_homelab_compat.md").is_file()
    assert not (tmp_path / "doc" / "plan" / "REQ_homelab_compat.md").exists()


def test_parse_issue_metadata_extracts_canonical_branch() -> None:
    meta = parse_issue_metadata(
        issue_number=60,
        title="[feat]-[scripts]: soporte -Issue en new-lifecycle-task para crear rama gh-<N> y asignar",
        labels=["enhancement", "harness:both", "area:scripts"],
        url="https://github.com/ACB75/aagy/issues/60",
    )
    assert meta["issue"] == 60
    assert meta["type"] == "feat"
    assert meta["project"] == "scripts"
    assert meta["branch"].startswith("feat/scripts/gh-60-")
    valid, _ = validate_branch_name(meta["branch"])
    assert valid is True

    # Infiere fix y proyecto desde labels cuando el título no lleva prefijo [type]-[proj]
    bug_meta = parse_issue_metadata(
        issue_number=99,
        title="Fallo de timeout en hook PreToolUse",
        labels=["bug", "area:infra"],
    )
    assert bug_meta["type"] == "fix"
    assert bug_meta["project"] == "infra"
    assert bug_meta["branch"].startswith("fix/infra/gh-99-")
    assert validate_branch_name(bug_meta["branch"])[0] is True


def test_bind_github_issue_and_cli_integration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_v2_repo(tmp_path)
    (tmp_path / ".git").mkdir()
    calls: list[list[str]] = []

    class DummyProc:
        def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[:3] == ["gh", "issue", "view"]:
            payload = {
                "number": 60,
                "title": "[feat]-[scripts]: soporte -Issue en new-lifecycle-task",
                "labels": [{"name": "enhancement"}, {"name": "area:scripts"}],
                "url": "https://github.com/ACB75/aagy/issues/60",
            }
            return DummyProc(0, json.dumps(payload))
        if cmd[:3] == ["git", "branch", "--show-current"]:
            return DummyProc(0, "main\n")
        return DummyProc(0, "")

    monkeypatch.setattr("new_lifecycle_task.subprocess.run", fake_run)

    exit_code = main(["--issue", "60", "--repo-root", str(tmp_path), "--phase", "REQ"])
    assert exit_code == 0

    active_file = tmp_path / ".governance" / "active-issue.json"
    assert active_file.is_file()
    saved = json.loads(active_file.read_text(encoding="utf-8"))
    assert saved["issue"] == 60
    assert saved["branch"] == "feat/scripts/gh-60-soporte-issue-en-new-lifecycle-task"
    assert any(c[:4] == ["gh", "issue", "edit", "60"] and "@me" in c for c in calls)
    assert any(c[:3] == ["git", "checkout", "-b"] and saved["branch"] in c for c in calls)


def test_create_sub_issue_links_via_graphql(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    class DummyProc:
        def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[:3] == ["gh", "issue", "create"]:
            return DummyProc(0, "https://github.com/ACB75/aagy/issues/75\n")
        if cmd[:3] == ["gh", "issue", "view"] and "64" in cmd:
            return DummyProc(0, json.dumps({"id": "I_parent_64", "number": 64}))
        if cmd[:3] == ["gh", "issue", "view"] and "75" in cmd:
            return DummyProc(0, json.dumps({"id": "I_child_75", "number": 75}))
        if cmd[:3] == ["gh", "api", "graphql"]:
            return DummyProc(0, json.dumps({"data": {"addSubIssue": {"issue": {"number": 64}, "subIssue": {"number": 75}}}}))
        return DummyProc(0, "")

    monkeypatch.setattr("new_lifecycle_task.subprocess.run", fake_run)

    res = create_sub_issue(
        parent_issue=64,
        title="[feat]-[scripts]: sub-tarea de artefactos",
        body="Detalle de sub-issue.",
        repo_root=tmp_path,
    )
    assert res["parent_issue"] == 64
    assert res["sub_issue"] == 75
    assert res["linked"] is True
    assert any(c[:3] == ["gh", "api", "graphql"] and any("addSubIssue" in arg for arg in c) for c in calls)


def test_format_and_attach_lifecycle_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _seed_v2_repo(tmp_path)
    plans_dir = tmp_path / "doc" / "06-backlog" / "plans"
    plans_dir.mkdir(parents=True, exist_ok=True)
    req_path = plans_dir / "REQ_scripts_gh_64.md"
    plan_path = plans_dir / "PLAN_scripts_gh_64.md"
    req_path.write_text(
        "# REQ\n\n## Criterios de Aceptación\n\n- [ ] Soportar addSubIssue\n- [ ] Adjuntar Mermaid\n",
        encoding="utf-8",
    )
    plan_path.write_text(
        "# PLAN\n\n```mermaid\nflowchart LR\n  A[\"Issue #64\"] --> B[\"Sub-Issue\"]\n```\n",
        encoding="utf-8",
    )

    comment = format_lifecycle_artifacts_comment(
        task_id="feat/scripts/gh-64",
        artifacts=[req_path, plan_path],
        repo_root=tmp_path,
    )
    assert "REQ_scripts_gh_64.md" in comment
    assert "PLAN_scripts_gh_64.md" in comment
    assert "- [ ] Soportar addSubIssue" in comment
    assert "```mermaid" in comment

    calls: list[list[str]] = []

    class DummyProc:
        def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return DummyProc(0, "")

    monkeypatch.setattr("new_lifecycle_task.subprocess.run", fake_run)

    posted = attach_lifecycle_artifacts(
        issue_number=64,
        task_id="feat/scripts/gh-64",
        artifacts=[req_path, plan_path],
        repo_root=tmp_path,
    )
    assert "REQ_scripts_gh_64.md" in posted
    assert any(c[:4] == ["gh", "issue", "comment", "64"] for c in calls)



