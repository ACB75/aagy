---
name: ai-first-engineering
description: "Engineering operating model for t. Use when setting team process, review gates, or ownership rules for a codebase largely written by agents."
metadata:
  origin: AAGY
---

# AI-First Engineering

Use this skill when designing process, reviews, and architecture for teams shipping with AI-assisted code generation.

## Cuándo usarlo

Engineering operating model for t. Use when setting team process, review gates, or ownership rules for a codebase largely written by agents.

## Uso

Se carga sola cuando la tarea encaja con su `description`, o al pedirla por su nombre: `ai-first-engineering`.

## Reglas

- Si algo de aquí choca con `rules/AGENTS.md`, manda `rules/AGENTS.md`.
- No escribas datos de proyectos consumidores ni credenciales en el resultado.

## Process Shifts

1. Planning quality matters more than typing speed.
2. Eval coverage matters more than anecdotal confidence.
3. Review focus shifts from syntax to system behavior.

## Architecture Requirements

Prefer architectures that are agent-friendly:

- explicit boundaries
- stable contracts
- typed interfaces
- deterministic tests

Avoid implicit behavior spread across hidden conventions.

## Code Review in AI-First Teams

Review for:

- behavior regressions
- security assumptions
- data integrity
- failure handling
- rollout safety

Minimize time spent on style issues already covered by automation.

## Hiring and Evaluation Signals

Strong AI-first engineers:

- decompose ambiguous work cleanly
- define measurable acceptance criteria
- produce high-signal prompts and evals
- enforce risk controls under delivery pressure

## Testing Standard

Raise testing bar for generated code:

- required regression coverage for touched domains
- explicit edge-case assertions
- integration checks for interface boundaries

## Paridad

Claude Code: el mismo skill `ai-first-engineering` en el paquete `aagy-ecc-extras`, espejado desde la raíz por `sync_aagy_ecc.py`.
