---
title: "**Mover `doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` a `doc/adr/TEMPLATE_ADR.md` y renombrar `doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md` a `doc/post-mortem/TEMPLATE_POSTMORTEM.md`**"
status: COMPLETED
completed_at: "2026-11-20 20:49:54"
---

# TODO: **Mover `doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` a `doc/adr/TEMPLATE_ADR.md` y renombrar `doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md` a `doc/post-mortem/TEMPLATE_POSTMORTEM.md`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 20:49:54

### Detalle Original

- **01 - ROLE:** Documentation Governance Architect & Repository Hygiene Specialist.
- **02 - CONTEXT:** `[Sector: Documentation Spine & Governance]` `[Data Type: Markdown templates, .governance/docs-map.json, scripts/skills references]` `[Objective: Mover doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md a doc/adr/TEMPLATE_ADR.md y renombrar doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md a doc/post-mortem/TEMPLATE_POSTMORTEM.md manteniendo cero enlaces rotos]` `[Restrictions: Actualizar todas las referencias en scripts, skills, reglas, INDEX.md y docs-map.json; verificar con audit-workspace.ps1 y lint-markdown.ps1]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Actualmente las plantillas de ADR/Requisitos y Post-Mortem tienen nombres y ubicaciones inconsistentes (`doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` suelto en `doc/` y `TEMPLATE_POSTMORTEM_5W.md` en `doc/post-mortem/`).
  - Mover o renombrar archivos sin actualizar referencias rompe `.governance/docs-map.json`, scripts de automatización y enlaces Markdown.
- **04 - PHASE 2 (STRATEGY):**
  - Localizar todas las referencias con búsqueda global (`Select-String` / `git grep`) antes de mover/renombrar usando `git mv`.
  - Actualizar referencias en scripts, skills, `doc/INDEX.md` y `.governance/docs-map.json`.
- **05 - PHASE 3 (EXECUTION):**
    1. Ejecutar `git mv doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md doc/adr/TEMPLATE_ADR.md` y `git mv doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md doc/post-mortem/TEMPLATE_POSTMORTEM.md`.
    2. Actualizar todas las referencias detectadas en `scripts/`, `skills/`, `doc/` y `.governance/docs-map.json`.
    3. Validar con `lint-markdown.ps1`, `audit-workspace.ps1` y `pytest` (exit code `0`).
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Verificar que ningún test unitario ni skill (`architecture-decision-records`, `todo-lifecycle`, `lifecycle-coordinator`) apunte a los nombres anteriores.
- **07 - PHASE 5 (FORMAT):**
  - Rutas renombradas con `git mv`, cero enlaces rotos y auditoría completa en verde.
- **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~800 tokens).
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Mover doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md a doc/adr/TEMPLATE_ADR.md y TEMPLATE_POSTMORTEM_5W.md a TEMPLATE_POSTMORTEM.md

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `refactor/ecc/doc-templates-standardization`
- **Commit SHA**: `0fb1a8f`
- **Fecha**: `2026-11-20 20:49:54`
- **Gobernanza**: Quality Gate A / markdownlint OK
