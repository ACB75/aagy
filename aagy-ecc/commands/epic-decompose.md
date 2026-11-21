---
description: Split an approved REQ/PLAN or goal into an epic of atomic tasks in the shared TODO.md, ready for Claude or agy to claim.
---

# epic-decompose

Crea una épica (objetivo grande) en el backlog compartido y la parte en tareas
atómicas que Claude o Antigravity pueden reclamar. Equivale a la sección "Épicas"
de la skill `shared-backlog`.

## Uso

```text
/epic-decompose doc/06-backlog/plans/PLAN_<id>.md
/epic-decompose "<objetivo en una frase>"
```

## Qué hacer

Script: `"${CLAUDE_PLUGIN_ROOT}/scripts/py/backlog.py"` (o `scripts/py/backlog.py` en el repo aagy).

1. Lee el `REQ_`/`PLAN_` indicado (o pide uno si el objetivo es ambiguo y no hay plan).
2. Propón al usuario la lista de tareas: atómicas (una rama y un PR cada una), en orden
   de dependencias, cada una con su criterio de "hecho". Espera su visto bueno.
3. Crea la épica: `backlog.py epic add "<título>" --objective "<objetivo>"`.
4. Por cada tarea, en orden: `backlog.py add "<título>" --epic <id-épica> --detail "<7 fases>"`,
   con las 7 fases de `todo-lifecycle` (ROLE, CONTEXT, ANALYSIS, STRATEGY, EXECUTION, CRITIC, FORMAT).
5. Muestra `backlog.py epic sync <id-épica>` y di qué tarea puede empezar cada agente.
