---
description: Local model (Ollama) - status, on/off/auto and delegate simple tasks through the aagy-local MCP server.
---

# aagy-local

Modelo local con Ollama. Es el equivalente de la skill `aagy-local` de `aagy`: los
dos usan `scripts/py/local_model.py` y el servidor MCP `aagy-local`, que el plugin
registra en `.mcp.json`.

## Uso

```text
/aagy-local            # estado: modo pedido, modo efectivo, modelo
/aagy-local on|off|auto
```

## Qué hacer

Script: `"${CLAUDE_PLUGIN_ROOT}/scripts/py/local_model.py"` (en el repo aagy también
vale `scripts/py/local_model.py`). Usa `python3`, o `python` si no existe. Ejecuta
desde la carpeta del repo en el que trabajas.

1. Sin argumentos: `local_model.py status` y resume en una línea.
2. `on`, `off`, `auto`: `local_model.py <modo>`. Guarda `local_model.mode` en
   `.governance/aagy.json`. Di que el cambio de herramientas MCP se ve en la próxima sesión.

## Reglas

1. Los modelos y la URL se leen con `aagy_config` (`local_model.*`); el plugin no trae nombres de modelo.
2. Al modelo local solo van tareas sencillas del catálogo (`local_run`). Lo que requiere pensar se queda en Claude.
3. Con ficheros privados, usa `local_run` con `paths`: su contenido no entra en el contexto.

## Paridad

Antigravity: skill `aagy-local` de `aagy`. Mismo script y mismo servidor MCP.
