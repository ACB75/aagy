---
name: safety-guard
description: "Block destructive rm, drop, firewall flush, or purge commands."
metadata:
  origin: AAGY
---

# Safety Guard — Prevent Destructive Operations


## Uso

Se carga sola cuando la tarea encaja con su `description`, o al pedirla por su nombre: `safety-guard`.

## Reglas

- Si algo de aquí choca con `rules/AGENTS.md`, manda `rules/AGENTS.md`.
- No escribas datos de proyectos consumidores ni credenciales en el resultado.
## When to Use

- When working on production systems
- When agents are running autonomously (full-auto mode)
- When you want to restrict edits to a specific directory
- During sensitive operations (migrations, deploys, data changes)

## How It Works

Three modes of protection:

### Mode 1: Careful Mode

Intercepts destructive commands before execution and warns:

```
Watched patterns:
- rm -rf (especially /, ~, or project root)
- git push --force
- git reset --hard
- git checkout . (discard all changes)
- DROP TABLE / DROP DATABASE
- docker system prune
- kubectl delete
- chmod 777
- sudo rm
- npm publish (accidental publishes)
- Any command with --no-verify
```

When detected: shows what the command does, asks for confirmation, suggests safer alternative.

### Mode 2: Freeze Mode

Locks file edits to a specific directory tree:

```
/safety-guard freeze src/components/
```

Any Write/Edit outside `src/components/` is blocked with an explanation. Useful when you want an agent to focus on one area without touching unrelated code.

### Mode 3: Guard Mode (Careful + Freeze combined)

Both protections active. Maximum safety for autonomous agents.

```
/safety-guard guard --dir src/api/ --allow-read-all
```

Agents can read anything but only write to `src/api/`. Destructive commands are blocked everywhere.

### Unlock

```
/safety-guard off
```

## Implementation

Uses PreToolUse hooks to intercept Bash, Write, Edit, and MultiEdit tool calls. Checks the command/path against the active rules before allowing execution.

## Integration

- Enable by default for `codex -a never` sessions
- Pair with observability risk scoring in AAGY 2.0
- Logs all blocked actions to `~/.claude/safety-guard.log`

## Paridad

Claude Code: el mismo skill `safety-guard` en el núcleo de `aagy-ecc`, espejado desde la raíz por `sync_aagy_ecc.py`.
