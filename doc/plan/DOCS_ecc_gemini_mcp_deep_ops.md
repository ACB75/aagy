# Fase 3: Documentación Técnica, Espina Dorsal y Release Notes

> **Referencia de Ingeniería**: [`REQ_ecc_gemini_mcp_deep_ops.md`](REQ_ecc_gemini_mcp_deep_ops.md) y [`PLAN_ecc_gemini_mcp_deep_ops.md`](PLAN_ecc_gemini_mcp_deep_ops.md)  
> **ID de Tarea**: `feat/ecc/gemini-mcp-deep-ops`  
> **Fecha**: `2026-11-20` | **Versión Semántica**: `v3.2.0`  
> **Estado**: `COMPLETO Y VERIFICADO`  

---

## 1. Notas de la Versión (Release Notes / Changelog)

### [`v3.2.0`] - 2026-11-20

#### 🚀 Nuevas Funcionalidades (`feat`)

- **`[ecc,skills,plugins]`**: Integración de perfil opcional `gemini-mcp` y skill `gemini-deep-ops`.
  - Plantilla del plugin opcional en `templates/plugins/gemini-mcp/` con `"disabled": true` por defecto y parametrización segura de `${GEMINI_API_KEY}`.
  - Skill Tier 2 [`skills/gemini-deep-ops/SKILL.md`](file:///c:/Workspace/projects/ecc/skills/gemini-deep-ops/SKILL.md) para análisis de volcados, logs masivos y diagnósticos 5W sin sobrecarga de prompt en reposo.
  - Utilidad CLI [`scripts/ecc-agy/toggle_gemini_mcp.py`](file:///c:/Workspace/projects/ecc/scripts/ecc-agy/toggle_gemini_mcp.py) y wrappers [`toggle-gemini-mcp.ps1`](file:///c:/Workspace/projects/ecc/scripts/bin/ecc-agy/toggle-gemini-mcp.ps1) / `.sh`.
  - Herramienta de soporte [`scripts/ecc-agy/gemini_deep_ops.py`](file:///c:/Workspace/projects/ecc/scripts/ecc-agy/gemini_deep_ops.py) y wrappers [`gemini-deep-ops.ps1`](file:///c:/Workspace/projects/ecc/scripts/bin/ecc-agy/gemini-deep-ops.ps1) / `.sh`.
  - Manual de operaciones en [`doc/manual/MANUAL_gemini_deep_ops_multimodal.md`](file:///c:/Workspace/projects/ecc/doc/manual/MANUAL_gemini_deep_ops_multimodal.md).

#### 🛡️ Mejoras de Rendimiento y Contexto (`perf`)

- Cero tokens de sobrecarga en reposo en el catálogo Tier 1 global.
- Ahorro de ~4.500–10.000 tokens por turno respecto a la inyección indiscriminada de herramientas MCP de Gemini.

#### ⚠️ Certificación de Retrocompatibilidad (Zero-Breaking Policy)

- **Estado**: ✅ **100% RETROCOMPATIBLE (Zero Breaking Changes)**.
- Todos los arneses y flujos existentes operan sin alteraciones.

---

## 2. Matriz de Promoción Multi-Tier Home-Lab (ADR-0006)

| Entorno | Tag Semántico / Commit | Host Destino | Estado de Validación |
| :--- | :--- | :--- | :---: |
| **LOCAL** | `HEAD` (`main`) | Estación de trabajo Windows 11 / WSL | ✅ Verificado (Tests en verde) |
| **SANDBOX** | `v3.2.0-sandbox` | Servidor FRACTAL (Docker Compose / K8s) | ⏳ Listo para despliegue |
| **LIVE** | `v3.2.0` | Servidor NEO (Producción Home-Lab) | 🔒 Bloqueado hasta validación Sandbox |

---

## 3. Actualización de la Espina Dorsal Documental (Docs Spine)

- [x] **Métricas en [`doc/STATUS.md`](../STATUS.md)**:
  - Registrada la integración zero-overhead de `gemini-mcp` y skill `gemini-deep-ops`.
- [x] **Historial en [`doc/LOG.md`](../LOG.md)**:
  - Registrada la tarea `feat/ecc/gemini-mcp-deep-ops`.
