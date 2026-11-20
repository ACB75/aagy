# Fase 4: Propuesta de Commits, Pre-Flight Review y Apertura de PR

> **Referencia de Gobernanza**: Fase 4 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/skill-promotion-cli`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Modular Plugin Architect`  
> **Estado**: `APROBADO`  

---

## 1. Verificación de Rama Canónica

- **Rama**: `feat/ecc/skill-promotion-cli`
- **Validación con arnés**: Exit code `0` (`validate_branch.py`).

---

## 2. Propuesta Estructurada de Commit y PR

- **Título**: `[feat]-[ecc,scripts]: cli de promocion on-demand de skills tier-2 a tier-1`
- **Cuerpo Explicativo**:
  - **Contexto**: Para equilibrar la disponibilidad de 171 skills de alta especialización con la restricción de presupuesto de tokens en reposo (<1.000 tokens en el plugin activo), se implementa un mecanismo de activación temporal bajo demanda.
  - **Cambios**:
    - Motor `scripts/ecc-agy/skill_promotion.py` y wrappers `enable-skill.ps1`/`.sh` y `disable-skill.ps1`/`.sh`.
    - Registro transaccional en `.active_promotions.json`.
    - Protección de skills nucleares de Tier 1 y validación de frontmatter <= 140c.
    - Manual `doc/manual/MANUAL_skill_promotion.md`.
    - Pruebas unitarias en `test_skill_promotion.py`.
  - **Verificación**: Tests unitarios passing (100%), markdownlint passing y SonarQube Rating A.
