---
title: "**Construir instalador e infraestructura de pre-commit hooks nativos para validación determinista de commits y markdown**"
status: COMPLETED
completed_at: "2026-11-20 20:29:16"
---

# TODO: **Construir instalador e infraestructura de pre-commit hooks nativos para validación determinista de commits y markdown**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 20:29:16

### Detalle Original

- **01 - ROLE:** Git Operations Engineer & Developer Tooling Specialist.
- **02 - CONTEXT:** `[Sector: Developer Infrastructure & Tooling]` `[Data Type: Git hooks (POSIX sh & pwsh), PowerShell y Bash]` `[Objective: Crear una utilidad de instalación de git hooks que intercepte 'git commit' localmente y ejecute format_commit.py --strict sobre el mensaje propuesto y lint-markdown.ps1 sobre los archivos staged, previniendo commits no conformes antes de subir a origin]` `[Restrictions: Tiempo de ejecución < 800ms; soporte nativo dual Windows 11 (pwsh) y Linux/WSL (bash)]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Actualmente la validación de formato depende de que el desarrollador invoque `format-commit.ps1` o de que la PR corra `audit-workspace.ps1`.
  - Si un desarrollador humano o agente emite un commit manual fuera del arnés, puede eludir la regla y romper la uniformidad del monorepo.
- **04 - PHASE 2 (STRATEGY):**
  - Hook `commit-msg` para validar el título `[type]-[projects]: <title>` y el cuerpo explicativo.
  - Hook `pre-commit` para validar con markdownlint solo los archivos `.md` en el área de preparación (*staged*).
  - Scripts idempotentes de instalación en `scripts/bin/aagy/install-git-hooks.ps1` y `.sh`.
- **05 - PHASE 3 (EXECUTION):**
    1. Implementar scripts de hooks en `scripts/aagy/hooks/` (POSIX sh para compatibilidad Git universal).
    2. Crear instalador `install-git-hooks.ps1` y `install-git-hooks.sh` que vincule o copie a `.git/hooks/`.
    3. Añadir soporte para bypass controlado en emergencias (`git commit --no-verify`).
    4. Crear test unitario en `test_scripts_bin.py` verificando la instalación y el comportamiento del hook.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Evitar que el hook tarde más de 1 segundo en validar, asegurando que solo revise los archivos staged (`git diff --cached --name-only`).
- **07 - PHASE 5 (FORMAT):**
  - Scripts idempotentes, código limpio sin dependencias externas y tests pasando con exit code `0`.
- **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.200 tokens).
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Hooks pre-commit y commit-msg, instalador install-git-hooks.ps1/sh, manual MANUAL_git_hooks.md y test_git_hooks.py

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/aagy/git-pre-commit-hooks`
- **Commit SHA**: `8c3c5ee`
- **Fecha**: `2026-11-20 20:29:16`
- **Gobernanza**: Quality Gate A / markdownlint OK
