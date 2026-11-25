"""Tests unitarios para el resolvedor de `.governance/docs-map.json` (`docs_map.py`)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from docs_map import (
    DOCS_MAP_REL,
    LEGACY_DEFAULTS,
    V2_DEFAULTS,
    load_docs_map,
    resolve_doc_path,
    resolve_doc_rel,
    validate_docs_map_targets,
    validate_repo_relative_path,
)


def test_legacy_fallback_without_docs_map(tmp_path: Path) -> None:
    """Si no existe .governance/docs-map.json, usa rutas clásicas heredadas (esquema v1)."""
    dmap = load_docs_map(tmp_path)
    assert dmap.schema_version == 1
    assert dmap.relative("todo") == "doc/TODO.md"
    assert dmap.relative("todo_done") == "doc/TODO_DONE"
    assert dmap.relative("ideas") == "doc/IDEAS.md"
    assert dmap.relative("plans") == "doc/plan"
    assert dmap.relative("templates") == "doc/templates"
    assert dmap.relative("adr_dir") == "doc/adr"
    assert dmap.relative("adr_template") == "doc/adr/TEMPLATE_ADR.md"
    assert dmap.relative("postmortems") == "doc/post-mortem"
    assert dmap.relative("postmortem_template") == "doc/post-mortem/TEMPLATE_POSTMORTEM.md"
    assert dmap.resolve("todo") == (tmp_path / "doc" / "TODO.md").resolve()
    assert resolve_doc_rel(tmp_path, "todo_done") == "doc/TODO_DONE"
    assert resolve_doc_path(tmp_path, "ideas") == (tmp_path / "doc" / "IDEAS.md").resolve()


def test_v1_partial_mapping_inherits_legacy_defaults(tmp_path: Path) -> None:
    """Un docs-map v1 parcial respeta sus claves y cae en fallback clásico para el resto."""
    gov_dir = tmp_path / ".governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "docs-map.json").write_text(
        json.dumps(
            {
                "constitution": "AGENTS.md",
                "map": "doc/CUSTOM_INDEX.md",
                "status": "doc/STATUS.md",
                "history": "doc/LOG.md",
                "adr_dir": "doc/decisions",
                "adr_index": "doc/decisions/README.md",
            }
        ),
        encoding="utf-8",
    )

    dmap = load_docs_map(tmp_path)
    assert dmap.schema_version == 1
    assert dmap.relative("map") == "doc/CUSTOM_INDEX.md"
    assert dmap.relative("adr_dir") == "doc/decisions"
    assert dmap.relative("todo") == LEGACY_DEFAULTS["todo"]
    assert dmap.relative("templates") == LEGACY_DEFAULTS["templates"]


def test_v2_schema_mapping_resolves_all_paths(tmp_path: Path) -> None:
    """Un esquema v2 completo resuelve todas las carpetas numeradas y plantillas."""
    gov_dir = tmp_path / ".governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "docs-map.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "constitution": "AGENTS.md",
                "map": "doc/INDEX.md",
                "context": "doc/CONTEXT.md",
                "status": "doc/STATUS.md",
                "history": "doc/LOG.md",
                "adr_dir": "doc/02-adr",
                "adr_index": "doc/02-adr/README.md",
                "paths": {
                    "doc_root": "doc",
                    "governance": "doc/00-governance",
                    "references": "doc/00-governance/references",
                    "templates": "doc/00-governance/templates",
                    "adr_template": "doc/00-governance/templates/TEMPLATE_ADR.md",
                    "postmortem_template": "doc/00-governance/templates/TEMPLATE_POSTMORTEM.md",
                    "architecture": "doc/01-architecture",
                    "domain_and_flows": "doc/03-domain-and-flows",
                    "operations": "doc/04-operations",
                    "postmortems": "doc/05-post-mortems",
                    "backlog": "doc/06-backlog",
                    "ideas": "doc/06-backlog/IDEAS.md",
                    "todo": "doc/06-backlog/TODO.md",
                    "todo_done": "doc/06-backlog/done",
                    "plans": "doc/06-backlog/plans",
                    "quick": "doc/06-backlog/quick",
                },
            }
        ),
        encoding="utf-8",
    )

    dmap = load_docs_map(tmp_path)
    assert dmap.schema_version == 2
    for key, expected in V2_DEFAULTS.items():
        assert dmap.relative(key) == expected
    assert dmap.resolve("quick") == (tmp_path / "doc" / "06-backlog" / "quick").resolve()


@pytest.mark.parametrize(
    "bad_path",
    [
        "",
        "   ",
        "../outside.md",
        "doc/../../etc/passwd",
        "/etc/passwd",
        "\\Windows\\win.ini",
        "C:\\Windows\\win.ini",
        "doc/bad\x00path.md",
    ],
)
def test_path_traversal_and_unsafe_paths_rejected(tmp_path: Path, bad_path: str) -> None:
    """Valida bloqueo estricto contra path traversal, rutas absolutas o nulas."""
    with pytest.raises(ValueError):
        validate_repo_relative_path(tmp_path, bad_path)

    gov_dir = tmp_path / ".governance"
    gov_dir.mkdir(exist_ok=True)
    (gov_dir / "docs-map.json").write_text(
        json.dumps({"schema_version": 2, "paths": {"todo": bad_path}}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        load_docs_map(tmp_path)


def test_malformed_json_raises_value_error(tmp_path: Path) -> None:
    """Un docs-map.json malformado o no-objeto debe lanzar ValueError."""
    gov_dir = tmp_path / ".governance"
    gov_dir.mkdir(parents=True)
    (gov_dir / "docs-map.json").write_text("{ invalid json", encoding="utf-8")

    with pytest.raises(ValueError):
        load_docs_map(tmp_path)

    (gov_dir / "docs-map.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ValueError):
        load_docs_map(tmp_path)


def test_validate_docs_map_targets_detects_missing_and_valid(tmp_path: Path) -> None:
    """validate_docs_map_targets reporta objetivos inexistentes si existe docs-map.json."""
    assert validate_docs_map_targets(tmp_path) == []

    gov_dir = tmp_path / ".governance"
    gov_dir.mkdir(parents=True)
    (tmp_path / "AGENTS.md").write_text("# Agents", encoding="utf-8")
    (gov_dir / "docs-map.json").write_text(
        json.dumps({"constitution": "AGENTS.md", "map": "doc/MISSING_INDEX.md"}),
        encoding="utf-8",
    )

    issues = validate_docs_map_targets(tmp_path)
    assert any("map" in issue and "doc/MISSING_INDEX.md" in issue for issue in issues)
    assert not any("constitution" in issue for issue in issues)


def test_cli_invocation_and_flags(tmp_path: Path) -> None:
    """Verifica ejecución CLI (--key, --relative, --json, --validate) y códigos de salida."""
    script_path = Path(__file__).resolve().parent.parent / "docs_map.py"
    gov_dir = tmp_path / ".governance"
    gov_dir.mkdir(parents=True)
    todo_file = tmp_path / "doc" / "06-backlog" / "TODO.md"
    todo_file.parent.mkdir(parents=True)
    todo_file.write_text("# TODO", encoding="utf-8")
    (gov_dir / "docs-map.json").write_text(
        json.dumps({"schema_version": 2, "paths": {"todo": "doc/06-backlog/TODO.md"}}),
        encoding="utf-8",
    )

    res_rel = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(tmp_path), "--key", "todo", "--relative"],
        capture_output=True,
        text=True,
    )
    assert res_rel.returncode == 0
    assert res_rel.stdout.strip() == "doc/06-backlog/TODO.md"

    res_abs = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(tmp_path), "--key", "todo"],
        capture_output=True,
        text=True,
    )
    assert res_abs.returncode == 0
    assert Path(res_abs.stdout.strip()).resolve() == todo_file.resolve()

    res_json = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
    )
    assert res_json.returncode == 0
    payload = json.loads(res_json.stdout)
    assert payload["schema_version"] == 2
    assert payload["paths"]["todo"] == "doc/06-backlog/TODO.md"

    res_bad_key = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(tmp_path), "--key", "non_existent"],
        capture_output=True,
        text=True,
    )
    assert res_bad_key.returncode != 0
