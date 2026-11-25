---
description: Claude's fixed git worktree (<repo>-aagy-ecc) - status, init and recycle after the PR is merged.
---

# aagy-worktree

Worktree fijo de Claude Code: Claude trabaja solo en `<repo>-aagy-ecc`, Antigravity en
`<repo>-aagy` y el checkout principal `<repo>` es del usuario.

## Cuándo usarlo

Al empezar en un repo con worktrees por agente, o para reciclar el worktree tras fusionarse la PR.

## Uso

```text
/aagy-worktree                 # dónde estoy y estado de los tres checkouts
/aagy-worktree init            # crear los worktrees que falten (una vez por repo)
/aagy-worktree recycle         # reciclar mi worktree tras fusionarse la PR
/aagy-worktree recycle --hard-recreate
```

## Qué hacer

Script: `"${CLAUDE_PLUGIN_ROOT}/scripts/py/agent_worktree.py"` (en el repo aagy
también vale `scripts/py/agent_worktree.py`). Usa `python3`, o `python` si no existe.

1. Sin argumentos: `agent_worktree.py where --json` y `agent_worktree.py status`.
   Resume en español dónde está la sesión y en qué rama está cada checkout. Si la
   sesión no está en `<repo>-aagy-ecc`, dilo y trabaja con `cd` a esa carpeta.
2. `init`: ejecútalo solo si el usuario lo pide. Crea `<repo>-aagy` y `<repo>-aagy-ecc`
   desacoplados en `origin/main`, copia los `.env` y regenera dependencias.
3. `recycle`: `agent_worktree.py recycle --agent claude [--hard-recreate]`.
   - Código 3: hay trabajo sin guardar. Enseña la lista al usuario y no borres nada.
   - Código 4: la PR no está fusionada. No hagas nada más.
   - Código 5: falta `gh`.

## Reglas

- Nunca uses `git worktree add/remove`, `EnterWorktree` ni `claude --worktree`: el hook los bloquea.
- Manual: `doc/04-operations/runbooks/MANUAL_agent_worktrees.md`.

## Paridad

Antigravity: skill `agent-worktrees`. Mismo script (`agent_worktree.py`).
