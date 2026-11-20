# Fase 3: Documentación Técnica y Release Notes | Analizador de Bloqueos DDL

> **Referencia de Ingeniería**: [`REQ_ecc_audit_pg_locks.md`](REQ_ecc_audit_pg_locks.md) y [`PLAN_ecc_audit_pg_locks.md`](PLAN_ecc_audit_pg_locks.md)  
> **ID de Tarea**: `feat/ecc/audit-pg-locks`  
> **Fecha**: 2026-11-20 | **Versión Semántica**: `v3.5.0`  
> **Estado**: `COMPLETO Y VERIFICADO`  

---

## 1. Notas de la Versión (Release Notes / Changelog)

### [`v3.5.0`] - 2026-11-20

#### 🚀 Nuevas Funcionalidades (`feat`)

- **`[scripts,cluster]`**:
  - Implementación de `scripts/ecc-agy/audit_pg_locks.py` para análisis estático de migraciones y esquemas SQL en PostgreSQL LTS.
  - Clasificación en tres niveles de riesgo (`HIGH`, `MEDIUM`, `LOW`) ante bloqueos pesados como `ACCESS EXCLUSIVE` y bloqueos de escritura `SHARE`.
  - Catálogo de recomendaciones y remediaciones seguras de concurrencia (`CREATE INDEX CONCURRENTLY`, `NOT VALID`, etc.).
  - Wrappers CLI `scripts/bin/ecc-agy/audit-pg-locks.ps1` y `scripts/bin/ecc-agy/audit-pg-locks.sh`.
  - Integración en `complete-task-pr.ps1` y `complete-task-pr.sh` para escaneo automático de archivos `.sql` modificados.
- **`[doc]`**:
  - Manual operativo [`doc/manual/MANUAL_audit_pg_locks.md`](../manual/MANUAL_audit_pg_locks.md).

#### 🛡️ Mejoras de Rendimiento y Seguridad (`perf`, `sec`)

- Análisis léxico estático ultra-rápido ($< 100\text{ ms}$).
- Prevención activa de agotamiento de conexiones en la base de datos central multitenant de Home-Lab.
- Omisión limpia (`SKIPPED`) si no se detectan archivos `.sql`.

#### ⚠️ Certificación de Retrocompatibilidad (Zero-Breaking Policy)

- **Estado**: ✅ **100% RETROCOMPATIBLE (Zero Breaking Changes)**.
- *Confirmación*: No altera bases de datos ni código de producción en ejecución; análisis estático no destructivo.

---

## 2. Matriz de Promoción Multi-Tier Home-Lab (ADR-0006)

| Entorno | Tag Semántico / Commit | Host Destino | Estado de Validación |
| :--- | :--- | :--- | :---: |
| **LOCAL** | `HEAD` (`feat/ecc/audit-pg-locks`) | Estación de trabajo Windows 11 / WSL | ✅ Verificado (Tests en verde) |
| **SANDBOX** | `v3.5.0-sandbox` | Servidor FRACTAL (Docker Compose / K8s) | ⏳ Listo para despliegue |
| **LIVE** | `v3.5.0` | Servidor NEO (Producción Home-Lab) | 🔒 Bloqueado hasta validación Sandbox |

---

## 3. Actualización de la Espina Dorsal Documental (Docs Spine)

- [x] **Manual de Operaciones**: `doc/manual/MANUAL_audit_pg_locks.md`.
- [x] **Índice Maestro**: Actualización de `doc/INDEX.md`.
- [x] **Registro de Cambios**: Registro en `doc/LOG.md`.
- [x] **Métricas de Salud**: Actualización en `doc/STATUS.md`.
