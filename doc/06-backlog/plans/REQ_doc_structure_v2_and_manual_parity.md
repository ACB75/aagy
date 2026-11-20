# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `refactor/aagy/doc-structure-v2-manual-parity`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Documentation Governance & Developer Experience Architect`  
> **Estado**: `APROBADO`

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**: La estructura actual de `doc/` mezcla documentos vivos (`INDEX.md`, `STATUS.md`, `LOG.md`) con backlog (`TODO.md`, `IDEAS.md`), guías sueltas (`README.md`, `STACK_MODERNO_GOOGLE.md`, `the-security-guide.md`) y rutas acopladas en 12 scripts. Además, faltan carpetas estructuradas para contexto técnico (`CONTEXT.md`), dominio/flujos (`.puml`, `.bpmn`, `.mmd`) y operaciones (`runbooks/`, `setup-guides/`), así como un mapeo 1-a-1 para que el usuario pueda ejecutar manualmente en terminal el mismo flujo que ejecuta el plugin.
- **Objetivo Principal**: Definir e implantar la arquitectura documental `/doc` v2 (numerada `00-governance`..`06-backlog`), parametrizar las rutas en `.governance/docs-map.json` con retrocompatibilidad, soportar el flujo flexible `[IDEAS -> REQUISITOS -> PLAN -> TODO]` desde cualquier punto de entrada y garantizar paridad 1-a-1 entre ejecución manual y plugin.
- **Alcance (`In-Scope`)**:
  - Nueva jerarquía `/doc` v2:
    - Raíz `/doc`: `INDEX.md` (se elimina duplicidad con `doc/README.md`, dejando `README.md` solo en la raíz del repo), `CONTEXT.md`, `STATUS.md`, `LOG.md`.
    - `00-governance/`: `DOC_STANDARDS.md`, `MANUAL_WORKFLOW.md`, `references/the-security-guide.md`, `references/google-modern-stack.md` (rename de `STACK_MODERNO_GOOGLE.md`), y `templates/` (`TEMPLATE_ADR.md`, `TEMPLATE_POSTMORTEM.md`, `TEMPLATE_REQUISITOS_ARQUITECTURA.md` y plantillas `01..04_*` del lifecycle).
    - `01-architecture/`: `api-contracts/` y `dgrms/` (`c4-context.mmd`, `network-topology.mmd`, etc.).
    - `02-adr/`: `ADR-NNNN-*.md`.
    - `03-domain-and-flows/`: `business-processes/`, `domain-models/`, `sequences/` y `dgrms/`.
    - `04-operations/`: `runbooks/` y `setup-guides/`.
    - `05-post-mortems/`: `PM_<id>_<fecha>.md`.
    - `06-backlog/`: `IDEAS.md`, `TODO.md`, `done/`, `plans/`, `quick/`.
  - Convención transversal `<folder>/dgrms/` separando `.puml` (casos de uso), `.bpmn` (negocio) y `.mmd` (dominio, arquitectura, actividad y flujo).
  - Parametrización de los 12 scripts en `scripts/py/` y `scripts/pwsh/` leyendo `.governance/docs-map.json` con *fallback* a rutas heredadas.
  - Absorción de la antigua `Tarea 3.5` (renames de `TEMPLATE_ADR.md` y `TEMPLATE_POSTMORTEM.md`) para evitar doble movimiento.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Re-escribir el contenido histórico de ADRs o `TODO_DONE/` ya archivados (solo se reubican y actualizan enlaces).
  - Ejecutar en este paso la migración física `/ecc` $\rightarrow$ `/aagy` (`Tarea 5.1`, que permanece como última tarea del backlog).

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Jerarquía `/doc` v2 Limpia y Sin Duplicidad)**: Raíz `/doc` contiene exclusivamente `INDEX.md`, `CONTEXT.md`, `STATUS.md` y `LOG.md`. `the-security-guide.md` se conserva en `00-governance/references/` y `STACK_MODERNO_GOOGLE.md` se renombra a `google-modern-stack.md` siguiendo convenciones del proyecto.
- **`RF-02` (Convención Universal de Diagramas `<folder>/dgrms/`)**: Toda carpeta con diagramas utiliza la subcarpeta `dgrms/` organizando `.puml` (casos de uso), `.bpmn` (procesos de negocio) y `.mmd` (dominio, arquitectura, actividad y flujo), documentado en `00-governance/DOC_STANDARDS.md`.
- **`RF-03` (Parametrización de Rutas en `.governance/docs-map.json`)**: Todos los scripts (`archive_todo.py`, `sync_ideas_todo.py`, `new_lifecycle_task.py`, `generate_postmortem.py`, `complete-task-pr.ps1`, `format_commit.py`, `map-docs.ps1`, `lint-markdown.ps1`) resuelven las rutas dinámicamente desde `.governance/docs-map.json` con *fallback* automático a las rutas clásicas (`doc/TODO.md`, `doc/adr/`, etc.) para mantener compatibilidad con `home-lab`.
- **`RF-04` (Flujo Flexible `[IDEAS -> REQUISITOS -> PLAN -> TODO]`)**: Los scripts y plantillas permiten iniciar trabajo desde cualquiera de los 4 puntos de entrada (`IDEAS`, `REQ`, `PLAN` o `TODO`) sin forzar pasos previos innecesarios cuando la tarea ya está definida.
- **`RF-05` (Paridad 1-a-1 Manual $\leftrightarrow$ Plugin)**: Cada operación automatizada por el plugin (`aagy` / `ecc`) dispone de un comando CLI idempotente documentado en `00-governance/MANUAL_WORKFLOW.md` para su ejecución manual en terminal, incluyendo el ciclo Git (`validate_branch.py`, `complete-task-pr.ps1` con gate obligatorio de `pytest` + `lint-markdown` + SonarQube).
- **`RF-06` (Absorción de `Tarea 3.5`)**: Los renames `TEMPLATE_ADR.md` y `TEMPLATE_POSTMORTEM.md` se aplican directamente en `00-governance/templates/` dentro de esta intervención.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [ ] **`CA-01`**: Dado el nuevo árbol `/doc` v2, cuando se ejecuten `lint-markdown.ps1` y `audit-workspace.ps1`, entonces ambos devolverán código de salida `0` y cero enlaces rotos en `INDEX.md` y `.governance/docs-map.json`.
- [ ] **`CA-02`**: Dado un repositorio con estructura v2 (este repo) y otro con estructura clásica (`home-lab`), cuando se ejecuten `archive_todo.py`, `sync_ideas_todo.py`, `new_lifecycle_task.py` y `generate_postmortem.py`, entonces resolverán las rutas correctas en ambos casos sin error.
- [ ] **`CA-03`**: Dado el parámetro `-Phase` (o equivalente) en `new-lifecycle-task.ps1` y el flujo manual en `MANUAL_WORKFLOW.md`, cuando el usuario inicie desde `IDEAS`, `REQ`, `PLAN` o `TODO`, entonces podrá completar el flujo end-to-end hasta `complete-task-pr.ps1` (con `pytest` 100% verde) sin depender del agente.
- [ ] **`CA-04`**: Cobertura de tests unitarios/integración $\ge 80\%$ sobre la nueva lógica de resolución de rutas y flujo flexible (`pytest` en verde, exit code `0`).

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | No modifica contratos de microservicios ni DTOs de `home-lab-sdk`. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin cambios en bases de datos ni DDL. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin cambios en Traefik, Apache ni Split-DNS. |
| **Resolución Split-DNS** | `NO` | - | Sin impacto. |
| **Restricciones de Hardware** | `NO` | - | Scripts ligeros en Python stdlib / PowerShell. |
| **Compatibilidad Scripts `home-lab`** | `SÍ` | `Medio` | `home-lab` usa actualmente la estructura clásica `doc/`. Mitigación: `.governance/docs-map.json` con *fallback* automático garantiza operación 100% retrocompatible hasta que `home-lab` adopte v2. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

