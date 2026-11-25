"""Tests de la plantilla base y sus puntos de extensión (doc_templates.py, #92)."""

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import doc_templates as dt  # noqa: E402
from new_lifecycle_task import scaffold_lifecycle_task  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES = REPO_ROOT / "doc" / "00-governance" / "templates"
ECC_TEMPLATES = REPO_ROOT / "aagy-ecc" / "templates" / "lifecycle"
# Nombres de proyectos consumidores que no pueden aparecer en las plantillas del plugin (CA-03).
FORBIDDEN = ("home-lab", "home.lab", "homelab", "kakebo", "cluster-lb")


def test_plugin_templates_follow_base():
    assert dt.check_dir(TEMPLATES) == {}


def test_mirrored_templates_follow_base():
    assert dt.check_dir(ECC_TEMPLATES) == {}


def test_plugin_templates_are_project_agnostic():
    for path in TEMPLATES.rglob("*.md"):
        text = path.read_text(encoding="utf-8").lower()
        assert not [w for w in FORBIDDEN if w in text], path.name


def test_check_reports_missing_and_misordered_sections():
    base = (TEMPLATES / dt.BASE_TEMPLATE).read_text(encoding="utf-8")
    assert dt.check_template(base) == []
    broken = base.replace("## 5. Preguntas abiertas", "## 5. Otra cosa")
    assert any("Preguntas abiertas" in p for p in dt.check_template(broken))
    swapped = base.replace("## 0. Estado actual", "## 0. Contexto y objetivos").replace(
        "## 1. Contexto y objetivos", "## 1. Estado actual")
    assert dt.check_template(swapped)
    assert any("marcador" in p for p in dt.check_template(base.replace(dt.EXTENSION_MARKER, "")))


def _consumer(tmp_path: Path, extensions: dict) -> Path:
    (tmp_path / ".governance").mkdir()
    (tmp_path / ".governance" / "docs-map.json").write_text(
        json.dumps({"schema_version": 2, dt.EXTENSIONS_KEY: extensions}), encoding="utf-8")
    ext = tmp_path / "ext"
    ext.mkdir()
    (ext / "impact.md").write_text("## Matriz propia\n\nfila", encoding="utf-8")
    (ext / "common.md").write_text("## Común\n\nsiempre", encoding="utf-8")
    return tmp_path


def test_apply_extensions_inserts_declared_sections(tmp_path):
    root = _consumer(tmp_path, {"REQ": ["ext/impact.md"], "*": ["ext/common.md"]})
    text = f"## 1. Contexto\n\n{dt.EXTENSION_MARKER}\n\n## 2. Criterios de aceptación\n"
    req = dt.apply_extensions(text, "REQ", root)
    assert "## Matriz propia" in req and "## Común" in req and dt.EXTENSION_MARKER not in req
    assert req.index("## Común") < req.index("## 2. Criterios")
    plan = dt.apply_extensions(text, "PLAN", root)
    assert "## Matriz propia" not in plan and "## Común" in plan


def test_apply_extensions_ignores_paths_outside_repo(tmp_path):
    (tmp_path / "repo").mkdir()
    root = _consumer(tmp_path / "repo", {"REQ": ["../secret.md"]})
    (tmp_path / "secret.md").write_text("## Fuera", encoding="utf-8")
    out = dt.apply_extensions(f"a\n{dt.EXTENSION_MARKER}\nb", "REQ", root)
    assert "Fuera" not in out


def test_apply_extensions_without_docs_map_removes_marker(tmp_path):
    assert dt.apply_extensions(f"a\n\n{dt.EXTENSION_MARKER}\n\nb", "REQ", tmp_path) == "a\n\nb"


def test_find_template_falls_back_to_plugin(tmp_path):
    found = dt.find_template("01_TOMA_REQUISITOS_E_IMPACTO.md", tmp_path / "missing")
    assert found is not None and found.is_file()
    assert dt.find_template("NO_EXISTE.md", tmp_path) is None


def test_scaffold_uses_plugin_templates_and_extensions(tmp_path):
    """CA-01 y CA-02: un repo sin plantillas propias recibe la base y su extensión."""
    root = _consumer(tmp_path, {"REQ": ["ext/impact.md"]})
    created = scaffold_lifecycle_task("feat/demo/x", root, phase="REQ")
    req = next(p for p in created if p.name.startswith("REQ_"))
    text = req.read_text(encoding="utf-8")
    titles = dt.section_titles(text)
    assert titles[0] == "Estado actual"
    assert "Matriz propia" in titles
    assert "feat/demo/x" in text and dt.EXTENSION_MARKER not in text


def test_cli_check(tmp_path, capsys):
    assert dt.main(["check", str(TEMPLATES)]) == 0
    (tmp_path / "MAL.md").write_text("# nada", encoding="utf-8")
    assert dt.main(["check", str(tmp_path)]) == 1
    assert "MAL.md" in capsys.readouterr().out
