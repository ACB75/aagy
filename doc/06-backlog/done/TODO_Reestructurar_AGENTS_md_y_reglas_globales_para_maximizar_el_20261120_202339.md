---
title: "**Reestructurar `AGENTS.md` y reglas globales para maximizar el hit-ratio del Gemini Context Caching**"
status: COMPLETED
completed_at: "2026-11-20 20:23:39"
---

# TODO: **Reestructurar `AGENTS.md` y reglas globales para maximizar el hit-ratio del Gemini Context Caching**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 20:23:39

### Detalle Original

- **01 - ROLE:** Gemini LLM Systems Performance & Context Caching Architect.
- **02 - CONTEXT:** `[Sector: LLM Runtime Optimization]` `[Data Type: Markdown rules (AGENTS.md, rules/AGENTS.md, .gemini/GEMINI.md)]` `[Objective: Reestructurar el contenido de AGENTS.md y reglas asociadas de manera que el prefijo del prompt permanezca 100% idéntico entre turnos y sesiones, permitiendo al compilador de contexto de Gemini 3.8 reutilizar los KV-caches y reducir la latencia TTFT en un 60%]` `[Restrictions: Preservar intactas todas las reglas de gobernanza, SRE y Trunk-Based]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Gemini 3.8 implementa *context caching* por coincidencia exacta de prefijo. Cualquier sección volátil colocada al inicio del prompt invalida toda la memoria de claves/valores posterior.
  - Las secciones dinámicas deben quedar delimitadas estrictamente al final del contexto del sistema.
- **04 - PHASE 2 (STRATEGY):**
  - *Enfoque A*: Mantener un único archivo grande y reordenar manualmente sus secciones.
  - *Enfoque B (Recomendado)*: Dividir la estructura conceptual de reglas en dos bloques: Bloque Estático Invariable (Google 5-Pillar, SRE, Trunk-Based, Stack Standards) y Bloque Contextual / Per-Project Rules.
- **05 - PHASE 3 (EXECUTION):**
    1. Auditar y reordenar `AGENTS.md` y `rules/AGENTS.md` asegurando que el bloque estático de alta densidad ocupe el prefijo continuo.
    2. Documentar la directiva de estabilidad de prefijos para desarrolladores en `doc/manual/`.
    3. Añadir test en `test_workspace_audit.py` que verifique la invariancia de prefijo de las reglas core.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Confirmar que el reordenamiento no altere la precedencia de evaluación de directivas en Antigravity ni confunda a los subagentes.
- **07 - PHASE 5 (FORMAT):**
  - Reglas formateadas, markdownlint validado y exit code `0` en tests.
- **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.000 tokens). Tarea de reordenamiento y formato.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Reestructuración binaria de AGENTS.md, marcador GEMINI CONTEXT CACHING, manual MANUAL_gemini_prompt_caching.md y test de invariancia.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/ecc/prompt-caching-static-reorder`
- **Commit SHA**: `aa83290`
- **Fecha**: `2026-11-20 20:23:39`
- **Gobernanza**: Quality Gate A / markdownlint OK
