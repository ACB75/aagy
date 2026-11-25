# ADR-0006: Un Worktree Fijo por Agente y Reciclado tras el Merge

**Date**: 2026-11-22
**Status**: accepted
**Deciders**: Master
**Requisitos**: [`REQ_aagy_agent_worktrees.md`](../06-backlog/plans/REQ_aagy_agent_worktrees.md) · **Plan**: [`PLAN_aagy_agent_worktrees.md`](../06-backlog/plans/PLAN_aagy_agent_worktrees.md)

## Context

Master, Claude Code y Antigravity trabajaban en la misma carpeta (`<padre>\app`, `...\aagy`). Un cambio sin commit, un `checkout` o un `reset` de cualquiera afectaba a los otros dos. `backlog.py claim --worktree` ya creaba un worktree por tarea (`<repo>.wt/<id>`), pero la ruta cambiaba con cada tarea, Antigravity tenía que abrir una carpeta nueva cada vez y nada protegía el checkout de Master. Además, `complete-task-pr.ps1` terminaba con `git checkout -f main`, que falla dentro de un worktree (git no deja `main` en dos worktrees) y descarta cambios sin avisar.

## Decision

1. **Carpetas fijas hermanas del mismo clon**: `<repo>` es de Master; `<repo>-aagy` de Antigravity; `<repo>-aagy-ecc` de Claude Code. Patrón genérico: vale para `app`, `aagy` y cualquier repo consumidor. Los worktrees de agente nunca tienen `main` en checkout: reposan desacoplados en `origin/main`.
2. **CLI único** [`agent_worktree.py`](../../scripts/py/agent_worktree.py) (`init`, `where`, `status`, `recycle`, `guard`, `notice`), espejado en `aagy-ecc`.
3. **Reciclado limpio en sitio**: tras comprobar con `gh` que la PR está fusionada (squash: no basta con ancestros), `git switch --detach origin/main` + `reset --hard` + `clean -ffdx`. Si Windows no deja borrar algo, se recrea el worktree. Así la carpeta abierta en el IDE sigue siendo válida.
4. **Nunca se pierde trabajo**: si hay cambios sin commit, commits posteriores al último de la PR, commits sin push o stash de la rama, el reciclado se para y avisa (código 3).
5. **Configuración y generados**: los `.env` ignorados se copian del principal; `node_modules` y `.venv` se regeneran desde su lockfile, solo si el principal los tiene.
6. **Principal al día**: cada reciclado hace `merge --ff-only origin/main` en el principal si está en `main` y sin cambios; si no, lo deja y avisa. Sin tareas programadas.
7. **Guarda dura**: hooks PreToolUse en ambos harnesses deniegan escrituras y comandos que modifican fuera del worktree propio, `git worktree add|remove|move` a mano y el worktree nativo de Claude Code. Se activa con el marcador `$(git common dir)/aagy-worktrees.json`.
8. **Disparadores**: final de `complete-task-pr` (espera hasta 120 s al merge), siguiente `backlog.py claim` o `done` y, en Claude Code, `SessionStart`.

## Consequences

### Positive

- Master puede tener su checkout con cambios sin miedo a que un agente los pise, y se le actualiza solo.
- Antigravity y Claude abren siempre la misma carpeta.
- El relevo funciona: `handoff` suelta la rama y el otro agente la abre en su worktree.

### Negative

- Un agente hace una tarea a la vez en su worktree (`claim --worktree` sigue como excepción).
- Regenerar dependencias tras cada merge cuesta tiempo (`--no-install` para saltarlo).
- La guarda de comandos es heurística: un script puede escribir donde quiera. La regla Tier 1 completa la protección.

### Alternatives Considered

- **Borrado físico siempre**: falla en Windows si la carpeta está abierta en el IDE.
- **Clones separados por agente**: duplican `.git` y rompen el estado común del backlog.
- **Worktree nativo de Claude Code** (`.claude/worktrees/`): ramas `worktree-*` fuera de la convención y sin equivalente en Antigravity.
