"""#107: topes de tokens en reglas, catálogo y mensajes de hooks."""

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "py"))
sys.path.insert(0, str(REPO_ROOT / "aagy-ecc" / "scripts" / "hooks"))

import hook_safety  # noqa: E402
import optimize_catalog_tokens as catalog  # noqa: E402
import session_start_rules  # noqa: E402

SESSION_RULES_MAX_BYTES = 2048


def test_session_start_rules_index_fits_cap():
    rules = REPO_ROOT / "aagy-ecc" / "rules" / "AGENTS.md"
    context = session_start_rules.build_response(rules)["hookSpecificOutput"]["additionalContext"]
    assert len(context.encode("utf-8")) <= SESSION_RULES_MAX_BYTES


def test_project_template_does_not_import_global_rules():
    text = (REPO_ROOT / "aagy-ecc" / "project-template" / "CLAUDE.md").read_text(encoding="utf-8")
    assert "rules/AGENTS.md" not in text and "Branch" not in text
    assert "@AGENTS.md" in text


def test_catalog_descriptions_fit_cap():
    assert catalog.long_descriptions(REPO_ROOT) == []


def test_long_description_is_reported(tmp_path):
    skill = tmp_path / "skills" / "x" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("---\nname: x\ndescription: " + "a" * 201 + "\n---\n", encoding="utf-8")
    assert catalog.long_descriptions(tmp_path) == [("skills/x/SKILL.md", 201)]


def test_hook_messages_are_one_line_unless_verbose():
    command = "rm -rf / " + "x" * 300 + "\n" + "segunda línea"
    short = hook_safety.deny_reason(command)
    assert "\n" not in short and len(short) <= hook_safety.ONE_LINE_MAX
    full = hook_safety.deny_reason(command, verbose=True)
    assert "segunda línea" in full and "patrón" in full
