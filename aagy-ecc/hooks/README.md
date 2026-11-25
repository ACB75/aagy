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
| Inicio | `SessionStart` | `scripts/hooks/session_start_rules.py`, `agent_worktree.py recycle` | Asimetría: sin evento |
| Compactación | `PreCompact` | `backlog.py checkpoint --auto` | Asimetría: sin evento |
| Fin de sesión | `SessionEnd` | `backlog.py handoff --auto` | Asimetría: sin evento |

`audit_plugin_parity.py` comprueba que los eventos y los motores coinciden, salvo esas tres
asimetrías, y que el `hooks.json` raíz no usa rutas relativas. Las asimetrías y cómo se cubren
están en `doc/01-architecture/MANUAL_aagy_ecc_parity_and_migration.md`.

`scripts/py/` es una copia generada desde la raíz del repositorio; no se edita a mano.
