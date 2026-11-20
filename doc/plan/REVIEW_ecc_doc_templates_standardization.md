# Fase 4: Propuesta de Commits, Pre-Flight Review y Apertura de PR

> **Referencia de Gobernanza**: Fase 4 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `refactor/ecc/doc-templates-standardization`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Documentation Governance Architect`  
> **Estado**: `APROBADO`  

---

## 1. Verificación de Rama Canónica

- **Rama**: `refactor/ecc/doc-templates-standardization`
- **Validación con arnés**: Exit code `0` (`validate_branch.py`).

---

## 2. Propuesta Estructurada de Commit y PR

- **Título**: `[refactor]-[doc,scripts]: reubicacion y estandarizacion de plantillas adr y postmortem`
- **Cuerpo Explicativo**:
  - **Contexto**: Las plantillas de toma de requisitos y post-mortem se encontraban dispersas con nombres no normalizados.
  - **Cambios**:
    - `doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` movido a `doc/adr/TEMPLATE_ADR.md`.
    - `doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md` renombrado a `doc/post-mortem/TEMPLATE_POSTMORTEM.md`.
    - Actualización de `generate_postmortem.py`, `generate-postmortem.ps1` / `.sh` y tests unitarios.
    - Sincronización de enlaces en `README.md`, `doc/INDEX.md`, `doc/README.md`.
  - **Verificación**: Tests unitarios passing (100%), markdownlint passing y SonarQube Rating A.
