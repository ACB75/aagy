---
description: Split an approved REQ/PLAN or goal into an epic of atomic tasks in the shared TODO.md, ready for Claude or agy to claim.
---

# epic-decompose

Crea una épica en el backlog compartido y la parte en tareas atómicas que Claude o
Antigravity pueden reclamar.

## Cuándo usarlo

Con un REQ o PLAN aprobado, o un objetivo grande que no cabe en una sola PR.

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
4. Por cada tarea, en orden: `backlog.py add "<título>" --epic <id-épica> --issue <N>`. La issue
   lleva las secciones comunes (Motivación, Criterios de aceptación, Paridad, Artefactos).
5. Muestra `backlog.py epic sync <id-épica>` y di qué tarea puede empezar cada agente.

## Reglas

- Una tarea es una rama y una PR. No crees tareas sin el visto bueno del usuario.
- Toda tarea con issue apunta a una issue abierta (`backlog.py gh-sync --check`).

## Paridad

Antigravity: skill `shared-backlog` (sección Épicas).
