---
title: "**Unificar y optimizar `auto-evolve`, `instinct_manager`, `agent-self-evaluation` y skills de aprendizaje continuo en un motor único para `aagy`**"
status: COMPLETED
completed_at: "2026-11-20 22:40:17"
---

# TODO: **Unificar y optimizar `auto-evolve`, `instinct_manager`, `agent-self-evaluation` y skills de aprendizaje continuo en un motor único para `aagy`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 22:40:17

### Detalle Original

- **01 - ROLE:** Autonomous Agent Reliability & Self-Improvement Systems Architect.
- **02 - CONTEXT:** `[Sector: Agent Self-Discovery & Continuous Learning]` `[Data Type: auto-evolve, instinct_manager.py, hooks.json, skills de evaluación/aprendizaje]` `[Objective: Unificar las piezas sueltas de autodescubrimiento y automejora en un flujo determinista y acotado en presupuesto para aagy]` `[Restrictions: Toma de requisitos dedicada previa a la implementación; cero inflación de AGENTS.md/rules/; promoción segura con smoke-test y gate de presupuesto]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Existen piezas desconectadas (`auto-evolve.ps1` orientado a `app`, `instinct_manager.py`, skills legacy `continuous-learning-v2` / `eval-harness` / `agent-self-evaluation`).
  - Ver requisitos aprobados en [`REQ_aagy_unified_self_improvement.md`](../plans/REQ_aagy_unified_self_improvement.md).
- **04 - PHASE 2 (STRATEGY):**
  - Definir requisitos formales primero y consolidar un único motor agnóstico conectado al ciclo de vida y presupuesto.
- **05 - PHASE 3 (EXECUTION):**
    1. Completar toma de requisitos (`REQ_`).
    2. Unificar módulos y eliminar redundancias.
    3. Validar con `pytest` y `audit-workspace.ps1` (exit `0`).
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Evitar auto-generación de reglas/skills que desborden el presupuesto de tokens.
- **07 - PHASE 5 (FORMAT):**
  - Motor unificado, documentado y cubierto por tests.
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens); **Carbon ($C_6$)** para implementación.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/aagy/unified-self-improvement`
- **Commit SHA**: `736d577`
- **Fecha**: `2026-11-20 22:40:17`
- **Gobernanza**: Quality Gate A / markdownlint OK
