---
description: Show progress of epics in the shared backlog - tasks per state, owners (claude/agy) and pending handoffs.
---

# epic-sync

## Uso

```text
/epic-sync [<id-épica>]
```

## Qué hacer

1. Ejecuta `"${CLAUDE_PLUGIN_ROOT}/scripts/py/backlog.py" epic sync $ARGUMENTS`.
2. Resume en español: por épica, cuántas tareas hay en cada estado, quién tiene las
   que están en curso, qué relevos esperan y qué está bloqueado (con su nota, usando
   `backlog.py list --epic <id>`).
