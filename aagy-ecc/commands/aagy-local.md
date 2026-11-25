---
description: Local model (Ollama) - status, on/off/auto, bench and usage; tasks go through the aagy-local MCP server the machine registers.
---

# aagy-local

Modelo local con Ollama. Las tareas pasan por el servidor MCP `aagy-local`, que no va en el plugin: lo instala
y registra cada equipo a nivel de usuario (`MANUAL_local_model.md` §3).

## Cuándo usarlo

Para ver o cambiar el modo del modelo local, medirlo o revisar su uso.

## Uso

```text
/aagy-local            # estado: modo pedido, modo efectivo, modelo
/aagy-local on|off|auto
/aagy-local bench      # mide precisión y tokens/s de los modelos configurados
/aagy-local usage      # resumen del registro de uso (sin contenido)
```

## Qué hacer

Script: `"${CLAUDE_PLUGIN_ROOT}/scripts/py/local_model.py"` (en el repo aagy también
vale `scripts/py/local_model.py`). Usa `python3`, o `python` si no existe. Ejecuta
desde la carpeta del repo en el que trabajas.

1. Sin argumentos: `local_model.py status` y resume en una línea.
2. `on`, `off`, `auto`, `bench`, `usage`: `local_model.py <subcomando>`. Los modos se guardan como `local_model.mode` en
   `.governance/aagy.json`. Di que el cambio de herramientas MCP se ve en la próxima sesión.

## Reglas

1. Los modelos y la URL se leen con `aagy_config` (`local_model.*`); el plugin no trae nombres de modelo.
2. Al modelo local solo van tareas sencillas del catálogo (`local_run`). Lo que requiere pensar se queda en Claude.
3. Con ficheros privados, usa `local_run` con `paths`: su contenido no entra en el contexto. La guarda
   `local_private_guard.py` avisa antes de leer un fichero de `local_model.private_globs`.
4. El estado completo lo da DOC-16 del doctor.

## Paridad

Antigravity: skill `aagy-local` de `aagy`. Mismo script; el servidor MCP lo registra el equipo en los dos harnesses.
