"""
Tests unitarios para la auditoría de higiene, tokens y presupuesto de contexto (workspace_audit.py).
"""
import sys
from pathlib import Path

# Añadir ruta para importar scripts/ecc-agy
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from workspace_audit import (
    audit_agents,
    audit_mcps,
    audit_rules,
    audit_skills,
    check_agent,
    clean_targets,
    frontmatter_field,
    read_frontmatter,
    scan_dead_artifacts,
    scan_hygiene,
    AgentTarget,
    audit_target_budget,
    MAX_RULE_FILE_BYTES,
    MAX_RULES_TOTAL_TOKENS,
    MAX_EAGER_CUSTOMIZATION_TOKENS,
)


def test_read_frontmatter_and_fields():
    content = """---
name: test-skill
description: "A short valid skill description."
model: flash
---
# Body
Some markdown content.
"""
    fm = read_frontmatter(content)
    assert fm != ""
    assert frontmatter_field(fm, "name") == "test-skill"
    assert frontmatter_field(fm, "description") == "A short valid skill description."
    assert frontmatter_field(fm, "model") == "flash"
    assert frontmatter_field(fm, "non_existent") is None


def test_audit_skills_length_limits(tmp_path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    # Skill válida (<= 140 chars)
    s1 = skills_dir / "valid-skill"
    s1.mkdir()
    (s1 / "SKILL.md").write_text(
        "---\nname: valid-skill\ndescription: \"Short valid description.\"\n---\nBody",
        encoding="utf-8",
    )

    # Skill que excede 140 chars
    s2 = skills_dir / "long-skill"
    s2.mkdir()
    long_desc = "x" * 150
    (s2 / "SKILL.md").write_text(
        f"---\nname: long-skill\ndescription: \"{long_desc}\"\n---\nBody",
        encoding="utf-8",
    )

    count, chars, violations = audit_skills(skills_dir)
    assert count == 2
    assert len(violations) == 1
    assert "long-skill" in violations[0]


def test_audit_agents_rules_and_models(tmp_path):
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()

    # Agente válido (<= 120 chars, model flash)
    a1 = agents_dir / "valid-agent.md"
    a1.write_text(
        "---\nname: valid-agent\ndescription: \"Short agent desc.\"\nmodel: flash\n---\nBody",
        encoding="utf-8",
    )

    # Agente con descripción larga (> 120 chars)
    a2 = agents_dir / "long-agent.md"
    long_desc = "a" * 130
    a2.write_text(
        f"---\nname: long-agent\ndescription: \"{long_desc}\"\nmodel: inherit\n---\nBody",
        encoding="utf-8",
    )

    # Agente con modelo no óptimo
    a3 = agents_dir / "bad-model-agent.md"
    a3.write_text(
        "---\nname: bad-model\ndescription: \"Desc\"\nmodel: pro\n---\nBody",
        encoding="utf-8",
    )

    # Agente read-only con tools de escritura
    a4 = agents_dir / "code-reviewer.md"
    a4.write_text(
        "---\nname: code-reviewer\ndescription: \"Reviews code.\"\nmodel: flash\ntools:\n  - edit_file\n---\nBody",
        encoding="utf-8",
    )

    count, chars, violations = audit_agents(agents_dir)
    assert count == 4
    assert any("long-agent.md" in v for v in violations)
    assert any("bad-model-agent.md" in v and "pro" in v for v in violations)
    assert any("code-reviewer.md" in v and "write tools" in v for v in violations)


def test_scan_hygiene_and_clean(tmp_path):
    # Crear backups y cachés
    bak_file = tmp_path / "test.bak"
    bak_file.write_text("old", encoding="utf-8")
    cache_dir = tmp_path / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "test.pyc").write_text("compiled", encoding="utf-8")
    empty_dir = tmp_path / "empty_folder"
    empty_dir.mkdir()

    report = scan_hygiene(tmp_path)
    assert len(report.backups) == 1
    assert len(report.caches) == 1
    assert len(report.empty_dirs) == 1

    clean_targets(report.all_targets())
    assert not bak_file.exists()
    assert not cache_dir.exists()
    assert not empty_dir.exists()


