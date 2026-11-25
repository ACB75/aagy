---
name: aagy-ui
description: "UI status in one line (branch, local mode, task), desktop notifications, VS Code extension recommendations."
metadata:
  origin: AAGY
  cost: free
---

# aagy-ui

UI de Antigravity. Es el equivalente del comando `/aagy-ui` de Claude Code: los dos
usan `scripts/py/aagy_ui.py`, `aagy_statusline.py` y `aagy_notify.py`.

## Cuándo usarla

- El usuario pide "estado", "status line", `/aagy-ui`, avisos de escritorio o extensiones recomendadas.

## Uso

Mismos subcomandos que `/aagy-ui` de Claude Code; los que Antigravity no puede tener lo dicen.

```text
/aagy-ui                       # estado en una línea: rama | contexto | modo local | épica y tarea
/aagy-ui config                # configuración ui.* y si los avisos están activos aquí
/aagy-ui notify auto|on|off    # avisos de escritorio al terminar (hook Stop)
/aagy-ui vscode [--apply]      # extensiones recomendadas (TODO, Git) en .vscode/extensions.json
/aagy-ui usage [daily|monthly|session]  # tokens estimados por día, mes o sesión (sin coste en $)
/aagy-ui statusline | ccusage  # no aplican en Antigravity (ver Paridad)
```

## Qué hacer

Scripts en `<source_repo>/scripts/py/`, con `source_repo` de
`~/.gemini/config/plugins/aagy/.aagy-install.json` (en el repo aagy, `scripts/py/`).
Ejecuta desde la carpeta del repo en el que trabajas.

1. Sin argumentos: `aagy_statusline.py --plain --agent agy` y muestra la línea tal cual. El contexto es la
   estimación de `session_token_monitor.py` frente a su umbral de `/compact`, con los mismos colores y umbrales
   (`ui.context_warn_pct`, `ui.context_crit_pct`).
2. `config`: `aagy_ui.py status --harness agy`.
3. `notify`, `vscode`: `aagy_ui.py <argumentos>`.
4. `usage [daily|monthly|session]`: `aagy_ui.py usage <informe> --harness agy` y muestra la tabla tal cual.
   Lee los transcripts de `~/.gemini/antigravity/brain/` con `session_token_monitor.py`; no llama a ninguna API.
5. `statusline`, `ccusage`: di en una línea por qué no aplican (Paridad).

## Reglas

1. La configuración es `ui.*` de `aagy_config`; el plugin no guarda datos de nadie.
2. Las extensiones son opcionales y gratuitas (Open VSX); no las instales sin que el usuario lo pida.
3. Guía completa: `doc/04-operations/runbooks/MANUAL_ui.md`.

## Paridad

Claude Code: comando `/aagy-ui` de `aagy-ecc`. Mismos scripts, claves `ui.*` y variables `AAGY_UI_*`.
Asimetrías: Antigravity no tiene status line nativa (el estado sale con `/aagy-ui`), ni evento de permiso
(solo avisa en `Stop`, sin medir la duración del turno), y `ccusage` solo lee transcripts de Claude Code: `usage` da tokens estimados, sin coste en $.
