# Fase 3: Documentación Técnica y Release Notes | Validador Ingress / DNS / Portal

> **Referencia de Ingeniería**: [`REQ_ecc_validate_ingress_routes.md`](REQ_ecc_validate_ingress_routes.md) y [`PLAN_ecc_validate_ingress_routes.md`](PLAN_ecc_validate_ingress_routes.md)  
> **ID de Tarea**: `feat/ecc/validate-ingress-routes`  
> **Fecha**: 2026-11-20 | **Versión Semántica**: `v3.6.0`  
> **Estado**: `COMPLETO Y VERIFICADO`  

---

## 1. Notas de la Versión (Release Notes / Changelog)

### [`v3.6.0`] - 2026-11-20

#### 🚀 Nuevas Funcionalidades (`feat`)

- **`[cluster,net,scripts]`**:
  - Implementación de `scripts/ecc-agy/validate_ingress_routes.py` para comprobación estática de congruencia entre etiquetas Traefik (`docker-compose*.yml`), resolución Split-DNS (`Corefile` de CoreDNS) y el catálogo central `/portal`.
  - Capacidad `--fix` para emitir sugerencias exactas de configuración para registros DNS faltantes y entradas en el mapa de `/portal`.
  - Wrappers CLI `scripts/bin/ecc-agy/validate-ingress-routes.ps1` y `validate-ingress-routes.sh`.
- **`[doc]`**:
  - Manual operativo [`doc/manual/MANUAL_ingress_routes_validator.md`](../manual/MANUAL_ingress_routes_validator.md).

#### 🛡️ Mejoras de Rendimiento y Seguridad (`perf`, `sec`)

- Análisis estático determinista sin requerir daemon de Docker en ejecución ($< 150\text{ ms}$).
- Exclusión automática de servicios internos sin Ingress (ej. PostgreSQL, Redis, exportadores locales).
- Omisión limpia (`SKIPPED`) si no se detectan archivos de infraestructura.

#### ⚠️ Certificación de Retrocompatibilidad (Zero-Breaking Policy)

- **Estado**: ✅ **100% RETROCOMPATIBLE (Zero Breaking Changes)**.
- *Confirmación*: Herramienta no invasiva; no modifica archivos en modo normal salvo si se solicita con `--fix` como sugerencia.

---

## 2. Matriz de Promoción Multi-Tier Home-Lab (ADR-0006)

| Entorno | Tag Semántico / Commit | Host Destino | Estado de Validación |
| :--- | :--- | :--- | :---: |
| **LOCAL** | `HEAD` (`feat/ecc/validate-ingress-routes`) | Estación de trabajo Windows 11 / WSL | ✅ Verificado (Tests en verde) |
| **SANDBOX** | `v3.6.0-sandbox` | Servidor FRACTAL (Docker Compose / K8s) | ⏳ Listo para despliegue |
| **LIVE** | `v3.6.0` | Servidor NEO (Producción Home-Lab) | 🔒 Bloqueado hasta validación Sandbox |

---

## 3. Actualización de la Espina Dorsal Documental (Docs Spine)

- [x] **Manual de Operaciones**: `doc/manual/MANUAL_ingress_routes_validator.md`.
- [x] **Índice Maestro**: Actualización de `doc/INDEX.md`.
- [x] **Registro de Cambios**: Registro en `doc/LOG.md`.
- [x] **Métricas de Salud**: Actualización en `doc/STATUS.md`.
