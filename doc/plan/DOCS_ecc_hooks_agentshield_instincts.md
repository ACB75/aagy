# Fase 3: Documentación Técnica, Espina Dorsal y Release Notes

> **Referencia de Ingeniería**: [`REQ_ecc_hooks_agentshield_instincts.md`](REQ_ecc_hooks_agentshield_instincts.md) y [`PLAN_ecc_hooks_agentshield_instincts.md`](PLAN_ecc_hooks_agentshield_instincts.md)  
> **ID de Tarea**: `feat/ecc/hooks-agentshield-instincts`  
> **Fecha**: `2026-11-20` | **Versión Semántica**: `v3.3.0`  
> **Estado**: `COMPLETO Y VERIFICADO`  

---

## 1. Notas de la Versión (Release Notes / Changelog)

### [`v3.3.0`] - 2026-11-20

#### 🚀 Nuevas Funcionalidades (`feat`, `sec`)

- **`[ecc,sec,hooks]`**: Adopción de hooks deterministas, auditoría AgentShield e instintos por proyecto.
  - Manifiesto [`hooks.json`](file:///c:/Workspace/projects/ecc/hooks.json) para intercepción de seguridad en `PreToolUse` y formateo automático de Markdown en `PostToolUse`.
  - Módulo de seguridad *AgentShield* en [`scripts/ecc-agy/security_audit.py`](file:///c:/Workspace/projects/ecc/scripts/ecc-agy/security_audit.py) auditando sintaxis de hooks, timeouts, inyecciones de comandos, detección de secretos en MCPs y prevención de *prompt injection* en skills.
  - Gestor de instintos por proyecto [`scripts/ecc-agy/instinct_manager.py`](file:///c:/Workspace/projects/ecc/scripts/ecc-agy/instinct_manager.py) y wrappers [`manage-instincts.ps1`](file:///c:/Workspace/projects/ecc/scripts/bin/ecc-agy/manage-instincts.ps1) / `.sh`, persistiendo aprendizajes en `.agents/instincts/` sin inflar `AGENTS.md`.

#### 🛡️ Mejoras de Seguridad y Automatización

- Enforzamiento automático a nivel de ciclo de vida del agente sin consumir tokens en el prompt del sistema.
- Blindaje integral del arnés frente a configuraciones maliciosas o filtración de credenciales.

#### ⚠️ Certificación de Retrocompatibilidad (Zero-Breaking Policy)

- **Estado**: ✅ **100% RETROCOMPATIBLE (Zero Breaking Changes)**.

---

## 2. Matriz de Promoción Multi-Tier Home-Lab (ADR-0006)

| Entorno | Tag Semántico / Commit | Host Destino | Estado de Validación |
| :--- | :--- | :--- | :---: |
| **LOCAL** | `HEAD` (`main`) | Estación de trabajo Windows 11 / WSL | ✅ Verificado (Tests en verde) |
| **SANDBOX** | `v3.3.0-sandbox` | Servidor FRACTAL (Docker Compose / K8s) | ⏳ Listo para despliegue |
| **LIVE** | `v3.3.0` | Servidor NEO (Producción Home-Lab) | 🔒 Bloqueado hasta validación Sandbox |

---

## 3. Actualización de la Espina Dorsal Documental (Docs Spine)

- [x] **Métricas en [`doc/STATUS.md`](../STATUS.md)**:
  - Registrada la suite AgentShield, hooks deterministas y motor de instintos.
- [x] **Historial en [`doc/LOG.md`](../LOG.md)**:
  - Registrada la tarea `feat/ecc/hooks-agentshield-instincts`.
