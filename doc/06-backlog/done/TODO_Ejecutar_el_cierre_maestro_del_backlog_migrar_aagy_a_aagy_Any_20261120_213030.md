---
title: "**Ejecutar el cierre maestro del backlog: migrar `/aagy` a `/aagy` (*Anything Antigravity*) conservando el historial Git, aplicando *full rename* a `aagy` y sincronizando el plugin `aagy` para Claude Code en `aagy/aagy/`**"
status: COMPLETED
completed_at: "2026-11-20 21:30:30"
---

# TODO: **Ejecutar el cierre maestro del backlog: migrar `/aagy` a `/aagy` (*Anything Antigravity*) conservando el historial Git, aplicando *full rename* a `aagy` y sincronizando el plugin `aagy` para Claude Code en `aagy/aagy/`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 21:30:30

### Detalle Original

- **01 - ROLE:** Principal Release & Repository Migration Architect (experto en rebranding estructural de monorepos, migración segura de git remotes/workspaces y publicación de plugins multiagente).
- **02 - CONTEXT:** `[Sector: Repository Lifecycle & Brand Migration]` `[Data Type: Git repo /aagy -> /aagy (preservando historial), plugin aagy + plugin Claude Code aagy/aagy/ sincronizado]` `[Objective: Migrar el repositorio actual /aagy a /aagy ("Anything Antigravity") conservando el historial Git, renombrando el remoto en GitHub (gh repo rename aagy), aplicando full rename a aagy (incluido ~/.gemini/config/plugins/aagy) y manteniendo dentro de aagy/aagy/ el plugin para Claude Code llamado aagy siempre sincronizado con aagy para paridad multiagente]` `[Restrictions: Ejecutar EXCLUSIVAMENTE como última tarea del TODO.md tras completar y verificar todas las prioridades anteriores; conservar el historial Git completo; NO regenerar ni purgar la documentación en esta tarea (se ajustará a posteriori); prohibido ejecutar rm/delete destructivo sin verificación previa en /aagy y confirmación explícita del usuario; mantener 0 enlaces rotos y 100% cumplimiento de budget hard gate + paridad aagy<->aagy]`.
- **03 - PHASE 1 (ANALYSIS):**
  - El directorio/nombre raíz `/aagy` ya no refleja la identidad nativa de *Anything Antigravity* (`/aagy`), y es necesario unificar el ecosistema manteniendo el plugin de Claude Code (`aagy`) sincronizado dentro de `aagy/aagy/`.
  - La documentación se actualizará a posteriori, por lo que esta tarea se centra exclusivamente en la migración limpia de repositorio, remoto, plugin instalado y paridad `aagy` $\leftrightarrow$ `aagy` sin duplicar trabajo documental.
- **04 - PHASE 2 (STRATEGY):**
  - *Enfoque A (In-Place Rename)*: Renombrar carpeta y editar archivos en sitio, arriesgando romper rutas activas antes de validar.
  - *Enfoque B (History-Preserving Cutover & Dual-Plugin Parity - Recomendado)*:
      1. Verificar que todas las tareas previas (`2.3` a `4.4`) estén archivadas en `TODO_DONE/` y en verde (`audit-workspace.ps1` + `pytest`).
      2. Migrar `<padre>\aagy` hacia `<padre>\aagy` (*Anything Antigravity*) **conservando el historial Git completo** y renombrar el remoto (`gh repo rename aagy`), aplicando *full rename* a `aagy` (`plugin.json`, `package.json`, rutas y `~/.gemini/config/plugins/aagy`).
      3. Estructurar y sincronizar dentro de `aagy/aagy/` el plugin para Claude Code llamado **`aagy`** (con chequeo de paridad automatizado `aagy` $\leftrightarrow$ `aagy` para operar de forma idéntica en multiagentes).
      4. Validar integridad completa en `/aagy` (`pytest`, `audit-workspace.ps1`, `lint-markdown.ps1`, smoke-test de ambos plugins) y, solo tras confirmación explícita del usuario, eliminar el antiguo directorio `/aagy`.
- **05 - PHASE 3 (EXECUTION):**
    1. Gate previo: confirmar backlog previo (`2.3`–`4.4`) completado al 100%.
    2. Crear `/aagy` preservando el historial Git (`git log` íntegro), renombrar remoto en GitHub (`gh repo rename aagy`) y ejecutar *full rename* de identidad a `aagy` / *Anything Antigravity*.
    3. Consolidar dentro de `aagy/aagy/` el plugin de Claude Code **`aagy`** y su mecanismo/script de sincronización y paridad continua con `aagy`.
    4. Validar `pytest`, `audit-workspace.ps1` y `lint-markdown.ps1` con código de salida `0`.
    5. Actualizar el plugin instalado a `~/.gemini/config/plugins/aagy`, obtener confirmación final del usuario y retirar `/aagy`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Riesgo crítico de pérdida irreversible si se borra `/aagy` antes de validar el 100% de tests, git remote y enlaces en `app` o `~/.gemini/`. Mitigación: cutover en dos pasos con verificación integral en `/aagy` y confirmación explícita antes de borrar `/aagy`.
- **07 - PHASE 5 (FORMAT):**
  - Repositorio `/aagy` operativo con historial íntegro, remoto renombrado, `aagy/aagy/` sincronizado, tests y `audit-workspace.ps1` en verde (exit `0`).
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens) para la auditoría de cutover y paridad; **Carbon ($C_6$)** para *full rename* y validación.
- **COMPACT TRIGGER:** Al completar el cutover final en `/aagy`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `chore/aagy/repo-migration-cutover`
- **Commit SHA**: `90facff`
- **Fecha**: `2026-11-20 21:30:30`
- **Gobernanza**: Quality Gate A / markdownlint OK
