# Fase 4: Propuesta de Commits, Pre-Flight Review y Apertura de PR

> **Referencia de Gobernanza**: Fase 4 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/prompt-caching-static-reorder`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Gemini LLM Systems Architect`  
> **Estado**: `APROBADO`  

---

## 1. Verificación de Rama Canónica

- **Rama**: `feat/ecc/prompt-caching-static-reorder`
- **Validación con arnés**: Exit code `0` (`validate_branch.py`).

---

## 2. Propuesta Estructurada de Commit y PR

- **Título**: `[perf]-[ecc,rules]: alineacion de context caching de gemini 3.8 y reordenamiento estatico de reglas`
- **Cuerpo Explicativo**:
  - **Contexto**: Los modelos Gemini 3.8 operan con context caching por prefijo exacto. Las reglas unificadas contenían directivas operativas mezcladas con principios universales, lo que reducía la reutilización de caché entre turnos.
  - **Cambios**:
    - Reordenamiento de `AGENTS.md` y `rules/AGENTS.md` en Bloque Estático Invariable (Google 5-Pillars, SRE, Security, Quality, Multi-Stack, Microservice SDK Parity) y Bloque Contextual / Dinámico.
    - Sincronización idéntica con el plugin global `~/.gemini/config/plugins/ecc-agy/rules/AGENTS.md`.
    - Creación de `doc/manual/MANUAL_gemini_prompt_caching.md`.
    - Pruebas unitarias de invariancia de prefijo en `test_workspace_audit.py`.
  - **Verificación**: Tests unitarios passing (100%), markdownlint passing y SonarQube Rating A.
