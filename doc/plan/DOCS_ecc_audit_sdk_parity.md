# Fase 3: Documentación Técnica y Release Notes | Linter de Paridad SDK

> **Referencia de Ingeniería**: [`REQ_ecc_audit_sdk_parity.md`](REQ_ecc_audit_sdk_parity.md) y [`PLAN_ecc_audit_sdk_parity.md`](PLAN_ecc_audit_sdk_parity.md)  
> **ID de Tarea**: `feat/ecc/audit-sdk-parity`  
> **Fecha**: 2026-11-20 | **Versión Semántica**: `v3.4.0`  
> **Estado**: `COMPLETO Y VERIFICADO`  

---

## 1. Notas de la Versión (Release Notes / Changelog)

### [`v3.4.0`] - 2026-11-20

#### 🚀 Nuevas Funcionalidades (`feat`)

- **`[scripts,sdk]`**:
  - Implementación de `scripts/ecc-agy/audit_sdk_parity.py` para análisis estático determinista de rutas y endpoints en controladores de microservicios (Go, Python, Java) y cotejo de paridad frente a clientes polyglot en `home-lab-sdk/`.
  - Wrappers de invocación multiplataforma `scripts/bin/ecc-agy/audit-sdk-parity.ps1` y `scripts/bin/ecc-agy/audit-sdk-parity.sh`.
  - Integración en la compuerta de validación previa de `complete-task-pr.ps1`.
- **`[doc]`**:
  - Manual operativo [`doc/manual/MANUAL_sdk_parity_audit.md`](../manual/MANUAL_sdk_parity_audit.md).

#### 🛡️ Mejoras de Rendimiento y Seguridad (`perf`, `sec`)

- Análisis léxico y regex compilado con ejecución $< 150\text{ ms}$.
- Zero dependencias externas (stdlib pura).
- Exclusión automática de rutas de diagnóstico `/metrics`, `/health`, `/livez`, `/readyz`.

#### ⚠️ Certificación de Retrocompatibilidad (Zero-Breaking Policy)

- **Estado**: ✅ **100% RETROCOMPATIBLE (Zero Breaking Changes)**.
- *Confirmación*: Repositorios sin `services/` o `home-lab-sdk/` se omiten elegantemente con estado `SKIPPED` y código 0.

---

## 2. Matriz de Promoción Multi-Tier Home-Lab (ADR-0006)

| Entorno | Tag Semántico / Commit | Host Destino | Estado de Validación |
| :--- | :--- | :--- | :---: |
| **LOCAL** | `HEAD` (`feat/ecc/audit-sdk-parity`) | Estación de trabajo Windows 11 / WSL | ✅ Verificado (Tests en verde) |
| **SANDBOX** | `v3.4.0-sandbox` | Servidor FRACTAL (Docker Compose / K8s) | ⏳ Listo para despliegue |
| **LIVE** | `v3.4.0` | Servidor NEO (Producción Home-Lab) | 🔒 Bloqueado hasta validación Sandbox |

---

## 3. Actualización de la Espina Dorsal Documental (Docs Spine)

- [x] **Manual de Operaciones**: `doc/manual/MANUAL_sdk_parity_audit.md`.
- [x] **Índice Maestro**: Actualización de `doc/INDEX.md`.
- [x] **Registro de Cambios**: Registro en `doc/LOG.md`.
- [x] **Métricas de Salud**: Actualización en `doc/STATUS.md`.
