---
title: "**Extender `git-flow-helper.ps1` para despliegue automatizado por etiquetas de promoción (`vX.Y.Z-sandbox` y `vX.Y.Z`)**"
status: COMPLETED
completed_at: "2026-11-20 21:17:40"
---

# TODO: **Extender `git-flow-helper.ps1` para despliegue automatizado por etiquetas de promoción (`vX.Y.Z-sandbox` y `vX.Y.Z`)**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 21:17:40

### Detalle Original

- **01 - ROLE:** Release Automation & Multi-Tier Deployment Engineer.
- **02 - CONTEXT:** `[Sector: Continuous Delivery & Infrastructure Automation]` `[Data Type: PowerShell git-flow-helper.ps1, SSH / Docker Compose commands]` `[Objective: Integrar en la acción 'promote' de git-flow-helper.ps1 la capacidad opcional (-Deploy) de conectarse al host de Home-Lab mediante SSH o localmente, ejecutar el pull de imágenes o checkout del tag, levantar los contenedores y verificar los healthchecks automáticos con rollback en < 2 minutos si fallan]` `[Restrictions: No interrumpir servicios no afectados; rollback garantizado ante cualquier código de salida no-cero]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Actualmente `git-flow-helper.ps1 -Action promote` crea el tag semántico anotado y lo sube a GitHub, pero el despliegue físico en el servidor de destino requiere pasos manuales por SSH.
  - Se busca cerrar el ciclo Trunk-Based para que la promoción ejecute el despliegue y valide las sondas de salud de forma unificada.
- **04 - PHASE 2 (STRATEGY):**
  - Añadir parámetro `-Deploy` y `-Environment [sandbox|live]`.
  - Secuencia de despliegue: Backup de estado -> Pull/Recreate contenedores -> Liveness probes (3 intentos x 5s) -> Si OK: Confirmar tag; Si FAIL: Ejecutar rollback automático al tag anterior.
- **05 - PHASE 3 (EXECUTION):**
    1. Actualizar `scripts/bin/ecc-agy/git-flow-helper.ps1` con la lógica de despliegue y sondas de salud.
    2. Añadir modo `-DryRun` para simular la secuencia sin impactar contenedores reales.
    3. Incorporar tests en `test_git_flow_helper.py` o suite de integración.
    4. Actualizar ADR-0006 con el flujo automatizado de promoción y despliegue.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Evitar fallos de red durante el despliegue; asegurar que los secretos (`.env`) nunca se expongan en logs del pipeline.
- **07 - PHASE 5 (FORMAT):**
  - Script PowerShell endurecido con manejo de errores estricto (`Set-StrictMode`, `$ErrorActionPreference = 'Stop'`).
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens) para el protocolo de resiliencia y rollback; **Carbon ($C_6$)** para la implementación en PowerShell.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Extension de git-flow-helper.ps1 y .sh para despliegue automatizado por etiquetas, sondas de salud y rollback

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/ecc/git-flow-deploy`
- **Commit SHA**: `e57794f`
- **Fecha**: `2026-11-20 21:17:40`
- **Gobernanza**: Quality Gate A / markdownlint OK
