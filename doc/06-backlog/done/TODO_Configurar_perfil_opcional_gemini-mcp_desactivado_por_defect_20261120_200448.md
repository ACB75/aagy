---
title: "**Configurar perfil opcional `gemini-mcp` desactivado por defecto y skill bajo demanda para `ecc-agy` y `home-lab`**"
status: COMPLETED
completed_at: "2026-11-20 20:04:48"
---

# TODO: **Configurar perfil opcional `gemini-mcp` desactivado por defecto y skill bajo demanda para `ecc-agy` y `home-lab`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 20:04:48

### Detalle Original

- **01 - ROLE:** Gemini Platform Architect & Developer Experience Engineer (experto en MCP, SDK oficial `google-genai` y flujos multimodales de bajo consumo de contexto).
- **02 - CONTEXT:** `[Sector: Multimodal AI Tooling & Home-Lab Diagnostics]` `[Data Type: Plugin AGY (plugin.json, mcp_config.json), Skill Tier 2 (SKILL.md), Wrapper CLI Python/PowerShell]` `[Objective: Aprovechar las capacidades diferenciales de RLabs-Inc/gemini-mcp (Context Caching, Deep Research, análisis de PDFs/vídeos/logs, Structured JSON Output) en ecc-agy y home-lab con 0 tokens en reposo]` `[Restrictions: Jamás habilitar las 30+ tools MCP por defecto; cero secretos hardcoded (GEMINI_API_KEY vía entorno); sin dependencias de terceros no oficiales en scripts propios]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Antigravity ya ejecuta Gemini de forma nativa y dispone de `search_web`, `image-generator` y `gemini-api-docs`, por lo que activar `gemini-mcp` completo siempre duplica herramientas e infla el presupuesto.
  - Las capacidades realmente diferenciales para `ecc-agy` y `home-lab` son el análisis masivo de logs/PDFs/capturas para Post-Mortems 5W (`fix/*`), *Context Caching* y salida JSON estructurada.
- **04 - PHASE 2 (STRATEGY):**
  - *Enfoque A (Plugin aislado `disabled: true`)*: Empaquetar `gemini-mcp` en un plugin independiente con `"disabled": true` en `plugin.json` para activación manual puntual.
  - *Enfoque B (Skill Tier 2 + CLI/SDK)*: Crear la skill `skills/gemini-deep-ops/SKILL.md` (`<= 140` chars, 0 tokens en Tier 1) que delega en un script ligero usando `google-genai` o el CLI `gcli`.
  - *Enfoque C (Combinado recomendado)*: Proveer la plantilla del plugin aislado (`disabled: true`) para sesiones interactivas puntuales y la skill `gemini-deep-ops` (sin MCP en prompt) para flujos reproducibles en `ecc` y `home-lab`.
- **05 - PHASE 3 (EXECUTION):**
    1. Crear plantilla/instalador del plugin opcional `gemini-mcp` con `"disabled": true` y lectura de `GEMINI_API_KEY` por entorno.
    2. Crear `skills/gemini-deep-ops/SKILL.md` (`<= 140` chars en `description`) en Tier 2 y script de apoyo en `scripts/bin/ecc-agy/`.
    3. Documentar el flujo de diagnóstico multimodal para `doc/postmortem/` en `home-lab`.
    4. Validar con `workspace_audit.py` (confirmando 0 incremento en Tier 1 y 0 exceso de budget) y smoke-test del script.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Verificar que el plugin opcional no se active accidentalmente tras `ecc-agy-sync` y que nunca se filtre `GEMINI_API_KEY` en logs o commits.
- **07 - PHASE 5 (FORMAT):**
  - Artefactos del plugin (`plugin.json`, `mcp_config.json`), `SKILL.md` validado por `markdownlint`, y smoke-test con exit code `0`.
- **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.000 tokens). Creación de plantillas y CLI deterministicos.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Integración zero-overhead de gemini-mcp y skill gemini-deep-ops completada con éxito

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/ecc/gemini-mcp-deep-ops`
- **Commit SHA**: `0eb4100`
- **Fecha**: `2026-11-20 20:04:48`
- **Gobernanza**: Quality Gate A / markdownlint OK
