---
name: agent-worktrees
description: "One fixed git worktree per agent (<repo>-aagy, <repo>-aagy-ecc), recycled after merge."
metadata:
  origin: AAGY
---

# agent-worktrees

Cada agente trabaja en su propio *git worktree* del mismo clon, y el checkout
principal es solo de Master:

| Carpeta | Quién |
| :--- | :--- |
| `<padre>/<repo>` (p. ej. `C:\Workspace\projects\home-lab`) | Master, en `main` |
| `<padre>/<repo>-aagy` | Antigravity (`agy`) |
| `<padre>/<repo>-aagy-ecc` | Claude Code (`claude`) |

En Claude Code los mismos pasos están en el comando `/aagy-worktree`.
Script: `scripts/py/agent_worktree.py` (+ `scripts/ps1/agent-worktree.ps1`, `scripts/sh/agent-worktree.sh`).

## Cuándo usarla

- Al empezar a trabajar en un repo que tiene worktrees por agente (`agent-worktree status`).
- Master pide "prepara los worktrees", "recicla mi worktree" o "por qué no puedo escribir aquí".
- Tras fusionarse una PR, si el reciclado no se hizo solo.

## Reglas

1. **Solo tu worktree**: escribe y ejecuta comandos que modifican solo en tu carpeta. El hook PreToolUse lo bloquea en el principal y en el worktree del otro agente. Leer sí puedes.
2. **Una tarea a la vez**: `backlog.py claim` crea la rama de la tarea en tu worktree. Para otra tarea en paralelo, `claim --worktree` (excepción).
3. **No gestiones worktrees a mano**: nada de `git worktree add/remove` ni del worktree nativo de Claude Code; usa el script.
4. **Trabajo sin guardar**: el reciclado nunca lo borra; si lo hay, se para y avisa. Haz commit y push, o pregunta a Master.

## Comandos

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

Se lanza solo al final de `complete-task-pr`, en el siguiente `backlog.py claim`
y, en Claude Code, al iniciar sesión. Antigravity no tiene hook de inicio: si la
PR se fusionó más tarde, el reciclado ocurre en el siguiente `claim`.

## Relevo entre agentes

`backlog.py handoff` suelta la rama (`git switch --detach`) si el worktree está
limpio, para que el otro agente la abra en el suyo con `claim`. Git no permite
la misma rama en dos worktrees a la vez.

Manual: `doc/04-operations/runbooks/MANUAL_agent_worktrees.md`.
