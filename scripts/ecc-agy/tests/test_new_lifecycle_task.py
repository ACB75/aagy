"""Tests para el instanciador del ciclo de vida de ingeniería (4 fases)."""

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from new_lifecycle_task import (
    render_template_content,
    scaffold_lifecycle_task,
    slugify_task_id,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


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
