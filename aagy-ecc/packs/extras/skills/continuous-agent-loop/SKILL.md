---
name: continuous-agent-loop
description: "Patterns for continuous autonomous agent loo. Use when running an agent loop that must self-check, gate on evals, and recover from failures."
metadata:
  origin: AAGY
---

# Continuous Agent Loop

This is the v1.8+ canonical loop skill name. It supersedes `autonomous-loops` while keeping compatibility for one release.

## Cuándo usarlo

Patterns for continuous autonomous agent loo. Use when running an agent loop that must self-check, gate on evals, and recover from failures.

## Uso

Se carga sola cuando la tarea encaja con su `description`, o al pedirla por su nombre: `continuous-agent-loop`.

## Qué hacer

Sigue las secciones de abajo en orden: Loop Selection Flow, Combined Pattern, Failure Modes, Recovery.

## Reglas

- Si algo de aquí choca con `rules/AGENTS.md`, manda `rules/AGENTS.md`.
- No escribas datos de proyectos consumidores ni credenciales en el resultado.

## Loop Selection Flow

```text
Start
  |
  +-- Need strict CI/PR control? -- yes --> continuous-pr
  |
  +-- Need RFC decomposition? -- yes --> rfc-dag
  |
  +-- Need exploratory parallel generation? -- yes --> infinite
  |
  +-- default --> sequential
```

## Combined Pattern

Recommended production stack:

1. RFC decomposition (`ralphinho-rfc-pipeline`)
2. quality gates (`plankton-code-quality` + `/quality-gate`)
3. eval loop (`agent-self-evaluation`)
4. session persistence (`nanoclaw-repl`)

## Failure Modes

- loop churn without measurable progress
- repeated retries with same root cause
- merge queue stalls
- cost drift from unbounded escalation

## Recovery

- freeze loop
- run `/harness-audit`
- reduce scope to failing unit
- replay with explicit acceptance criteria

## Paridad

Claude Code: el mismo skill `continuous-agent-loop` en el paquete `aagy-ecc-extras`, espejado desde la raíz por `sync_aagy_ecc.py`.
