---
name: promote
description: Promote project-scoped instincts to global scope
command: true
---

# Promote Command

Promote instincts and recurring candidates using the unified self-improvement engine (`scripts/py/self_improve.py`).

## Implementation

Run the unified self-improvement CLI from the repository root:

```bash
python3 scripts/py/self_improve.py --review [candidate-id] --repo-root .
python3 scripts/py/self_improve.py --promote [candidate-id] --confirm --repo-root .
```

## Usage

```bash
/promote                      # Auto-detect promotion candidates
/promote --dry-run            # Preview auto-promotion candidates
/promote --force              # Promote all qualified candidates without prompt
/promote grep-before-edit     # Promote one specific instinct from current project
```

## What to Do

1. Detect current project
2. If `instinct-id` is provided, promote only that instinct (if present in current project)
3. Otherwise, find cross-project candidates that:
   - Appear in at least 2 projects
   - Meet confidence threshold
4. Write promoted instincts to `~/.claude/homunculus/instincts/personal/` with `scope: global`
