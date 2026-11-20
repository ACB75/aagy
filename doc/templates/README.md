# Plantillas del Workflow de Ingeniería ECC & Home-Lab (`doc/templates/`)

> **Espina Dorsal del Ciclo de Vida**: Gobernanza, Retrocompatibilidad, Rendimiento y Calidad  
> **Flujo Canónico**: `1. Requisitos & Impacto` -> `2. Plan de Acción & TDD` -> `3. Documentación & Release Notes` -> `4. Commits & PR`  

---

## 1. Justificación del Orden del Flujo (1 -> 2 -> 3 -> 4)

El ciclo de desarrollo en el ecosistema ECC y `home-lab` sigue un orden estricto donde la **Fase 3 (Documentación y Release Notes)** antecede a la **Fase 4 (Propuesta de Commits y PR)**. Esto garantiza que:

1. **Inclusión Atómica de la Documentación**: Las notas de la versión, manuales, diagramas Mermaid y actualizaciones de la espina documental (`STATUS.md`, `LOG.md`, ADRs) formen parte del mismo árbol de trabajo antes de generar la propuesta de commit.
2. **Revisión Pre-Flight Exhaustiva**: Al ejecutar la Fase 4, el informe de pre-flight (`complete-task-pr.ps1 -ReviewOnly`) evalúa el árbol completo (código, tests, DTOs del SDK y documentación) sin dejar jamás documentación pendiente o desincronizada.
3. **Cero Deriva Contractual (Anti-Drift)**: El squash-merge final incorpora tanto la implementación como la trazabilidad de la versión en un único commit atómico reversible.

---

## 2. Índice de Plantillas Estandarizadas

| Fase | Plantilla | Propósito y Contenido Principal |
| :---: | :--- | :--- |
| **01** | [`01_TOMA_REQUISITOS_E_IMPACTO.md`](01_TOMA_REQUISITOS_E_IMPACTO.md) | Análisis de problema, requisitos funcionales (`RF`), criterios de aceptación (`CA`), matriz de impacto en Home-Lab (paridad `home-lab-sdk`, PostgreSQL LTS locks, Ingress/Split-DNS, memory throttling) y política estricta de *Zero-Breaking Changes*. |
| **02** | [`02_PLAN_ACCION_ARQUITECTURA.md`](02_PLAN_ACCION_ARQUITECTURA.md) | Inventario de reutilización (DRY first), diseño arquitectónico con diagramas Mermaid, sincronización previa de `home-lab-sdk`, desglose TDD (`RED` -> `GREEN` -> `REFACTOR` -> `VERIFY`) y plan de rollback inmediato (<2 min). |
| **03** | [`03_DOCUMENTACION_Y_RELEASE_NOTES.md`](03_DOCUMENTACION_Y_RELEASE_NOTES.md) | Redacción de Notas de la Versión SemVer (`vX.Y.Z`), certificación de retrocompatibilidad, matriz de promoción multi-tier (LOCAL, SANDBOX, LIVE), actualización de la espina documental (`STATUS.md`, `LOG.md`, ADRs) y autopsia Post-Mortem 5W en ramas `fix/*`. |
| **04** | [`04_PROPUESTA_COMMITS_PR.md`](04_PROPUESTA_COMMITS_PR.md) | Verificación de rama canónica, propuesta de título convencional `[type]-[projects]: <title>`, cuerpo explicativo estructurado, aviso de revisión previa (Pre-Flight Review), compuertas de calidad SonarQube Rating A y orquestación de PR con squash-automerge y tags de promoción. |

---

## 3. Guía Rápida de Uso

1. Al iniciar una nueva tarea en una rama aislada (`feat/*`, `fix/*`, `refactor/*`), crear la carpeta del plan si no existe y completar la **Fase 1** en `doc/plan/REQ_<id>.md`.
2. Definir la estrategia técnica y TDD en la **Fase 2** en `doc/plan/PLAN_<id>.md`.
3. Tras implementar y verificar las pruebas, redactar la **Fase 3** en `doc/plan/DOCS_<id>.md` (o actualizar `CHANGELOG.md` / `doc/LOG.md`).
4. Generar la **Fase 4** ejecutando:

   ```powershell
   pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -ReviewOnly
   ```

5. Tras el visto bueno del operador, fusionar y promover:

   ```powershell
   pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -Yes -Title "[type]-[projects]: <título>"
   pwsh -File scripts/bin/ecc-agy/git-flow-helper.ps1 -Action promote -Tag vX.Y.Z-sandbox
   ```