def test_scan_dead_artifacts(tmp_path):
    target_dir = tmp_path / "project"
    target_dir.mkdir()
    skills_dir = target_dir / "skills"
    skills_dir.mkdir()

    # Skill huérfana (directorio sin SKILL.md)
    orphan_skill = skills_dir / "broken-skill"
    orphan_skill.mkdir()

    target = AgentTarget("test-proj", target_dir)
    report = scan_dead_artifacts([target])
    assert len(report.orphan_skill_dirs) == 1
    assert report.total_issues >= 1


def test_audit_rules_file_size_limit_and_budget(tmp_path):
    rules_dir = tmp_path / "rules"
    rules_dir.mkdir()

    # Regla normal <= 24 KB
    r1 = rules_dir / "valid_rule.md"
    r1.write_text("Valid content", encoding="utf-8")

    chars, tokens, violations = audit_rules(tmp_path, include_rules=True)
    assert len(violations) == 0
    assert chars == len("Valid content")

    # Regla que excede 24.000 bytes
    r_big = rules_dir / "oversized_rule.md"
    r_big.write_text("x" * (MAX_RULE_FILE_BYTES + 500), encoding="utf-8")

    chars, tokens, violations = audit_rules(tmp_path, include_rules=True)
    assert any("oversized_rule.md" in v and "max limit of 24 KB" in v for v in violations)

    # Limpiar regla pesada y simular exceso agregado (> 16.000 tokens ~ 60.800 chars en varios archivos)
    r_big.unlink()
    for i in range(4):
        # Cada archivo ~20.000 chars (< 24 KB), total ~80.000 chars > 16.000 tokens
        rf = rules_dir / f"chunk_{i}.md"
        rf.write_text("y" * 20000, encoding="utf-8")

    chars, tokens, violations = audit_rules(tmp_path, include_rules=True)
    assert any("Aggregated rules exceed safe budget" in v for v in violations)


def test_audit_mcps_heavy_server_and_budget(tmp_path):
    # Caso 1: Sin mcp_config.json
    total, active, tokens, violations = audit_mcps(tmp_path)
    assert total == 0
    assert active == 0
    assert tokens == 0
    assert len(violations) == 0

    # Caso 2: gemini-mcp activo por defecto (sin "disabled": true)
    mcp_file = tmp_path / "mcp_config.json"
    mcp_file.write_text(
        '{"mcpServers": {"gemini-mcp": {"command": "npx", "args": ["gemini-mcp"]}}}',
        encoding="utf-8",
    )
    total, active, tokens, violations = audit_mcps(tmp_path)
    assert total == 1
    assert active == 1
    assert tokens > 0
    assert any("gemini-mcp" in v and "Must set '\"disabled\": true'" in v for v in violations)

    # Caso 3: gemini-mcp con "disabled": true (0 tokens en reposo, 0 violaciones)
    mcp_file.write_text(
        '{"mcpServers": {"gemini-mcp": {"command": "npx", "args": ["gemini-mcp"], "disabled": true}}}',
        encoding="utf-8",
    )
    total, active, tokens, violations = audit_mcps(tmp_path)
    assert total == 1
    assert active == 0
    assert tokens == 0
    assert len(violations) == 0

    # Caso 4: JSON malformado
    mcp_file.write_text('{ invalid json', encoding="utf-8")
    total, active, tokens, violations = audit_mcps(tmp_path)
    assert any("Invalid JSON" in v for v in violations)


def test_audit_target_budget_eager_customization_overflow(tmp_path):
    # Crear un plugin con muchas skills y agentes que superen 3.000 tokens eager
    plugin_dir = tmp_path / "my-plugin"
    plugin_dir.mkdir()
    (plugin_dir / "plugin.json").write_text('{"name": "test-plugin"}', encoding="utf-8")

    skills_dir = plugin_dir / "skills"
    skills_dir.mkdir()
    # 100 skills de 130 chars = 13.000 chars => ~3.421 tokens (> 3.000)
    for i in range(100):
        s = skills_dir / f"skill-{i}"
        s.mkdir()
        (s / "SKILL.md").write_text(
            f'---\nname: skill-{i}\ndescription: "{"z" * 130}"\n---\nBody',
            encoding="utf-8",
        )

    target = AgentTarget("test-plugin", plugin_dir, is_plugin=True)
    report = audit_target_budget(target)
    assert any("Eager customizations in plugin" in v and "exceed budget" in v for v in report.violations)

