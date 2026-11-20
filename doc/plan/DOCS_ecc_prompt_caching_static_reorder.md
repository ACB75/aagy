# Fase 3: Documentación y Notas de Release (`Release Notes`)

> **Referencia de Gobernanza**: Fase 3 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/prompt-caching-static-reorder`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Gemini LLM Systems Architect`  
> **Estado**: `APROBADO`  

---

## 1. Release Notes SemVer (`v2.5.0`)

### 1.1. Resumen Ejecutivo de la Versión

Se introduce la optimización de *prompt caching* y *context caching* para modelos Gemini 3.8 en el ecosistema Antigravity y plugin `ecc-agy`. Se reestructuran `AGENTS.md` y `rules/AGENTS.md` separando de forma estricta los invariantes estáticos universales en un prefijo continuo e inmutable, delimitando las directivas dinámicas de tarea en un sufijo contextual.

### 1.2. Cambios Introducidos

- **Optimizaciones de Rendimiento (`perf`)**:
  - Reordenamiento del conjunto de reglas `AGENTS.md` para maximizar el hit ratio de Gemini Context Caching.
  - Marcador formal `<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->`.
- **Documentación Técnica (`docs`)**:
  - Publicación del manual operativo `doc/manual/MANUAL_gemini_prompt_caching.md`.
- **Calidad y Verificación (`test`)**:
  - Test unitario de verificación de invariancia de prefijo en `test_workspace_audit.py`.

---

## 2. Actualización de la Espina Documental

- `STATUS.md`: Añadida optimización de context caching Gemini 3.8 completada.
- `LOG.md`: Registro de la tarea `feat/ecc/prompt-caching-static-reorder`.
- `doc/manual/MANUAL_gemini_prompt_caching.md`: Creado.
