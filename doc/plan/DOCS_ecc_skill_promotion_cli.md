# Fase 3: Documentación y Notas de Release (`Release Notes`)

> **Referencia de Gobernanza**: Fase 3 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/skill-promotion-cli`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Modular Plugin Architect`  
> **Estado**: `APROBADO`  

---

## 1. Release Notes SemVer (`v2.5.0`)

### 1.1. Resumen Ejecutivo de la Versión

Incorporación del sistema de promoción y desactivación dinámica de skills bajo demanda (`enable-skill` / `disable-skill`). Permite a desarrolladores y agentes activar temporalmente cualquiera de las 171 skills de Tier 2 en el plugin activo durante la realización de tareas especializadas y retirarla de forma limpia al terminar, protegiendo las 22 skills core de Tier 1 y manteniendo el presupuesto de tokens siempre en reposo en $< 1.000$ tokens.

### 1.2. Cambios Introducidos

- **Herramientas de CLI (`feat`)**:
  - `scripts/ecc-agy/skill_promotion.py`: Motor de validación de frontmatter, copia y sincronización con `.active_promotions.json`.
  - `scripts/bin/ecc-agy/enable-skill.ps1` y `enable-skill.sh`: Promoción on-demand.
  - `scripts/bin/ecc-agy/disable-skill.ps1` y `disable-skill.sh`: Retirada limpia de skills temporales.
- **Documentación (`docs`)**:
  - `doc/manual/MANUAL_skill_promotion.md`: Guía de arquitectura Two-Tier y gestión de skills.
- **Tests (`test`)**:
  - Suite unitaria `test_skill_promotion.py`.

---

## 2. Actualización de la Espina Documental

- `STATUS.md`: Añadido soporte de promoción on-demand de skills.
- `LOG.md`: Registro de la tarea `feat/ecc/skill-promotion-cli`.
- `doc/manual/MANUAL_skill_promotion.md`: Creado.
