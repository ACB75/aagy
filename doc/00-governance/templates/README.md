# Plantillas del Workflow de Ingeniería AAGY / `aagy` (`00-governance/templates/`)

> **Espina Dorsal del Ciclo de Vida**: Gobernanza, Retrocompatibilidad, Rendimiento y Calidad  
> **Flujo Canónico**: `1. Requisitos & Impacto` -> `2. Plan de Acción & TDD` -> `3. Documentación & Release Notes` -> `4. Commits & PR`  
> **Flujo Flexible CLI**: Ver [`MANUAL_WORKFLOW.md`](../MANUAL_WORKFLOW.md) (`IDEAS` | `REQ` | `PLAN` | `TODO`)

---

## 1. Justificación del Orden del Flujo (1 -> 2 -> 3 -> 4)

El ciclo de desarrollo en `aagy` y `home-lab` sitúa la **Fase 3 (Documentación y Release Notes)** antes de la **Fase 4 (Propuesta de Commits y PR)** para garantizar:

1. **Inclusión Atómica de la Documentación**: Notas de versión, manuales, diagramas y espina documental (`STATUS.md`, `LOG.md`, ADRs) viajan en el mismo árbol de trabajo que el código.
2. **Revisión Pre-Flight Exhaustiva**: [`complete-task-pr.ps1`](../../../scripts/pwsh/complete-task-pr.ps1) evalúa el conjunto completo (código, tests, SDK y documentación) antes de abrir o fusionar la PR.
3. **Cero Deriva Contractual**: El squash-merge integra implementación y trazabilidad documental en un único commit atómico reversible.

---

## 2. Índice de Plantillas Estandarizadas

| Plantilla | Propósito y Contenido Principal |
| :--- | :--- |
| [`01_TOMA_REQUISITOS_E_IMPACTO.md`](01_TOMA_REQUISITOS_E_IMPACTO.md) | Requisitos (`RF`), criterios `CA`, matriz Home-Lab y política *Zero-Breaking Changes*. |
| [`02_PLAN_ACCION_ARQUITECTURA.md`](02_PLAN_ACCION_ARQUITECTURA.md) | Inventario DRY, topología Mermaid, paridad SDK, TDD (`RED` $\rightarrow$ `GREEN` $\rightarrow$ `REFACTOR`) y rollback < 2 min. |
| [`03_DOCUMENTACION_Y_RELEASE_NOTES.md`](03_DOCUMENTACION_Y_RELEASE_NOTES.md) | Release Notes SemVer, promoción multi-tier (`LOCAL`/`SANDBOX`/`LIVE`) y espina documental. |
| [`04_PROPUESTA_COMMITS_PR.md`](04_PROPUESTA_COMMITS_PR.md) | Ramas canónicas, formato `[type]-[projects]: <title>`, Pre-Flight Review y automerge. |
| [`TEMPLATE_ADR.md`](TEMPLATE_ADR.md) | Plantilla canónica unificada para Architecture Decision Records (`doc/02-adr/`). |
| [`TEMPLATE_POSTMORTEM.md`](TEMPLATE_POSTMORTEM.md) | Plantilla canónica SRE 5W (*blameless*) para ramas `fix/*` (`doc/05-post-mortems/`). |

---

## 3. Guía Rápida de Uso

1. Instancia desde cualquier punto de entrada (`IDEAS`, `REQ`, `PLAN`, `TODO` o `ALL`):

   ```powershell
   pwsh -NoProfile -File scripts/pwsh/new-lifecycle-task.ps1 -TaskId "feat/<proyecto>/<id>" -Phase PLAN
   ```

2. Tras implementar y validar (`pytest`, `lint-markdown`, `map-docs`, `audit-workspace`), ejecuta Pre-Flight Review y squash-automerge:

   ```powershell
   pwsh -NoProfile -File scripts/pwsh/complete-task-pr.ps1 -ReviewOnly
   pwsh -NoProfile -File scripts/pwsh/complete-task-pr.ps1 -Yes -Title "[type]-[projects]: <título>"
   ```
