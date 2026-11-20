"""
Tests unitarios para el ciclo de vida y archivo de TODOs (archive_todo.py).
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from archive_todo import (
    adjust_relative_links,
    parse_todo_file,
    process_archive,
    slugify_title,
)


def test_slugify_title():
    assert slugify_title("Tarea 2.1: Auditoría y Poda de Contexto") == "Tarea_2_1_Auditoria_y_Poda_de_Contexto"
    assert slugify_title("[docs](http://example.com) Link Title") == "docs_Link_Title"
    assert slugify_title("") == "TAREA"


def test_adjust_relative_links(tmp_path):
    source_dir = tmp_path / "doc"
    source_dir.mkdir()
    target_dir = tmp_path / "doc" / "TODO_DONE"
    target_dir.mkdir()

    text = "Ver archivo [manual](manual/GUIA.md)."
    adjusted = adjust_relative_links(text, source_dir, target_dir)
    assert "../manual/GUIA.md" in adjusted


def test_parse_todo_file_and_process_archive(tmp_path):
    todo_file = tmp_path / "TODO.md"
    todo_content = """# BACKLOG

* [ ] **Tarea 1.1: Pendiente**
  * Detalle pendiente.

* [x] **Tarea 2.1: Completada**
  * Detalle completado línea 1.
  * Detalle completado línea 2.

* [ ] **Tarea 3.1: Otra pendiente**
"""
    todo_file.write_text(todo_content, encoding="utf-8")
    done_dir = tmp_path / "TODO_DONE"

    # Procesar archivo
    code = process_archive(
        todo_path=todo_file,
        done_dir=done_dir,
        archive_all=True,
        notes="Completado con éxito.",
    )
    assert code == 0

    # Verificar que se generó archivo en TODO_DONE
    archived_files = list(done_dir.glob("TODO_*.md"))
    assert len(archived_files) == 1
    content = archived_files[0].read_text(encoding="utf-8")
    assert "Tarea 2.1: Completada" in content
    assert "Completado con éxito." in content

    # Verificar que el TODO.md original se podó y sólo contiene tareas pendientes
    remaining_todo = todo_file.read_text(encoding="utf-8")
    assert "Tarea 2.1: Completada" not in remaining_todo
    assert "Tarea 1.1: Pendiente" in remaining_todo
    assert "Tarea 3.1: Otra pendiente" in remaining_todo


def test_cli_resolves_v2_docs_map_and_legacy_fallback(tmp_path):
    """CLI de archive_todo.py resuelve tanto v2 vía docs-map.json como fallback clásico."""
    script_path = Path(__file__).resolve().parent.parent / "archive_todo.py"

    # 1. Caso v2 con docs-map.json
    v2_root = tmp_path / "repo_v2"
    (v2_root / ".governance").mkdir(parents=True)
    (v2_root / "doc" / "06-backlog").mkdir(parents=True)
    v2_todo = v2_root / "doc" / "06-backlog" / "TODO.md"
    v2_done = v2_root / "doc" / "06-backlog" / "done"
    v2_todo.write_text("# TODO v2\n- [x] **Tarea A**\n- [ ] **Tarea B**\n", encoding="utf-8")
    (v2_root / ".governance" / "docs-map.json").write_text(
        json.dumps({"schema_version": 2, "paths": {"todo": "doc/06-backlog/TODO.md", "todo_done": "doc/06-backlog/done"}}),
        encoding="utf-8",
    )

    res_v2 = subprocess.run([sys.executable, str(script_path), "--repo-root", str(v2_root)], capture_output=True, text=True)
    assert res_v2.returncode == 0
    assert len(list(v2_done.glob("TODO_*.md"))) == 1
    assert "Tarea A" not in v2_todo.read_text(encoding="utf-8")

    # 2. Caso clásico home-lab sin docs-map.json
    legacy_root = tmp_path / "repo_legacy"
    (legacy_root / "doc").mkdir(parents=True)
    legacy_todo = legacy_root / "doc" / "TODO.md"
    legacy_done = legacy_root / "doc" / "TODO_DONE"
    legacy_todo.write_text("# TODO Legacy\n- [x] **Tarea Legacy**\n", encoding="utf-8")

    res_leg = subprocess.run([sys.executable, str(script_path), "--repo-root", str(legacy_root)], capture_output=True, text=True)
    assert res_leg.returncode == 0
    assert len(list(legacy_done.glob("TODO_*.md"))) == 1

