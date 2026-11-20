---
title: "**Ejecutar el cierre maestro: migrar `/aagy` a `/aagy` (*Anything Antigravity*) conservando historial Git, generar el nuevo `README.md` del repo, sincronizar `aagy/aagy-ecc/` y reinstalar el plugin limpio**"
status: COMPLETED
completed_at: "2026-11-20 23:02:13"
---

# TODO: **Ejecutar el cierre maestro: migrar `/aagy` a `/aagy` (*Anything Antigravity*) conservando historial Git, generar el nuevo `README.md` del repo, sincronizar `aagy/aagy-ecc/` y reinstalar el plugin limpio**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 23:02:13

### Detalle Original

- **01 - ROLE:** Principal Release & Repository Migration Architect.
- **02 - CONTEXT:** `[Sector: Repository Lifecycle & Brand Migration]` `[Data Type: Git repo /aagy -> /aagy (historial íntegro), README.md raíz, plugin ~/.gemini/config/plugins/aagy, aagy/aagy-ecc/]` `[Objective: (1) Migrar /aagy a /aagy conservando historial Git y renombrando el remoto (gh repo rename aagy); (2) Mantener aagy/aagy-ecc/ actualizado, operativo y sincronizado con aagy; (3) Generar un nuevo README.md en la raíz de /aagy reflejando la arquitectura final (aagy + aagy-ecc, /doc v2, scripts/{py,pwsh,sh}, instalación manual y paridad CLI); (4) Reinstalar limpiamente el plugin mediante install.ps1/.sh verificando smoke-test y retirando /aagy tras confirmación explícita]` `[Restrictions: Ejecutar como última tarea tras completar 0.2, 0.3 y 0.4; conservar historial Git; 0 referencias rotas; budget hard gate y pytest en verde]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Ver requisitos aprobados en [`REQ_aagy_clean_docs_and_repo_migration.md`](../plans/REQ_aagy_clean_docs_and_repo_migration.md).
- **04 - PHASE 2 (STRATEGY):**
  - Cutover preservando historial $\rightarrow$ sincronización `aagy` $\leftrightarrow$ `aagy-ecc` $\rightarrow$ nuevo `README.md` $\rightarrow$ reinstalación limpia (`install.ps1` / `.sh`) $\rightarrow$ verificación integral y retirada de `/aagy` con confirmación.
- **05 - PHASE 3 (EXECUTION):**
    1. Confirmar `0.2`, `0.3` y `0.4` completadas y en verde.
    2. Migrar `/aagy` $\rightarrow$ `/aagy` preservando historial Git y renombrar remoto (`gh repo rename aagy`).
    3. Sincronizar `aagy/aagy-ecc/` y generar el nuevo `README.md` de raíz.
    4. Reinstalar el plugin limpio (`./install.ps1`) en `~/.gemini/config/plugins/aagy` (y `aagy-ecc`), validando `pytest`, `audit-workspace.ps1` y `lint-markdown.ps1` (exit `0`).
    5. Solicitar confirmación final al usuario para retirar `/aagy`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: No eliminar `/aagy` hasta verificar el plugin reinstalado y el 100% de tests en verde en `/aagy`.
- **07 - PHASE 5 (FORMAT):**
  - `/aagy` operativo, `README.md` nuevo, plugin reinstalado y tests en verde.
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens); **Carbon ($C_6$)** para `README.md`, reinstalación y tests.
- **COMPACT TRIGGER:** Al completar el cutover final en `/aagy`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `chore/aagy/clean-docs-and-repo-migration`
- **Commit SHA**: `31969be`
- **Fecha**: `2026-11-20 23:02:13`
- **Gobernanza**: Quality Gate A / markdownlint OK
