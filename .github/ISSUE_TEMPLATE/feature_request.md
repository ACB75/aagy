---
name: Feature Request (feat)
about: Proponer una nueva funcionalidad o capacidad para aagy / aagy-ecc
title: "[feat]-[aagy,aagy-ecc]: "
labels:
  - enhancement
  - harness:both
assignees:
  - ACB75
---

# Feature Request (`feat/*`)

## 1. Motivación y Contexto

Describe el problema o necesidad operativa en el ecosistema `aagy` (Antigravity) y `aagy-ecc` (Claude Code).

## 2. Requisitos Funcionales y Criterios de Aceptación (Given / When / Then)

- **Given**: contexto inicial.
- **When**: acción o comando ejecutado.
- **Then**: resultado observable y código de salida (`exit 0`).

## 3. Alcance y Paridad Multi-Harness (`aagy <-> aagy-ecc`)

- [ ] Aplica a `aagy` (Google Antigravity / Gemini)
- [ ] Aplica a `aagy-ecc` (Claude Code)
- [ ] Requiere espejo automático en `scripts/py/sync_aagy_ecc.py`
- [ ] Respeta presupuesto de tokens (`description <= 140c` en skills, `<= 120c` en subagentes, `rules/AGENTS.md <= 12 KB`)

## 4. Artefactos de Lifecycle Vinculados

- **Requisitos (`Fase 1`)**: `doc/06-backlog/plans/REQ_<slug>.md`
- **Plan TDD (`Fase 2`)**: `doc/06-backlog/plans/PLAN_<slug>.md`
- **ADR (si aplica)**: `doc/02-adr/ADR_aagy_NNNN_<slug>.md`
