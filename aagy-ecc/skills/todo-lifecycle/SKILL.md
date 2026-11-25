---
name: todo-lifecycle
description: "Shape TODO.md tasks with the common sections and archive completed items."
metadata:
  origin: AAGY
---

# todo-lifecycle

Formato de las tareas de `TODO.md` y archivado de las completadas en `todo_done` (ruta de `.governance/docs-map.json`, normalmente `doc/06-backlog/done/`).

## Cuándo usarlo

- Al añadir o refinar tareas en `TODO.md`.
- Al marcar una tarea como hecha (`- [x]`).
- Para dejar `TODO.md` solo con tareas pendientes.

## Uso

```bash
python <PLUGIN>/scripts/py/archive_todo.py --all-completed --notes "<cómo se verificó>"
python <PLUGIN>/scripts/py/archive_todo.py --complete "<título>" --notes "<entregable>"
python <PLUGIN>/scripts/py/backlog.py gh-sync --check
```

Envoltorios: `<PLUGIN>/scripts/ps1/aagy.ps1 archive-todo` y `<PLUGIN>/scripts/sh/aagy.sh archive-todo`.

## Qué hacer

1. Una tarea es `- [ ] **Título**` seguida de `<!-- aagy-task: id=... epic=... issue=N deps=a,b -->`.
2. Su issue (o su nota `QUICK_`) lleva las secciones comunes: Motivación, Criterios de aceptación, Paridad y Artefactos.
3. Al terminar, marca `[x]` y archiva con `archive_todo.py`.

## Reglas

1. Nunca dejes tareas `[x]` en `TODO.md`.
2. Archiva siempre con el script (`TODO_<título>_<fecha>.md`), que resuelve las rutas con `docs_map.py`.
3. Toda issue abierta tiene su tarea y al revés (`gh-sync --check`).

## Paridad

Claude Code: la skill se espeja en `aagy-ecc`; `/aagy-todo` usa el mismo backlog. Mismos scripts.
