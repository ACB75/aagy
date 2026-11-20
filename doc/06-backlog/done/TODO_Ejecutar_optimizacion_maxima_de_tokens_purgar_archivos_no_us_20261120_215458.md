---
title: "**Ejecutar optimización máxima de tokens, purgar archivos no usados, unificar skills/agents/rules duplicados y reestructurar `scripts/{py,sh,pwsh}/tests/`**"
status: COMPLETED
completed_at: "2026-11-20 21:54:58"
---

# TODO: **Ejecutar optimización máxima de tokens, purgar archivos no usados, unificar skills/agents/rules duplicados y reestructurar `scripts/{py,sh,pwsh}/tests/`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 21:54:58

### Detalle Original

- **01 - ROLE:** Principal Agentic Runtime & Token Budget Optimizer (experto en compresión de system prompts, poda de contexto y arquitectura modular de plugins Antigravity / Claude Code).
- **02 - CONTEXT:** `[Sector: Token Optimization & Plugin Architecture]` `[Data Type: rules/ (39 archivos), skills/ (263), agents/ (49), commands/ (97), scripts/ (192)]` `[Objective: (1) Eliminar duplicación entre rules/AGENTS.md y <repo>/AGENTS.md; (2) Dejar en rules/ únicamente AGENTS.md + pr-automerge-lifecycle.md, moviendo las 37 reglas de lenguaje/stack a skills lazy-loaded (unificando duplicados/similares); (3) Purgar skills/agents/commands muertos o redundantes unificando similares y separando Core Tier-1 vs Tier-2; (4) Reestructurar scripts/ en scripts/py/ (+ /tests), scripts/sh/ (+ /tests) y scripts/ps1/ (+ /tests)]` `[Restrictions: Cero pérdida de cobertura (pytest >= 80% en verde); cero incremento en reglas siempre activas; mantener presupuesto rules <= 24 KB/archivo y <= 20k tokens agregados]`.
- **03 - PHASE 1 (ANALYSIS):**
  - El plugin actual carga `39` archivos en `rules/` en cada turno y duplica `AGENTS.md`, mientras el repo arrastra `263` skills, `49` agentes, `97` comandos legacy y `192` scripts mezclados en `scripts/aagy/` y `scripts/bin/aagy/`.
- **04 - PHASE 2 (STRATEGY):**
  - Auditar uso real, unificar duplicados/similares en `skills/`, `agents/` y `rules/`, migrar guías de stack a skills lazy-loaded, purgar artefactos muertos y reorganizar `scripts/` por runtime (`py/`, `sh/`, `ps1/`) con su propia subcarpeta `tests/`.
- **05 - PHASE 3 (EXECUTION):**
    1. Deduplicar `AGENTS.md` y migrar las `37` reglas de stack a skills lazy-loaded unificadas.
    2. Unificar y podar `skills/`, `agents/` y `commands/` dejando solo Core Tier-1 + catálogo Tier-2 limpio.
    3. Reorganizar `scripts/` en `scripts/py/tests/`, `scripts/sh/tests/` y `scripts/ps1/tests/` actualizando invocaciones en `hooks.json` y skills.
    4. Ejecutar `pytest`, `audit-workspace.ps1` y `lint-markdown.ps1` con código de salida `0`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Verificar que ningún hook o skill activo rompa rutas tras mover `scripts/bin/aagy/` $\rightarrow$ `scripts/ps1/` / `scripts/sh/` / `scripts/py/`.
- **07 - PHASE 5 (FORMAT):**
  - Plugin ordenado, consumo mínimo de tokens en `rules/` y `customizations`, y tests 100% en verde.
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens) para poda y unificación; **Carbon ($C_6$)** para migración de rutas y tests.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `refactor/aagy/token-opt-and-scripts-reorg`
- **Commit SHA**: `29d39c1`
- **Fecha**: `2026-11-20 21:54:58`
- **Gobernanza**: Quality Gate A / markdownlint OK
