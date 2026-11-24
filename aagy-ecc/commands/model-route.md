---
description: Recommend the best model tier for the current task based on complexity, risk, and budget.
---

# Model Route Command

Recommend the best model tier for the current task by complexity and budget.

## Usage

`/model-route [task-description] [--budget low|med|high]`

## Routing Heuristic

- `haiku`: deterministic, low-risk mechanical changes
- `sonnet`: default for implementation and refactors
- `opus`: architecture, deep review, ambiguous requirements
- `local`: only when the `aagy-local` MCP server is available (`local_status` mode `tool`) and the task is one of its catalog tasks (classify, summarize, extract, translate, complete); run it with `local_run`. Private files always go here with `paths`.

## Required Output

- recommended model
- confidence level
- why this model fits
- fallback model if first attempt fails

## Arguments

$ARGUMENTS:

- `[task-description]` optional free-text
- `--budget low|med|high` optional
