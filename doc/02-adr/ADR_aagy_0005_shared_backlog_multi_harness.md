# ADR-0005: Backlog Compartido entre Claude Code y Antigravity

**Date**: 2026-11-21
**Status**: accepted
**Deciders**: Master
**Requisitos**: [`REQ_aagy_shared_backlog_multi_harness.md`](../06-backlog/plans/REQ_aagy_shared_backlog_multi_harness.md) · **Plan**: [`PLAN_aagy_shared_backlog_multi_harness.md`](../06-backlog/plans/PLAN_aagy_shared_backlog_multi_harness.md)

## Context

Claude Code (`aagy-ecc`) y Antigravity (`aagy`) trabajan en el mismo PC y en la misma carpeta, a veces a la vez y a veces por relevos, sobre todo cuando uno se queda sin tokens. Cada uno llevaba su lista de tareas dentro de su sesión (`TodoWrite` / `task.md`), invisible para el otro. `doc/06-backlog/TODO.md` ya era común, pero no decía quién tenía cada tarea ni dónde se había quedado.

## Decision

1. **Una fuente de verdad en el repo**: `TODO.md` define tareas y épicas (`## Épica: <título>`); cada tarea puede llevar `<!-- aagy-task: id=... epic=... -->`. Se descartan GitHub Issues y un servidor MCP de tareas: los dos agentes comparten máquina y carpeta.
2. **Estado vivo fuera de la rama**: dueño, estado, rama, último commit y nota viven en `$(git rev-parse --git-common-dir)/aagy-backlog/state.json`, común a todos los worktrees y no versionado. Así no hay conflictos de merge en `TODO.md` y los dos agentes ven el mismo estado al instante.
3. **CLI único** [`backlog.py`](../../scripts/py/backlog.py) (`list`, `next`, `claim`, `checkpoint`, `handoff`, `review`, `block`, `release`, `done`, `add`, `epic add|sync|close`, `init`) con lock por fichero `O_EXCL` y escritura atómica, espejado en `aagy-ecc` por `sync_aagy_ecc.py`.
4. **Modo simultáneo con worktrees**: `claim --worktree` crea `<repo>.wt/<id>` en su propia rama estándar (`feat/<proyecto>/<id>` por defecto).
5. **Relevo resistente a cortes**: checkpoint sin coste de tokens en cada `Stop` (ambos harnesses) y en `PreCompact`; relevo en `SessionEnd` (Claude Code); un claim sin actualizar durante 4 h (`AAGY_BACKLOG_TTL_HOURS`) queda libre.
6. **Superficie por harness**: `/aagy-todo` y `/epic-decompose|claim|sync|close` en `aagy-ecc`; skill `shared-backlog` (perfil `generic`) en ambos.

## Consequences

### Positive

- Cualquier agente puede continuar la tarea del otro con la nota `quick/HANDOFF_<id>.md`, la rama y el último commit.
- Funciona en cualquier repo del home-lab (`backlog.py init`) y sin red.
- Los comandos `epic-*` que citaban `dev-team` y `story-lifecycle` ya existen.

### Negative

- El estado vivo no queda en el historial git; el estado final se escribe en `TODO.md` (`- [x]`) y en `done/` al cerrar.
- Antigravity no tiene `PreCompact` ni `SessionEnd`, y su hook `Stop` usa la ruta relativa `scripts/py/` (solo dentro del repo aagy); fuera de él depende de la regla de checkpoint por paso y del TTL.

### Risks

- Un corte por límite de uso no ejecuta hooks: se mitiga con el checkpoint de cada turno y el TTL de 4 h.
