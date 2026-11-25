# Fase 2: Plan de Acción — UI de Claude Code y Antigravity

> **Requisitos**: [REQ_aagy_ui.md](REQ_aagy_ui.md) | **Issue**: #116 | **Rama**: `feat/aagy/ui-statusline-notify`
> **Fecha**: `2026-11-25` | **Estado**: `EN CURSO`

---

## 1. Diseño

```mermaid
flowchart LR
    CC[Claude Code] -- JSON stdin --> SL[aagy_statusline.py]
    SL --> CFG[aagy_config ui.*]
    SL --> LM[local_model.load_settings]
    SL --> BL[.git/aagy-backlog/state.json]
    SL -. caché 5 min .-> CU[ccusage daily --json]
    CC -- Stop / Notification --> NT[aagy_notify.py]
    NT --> OS{SO}
    OS --> W[powershell.exe toast]
    OS --> M[osascript]
    OS --> L[notify-send]
    UI[aagy_ui.py] -- statusline on/off/repair --> ST[settings.json]
    UI -- vscode --apply --> EX[.vscode/extensions.json]
```

| Módulo | Responsabilidad |
| :--- | :--- |
| `scripts/py/aagy_statusline.py` | Lee el JSON, calcula los segmentos y los pinta. `--plain` para Antigravity. `--refresh-usage` rellena la caché de `ccusage`. |
| `scripts/py/aagy_notify.py` | Decide si avisar y lanza el backend del SO sin esperar. `--dry-run` imprime el comando. |
| `scripts/py/aagy_ui.py` | CLI: `status`, `statusline on/off`, `repair`, `notify`, `ccusage`, `usage`, `vscode`. |
| `aagy-ecc/commands/aagy-ui.md` | Comando `/aagy-ui`. |
| `skills/aagy-ui/SKILL.md` | Skill de Antigravity (excluida del espejo, como `aagy-local`). |

## 2. Pasos TDD

| Paso | RED (test) | GREEN |
| :--- | :--- | :--- |
| 1 | `test_aagy_statusline.py`: segmentos con JSON completo, sin `context_window` (transcript), umbrales de color, `ui.statusline=false`, `--plain`, tarea del backlog, `ccusage` desde caché | `aagy_statusline.py` |
| 2 | `test_aagy_notify.py`: modos `auto/on/off`, CI, duración mínima del turno, `stop_hook_active`, comando por SO sin inyección | `aagy_notify.py` |
| 3 | `test_aagy_ui.py`: `statusline on/off` idempotente, no pisa una ajena, `repair` de ruta vieja, `notify`/`ccusage` en `.governance/aagy.json`, `vscode --apply` fusiona y respeta JSONC | `aagy_ui.py` |
| 4 | `test_sync_aagy_ecc.py` y `audit_plugin_parity.py` en verde | espejo, hooks, `aagy_config` (clave `ui`) |

## 3. Verificación

- `python scripts/py/ci_local.py run` (los fallos que requieren `pwsh` ya existían en Linux).
- Prueba manual: `echo '<json>' | python scripts/py/aagy_statusline.py` y `python scripts/py/aagy_notify.py --event notification --dry-run`.

## 4. Rollback (`<2` min)

`git revert <sha>` y `python scripts/py/aagy_ui.py statusline off`; reinstalar el plugin. Los avisos se apagan al momento con `AAGY_UI_NOTIFY=off`.
