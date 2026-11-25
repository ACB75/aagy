import sys
from pathlib import Path
import pytest

# Asegurar importación de scripts/py/format_commit.py
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from format_commit import (
    validate_commit_message,
    format_commit_message,
)


def test_validate_valid_commit():
    valid_msg = """feat-[scripts]: implement tenant storage manager

Introduce isolated storage telemetry and directory quotas per tenant.
- Enforce hermetic environments in scripts inventory.
- Verified with 100% unit tests passing.
"""
    result = validate_commit_message(valid_msg)
    assert result.is_valid is True
    assert result.commit_type == "feat"
    assert result.projects == ("scripts",)
    assert result.title == "implement tenant storage manager"
    assert result.body_length > 20
    assert len(result.errors) == 0


def test_validate_multi_project_commit():
    multi_proj_msg = """fix-[doc,scripts]: resolve cross-service jwt verification

Normalize curve parameters and ensure public keys match Ed25519 specification.
- Verified with auth actuator health tests.
"""
    result = validate_commit_message(multi_proj_msg)
    assert result.is_valid is True
    assert result.commit_type == "fix"
    assert result.projects == ("doc", "scripts")
    assert len(result.errors) == 0


def test_validate_aagy_commit():
    aagy_msg = """feat-[aagy]: incorporar baseline de software reliability engineering sre

- Formalizar regla transversal de SRE en AGENTS.md, rules/AGENTS.md y .gemini/GEMINI.md.
- Crear skill sre-reliability/SKILL.md y agente sre-engineer.md con presupuesto de tokens acotado.
- Sincronizar plugin global en ~/.gemini/config/plugins/aagy/.
- Verificado con audit-workspace.ps1 (6/6 fases OK).
"""
    result = validate_commit_message(aagy_msg)
    assert result.is_valid is True
    assert result.commit_type == "feat"
    assert result.projects == ("aagy",)
    assert result.title == "incorporar baseline de software reliability engineering sre"
    assert len(result.errors) == 0


def test_validate_backwards_compatible_plus_commit():
    # Asegura compatibilidad hacia atrás con commits previos que usaban '+'
    legacy_msg = """feat+[aagy]: legacy format with plus

This commit uses the legacy plus separator and must still validate cleanly.
- Preserves backwards compatibility with git history.
"""
    result = validate_commit_message(legacy_msg)
    assert result.is_valid is True
    assert result.commit_type == "feat"
    assert result.projects == ("aagy",)
    assert len(result.errors) == 0


def test_validate_rejects_single_line_commit():
    single_line = "feat-[scripts]: quick commit without explanation"
    result = validate_commit_message(single_line, strict=True)
    assert result.is_valid is False
    assert any("Cuerpo explicativo" in e for e in result.errors)


def test_validate_rejects_invalid_title_format():
    invalid_header = """invalidtype-[scripts]: standard commit format

Here is an explanation of the change that is long enough.
"""
    result = validate_commit_message(invalid_header)
    assert result.is_valid is False
    assert any("Tipo 'invalidtype' no reconocido" in e for e in result.errors)


def test_format_commit_message():
    output = format_commit_message(
        commit_type="refactor",
        projects=["infra", "scripts"],
        title="streamline traefik dynamic routing",
        body="Consolidated entrypoints and verified TLS passthrough.",
    )
    assert output.startswith("refactor-[infra,scripts]: streamline traefik dynamic routing\n\n")
    assert "Consolidated entrypoints" in output

    # Validar que el resultado de format_commit_message pasa la validación
    result = validate_commit_message(output)
    assert result.is_valid is True


MSG_BODY = "\n\nCuerpo explicativo suficientemente largo para la validación.\n"


def test_projects_come_from_consumer_repo(tmp_path, monkeypatch):
    """La lista de proyectos la declara el repo (`projects` de .governance/aagy.json)."""
    import format_commit as fc

    (tmp_path / ".governance").mkdir()
    (tmp_path / ".governance" / "aagy.json").write_text('{"projects": ["api", "web"]}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert fc.allowed_projects() == frozenset({"api", "web"})
    assert validate_commit_message("feat-[api,web]: algo" + MSG_BODY).is_valid
    assert not validate_commit_message("feat-[otro]: algo" + MSG_BODY).is_valid


def test_without_declared_projects_any_slug_is_valid():
    assert validate_commit_message("feat-[cualquiera]: algo" + MSG_BODY, projects=None).is_valid
    assert not validate_commit_message("feat-[Mal Slug]: algo" + MSG_BODY, projects=None).is_valid
