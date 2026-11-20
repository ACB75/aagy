# Fase 3: Documentación Técnica y Release Notes | Despliegue Tagged en git-flow-helper

> **Referencia de Ingeniería**: [`REQ_ecc_git_flow_deploy.md`](REQ_ecc_git_flow_deploy.md) y [`PLAN_ecc_git_flow_deploy.md`](PLAN_ecc_git_flow_deploy.md)  
> **ID de Tarea**: `feat/ecc/git-flow-deploy`  
> **Fecha**: 2026-11-20 | **Versión Semántica**: `v3.7.0`  
> **Estado**: `COMPLETO Y VERIFICADO`  

---

## 1. Notas de la Versión (Release Notes / Changelog)

### [`v3.7.0`] - 2026-11-20

#### 🚀 Nuevas Funcionalidades (`feat`)

- **`[scripts,infra]`**:
  - Extensión de `git-flow-helper.ps1` y `git-flow-helper.sh` con la capacidad de despliegue automatizado por etiquetas (`-Deploy`, `-Environment [sandbox|live]`, `-DryRun`).
  - Sondas de salud integradas (liveness probes con 3 reintentos x 5s) tras levantar los contenedores de Home-Lab.
  - Mecanismo de rollback automático desatendido en $< 2\text{ minutos}$ ante fallos en sondas o códigos de salida no-cero.
- **`[doc]`**:
  - Manual operativo [`doc/manual/MANUAL_multitier_deployment.md`](../manual/MANUAL_multitier_deployment.md).
  - Actualización de la matriz de promoción en `doc/STATUS.md` y `doc/INDEX.md`.

#### 🛡️ Mejoras de Rendimiento y Seguridad (`perf`, `sec`)

- Modo `-DryRun` para simulación segura sin mutaciones de infraestructura.
- Protección estricta de variables de entorno y secretos (`.env`) en logs de despliegue.
- Verificación atómica de salud antes de declarar la versión desplegada.

#### ⚠️ Certificación de Retrocompatibilidad (Zero-Breaking Policy)

- **Estado**: ✅ **100% RETROCOMPATIBLE (Zero Breaking Changes)**.
- *Confirmación*: La invocación de `promote` sin `-Deploy` mantiene el comportamiento exacto previo (solo etiquetado y push a GitHub).

---

## 2. Matriz de Promoción Multi-Tier Home-Lab (ADR-0006)

| Entorno | Tag Semántico / Commit | Host Destino | Pipeline de Despliegue |
| :--- | :--- | :--- | :---: |
| **LOCAL** | `HEAD` (`main`) | Estación Windows 11 / WSL | `complete-task-pr.ps1` (Tests & Quality Gates) |
| **SANDBOX** | `vX.Y.Z-sandbox` | FRACTAL (`192.168.1.100`) | `git-flow-helper.ps1 -Action promote -Tag vX.Y.Z-sandbox -Deploy` |
| **LIVE** | `vX.Y.Z` | NEO (`192.168.1.200`) | `git-flow-helper.ps1 -Action promote -Tag vX.Y.Z -Deploy -Environment live` |

---

## 3. Actualización de la Espina Dorsal Documental (Docs Spine)

- [x] **Manual de Operaciones**: `doc/manual/MANUAL_multitier_deployment.md`.
- [x] **Índice Maestro**: Actualización de `doc/INDEX.md`.
- [x] **Registro de Cambios**: Registro en `doc/LOG.md`.
- [x] **Métricas de Salud**: Actualización en `doc/STATUS.md`.
