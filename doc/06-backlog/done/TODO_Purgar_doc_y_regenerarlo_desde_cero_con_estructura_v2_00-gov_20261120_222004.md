---
title: "**Purgar `/doc` y regenerarlo desde cero con estructura v2 (`00-governance`..`06-backlog`, `<folder>/dgrms/`), parametrizar scripts y garantizar paridad manual $\leftrightarrow$ plugin**"
status: COMPLETED
completed_at: "2026-11-20 22:20:04"
---

# TODO: **Purgar `/doc` y regenerarlo desde cero con estructura v2 (`00-governance`..`06-backlog`, `<folder>/dgrms/`), parametrizar scripts y garantizar paridad manual $\leftrightarrow$ plugin**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 22:20:04

### Detalle Original

- **01 - ROLE:** Documentation Governance & Developer Experience Architect.
- **02 - CONTEXT:** `[Sector: Documentation Architecture & CLI Workflow Parity]` `[Data Type: /doc v2, .governance/docs-map.json, scripts/{py,sh,pwsh}, diagramas .puml/.bpmn/.mmd]` `[Objective: Purgar doc/plan/ y documentación obsoleta que no siga convención; regenerar /doc v2 (raíz solo INDEX.md, CONTEXT.md, STATUS.md, LOG.md; 00-governance a 06-backlog; dgrms/ en todas las carpetas con diagramas; the-security-guide.md conservado y STACK_MODERNO_GOOGLE.md renombrado a google-modern-stack.md); parametrizar rutas vía .governance/docs-map.json con fallback retrocompatible para home-lab; habilitar flujo flexible [IDEAS -> REQUISITOS -> PLAN -> TODO] y paridad 1-a-1 manual]` `[Restrictions: Zero-Breaking con home-lab mediante fallback; validar rutas contra path traversal; ver REQ_doc_structure_v2_and_manual_parity.md]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Ver requisitos aprobados en [`REQ_doc_structure_v2_and_manual_parity.md`](../plans/REQ_doc_structure_v2_and_manual_parity.md).
- **04 - PHASE 2 (STRATEGY):**
  - Implementar resolvedor `.governance/docs-map.json` con fallback $\rightarrow$ migrar/regenerar `/doc` v2 $\rightarrow$ documentar `DOC_STANDARDS.md` y `MANUAL_WORKFLOW.md`.
- **05 - PHASE 3 (EXECUTION):**
    1. Implementar resolvedor de rutas + tests unitarios.
    2. Purgar `doc/` heredado y regenerar árbol `/doc` v2 rescatando ADRs (`02-adr/`), `the-security-guide.md`, `google-modern-stack.md` y plantillas renombradas (`TEMPLATE_ADR.md`, `TEMPLATE_POSTMORTEM.md`).
    3. Actualizar scripts para flujo flexible y paridad CLI manual, verificando `pytest` y `lint-markdown.ps1` (exit `0`).
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Confirmar que `home-lab` sigue operando sin errores gracias al *fallback* y que `complete-task-pr.ps1` mantiene el gate de `pytest` verde.
- **07 - PHASE 5 (FORMAT):**
  - Árbol `/doc` v2 limpio, cero enlaces rotos y tests en verde.
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens); **Carbon ($C_6$)** para scripts y tests.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `refactor/doc/structure-v2-and-parity`
- **Commit SHA**: `aeb8095`
- **Fecha**: `2026-11-20 22:20:04`
- **Gobernanza**: Quality Gate A / markdownlint OK
