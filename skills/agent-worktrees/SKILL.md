---
name: agent-worktrees
description: "One fixed git worktree per agent (<repo>-aagy, <repo>-aagy-ecc), recycled after merge."
metadata:
  origin: AAGY
---

# agent-worktrees

Cada agente trabaja en su propio *git worktree* del mismo clon, y el checkout
principal es solo del usuario:

| Carpeta | Quién |
| :--- | :--- |
| `<padre>/<repo>` | El usuario, en `main` |
| `<padre>/<repo>-aagy` | Antigravity (`agy`) |
| `<padre>/<repo>-aagy-ecc` | Claude Code (`claude`) |

Script: `<PLUGIN>/scripts/py/agent_worktree.py` (+ `<PLUGIN>/scripts/ps1/aagy.ps1 agent-worktree`, `<PLUGIN>/scripts/sh/aagy.sh agent-worktree`).

## Cuándo usarlo

- Al empezar a trabajar en un repo que tiene worktrees por agente (`agent-worktree status`).
- El usuario pide "prepara los worktrees", "recicla mi worktree" o "por qué no puedo escribir aquí".
- Tras fusionarse una PR, si el reciclado no se hizo solo.

## Uso

| Acción | Comando |
| :--- | :--- |
| Crear los worktrees (una vez por repo) | `agent-worktree init` |
| Ver estado | `agent-worktree status` |
| ¿Dónde estoy? | `agent-worktree where` |
| Reciclar tras el merge | `agent-worktree recycle --agent agy` |
| Forzar borrado y recreación | `agent-worktree recycle --agent agy --hard-recreate` |

`recycle` comprueba con `gh` que la PR está fusionada, limpia el worktree sobre
`origin/main` (o lo recrea si una carpeta está bloqueada), copia los `.env` del
principal, regenera `node_modules`/`.venv` desde sus lockfiles y actualiza el
principal con `--ff-only` solo si está limpio en `main`.

Se lanza solo al final de `complete_task_pr.py --merge`, en el siguiente `backlog.py claim`
y, en Claude Code, al iniciar sesión. Antigravity no tiene hook de inicio: si la
PR se fusionó más tarde, el reciclado ocurre en el siguiente `claim`.

## Qué hacer

1. Al empezar, `agent-worktree where`: si no estás en tu worktree, trabaja con `cd` a él.
2. Tras fusionarse la PR, `agent-worktree recycle --agent agy`. Si para por trabajo sin guardar, enséñalo y no borres nada.

## Reglas

1. **Solo tu worktree**: escribe y ejecuta comandos que modifican solo en tu carpeta. El hook PreToolUse lo bloquea en el principal y en el worktree del otro agente. Leer sí puedes.
2. **Una tarea a la vez**: `backlog.py claim` crea la rama de la tarea en tu worktree. Para otra tarea en paralelo, `claim --worktree` (excepción).
3. **No gestiones worktrees a mano**: nada de `git worktree add/remove` ni del worktree nativo de Claude Code; usa el script.
4. **Trabajo sin guardar**: el reciclado nunca lo borra; si lo hay, se para y avisa. Haz commit y push, o pregunta al usuario.

## Paridad

Claude Code: comando `/aagy-worktree`. Mismo script (`agent_worktree.py`). Antigravity no tiene hook de inicio: el reciclado ocurre en el siguiente `claim` (asimetría).

## Relevo entre agentes

`backlog.py handoff` suelta la rama (`git switch --detach`) si el worktree está
limpio, para que el otro agente la abra en el suyo con `claim`. Git no permite
la misma rama en dos worktrees a la vez.

Manual: `doc/04-operations/runbooks/MANUAL_agent_worktrees.md`.
