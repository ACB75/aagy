# Fase 4: Propuesta de Commits, Pre-Flight Review y Apertura de PR

> **Referencia de Gobernanza**: Fase 4 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/git-pre-commit-hooks`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Git Operations Specialist`  
> **Estado**: `APROBADO`  

---

## 1. Verificación de Rama Canónica

- **Rama**: `feat/ecc/git-pre-commit-hooks`
- **Validación con arnés**: Exit code `0` (`validate_branch.py`).

---

## 2. Propuesta Estructurada de Commit y PR

- **Título**: `[feat]-[ecc,scripts]: infraestructura de pre-commit y commit-msg hooks nativos con instalador`
- **Cuerpo Explicativo**:
  - **Contexto**: Para evitar la elusión inadvertida de las reglas de formato de commit y sintaxis de documentación al realizar commits manuales, se construyen hooks nativos para Git locales.
  - **Cambios**:
    - `scripts/ecc-agy/hooks/pre-commit` y `commit-msg` en formato POSIX universal.
    - Scripts de instalación y desinstalación idempotentes `install-git-hooks.ps1` y `.sh`.
    - Manual operativo `doc/manual/MANUAL_git_hooks.md`.
    - Tests unitarios en `test_git_hooks.py`.
  - **Verificación**: Tests unitarios passing (100%), markdownlint passing y SonarQube Rating A.
