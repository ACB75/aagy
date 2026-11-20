#!/usr/bin/env python3
"""
Utilidad determinista para alternar el estado del plugin gemini-mcp (stdlib pura).

Permite habilitar o deshabilitar 'gemini-mcp' en mcp_config.json de forma segura,
garantizando zero-overhead de tokens en reposo.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

logger: logging.Logger = logging.getLogger("toggle-gemini-mcp")

SERVER_NAME: str = "gemini-mcp"
DEFAULT_MCP_CONFIG: str = "mcp_config.json"


@dataclass(frozen=True)
class MCPStatus:
    exists: bool
    is_disabled: bool
    server_name: str
    path: Path


def check_status(config_path: Path) -> MCPStatus:
    """Verifica si el servidor gemini-mcp existe y su estado en el archivo de configuración."""
    if not config_path.is_file():
        return MCPStatus(exists=False, is_disabled=True, server_name=SERVER_NAME, path=config_path)

    try:
        data = json.loads(config_path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError):
        return MCPStatus(exists=False, is_disabled=True, server_name=SERVER_NAME, path=config_path)

    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict) or SERVER_NAME not in servers:
        return MCPStatus(exists=False, is_disabled=True, server_name=SERVER_NAME, path=config_path)

    cfg = servers[SERVER_NAME]
    is_disabled = bool(cfg.get("disabled", False)) if isinstance(cfg, dict) else False
    return MCPStatus(exists=True, is_disabled=is_disabled, server_name=SERVER_NAME, path=config_path)


def toggle(config_path: Path, enable: bool) -> bool:
    """Activa o desactiva gemini-mcp en el archivo JSON."""
    if not config_path.is_file():
        logger.error("[ERROR] No se encontró el archivo de configuración en %s", config_path)
        return False

    try:
        data = json.loads(config_path.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.error("[ERROR] JSON inválido en %s: %s", config_path, exc)
        return False

    servers = data.setdefault("mcpServers", {})
    if not isinstance(servers, dict):
        logger.error("[ERROR] La clave 'mcpServers' no es un objeto válido.")
        return False

    server_cfg = servers.setdefault(SERVER_NAME, {
        "command": "npx",
        "args": ["-y", "@rlabs/gemini-mcp"],
        "env": {"GEMINI_API_KEY": "${GEMINI_API_KEY}"},
    })

    if isinstance(server_cfg, dict):
        server_cfg["disabled"] = not enable
    else:
        logger.error("[ERROR] Configuración de %s no es un objeto.", SERVER_NAME)
        return False

    try:
        config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        action = "HABILITADO" if enable else "DESHABILITADO (0 tokens en reposo)"
        logger.info("[OK] Servidor '%s' %s en %s", SERVER_NAME, action, config_path)
        return True
    except OSError as exc:
        logger.error("[ERROR] No se pudo escribir en %s: %s", config_path, exc)
        return False


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Alterna gemini-mcp en mcp_config.json.")
    parser.add_argument("--config", type=Path, default=None, help="Ruta a mcp_config.json.")
    parser.add_argument("--enable", action="store_true", help="Habilita gemini-mcp.")
    parser.add_argument("--disable", action="store_true", help="Deshabilita gemini-mcp.")
    parser.add_argument("--status", action="store_true", help="Muestra el estado actual.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)

    repo_root = Path(__file__).resolve().parent.parent.parent
    config_file = args.config.resolve() if args.config else repo_root / DEFAULT_MCP_CONFIG

    if not config_file.is_file():
        alt_config = repo_root / "templates" / "plugins" / SERVER_NAME / DEFAULT_MCP_CONFIG
        if alt_config.is_file():
            config_file = alt_config

    if args.status or (not args.enable and not args.disable):
        status = check_status(config_file)
        state_str = "DESACTIVADO (0 tokens en reposo)" if status.is_disabled else "ACTIVO"
        logger.info("Estado de '%s' en %s: %s (declarado: %s)", status.server_name, status.path, state_str, status.exists)
        return 0

    if args.enable:
        success = toggle(config_file, enable=True)
        return 0 if success else 1

    if args.disable:
        success = toggle(config_file, enable=False)
        return 0 if success else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
