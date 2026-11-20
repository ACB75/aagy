# Hooks de aagy-ecc

`hooks/hooks.json` replica en Claude Code los tres hooks deterministas del plugin
raíz `aagy` (`../../hooks.json`). Todos son Python 3 stdlib pura, se ejecutan
desde `${CLAUDE_PLUGIN_ROOT}` y nunca bloquean por error propio (fail-open).

| Evento Claude Code | Matcher | Script | Equivalente en `aagy` |
| :--- | :--- | :--- | :--- |
| `PreToolUse` | `Bash\|PowerShell` | `scripts/hooks/safety_check.py` | `scripts/ps1/safety-check.ps1` (`run_command`) |
| `PostToolUse` | `Write\|Edit\|MultiEdit` | `scripts/hooks/post_write_lint.py` | `scripts/ps1/hook-post-write.ps1` (`write_file` / `edit_file`) |
| `Stop` | (todos) | `scripts/py/self_improve.py --capture-stop` | `scripts/py/self_improve.py --capture-stop` |

- **Safety gate**: deniega `rm -rf /`, `mkfs`, `DROP DATABASE` y escrituras directas a
  `/dev/sd*` con `permissionDecision: deny`.
- **Linter Markdown**: si existe un `.markdownlint.json` subiendo desde el archivo y
  `markdownlint` está en el `PATH`, ejecuta `markdownlint --fix`; si no, no hace nada.
- **Self-improve**: captura pasiva del evento Stop (devuelve `{}`).

`scripts/py/` es una copia generada desde la raíz del repositorio por
`scripts/py/sync_aagy_ecc.py`; no se edita a mano.
