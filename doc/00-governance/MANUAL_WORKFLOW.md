# Guía de Flujo Manual y Paridad 1-a-1 (`MANUAL_WORKFLOW.md`)

> **Principio Operativo**: Cualquier flujo automatizado por el plugin (`aagy` / `ecc`) puede ejecutarse de forma determinista desde terminal (`pwsh`, `bash` o `python`) sin depender del agente.  
> **Contrato de Rutas**: [`.governance/docs-map.json`](../../.governance/docs-map.json) | **Estándar**: [`DOC_STANDARDS.md`](DOC_STANDARDS.md)

---

## 1. Puntos de Entrada Flexibles `[IDEAS -> REQUISITOS -> PLAN -> TODO]`

El ciclo de vida no impone burocracia lineal rígida cuando el alcance ya está claro. Puedes iniciar el trabajo desde cualquiera de los 4 puntos de entrada usando `new-lifecycle-task`:

| Punto de Entrada | Flag CLI (`-Phase` / `--phase`) | Artefactos Generados | Cuándo Usarlo |
| :--- | :---: | :--- | :--- |
| **1. Ideas** | `IDEAS` | Registra bloque `## Idea ...` en `IDEAS.md` | Propuesta exploratoria pendiente de maduración o priorización. |
| **2. Requisitos** | `REQ` / `ALL` | `REQ_`, `PLAN_`, `DOCS_`, `REVIEW_` en `plans/` | Features complejas, cambios transversales o impacto Home-Lab/SDK. |
| **3. Plan Técnico** | `PLAN` | `PLAN_`, `DOCS_`, `REVIEW_` en `plans/` (omite `REQ_`) | Requisitos ya aprobados externamente o refactors acotados. |
| **4. Tarea Directa** | `TODO` | Tarea 7-fases en `TODO.md` + `quick/QUICK_<slug>.md` | Cambios atómicos, hotfixes pequeños o tareas ya definidas sin ceremonia. |
| **Docs / Review** | `DOCS` / `REVIEW` | `DOCS_`+`REVIEW_` o solo `REVIEW_` | Cierre de documentación y preparación de PR tras implementación previa. |

### Ejemplos de Inicio por Punto de Entrada

```powershell
# Entrada 1: Registrar idea en doc/06-backlog/IDEAS.md
pwsh -NoProfile -File scripts/bin/ecc-agy/new-lifecycle-task.ps1 -TaskId "feat/aagy/mi-idea" -Phase IDEAS

# Transformar ideas Approved -> TODO.md (metodología 7 fases)
pwsh -NoProfile -File scripts/bin/ecc-agy/sync-ideas-todo.ps1

# Entrada 2: Ciclo completo 4 fases (REQ + PLAN + DOCS + REVIEW)
pwsh -NoProfile -File scripts/bin/ecc-agy/new-lifecycle-task.ps1 -TaskId "feat/kakebo/export-csv" -Phase REQ

# Entrada 3: Saltar REQ e iniciar directo en PLAN
pwsh -NoProfile -File scripts/bin/ecc-agy/new-lifecycle-task.ps1 -TaskId "refactor/scripts/cache" -Phase PLAN

# Entrada 4: Tarea rápida directa a TODO.md + quick/
pwsh -NoProfile -File scripts/bin/ecc-agy/new-lifecycle-task.ps1 -TaskId "fix/doc/broken-anchor" -Phase TODO
```

En Linux / WSL / macOS (`bash`):

```bash
bash scripts/bin/ecc-agy/new-lifecycle-task.sh --task-id "refactor/scripts/cache" --phase PLAN
bash scripts/bin/ecc-agy/sync-ideas-todo.sh
```

---

## 2. Matriz de Paridad 1-a-1 Manual $\leftrightarrow$ Plugin (`aagy` / `ecc`)

