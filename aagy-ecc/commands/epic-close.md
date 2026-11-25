---
description: Close an epic in the shared backlog once all its tasks are done.
---

# epic-close

## Cuándo usarlo

Cuando todas las tareas de una épica están hechas.

## Uso

```text
/epic-close <id-épica>
```

## Qué hacer

1. Ejecuta `"${CLAUDE_PLUGIN_ROOT}/scripts/py/backlog.py" epic close <id-épica> --agent claude`.
2. Si falla porque quedan tareas sin terminar, enséñalas con `epic sync <id-épica>`.
3. Si cierra, propón archivar lo que quede marcado con `archive_todo.py --all-completed`.

## Reglas

- No fuerces el cierre de una épica con tareas pendientes.

## Paridad

Antigravity: skill `shared-backlog` (sección Épicas, `backlog.py epic close`).
