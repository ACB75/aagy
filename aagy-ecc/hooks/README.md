# Hooks de aagy-ecc

`hooks/hooks.json` replica en Claude Code los tres hooks deterministas del plugin
raíz `aagy` (`../../hooks.json`). Todos son Python 3 stdlib pura, se ejecutan
desde `${CLAUDE_PLUGIN_ROOT}` y nunca bloquean por error propio (fail-open).

| Evento Claude Code | Matcher | Script | Equivalente en `aagy` |
| :--- | :--- | :--- | :--- |
| `PreToolUse` | `Bash\|PowerShell` | `scripts/hooks/safety_check.py` | `scripts/ps1/safety-check.ps1` (`run_command`) |
| `PostToolUse` | `Write\|Edit\|MultiEdit` | `scripts/hooks/post_write_lint.py` | `scripts/ps1/hook-post-write.ps1` (`write_file` / `edit_file`) |
| `Stop` | (todos) | `scripts/py/self_improve.py --capture-stop` | `scripts/py/self_improve.py --capture-stop` |
| `PreToolUse` | `Bash\|PowerShell\|Write\|Edit\|MultiEdit\|NotebookEdit\|EnterWorktree` | `scripts/hooks/worktree_guard.py` | `scripts/ps1/agent-worktree.ps1 guard --agent agy` (`run_command` / `write_file` / `edit_file`) |
| `SessionStart` | `startup` | `scripts/py/agent_worktree.py --quiet recycle --agent claude --if-merged` | (sin equivalente: Antigravity recicla en `claim` y en `complete-task-pr`) |

- **Safety gate**: deniega `rm -rf /`, `mkfs`, `DROP DATABASE` y escrituras directas a
  `/dev/sd*` con `permissionDecision: deny`.
- **Linter Markdown**: si existe un `.markdownlint.json` subiendo desde el archivo y
  `markdownlint` está en el `PATH`, ejecuta `markdownlint --fix`; si no, no hace nada.
- **Self-improve**: captura pasiva del evento Stop (devuelve `{}`).
- **Worktree por agente**: si el repo activó `agent_worktree.py init`, deniega que Claude escriba en el
  checkout principal de Master o en el worktree de Antigravity, y el worktree nativo de Claude Code. Al
  iniciar sesión recicla `<repo>-aagy-ecc` si su PR ya está fusionada. Sin marcador no hace nada.

`scripts/py/` es una copia generada desde la raíz del repositorio por
`scripts/py/sync_aagy_ecc.py`; no se edita a mano.
