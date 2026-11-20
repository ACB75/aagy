"""
Tests unitarios para la integración zero-overhead de gemini-mcp y CLI gemini_deep_ops.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# Añadir ruta para importar scripts/py
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import gemini_deep_ops
import toggle_gemini_mcp


def test_template_gemini_mcp_config():
    repo_root = SCRIPTS_DIR.parent.parent
    template_dir = repo_root / "skills" / "gemini-deep-ops" / "templates" / "gemini-mcp"
    assert template_dir.is_dir()

    plugin_json_file = template_dir / "plugin.json"
    assert plugin_json_file.is_file()
    plugin_data = json.loads(plugin_json_file.read_text(encoding="utf-8"))
    assert plugin_data.get("name") == "gemini-mcp"
    assert plugin_data.get("disabled") is True

    mcp_config_file = template_dir / "mcp_config.json"
    assert mcp_config_file.is_file()
    mcp_data = json.loads(mcp_config_file.read_text(encoding="utf-8"))
    servers = mcp_data.get("mcpServers", {})
    assert "gemini-mcp" in servers
    assert servers["gemini-mcp"].get("disabled") is True

    # Verificar que no contenga claves secretas hardcodeadas
    raw_content = mcp_config_file.read_text(encoding="utf-8")
    assert "AIza" not in raw_content
    assert "${GEMINI_API_KEY}" in raw_content


def test_toggle_gemini_mcp(tmp_path):
    target_config = tmp_path / "mcp_config.json"
    target_config.write_text(
        json.dumps({
            "mcpServers": {
                "gemini-mcp": {
                    "command": "npx",
                    "args": ["-y", "@rlabs/gemini-mcp"],
                    "disabled": True
                }
            }
        }),
        encoding="utf-8",
    )

    # 1. Status inicial: disabled = True
    status = toggle_gemini_mcp.check_status(target_config)
    assert status.exists is True
    assert status.is_disabled is True

    # 2. Habilitar
    res_enable = toggle_gemini_mcp.toggle(target_config, enable=True)
    assert res_enable is True
    status_enabled = toggle_gemini_mcp.check_status(target_config)
    assert status_enabled.is_disabled is False

    # 3. Deshabilitar
    res_disable = toggle_gemini_mcp.toggle(target_config, enable=False)
    assert res_disable is True
    status_disabled = toggle_gemini_mcp.check_status(target_config)
    assert status_disabled.is_disabled is True


def test_gemini_deep_ops_cli_status():
    status = gemini_deep_ops.get_ops_status()
    assert isinstance(status, dict)
    assert "api_key_configured" in status
    assert "sdk_available" in status


def test_gemini_deep_ops_analyze_log_mock(tmp_path):
    sample_log = tmp_path / "sample.log"
    sample_log.write_text(
        "2026-11-20 18:00:00 [ERROR] OutOfMemoryError in Cluster Service: Heap exhausted at 99.8%\n"
        "2026-11-20 18:00:01 [FATAL] Process terminated with exit code 137 (OOMKilled)",
        encoding="utf-8",
    )

    report = gemini_deep_ops.analyze_log(
        log_path=sample_log,
        mock=True,
    )
    assert report.is_success is True
    assert "OutOfMemoryError" in report.summary
    assert report.severity == "CRITICAL"
    assert len(report.recommendations) > 0


def test_skill_gemini_deep_ops_frontmatter():
    repo_root = SCRIPTS_DIR.parent.parent
    skill_file = repo_root / "skills" / "gemini-deep-ops" / "SKILL.md"
    assert skill_file.is_file()

    content = skill_file.read_text(encoding="utf-8")
    assert content.startswith("---")
    # Buscar descripción
    import re
    match = re.search(r'^description:\s*(.+)$', content, re.MULTILINE)
    assert match is not None
    desc = match.group(1).strip().strip('"\'')
    assert len(desc) <= 140
