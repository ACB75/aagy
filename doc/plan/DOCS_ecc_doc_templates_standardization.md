# Fase 3: Documentación y Notas de Release (`Release Notes`)

> **Referencia de Gobernanza**: Fase 3 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `refactor/ecc/doc-templates-standardization`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Documentation Governance Architect`  
> **Estado**: `APROBADO`  

---

## 1. Release Notes SemVer (`v2.5.0`)

### 1.1. Resumen Ejecutivo de la Versión

Estandarización y reubicación canónica de plantillas documentales. Se centraliza la plantilla de arquitectura y ADR en `doc/adr/TEMPLATE_ADR.md` y se normaliza la plantilla de post-mortem en `doc/post-mortem/TEMPLATE_POSTMORTEM.md`, eliminando archivos sueltos en `doc/` y actualizando de forma transparente todas las referencias en arneses, scripts y documentación general.

### 1.2. Cambios Introducidos

- **Estructura y Gobernanza (`refactor`)**:
  - `doc/adr/TEMPLATE_ADR.md`: Nueva ubicación canónica para plantillas de requisitos y ADR.
  - `doc/post-mortem/TEMPLATE_POSTMORTEM.md`: Nombre simplificado y canónico para autopsias 5W.
  - Actualización de `scripts/ecc-agy/generate_postmortem.py` y wrappers `.ps1` / `.sh`.
  - Actualización de enlaces en `README.md`, `doc/INDEX.md`, `doc/README.md`.

---

## 2. Actualización de la Espina Documental

- `STATUS.md`: Estandarización de plantillas documentales completada.
- `LOG.md`: Registro de la tarea `refactor/ecc/doc-templates-standardization`.
