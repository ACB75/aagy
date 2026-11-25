# Hooks de aagy-ecc

`hooks/hooks.json` cubre en Claude Code los mismos momentos que el `hooks.json` raíz de
`aagy`, con **un solo motor Python** para los dos plugins (`scripts/py/`, copiado por
`sync_aagy_ecc.py`). Todos son Python 3 stdlib, se ejecutan desde `${CLAUDE_PLUGIN_ROOT}`
y nunca bloquean por error propio (fail-open). En `aagy`, el instalador sustituye
`${AAGY_PLUGIN_ROOT}` por la carpeta del plugin, así que los hooks funcionan en cualquier repo.

| Momento | Evento Claude Code | Motor (`scripts/py/`) | En `aagy` (Antigravity) |
| :--- | :--- | :--- | :--- |
| Antes de un comando | `PreToolUse` `Bash\|PowerShell` | `hook_safety.py --format claude` | `run_command`, `--format agy` |
| Antes de escribir | `PreToolUse` | `agent_worktree.py guard`, `local_private_guard.py` | `run_command`, `write_file`, `edit_file`, `view_file` |
| Después de escribir | `PostToolUse` | `hook_post_write.py --format claude` | `write_file`, `edit_file`, `--format agy` |
| Fin de turno | `Stop` | `self_improve.py --capture-stop`, `backlog.py checkpoint --auto` | `Stop` |
| Inicio | `SessionStart` | `scripts/hooks/session_start_rules.py`, `agent_worktree.py recycle` | `SessionStart` con `agent_worktree.py recycle --agent agy`; las reglas las lee de forma nativa |
| Compactación | `PreCompact` | `backlog.py checkpoint --auto` | Asimetría: sin evento |
| Fin de sesión | `SessionEnd` | `backlog.py handoff --auto` | Asimetría: sin evento |
| Inicio (UI) | `SessionStart` `startup` | `aagy_ui.py --quiet repair` | `SessionStart` (repara la status line del CLI) |
| Fin de turno (UI) | `Stop` | `aagy_notify.py --event stop` | `Stop`, `--format agy` |
| Permiso o espera | `Notification` | `aagy_notify.py --event notification` | Asimetría: sin evento; la status line del CLI lo suple con `tool_confirmation_pending` |

`audit_plugin_parity.py` comprueba que los eventos y los motores coinciden, salvo las tres
asimetrías (`PreCompact`, `SessionEnd`, `Notification`), y que el `hooks.json` raíz no usa rutas relativas. Las asimetrías y cómo se cubren
están en `doc/01-architecture/MANUAL_aagy_ecc_parity_and_migration.md`.

- **UI**: `repair` actualiza la ruta de la status line de aagy si el plugin cambió de versión. `aagy_notify.py`
  avisa en el escritorio al pedir permiso y al acabar un turno de más de `ui.notify_min_s` (30 s); se apaga con
  `ui.notify=off` y no hace nada sin escritorio. Ver `doc/04-operations/runbooks/MANUAL_ui.md`.

`scripts/py/` es una copia generada desde la raíz del repositorio; no se edita a mano.
