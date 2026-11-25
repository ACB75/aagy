---
name: aagy-local
description: "Local model (Ollama) switch and status: auto/off/tool, delegate simple tasks via aagy-local MCP."
metadata:
  origin: AAGY
---

# aagy-local

Modelo local con Ollama en Antigravity. Es el equivalente del comando `/aagy-local`
de Claude Code: los dos usan `scripts/py/local_model.py` y el mismo servidor MCP
`aagy-local` (`scripts/py/local_model_mcp.py`).

## Cuándo usarla

- El usuario pide "modelo local", "Ollama", `/aagy-local`, encenderlo, apagarlo o ver su estado.
- Después de instalar `aagy`, para registrar el servidor MCP en Antigravity.

## Uso

```text
/aagy-local            # estado: modo pedido, modo efectivo, modelo
/aagy-local on|off|auto
/aagy-local bench      # mide precisión y tokens/s de los modelos configurados
/aagy-local usage      # resumen del registro de uso (sin contenido)
/aagy-local register   # registra aagy-local en mcp_config.json de Antigravity
/aagy-local setup --tool <m> --only <m> --fim <m> [--pull]   # configura la máquina
```

## Qué hacer

Script: `<source_repo>/scripts/py/local_model.py`, con `source_repo` de
`~/.gemini/config/plugins/aagy/.aagy-install.json` (en el repo aagy, `scripts/py/local_model.py`).
Ejecuta desde la carpeta del repo en el que trabajas.

1. Sin argumentos: `local_model.py status` y resume en una línea.
2. `on`, `off`, `auto`, `bench`, `usage`: `local_model.py <subcomando>`. Los modos se guardan como `local_model.mode` en `.governance/aagy.json`.
3. `setup`: `local_model.py setup` con los argumentos del usuario. Los modelos los elige el usuario; no los inventes.
4. `register`: `local_model.py register-agy` y pide reiniciar Antigravity para que cargue el servidor.

## Reglas

1. Los modelos y la URL se leen con `aagy_config` (`local_model.*`); el plugin no trae nombres de modelo.
2. Al modelo local solo van tareas sencillas del catálogo (`local_run`). Lo que requiere pensar se queda en Gemini.
3. Con ficheros privados, usa `local_run` con `paths`: su contenido no entra en el contexto. La guarda
   `local_private_guard.py` avisa antes de leer un fichero de `local_model.private_globs`.
4. El estado completo lo da DOC-16 del doctor.

## Paridad

Claude Code: comando `/aagy-local` de `aagy-ecc`. Mismo script y mismo servidor MCP.
