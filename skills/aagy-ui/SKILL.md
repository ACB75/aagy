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

```text
/aagy-ui                     # estado en una línea: rama | modo local | épica y tarea
/aagy-ui notify auto|on|off  # avisos de escritorio al terminar (hook Stop)
/aagy-ui vscode [--apply]    # extensiones recomendadas (TODO, Git) en .vscode/extensions.json
```

## Qué hacer

Scripts en `<source_repo>/scripts/py/`, con `source_repo` de
`~/.gemini/config/plugins/aagy/.aagy-install.json` (en el repo aagy, `scripts/py/`).
Ejecuta desde la carpeta del repo en el que trabajas.

1. Sin argumentos: `aagy_statusline.py --plain --agent agy` y muestra la línea tal cual.
2. `notify`, `vscode`: `aagy_ui.py <argumentos>`.

## Reglas

1. La configuración es `ui.*` de `aagy_config`; el plugin no guarda datos de nadie.
2. Las extensiones son opcionales y gratuitas (Open VSX); no las instales sin que el usuario lo pida.
3. Guía completa: `doc/04-operations/runbooks/MANUAL_ui.md`.

## Paridad

Claude Code: comando `/aagy-ui` de `aagy-ecc`, con status line nativa y `ccusage`. Antigravity no tiene status line ni `ccusage`.
