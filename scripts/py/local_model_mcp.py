#!/usr/bin/env python3
"""
Servidor MCP genérico ``aagy-local`` (local_model_mcp.py).

Expone el modelo local (Ollama) al agente con solo dos herramientas genéricas:

- ``local_status``: modo pedido, modo efectivo y modelos disponibles.
- ``local_run(task, text | paths, params)``: ejecuta una tarea del catálogo
  declarativo (``classify``, ``summarize``, ``extract``, ``translate``,
  ``complete`` y las que añada el proyecto). Con ``paths`` el servidor lee los
  ficheros él mismo y solo devuelve el resultado.

Con el modo ``off``, o en ``auto`` sin Ollama, ``tools/list`` devuelve una lista
vacía: cero tokens en reposo. Protocolo MCP por stdio (JSON-RPC 2.0, un mensaje
por línea). Solo stdlib de Python. Se registra en aagy-ecc (``.mcp.json`` del
plugin) y en Antigravity (``local_model.py register-agy``).
"""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional, TextIO

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import local_model as lm  # noqa: E402

PROTOCOL_VERSION = "2024-11-05"
SERVER_VERSION = "1.0.0"
TOOL_STATUS = "local_status"
TOOL_RUN = "local_run"
ERR_METHOD = -32601
ERR_PARAMS = -32602
K_DESC = "description"


def _tools(settings: lm.Settings) -> List[Dict[str, Any]]:
    tasks = sorted(settings.tasks)
    return [
        {
            "name": TOOL_STATUS,
            K_DESC: "Estado del modelo local (Ollama): modo, modelo y si responde.",
            "inputSchema": {"type": "object", "properties": {}},
        },
        {
            "name": TOOL_RUN,
            K_DESC: "Tarea sencilla en el modelo local (clasificar, resumir, extraer, traducir, completar). "
                           "Usa paths para ficheros privados: su contenido no vuelve al contexto.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "enum": tasks},
                    "text": {"type": "string"},
                    "paths": {"type": "array", "items": {"type": "string"}},
                    "params": {"type": "object", K_DESC: "labels, fields, target_lang, max_words..."},
                },
                "required": ["task"],
            },
        },
    ]


class Server:
    """Estado mínimo del servidor: la configuración se relee en cada tools/list."""

    def __init__(self, root: Optional[Path] = None) -> None:
        self.root = (root or Path.cwd()).resolve()

    def settings(self) -> lm.Settings:
        return lm.load_settings(self.root)

    def list_tools(self) -> Dict[str, Any]:
        settings = self.settings()
        status = lm.get_status(settings)
        return {"tools": _tools(settings) if status.effective == lm.MODE_TOOL else []}

    def call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments") or {}
        settings = self.settings()
        if name == TOOL_STATUS:
            payload: Dict[str, Any] = asdict(lm.get_status(settings))
        elif name == TOOL_RUN:
            payload = lm.run_task(settings, args, self.root)
        else:
            raise KeyError(name)
        is_error = "error" in payload
        return {"content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}], "isError": is_error}

    def handle(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = message.get("method", "")
        msg_id = message.get("id")
        if msg_id is None:
            return None  # notificación (p. ej. notifications/initialized)
        try:
            result = self._dispatch(method, message.get("params") or {})
        except KeyError as exc:
            code = ERR_PARAMS if method == "tools/call" else ERR_METHOD
            return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": f"No soportado: {exc}"}}
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    def _dispatch(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if method == "initialize":
            return {
                "protocolVersion": params.get("protocolVersion", PROTOCOL_VERSION),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": lm.SERVER_NAME, "version": SERVER_VERSION},
            }
        if method == "ping":
            return {}
        if method == "tools/list":
            return self.list_tools()
        if method == "tools/call":
            return self.call_tool(params)
        raise KeyError(method)


def serve(stdin: TextIO, stdout: TextIO, server: Optional[Server] = None) -> None:
    srv = server or Server()
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            continue
        response = srv.handle(message)
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding=lm.ENCODING)
    serve(sys.stdin, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
