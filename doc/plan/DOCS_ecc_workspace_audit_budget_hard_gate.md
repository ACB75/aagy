# Fase 3: Documentación Técnica, Espina Dorsal y Release Notes

> **Referencia de Ingeniería**: [`REQ_ecc_workspace_audit_budget_hard_gate.md`](REQ_ecc_workspace_audit_budget_hard_gate.md) y [`PLAN_ecc_workspace_audit_budget_hard_gate.md`](PLAN_ecc_workspace_audit_budget_hard_gate.md)  
> **ID de Tarea**: `feat/ecc/workspace-audit-budget-hard-gate`  
> **Fecha**: `2026-11-20` | **Versión Semántica**: `v3.1.0`  
> **Estado**: `COMPLETO Y VERIFICADO`  

---

## 1. Notas de la Versión (Release Notes / Changelog)

### [`v3.1.0`] - 2026-11-20

#### 🚀 Nuevas Funcionalidades (`feat`)

- **`[ecc,scripts]`**: Implementado *hard gate* de presupuesto de contexto en `workspace_audit.py` y `audit-workspace.ps1`.
  - Validación de tamaño individual de archivos de reglas ($\le 24.000$ bytes / 24 KB según directivas de Antigravity).
  - Techo de seguridad agregado para reglas activas ($\le 16.000$ tokens frente al defaultRulesBudget de 20.000).
  - Auditoría de configuración de servidores MCP en `mcp_config.json`, exigiendo `"disabled": true` para servidores pesados como `gemini-mcp`.
  - Límite de personalizaciones eager en reposo ($\le 3.000$ tokens) para plugins activos.
  - Inclusión automática del plugin global `~/.gemini/config/plugins/ecc-agy` en los objetivos de auditoría.

#### 🛡️ Mejoras de Rendimiento y Seguridad (`perf`, `sec`)

- Prevención garantizada de desbordamientos de contexto (*context window overflow*) y de latencia excesiva en el primer turno (TTFT).
- Detección en reposo a coste 0 tokens para MCPs desactivados.

#### ⚠️ Certificación de Retrocompatibilidad (Zero-Breaking Policy)

- **Estado**: ✅ **100% RETROCOMPATIBLE (Zero Breaking Changes)**.
- El workspace actual y el plugin global `ecc-agy` cumplen estrictamente los umbrales configurados.

---

## 2. Matriz de Promoción Multi-Tier Home-Lab (ADR-0006)

| Entorno | Tag Semántico / Commit | Host Destino | Estado de Validación |
| :--- | :--- | :--- | :---: |
| **LOCAL** | `HEAD` (`main`) | Estación de trabajo Windows 11 / WSL | ✅ Verificado (Tests en verde) |
| **SANDBOX** | `v3.1.0-sandbox` | Servidor FRACTAL (Docker Compose / K8s) | ⏳ Listo para despliegue |
| **LIVE** | `v3.1.0` | Servidor NEO (Producción Home-Lab) | 🔒 Bloqueado hasta validación Sandbox |

---

## 3. Actualización de la Espina Dorsal Documental (Docs Spine)

- [x] **Métricas en [`doc/STATUS.md`](../STATUS.md)**:
  - Registrado el nuevo hard gate de presupuesto en `workspace_audit.py`.
- [x] **Historial en [`doc/LOG.md`](../LOG.md)**:
  - Registrada la tarea `feat/ecc/workspace-audit-budget-hard-gate`.