> **Invariante Canónico**: Queda terminantemente prohibido introducir cambios destructivos o de ruptura en consumidores existentes sin ruta de transición.

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible vía Fallback) | [ ] SÍ (Excepción Aprobada)`
- **Estrategia Aditiva (Non-Breaking)**:
  - Los scripts leen `.governance/docs-map.json` si declara `paths` / esquema v2; en ausencia de la clave o del archivo, hacen *fallback* transparente a las rutas clásicas (`doc/TODO.md`, `doc/TODO_DONE/`, `doc/plan/`, `doc/adr/`, `doc/post-mortem/`).

---

## 5. Compuertas SRE de Rendimiento y Persistencia Segura

- **Tiempo de Ejecución**: La resolución de `.governance/docs-map.json` añade $< 5\text{ ms}$ en Python stdlib; `audit-workspace.ps1` y `lint-markdown.ps1` completan en $< 10\text{ s}$.
- **Persistencia**: Uso exclusivo de `git mv` para preservar trazabilidad de archivos reubicados.

---

## 6. Threat Modeling y Bastionado de Seguridad

| Vector de Ataque / Amenaza | Riesgo (`Bajo/Medio/Alto/N/A`) | Mitigación y Bastionado Aplicado |
| :--- | :---: | :--- |
| **Path Traversal desde `docs-map.json`** | `Medio` | Validar que toda ruta leída de `.governance/docs-map.json` resuelva dentro de `RepoRoot` (`resolve().relative_to(repo_root)`). |
| **Merge de código con tests rotos** | `Alto` | `complete-task-pr.ps1` bloquea la PR/merge si `pytest`, `lint-markdown` o `sonar-audit` devuelven código distinto de `0`. |
| **Pérdida de plantillas o enlaces rotos** | `Bajo` | Verificación obligatoria con `audit-workspace.ps1` y `git mv` en Fase 3/4. |
