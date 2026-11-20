---
title: "**Implementar guardrail bloqueante de presupuesto de contexto (`rules` y `customizations`)**"
status: COMPLETED
completed_at: "2026-11-20 19:56:06"
---

# TODO: **Implementar guardrail bloqueante de presupuesto de contexto (`rules` y `customizations`)**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 19:56:06

### Detalle Original

- **01 - ROLE:** Principal AI Harness Architect & Context Budget Engineer (experto en optimización de *system prompts*, descubrimiento progresivo de plugins en Antigravity y *Quality Gates* deterministas en Python/PowerShell).
- **02 - CONTEXT:** `[Sector: AI Agent Governance & Context Optimization]` `[Data Type: Python stdlib CLI, JSON configs (mcp_config.json, plugin.json), Markdown (AGENTS.md, SKILL.md)]` `[Objective: Garantizar mediante un Quality Gate bloqueante que ninguna regla, skill, subagente o servidor MCP activo exceda jamás los límites de presupuesto de Antigravity (24 KB/archivo y 20.000 tokens en rules; umbral estricto en customizations eager)]` `[Restrictions: Cero dependencias externas en Python (stdlib pura); compatibilidad con audit-workspace.ps1 y complete-task-pr]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Actualmente `workspace_audit.py` valida `<= 140` chars en skills y `<= 120` chars en agentes, pero no inspecciona `mcp_config.json` ni el tamaño agregado de `AGENTS.md` / `GEMINI.md` frente al `defaultRulesBudget` (20.000 tokens / 24.000 bytes por archivo) ni la inyección *eager* de herramientas MCP en el *customization budget*.
  - Un servidor MCP como `gemini-mcp` (30+ tools) habilitado por defecto añade ~4.500–10.000+ tokens fijos por turno.
- **04 - PHASE 2 (STRATEGY):**
  - *Enfoque A (Estático puro)*: Estimar tokens (`len / 4` o heurística conservadora) sobre `AGENTS.md`, skills Tier 1, agentes activos y conteo de servidores/tools declarados en `mcp_config.json` activos (`disabled != true`).
  - *Enfoque B (Manifiesto + Caché)*: Mantener un manifiesto de huella estimada por MCP conocido cuando el servidor no expone esquema estático, bloqueando cualquier MCP activo no declarado o sin `"disabled": true` cuando supere el umbral.
  - *Enfoque C (Híbrido recomendado)*: Combinar validación estricta de `rules` (`<= 24.000` bytes/archivo y techo seguro `<= 16.000` tokens agregados) + validación de `customizations` (`Tier 1 + MCP activos <= MAX_EAGER_CUSTOMIZATION_TOKENS`) exigiendo `"disabled": true` en plugins pesados.
- **05 - PHASE 3 (EXECUTION):**
    1. Extender `scripts/aagy/workspace_audit.py` con auditoría de `rules` (bytes por archivo y tokens agregados) y de `mcp_config.json` en plugins activos (`disabled != true`).
    2. Definir constantes explícitas de presupuesto máximo y devolver código de salida distinto de `0` ante cualquier violación.
    3. Añadir pruebas unitarias en `scripts/aagy/tests/test_workspace_audit.py` cubriendo casos límite (archivo > 24 KB, rules > presupuesto, MCP pesado habilitado por defecto).
    4. Ejecutar `pytest` y `audit-workspace.ps1` para verificar exit code `0`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: ¿Qué pasa si un `mcp_config.json` usa `npx` y no tiene caché local de schemas? Contabilizar un coste mínimo conservador por servidor activo y exigir opt-in explícito para servidores pesados (`gemini-mcp`), evitando falsos negativos.
- **07 - PHASE 5 (FORMAT):**
  - Código Python tipado (`stdlib`), reporte estructurado en tabla/resumen y suite `pytest` con cobertura >= 80%.
- **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.200 tokens de razonamiento). Tarea de ingeniería pura en Python sin necesidad de Pro Thinking.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Hard gate implementado en workspace_audit.py, SonarQube Rating A alcanzado, 69 tests pasando

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/aagy/workspace-audit-budget-hard-gate`
- **Commit SHA**: `e0cf43e`
- **Fecha**: `2026-11-20 19:56:06`
- **Gobernanza**: Quality Gate A / markdownlint OK
