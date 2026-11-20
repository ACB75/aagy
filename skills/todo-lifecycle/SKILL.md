---
name: todo-lifecycle
description: "Transform tasks with 7-phase meta-prompt, archive completed TODOs into /TODO_DONE/, and prune active list."
metadata:
  origin: ECC-AGY
---

# TODO Lifecycle, Meta-Prompt Transformation & Completed Tasks Archive

Operational workflow to formulate tasks using the rigorous 7-phase meta-prompt, manage task completion in `TODO.md`, and archive completed items (`- [x]`) into the `todo_done` target resolved via `.governance/docs-map.json` (`doc/06-backlog/done/` or legacy `TODO_DONE/`).

## When to Use

- Whenever formulating or refining tasks to be added to `TODO.md`.
- Whenever a task in `TODO.md` is marked as completed (`- [x]`).
- Cleaning and pruning `TODO.md` so it contains only active or pending tasks (`- [ ]`).
- Generating audit-ready completion records under `done/` or legacy `TODO_DONE/`.

## Non-Negotiable Rules

1. **7-Phase Meta-Prompt Transformation**: Every task point must undergo the 7-phase transformation (Role of top 3-5 experts, Context with `[IN BRACKETS]`, Phase 1 Analysis, Phase 2 Strategy with 3 lateral approaches, Phase 3 Execution, Phase 4 Devil's Advocate Critic, Phase 5 Strict Format, and Golden Rule).
2. **Clean TODO.md**: Never leave completed items (`- [x]`) lingering in the primary `TODO.md`.
3. **Deterministic Archival**: Always delegate to canonical script `scripts/pwsh/archive-todo.ps1` (Windows) or `archive-todo.sh` (Linux), which auto-resolve routes via `docs_map.py`.
4. **Safe Slugs & Timestamps**: Ensure archived files follow `TODO_<title>_<timestamp>.md`.

## Commands

### Meta-Prompt Transformation

```powershell
# Generar transformación de 7 fases para una tarea
pwsh -NoProfile -File scripts/pwsh/transform-todo.ps1 -Task "Refactor de persistencia en caché Ignite"

# Validar cumplimiento en un documento Markdown
pwsh -NoProfile -File scripts/pwsh/transform-todo.ps1 -Validate doc/plan.md
```

### Archival of Completed Tasks

```powershell
# Archivar todas las tareas completadas en TODO.md
pwsh -NoProfile -File scripts/pwsh/archive-todo.ps1 -AllCompleted

# Archivar una tarea específica con notas de entregable
pwsh -NoProfile -File scripts/pwsh/archive-todo.ps1 -Complete "Configurar TLS" -Notes "Emitido certificado SAN y verificado en proxy."
```

### Linux / Debian (Bash)

```bash
scripts/sh/transform-todo.sh --task "Refactor de persistencia"
scripts/sh/archive-todo.sh --all-completed
```
