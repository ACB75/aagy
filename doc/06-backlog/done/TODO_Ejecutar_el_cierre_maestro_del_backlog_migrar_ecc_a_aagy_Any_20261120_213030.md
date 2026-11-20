---
title: "**Ejecutar el cierre maestro del backlog: migrar `/ecc` a `/aagy` (*Anything Antigravity*) conservando el historial Git, aplicando *full rename* a `aagy` y sincronizando el plugin `ecc` para Claude Code en `aagy/ecc/`**"
status: COMPLETED
completed_at: "2026-11-20 21:30:30"
---

# TODO: **Ejecutar el cierre maestro del backlog: migrar `/ecc` a `/aagy` (*Anything Antigravity*) conservando el historial Git, aplicando *full rename* a `aagy` y sincronizando el plugin `ecc` para Claude Code en `aagy/ecc/`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 21:30:30

### Detalle Original

- **01 - ROLE:** Principal Release & Repository Migration Architect (experto en rebranding estructural de monorepos, migración segura de git remotes/workspaces y publicación de plugins multiagente).
- **02 - CONTEXT:** `[Sector: Repository Lifecycle & Brand Migration]` `[Data Type: Git repo /ecc -> /aagy (preservando historial), plugin aagy + plugin Claude Code aagy/ecc/ sincronizado]` `[Objective: Migrar el repositorio actual /ecc a /aagy ("Anything Antigravity") conservando el historial Git, renombrando el remoto en GitHub (gh repo rename aagy), aplicando full rename a aagy (incluido ~/.gemini/config/plugins/aagy) y manteniendo dentro de aagy/ecc/ el plugin para Claude Code llamado ecc siempre sincronizado con aagy para paridad multiagente]` `[Restrictions: Ejecutar EXCLUSIVAMENTE como última tarea del TODO.md tras completar y verificar todas las prioridades anteriores; conservar el historial Git completo; NO regenerar ni purgar la documentación en esta tarea (se ajustará a posteriori); prohibido ejecutar rm/delete destructivo sin verificación previa en /aagy y confirmación explícita del usuario; mantener 0 enlaces rotos y 100% cumplimiento de budget hard gate + paridad aagy<->ecc]`.
- **03 - PHASE 1 (ANALYSIS):**
  - El directorio/nombre raíz `/ecc` ya no refleja la identidad nativa de *Anything Antigravity* (`/aagy`), y es necesario unificar el ecosistema manteniendo el plugin de Claude Code (`ecc`) sincronizado dentro de `aagy/ecc/`.
  - La documentación se actualizará a posteriori, por lo que esta tarea se centra exclusivamente en la migración limpia de repositorio, remoto, plugin instalado y paridad `aagy` $\leftrightarrow$ `ecc` sin duplicar trabajo documental.
- **04 - PHASE 2 (STRATEGY):**
  - *Enfoque A (In-Place Rename)*: Renombrar carpeta y editar archivos en sitio, arriesgando romper rutas activas antes de validar.
  - *Enfoque B (History-Preserving Cutover & Dual-Plugin Parity - Recomendado)*:
      1. Verificar que todas las tareas previas (`2.3` a `4.4`) estén archivadas en `TODO_DONE/` y en verde (`audit-workspace.ps1` + `pytest`).
      2. Migrar `c:\Workspace\projects\ecc` hacia `c:\Workspace\projects\aagy` (*Anything Antigravity*) **conservando el historial Git completo** y renombrar el remoto (`gh repo rename aagy`), aplicando *full rename* a `aagy` (`plugin.json`, `package.json`, rutas y `~/.gemini/config/plugins/aagy`).
      3. Estructurar y sincronizar dentro de `aagy/ecc/` el plugin para Claude Code llamado **`ecc`** (con chequeo de paridad automatizado `aagy` $\leftrightarrow$ `ecc` para operar de forma idéntica en multiagentes).
      4. Validar integridad completa en `/aagy` (`pytest`, `audit-workspace.ps1`, `lint-markdown.ps1`, smoke-test de ambos plugins) y, solo tras confirmación explícita del usuario, eliminar el antiguo directorio `/ecc`.
- **05 - PHASE 3 (EXECUTION):**
    1. Gate previo: confirmar backlog previo (`2.3`–`4.4`) completado al 100%.
    2. Crear `/aagy` preservando el historial Git (`git log` íntegro), renombrar remoto en GitHub (`gh repo rename aagy`) y ejecutar *full rename* de identidad a `aagy` / *Anything Antigravity*.
    3. Consolidar dentro de `aagy/ecc/` el plugin de Claude Code **`ecc`** y su mecanismo/script de sincronización y paridad continua con `aagy`.
    4. Validar `pytest`, `audit-workspace.ps1` y `lint-markdown.ps1` con código de salida `0`.
    5. Actualizar el plugin instalado a `~/.gemini/config/plugins/aagy`, obtener confirmación final del usuario y retirar `/ecc`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Riesgo crítico de pérdida irreversible si se borra `/ecc` antes de validar el 100% de tests, git remote y enlaces en `home-lab` o `~/.gemini/`. Mitigación: cutover en dos pasos con verificación integral en `/aagy` y confirmación explícita antes de borrar `/ecc`.
- **07 - PHASE 5 (FORMAT):**
  - Repositorio `/aagy` operativo con historial íntegro, remoto renombrado, `aagy/ecc/` sincronizado, tests y `audit-workspace.ps1` en verde (exit `0`).
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens) para la auditoría de cutover y paridad; **Carbon ($C_6$)** para *full rename* y validación.
- **COMPACT TRIGGER:** Al completar el cutover final en `/aagy`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `chore/aagy/repo-migration-cutover`
- **Commit SHA**: `90facff`
- **Fecha**: `2026-11-20 21:30:30`
- **Gobernanza**: Quality Gate A / markdownlint OK
