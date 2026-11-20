# Fase 3: Documentación y Notas de Release (`Release Notes`)

> **Referencia de Gobernanza**: Fase 3 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/git-pre-commit-hooks`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Git Operations Specialist`  
> **Estado**: `APROBADO`  

---

## 1. Release Notes SemVer (`v2.5.0`)

### 1.1. Resumen Ejecutivo de la Versión

Incorporación de la infraestructura de Git hooks locales en el arnés `ecc-agy`. Permite atrapar de forma determinista y preventiva mensajes de commit no conformes (`commit-msg`) y sintaxis Markdown no conforme (`pre-commit`) en el momento exacto de la confirmación local, eliminando re-trabajos y garantizando uniformidad en el historial del repositorio.

### 1.2. Cambios Introducidos

- **Herramientas de Desarrollador (`feat`)**:
  - `scripts/ecc-agy/hooks/pre-commit`: Hook POSIX para escaneo rápido de archivos `.md` en staging.
  - `scripts/ecc-agy/hooks/commit-msg`: Hook POSIX para validación estricta de mensajes de commit mediante `format_commit.py`.
  - `scripts/bin/ecc-agy/install-git-hooks.ps1` y `install-git-hooks.sh`: Instalador multiplataforma de hooks con soporte `-Uninstall`.
- **Documentación (`docs`)**:
  - `doc/manual/MANUAL_git_hooks.md`: Manual de uso, instalación y bypass con `--no-verify`.
- **Tests (`test`)**:
  - Suite unitaria `test_git_hooks.py`.

---

## 2. Actualización de la Espina Documental

- `STATUS.md`: Añadida infraestructura de git hooks.
- `LOG.md`: Registro de la tarea `feat/ecc/git-pre-commit-hooks`.
- `doc/manual/MANUAL_git_hooks.md`: Creado.
