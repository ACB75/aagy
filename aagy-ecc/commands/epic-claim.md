---
description: Take the next free task of an epic from the shared backlog (handoffs first), on its own branch or worktree.
---

# epic-claim

## Uso

```text
/epic-claim <id-épica> [--worktree]
```

## Qué hacer

1. Ejecuta `"${CLAUDE_PLUGIN_ROOT}/scripts/py/backlog.py" next --agent claude --epic <id-épica> --claim $ARGUMENTS`
   (añade `--worktree` si el usuario lo pide o si agy está trabajando a la vez en la misma carpeta).
2. Si la tarea viene de un relevo, lee `doc/06-backlog/quick/HANDOFF_<id>.md` y continúa desde ahí.
3. Cambia a la rama indicada (o abre el worktree) y sigue el flujo de `/aagy-todo`:
   `checkpoint` tras cada paso, `handoff` si te quedas sin presupuesto, `done` al verificar.
