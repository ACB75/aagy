#!/usr/bin/env python3
"""Pruebas de plantillas de GitHub Issues y Pull Request (.github/) — GH #59."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
GITHUB_DIR = REPO_ROOT / ".github"
ISSUE_TEMPLATE_DIR = GITHUB_DIR / "ISSUE_TEMPLATE"
PR_TEMPLATE = GITHUB_DIR / "pull_request_template.md"


def test_issue_templates_exist_and_have_frontmatter() -> None:
    expected = ("feature_request.md", "bug_report.md", "chore_refactor.md")
    for name in expected:
        path = ISSUE_TEMPLATE_DIR / name
        assert path.is_file(), f"Falta plantilla de issue: {path}"
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{name} debe iniciar con YAML frontmatter"
        assert "name:" in text and "about:" in text and "labels:" in text
        assert "harness:both" in text
        assert "aagy-ecc" in text


def test_pull_request_template_has_development_and_parity_checklist() -> None:
    assert PR_TEMPLATE.is_file(), "Falta .github/pull_request_template.md"
    text = PR_TEMPLATE.read_text(encoding="utf-8")
    assert "## 2. Development" in text
    assert "Closes #" in text
    assert "aagy <-> aagy-ecc" in text
    assert "sync_aagy_ecc.py --check" in text
    assert "audit-plugin-parity.ps1" in text
