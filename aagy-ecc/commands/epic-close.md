---
description: Close an epic in the shared backlog once all its tasks are done.
---

# epic-close

## Uso

```text
/epic-close <id-épica>
```

## Qué hacer

1. Ejecuta `"${CLAUDE_PLUGIN_ROOT}/scripts/py/backlog.py" epic close <id-épica> --agent claude`.
2. Si falla porque quedan tareas sin terminar, enséñalas (`epic sync <id-épica>`) y no fuerces el cierre.
3. Si cierra, propón archivar lo que quede marcado con `archive_todo.py --all-completed`.
