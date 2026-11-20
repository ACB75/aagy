#!/usr/bin/env python3
"""
Pruebas unitarias para audit_plugin_parity.py.
Valida la compuerta de paridad multi-harness entre Anything Antigravity (aagy)
y el plugin hermano para Claude Code (aagy).
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import pytest
from unittest.mock import patch

# Asegurar import de modulos aagy
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from audit_plugin_parity import (
    ParityAuditResult,
    audit_parity,
    main,
)


@pytest.fixture
def mock_repo_structure(tmp_path: Path):
    """Crea una estructura mock de repositorio con paridad aagy <-> aagy."""
    # Root plugin aagy
    root_plugin = tmp_path / "plugin.json"
    root_plugin.write_text(json.dumps({
        "name": "aagy",
        "displayName": "Anything Antigravity (aagy)",
        "version": "4.0.0"
    }), encoding="utf-8")

    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "tdd-workflow").mkdir()
    (skills_dir / "tdd-workflow" / "SKILL.md").write_text("# TDD", encoding="utf-8")

    # Claude Code plugin aagy-ecc
    claude_dir = tmp_path / "aagy-ecc"
    claude_plugin_dir = claude_dir / ".claude-plugin"
    claude_plugin_dir.mkdir(parents=True)
    (claude_plugin_dir / "plugin.json").write_text(json.dumps({
        "name": "aagy-ecc",
        "version": "4.0.0"
    }), encoding="utf-8")

    claude_skills_dir = claude_dir / "skills"
    claude_skills_dir.mkdir(parents=True)
    (claude_skills_dir / "tdd-workflow").mkdir()
    (claude_skills_dir / "tdd-workflow" / "SKILL.md").write_text("# TDD", encoding="utf-8")

    return tmp_path


def test_audit_parity_success(mock_repo_structure: Path):
    result = audit_parity(mock_repo_structure)
    assert result.is_valid is True
    assert result.status == "PASS"
    assert result.root_plugin_name == "aagy"
    assert result.claude_plugin_name == "aagy-ecc"
    assert len(result.discrepancies) == 0


def test_audit_parity_missing_claude_dir(tmp_path: Path):
    root_plugin = tmp_path / "plugin.json"
    root_plugin.write_text(json.dumps({"name": "aagy"}), encoding="utf-8")

    result = audit_parity(tmp_path)
    assert result.is_valid is False
    assert result.status == "FAIL"
    assert any("aagy" in d.lower() for d in result.discrepancies)


def test_audit_parity_wrong_root_name(mock_repo_structure: Path):
    root_plugin = mock_repo_structure / "plugin.json"
    root_plugin.write_text(json.dumps({"name": "wrong-name"}), encoding="utf-8")

    result = audit_parity(mock_repo_structure)
    assert result.is_valid is False
    assert any("wrong-name" in d for d in result.discrepancies)


def test_audit_parity_cli_json(mock_repo_structure: Path, capsys):
    with patch("sys.argv", ["audit_plugin_parity.py", "--repo-root", str(mock_repo_structure), "--json"]):
        exit_code = main()
        assert exit_code == 0
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "PASS"
        assert data["root_plugin_name"] == "aagy"


def test_audit_parity_cli_check_only(mock_repo_structure: Path):
    with patch("sys.argv", ["audit_plugin_parity.py", "--repo-root", str(mock_repo_structure), "--check-only"]):
        exit_code = main()
        assert exit_code == 0
