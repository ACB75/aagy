---
title: "**Implementar utilidades CLI para activar y desactivar dinámicamente skills especializadas de Tier 2 en el plugin activo**"
status: COMPLETED
completed_at: "2026-11-20 20:42:08"
---

# TODO: **Implementar utilidades CLI para activar y desactivar dinámicamente skills especializadas de Tier 2 en el plugin activo**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 20:42:08

### Detalle Original

- **01 - ROLE:** Modular Plugin Architect & CLI Ergonomics Engineer.
- **02 - CONTEXT:** `[Sector: AI Agent Plugin Management]` `[Data Type: PowerShell & Bash scripts, directory synchronization]` `[Objective: Proporcionar un comando rápido y seguro que permita al desarrollador promover temporalmente una skill de Tier 2 (ej. chrome-devtools, generative_ui, a11y-debugging) a la carpeta activa del plugin (~/.gemini/config/plugins/ecc-agy/skills/) para una tarea concreta, y retirarla al finalizar]` `[Restrictions: No comprometer archivos temporales en el repositorio Git; validar límites <= 140c de frontmatter en la skill promovida]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Contamos con 170 skills en el repositorio pero solo 22 en el plugin activo para mantener el presupuesto siempre activo en ~945 tokens.
  - Cuando surge una tarea puntual que requiere una skill especializada (ej. depuración de memoria o UI generativa), el desarrollador debe copiar la carpeta manualmente o recargar el plugin completo.
- **04 - PHASE 2 (STRATEGY):**
  - `enable-skill.ps1 -Name <skill>` valida que la skill exista en `skills/`, comprueba su frontmatter y la copia a la carpeta de plugin activo, registrándola en `.active_promotions.json`.
  - `disable-skill.ps1 -Name <skill>` elimina la copia del plugin activo y restaura el estado limpio.
- **05 - PHASE 3 (EXECUTION):**
    1. Implementar `scripts/bin/ecc-agy/enable-skill.ps1` y `.sh`.
    2. Implementar `scripts/bin/ecc-agy/disable-skill.ps1` y `.sh`.
    3. Añadir validación estricta de frontmatter y comprobación de presupuesto con `workspace_audit.py`.
    4. Crear batería de tests unitarios en `test_skill_promotion.py`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Evitar que la promoción de una skill sobrescriba accidentalmente una skill core de Tier 1 o que quede huérfana tras un crash de la sesión.
- **07 - PHASE 5 (FORMAT):**
  - Scripts documentados, con validación de parámetros y mensajes estructurados.
- **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.100 tokens).
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

CLI skill_promotion.py, enable-skill.ps1/sh, disable-skill.ps1/sh, registro .active_promotions.json y manual MANUAL_skill_promotion.md

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/ecc/skill-promotion-cli`
- **Commit SHA**: `e0a8de9`
- **Fecha**: `2026-11-20 20:42:08`
- **Gobernanza**: Quality Gate A / markdownlint OK