| Capacidad del Plugin / Agente | Windows 11 (`pwsh`) | Linux / WSL (`bash`) | Núcleo Python (`scripts/py/`) |
| :--- | :--- | :--- | :--- |
| **Resolver rutas (`docs-map.json`)** | `python scripts/py/docs_map.py --key <k>` | `python3 scripts/py/docs_map.py --key <k>` | [`docs_map.py`](../../scripts/py/docs_map.py) |
| **Validar nombre de rama** | `python scripts/py/validate_branch.py` | `python3 scripts/py/validate_branch.py` | [`validate_branch.py`](../../scripts/py/validate_branch.py) |
| **Instanciar ciclo de vida** | `scripts/bin/ecc-agy/new-lifecycle-task.ps1` | `scripts/bin/ecc-agy/new-lifecycle-task.sh` | [`new_lifecycle_task.py`](../../scripts/py/new_lifecycle_task.py) |
| **Ingerir `IDEAS.md` $\rightarrow$ `TODO.md`** | `scripts/bin/ecc-agy/sync-ideas-todo.ps1` | `scripts/bin/ecc-agy/sync-ideas-todo.sh` | [`sync_ideas_todo.py`](../../scripts/py/sync_ideas_todo.py) |
| **Archivar TODOs `[x]` $\rightarrow$ `done/`** | `scripts/bin/ecc-agy/archive-todo.ps1` | `scripts/bin/ecc-agy/archive-todo.sh` | [`archive_todo.py`](../../scripts/py/archive_todo.py) |
| **Generar Post-Mortem 5W (`fix/*`)** | `scripts/bin/ecc-agy/generate-postmortem.ps1` | `scripts/bin/ecc-agy/generate-postmortem.sh` | [`generate_postmortem.py`](../../scripts/py/generate_postmortem.py) |
| **Auditar enlaces y `docs-map.json`** | `scripts/bin/ecc-agy/map-docs.ps1` | `scripts/bin/ecc-agy/map-docs.sh` | [`map_docs.py`](../../scripts/py/map_docs.py) |
| **Lint/Fix Markdown (DavidAnson)** | `scripts/bin/ecc-agy/lint-markdown.ps1` | `scripts/bin/ecc-agy/lint-markdown.sh` | *(Invoca `npx markdownlint-cli`)* |
| **Auditoría Workspace & Budget** | `scripts/bin/ecc-agy/audit-workspace.ps1` | `scripts/bin/ecc-agy/audit-workspace.sh` | [`workspace_audit.py`](../../scripts/py/workspace_audit.py) |
| **SonarQube Rating A Gate** | `scripts/bin/ecc-agy/sonar-audit.ps1` | `scripts/bin/ecc-agy/sonar-audit.sh` | [`sonar_audit.py`](../../scripts/py/sonar_audit.py) |
| **Seguridad y AgentShield** | `scripts/bin/ecc-agy/security-audit.ps1` | `scripts/bin/ecc-agy/security-audit.sh` | [`security_audit.py`](../../scripts/py/security_audit.py) |
| **Validar formato de commit** | `scripts/bin/ecc-agy/format-commit.ps1` | `scripts/bin/ecc-agy/format-commit.sh` | [`format_commit.py`](../../scripts/py/format_commit.py) |
| **Paridad `aagy` $\leftrightarrow$ `ecc`** | `scripts/bin/ecc-agy/audit-plugin-parity.ps1` | `scripts/bin/ecc-agy/audit-plugin-parity.sh` | [`audit_plugin_parity.py`](../../scripts/py/audit_plugin_parity.py) |
| **Revisión previa e integración PR** | `scripts/bin/ecc-agy/complete-task-pr.ps1` | `scripts/bin/ecc-agy/complete-task-pr.sh` | *(Orquestador TBD + `gh` CLI)* |
| **Promoción Multi-Tier / CD** | `scripts/bin/ecc-agy/git-flow-helper.ps1` | `scripts/bin/ecc-agy/git-flow-helper.sh` | *(Tags `vX.Y.Z-sandbox` / `vX.Y.Z`)* |

---

## 3. Runbook End-to-End en Terminal (Sin Dependencia del Agente)

Secuencia recomendada para completar una tarea manualmente desde línea de comandos en Windows 11 (`pwsh`):

```powershell
# 1. Crear rama aislada desde main actualizado y validar gobernanza
git checkout main; git pull origin main
git checkout -b feat/aagy/mi-cambio
python scripts/py/validate_branch.py

# 2. (Opcional) Instanciar plantilla del punto de entrada elegido
pwsh -NoProfile -File scripts/bin/ecc-agy/new-lifecycle-task.ps1 -TaskId "feat/aagy/mi-cambio" -Phase PLAN

# 3. Implementar siguiendo TDD (RED -> GREEN -> REFACTOR) y verificar suites completas
python -m pytest scripts/py/tests scripts/pwsh/tests scripts/sh/tests -q

# 4. Ejecutar todas las compuertas de calidad antes de PR
pwsh -NoProfile -File scripts/bin/ecc-agy/lint-markdown.ps1 -Fix
pwsh -NoProfile -File scripts/bin/ecc-agy/lint-markdown.ps1 -CheckOnly
pwsh -NoProfile -File scripts/bin/ecc-agy/map-docs.ps1
pwsh -NoProfile -File scripts/bin/ecc-agy/audit-workspace.ps1 -Clean
pwsh -NoProfile -File scripts/bin/ecc-agy/audit-plugin-parity.ps1

# 5. Pre-Flight Review obligatorio y squash-automerge tras verificación
pwsh -NoProfile -File scripts/bin/ecc-agy/complete-task-pr.ps1 -ReviewOnly -Title "[feat]-[aagy]: descripcion concisa"
pwsh -NoProfile -File scripts/bin/ecc-agy/complete-task-pr.ps1 -Yes -Title "[feat]-[aagy]: descripcion concisa"
```
