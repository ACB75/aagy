---
name: gemini-deep-ops
description: "Large log analysis and 5W postmortem sections on demand, with the local model first. Zero tokens at rest."
metadata:
  origin: AAGY
---

# gemini-deep-ops

Análisis bajo demanda de logs grandes y secciones de postmortem. No gasta tokens en reposo.

## Cuándo usarlo

- Logs de más de 10.000 líneas o volcados de memoria que saturarían el contexto.
- La sección analítica de un postmortem 5W en una rama `fix/*`.
- No para desarrollo normal, edición de código ni búsquedas web.

## Uso

```bash
python <PLUGIN>/scripts/py/gemini_deep_ops.py analyze-log --file <ruta/al.log>
python <PLUGIN>/scripts/py/gemini_deep_ops.py postmortem --issue fix/<proyecto>/<id> --file <ruta/al.log>
```

Envoltorios: `<PLUGIN>/scripts/ps1/aagy.ps1 gemini-deep-ops` y `<PLUGIN>/scripts/sh/aagy.sh gemini-deep-ops`.

## Qué hacer

1. `analyze-log` resume el log con una heurística y, si el modelo local está activo, con `local_run`.
2. `postmortem` genera el bloque para `PM_<rama>_<fecha>.md` en la carpeta de postmortems.

## Reglas

1. Presupuesto 0 $: el servidor MCP de Gemini es de pago. `toggle_gemini_mcp.py --enable` se niega salvo que `budget` lo permita.
2. Si lo activas, desactívalo al acabar (`toggle_gemini_mcp.py --disable`).

## Paridad

Claude Code: la skill viaja en el paquete `extras` de `aagy-ecc`. Mismo script.
