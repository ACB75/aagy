"""
Tests unitarios para la promoción on-demand de skills Tier 2 a Tier 1 (skill_promotion.py).
"""
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_promote_and_demote_skill_lifecycle(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "py"))
    import skill_promotion

    # Simular estructura de repositorio (origen Tier 2)
    repo_skills = tmp_path / "repo" / "skills"
    repo_skills.mkdir(parents=True)

    # Skill Tier 2 válida
    specialized_skill = repo_skills / "chrome-devtools"
    specialized_skill.mkdir()
    (specialized_skill / "SKILL.md").write_text(
        "---\nname: chrome-devtools\ndescription: \"Inspect and debug browser pages.\"\n---\nBody",
        encoding="utf-8",
    )

    # Skill con descripción larga (>140)
    oversized_skill = repo_skills / "oversized-skill"
    oversized_skill.mkdir()
    (oversized_skill / "SKILL.md").write_text(
        f"---\nname: oversized-skill\ndescription: \"{'x' * 150}\"\n---\nBody",
        encoding="utf-8",
    )

    # Simular plugin activo (destino Tier 1)
    plugin_dir = tmp_path / "plugin"
    plugin_skills = plugin_dir / "skills"
    plugin_skills.mkdir(parents=True)

    # Skill core existente
    core_skill = plugin_skills / "engineering-lifecycle"
    core_skill.mkdir()
    (core_skill / "SKILL.md").write_text(
        "---\nname: engineering-lifecycle\ndescription: \"Core lifecycle.\"\n---\nBody",
        encoding="utf-8",
    )

    # Caso 1: Promover skill inexistente
    code, msg = skill_promotion.promote_skill("non-existent", repo_skills, plugin_dir)
    assert code != 0
    assert "no encontrada" in msg

    # Caso 2: Promover skill con descripción excesiva (>140)
    code, msg = skill_promotion.promote_skill("oversized-skill", repo_skills, plugin_dir)
    assert code != 0
    assert "140" in msg

    # Caso 3: Promover skill que ya es Core
    code, msg = skill_promotion.promote_skill("engineering-lifecycle", repo_skills, plugin_dir)
    assert code != 0
    assert "Core" in msg

    # Caso 4: Promover skill válida
    code, msg = skill_promotion.promote_skill("chrome-devtools", repo_skills, plugin_dir)
    assert code == 0
    assert (plugin_skills / "chrome-devtools" / "SKILL.md").exists()

    promotions_file = plugin_dir / ".active_promotions.json"
    assert promotions_file.exists()
    registry = json.loads(promotions_file.read_text(encoding="utf-8"))
    assert "chrome-devtools" in registry

    # Caso 5: Listar promociones
    active = skill_promotion.list_promotions(plugin_dir)
    assert "chrome-devtools" in active

    # Caso 6: Desactivar skill core (debe fallar)
    code, msg = skill_promotion.demote_skill("engineering-lifecycle", plugin_dir)
    assert code != 0
    assert "no es una skill promovida" in msg or "Core" in msg

    # Caso 7: Desactivar skill promovida (éxito)
    code, msg = skill_promotion.demote_skill("chrome-devtools", plugin_dir)
    assert code == 0
    assert not (plugin_skills / "chrome-devtools").exists()
    registry_after = json.loads(promotions_file.read_text(encoding="utf-8"))
    assert "chrome-devtools" not in registry_after
