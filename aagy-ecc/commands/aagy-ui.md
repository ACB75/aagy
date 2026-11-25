---
description: UI - status line (model, branch, context, cost, local mode, task), desktop notifications, ccusage, VS Code extensions.
---

# aagy-ui

UI de Claude Code. Es el equivalente de la skill `aagy-ui` de `aagy`: los dos usan
`scripts/py/aagy_ui.py`, `aagy_statusline.py` y `aagy_notify.py`.

## Cuándo usarlo

- El usuario pide la status line, avisos de escritorio, `ccusage`, `/aagy-ui` o extensiones recomendadas.

## Uso

```text
/aagy-ui                       # estado: status line, avisos y ccusage
/aagy-ui config                # igual que sin argumentos (mismo subcomando que en Antigravity)
/aagy-ui statusline on|off     # --scope user (defecto) | project | local
/aagy-ui notify auto|on|off    # avisos de escritorio (Stop largo y Notification)
/aagy-ui ccusage on|off        # segmento "hoy $X" (solo si ccusage está en el PATH)
/aagy-ui usage [daily|monthly|session|blocks]
/aagy-ui vscode [--apply]      # extensiones recomendadas en .vscode/extensions.json
```

## Qué hacer

Script: `"${CLAUDE_PLUGIN_ROOT}/scripts/py/aagy_ui.py"` (en el repo aagy también vale
`scripts/py/aagy_ui.py`). Usa `python`, o `python3` si no existe. Ejecuta desde la
carpeta del repo en el que trabajas.

1. Sin argumentos o `config`: `aagy_ui.py status` y resume en una línea.
2. Con argumentos: `aagy_ui.py <argumentos>` tal cual. Si `statusline on` dice que ya hay otra
   status line, pregunta antes de repetir con `--force`.
3. `usage`: muestra la salida de `ccusage`. Si no está instalado, da la pista de instalación; no lo instales tú.

## Reglas

1. La configuración es `ui.*` de `aagy_config` (`AAGY_UI_*` la sobrescribe); el plugin no guarda datos de nadie.
2. `ccusage` y las extensiones son opcionales y gratuitas; nunca se instalan solas.
3. Guía completa: `doc/04-operations/runbooks/MANUAL_ui.md`.

## Paridad

Antigravity: skill `aagy-ui` de `aagy`, con los mismos subcomandos, claves `ui.*` y variables `AAGY_UI_*`.
Asimetrías: allí no hay status line nativa (el estado sale con `/aagy-ui`), ni evento `Notification`, y
`ccusage` no lee sus transcripts.
