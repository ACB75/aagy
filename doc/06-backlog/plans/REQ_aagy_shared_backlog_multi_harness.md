# Fase 1: Toma de Requisitos — Backlog compartido Claude Code (`aagy-ecc`) ↔ Antigravity (`aagy`)

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería AAGY / Home-Lab
> **ID de Tarea**: `feat/aagy/shared-backlog-multi-harness`
> **Fecha**: `2026-11-21` | **Autor/Rol**: `Claude (toma de requisitos) / Master (aprobación)`
> **Estado**: `APROBADO` (Master, 2026-11-21, ver §8)

---

## 0. Estado actual (hallazgos en `main` @ `0f2f363`)

| Pieza | Dónde | Qué hace | Limitación para el trabajo conjunto |
| :--- | :--- | :--- | :--- |
| Backlog canónico | `doc/06-backlog/{IDEAS.md,TODO.md,plans/,quick/,done/}` vía `.governance/docs-map.json` | Ciclo `IDEAS → REQ → PLAN → TODO → done/` | Es un fichero de texto: no hay campo de **dueño**, **estado en curso** ni **bloqueo**. Dos agentes pueden coger la misma tarea. |
| Scripts del ciclo | `scripts/py/new_lifecycle_task.py`, `sync_ideas_todo.py`, `archive_todo.py` (+ wrappers ps1/sh) | Crean REQ/PLAN, ingieren ideas, archivan `- [x]` | Solo existen en la raíz (`aagy`). `aagy-ecc/scripts/py/` solo trae `docs_map.py`: en un repo consumidor Claude no puede ejecutar el ciclo. |
| Skill `todo-lifecycle` + agente `todo-archiver` | `skills/`, `agents/` (espejados en `aagy-ecc/` por `sync_aagy_ecc.py`) | Reglas de 7 fases y archivado | Igual en ambos lados, pero sin noción de "quién trabaja en qué". |
| Listas de tareas nativas | Antigravity: artefactos `task.md` / `implementation_plan.md` de la sesión. Claude Code: `TodoWrite` / `TaskCreate…` | Seguimiento dentro de **una** sesión | Privadas de cada sesión, no persisten ni se ven desde el otro agente. |
| `story-lifecycle` (`.stories/`) | skill opt-in | Ledger local épica → historia → sprint | Se declara a sí mismo "no canónico"; duplicaría a `TODO.md`. |
| Comandos `epic-*` (issues de GitHub) | Citados en `dev-team` y `story-lifecycle` | Coordinación multi-agente con *claim* | **No existen**: no hay `commands/epic-*.md` en ninguno de los dos plugins. |
| SessionStart de `aagy-ecc` | `aagy-ecc/hooks/` | Inyecta `rules/AGENTS.md` | No inyecta el backlog activo, así que Claude no ve qué hay pendiente al arrancar. |

**Conclusión**: ya existe una fuente de verdad compartida (`doc/06-backlog/`). Lo que falta es un **protocolo de coordinación** (dueño, estado, *claim*/*release*, handoff) y que ambos plugins traigan las mismas herramientas para operarlo.

---

## 1. Contexto, Necesidad y Objetivos

- **Problema**: Claude Code y Antigravity trabajan sobre el mismo repositorio pero cada uno lleva su lista de tareas en su propia sesión. No hay forma de que uno recoja, continúe o entregue trabajo del otro sin que Master copie y pegue a mano.
- **Objetivo Principal**: Que ambos agentes lean y actualicen **el mismo backlog y los mismos REQ/PLAN**, con un estado por tarea que diga quién la tiene, en qué rama y qué falta, de forma que cualquiera de los dos pueda continuar la tarea del otro.
- **Alcance (`In-Scope`)**:
  - Formato de tarea con metadatos de coordinación en `TODO.md` (retrocompatible).
  - CLI determinista único (`scripts/py/backlog.py` + wrappers ps1/sh) con `list`, `next`, `claim`, `release`, `handoff`, `done`.
  - Empaquetar en `aagy-ecc` los scripts del ciclo que hoy faltan (espejo vía `sync_aagy_ecc.py`).
  - Comando Claude (`/aagy-todo`) y workflow/skill equivalente en Antigravity con el mismo contrato.
  - Resumen del backlog activo en el arranque de sesión de ambos harnesses.
  - Regla en `rules/AGENTS.md`: la lista nativa de la sesión es borrador; el estado persistente vive en `TODO.md`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Sincronización en tiempo real entre sesiones simultáneas (se resuelve con bloqueo y git, no con un servicio).
  - Integración con Jira/Linear/Taiga.
  - Cambiar la metodología de 7 fases.

---

## 2. Opciones evaluadas

| Opción | Cómo funciona | A favor | En contra |
| :--- | :--- | :--- | :--- |
| **A. Backlog markdown en el repo + protocolo de *claim* (recomendada)** | `TODO.md` sigue siendo la verdad; cada tarea lleva `owner`, `status`, `branch`, `updated`. `backlog.py` edita con bloqueo de fichero. | Reutiliza todo lo existente, cero infraestructura, visible en git y en PRs, funciona offline en FRACTAL. | Si los dos agentes editan en ramas distintas a la vez, el estado se reconcilia al hacer merge (conflictos en `TODO.md`). |
| **B. GitHub Issues como autoridad (comandos `epic-*`)** | Cada tarea es un issue; labels = estado, assignee/label = agente. | Funciona entre máquinas y con sesiones de Claude en la nube; *claim* atómico; historial. | Requiere `gh` y red; más tokens por consulta; duplica `TODO.md` si no se elige uno solo. |
| **C. Servidor MCP local de tareas (SQLite)** | Ambos harnesses se conectan al mismo MCP `aagy-tasks`. | Atómico y en tiempo real. | Proceso nuevo que mantener; el estado no queda en git; más superficie de seguridad. |

**Decisión**: A. Los dos agentes trabajan en el mismo PC (FRACTAL) sobre la misma carpeta, así que no hace falta GitHub Issues ni un servidor. El CLI se diseña con un contrato que permitiría otro *backend* más adelante.

---

## 3. Requisitos Funcionales (`RF`)

- **`RF-01` Formato de tarea**: cada entrada de `TODO.md` admite una línea de metadatos opcional, p. ej. `<!-- aagy-task: id=shared-backlog owner=claude status=in_progress branch=feat/aagy/shared-backlog updated=2026-11-21T05:00Z -->`. Entradas sin metadatos se leen como `owner=none status=todo`.
- **`RF-02` Estados**: `todo → in_progress → review → done`, más `handoff` (pendiente de relevo, ver `RF-11`) y `blocked` (con motivo). `done` se sigue archivando con `archive_todo.py`.
- **`RF-03` Claim/Release**: `backlog.py claim <id> --agent claude|agy` falla si otra entidad la tiene `in_progress` y su `updated` es más reciente que el TTL (4 h, confirmado). `release` y `--force` existen para Master.
- **`RF-04` Handoff**: `backlog.py handoff <id> --to agy --note "..."` deja nota de traspaso (qué se hizo, qué falta, rama) en la propia tarea o en `quick/QUICK_<id>.md`.
- **`RF-05` Next**: `backlog.py next --agent <x>` devuelve la siguiente tarea libre según orden topológico/prioridad del fichero.
- **`RF-06` Concurrencia local**: toda escritura toma un lock (`doc/06-backlog/.backlog.lock`, ignorado en git) y reescribe de forma atómica (temp + rename).
- **`RF-07` Paridad**: el CLI vive en `scripts/py/` y se espeja a `aagy-ecc/scripts/py/` junto con `new_lifecycle_task.py`, `sync_ideas_todo.py`, `archive_todo.py`; `audit_plugin_parity.py` lo verifica.
- **`RF-08` Arranque de sesión**: ambos harnesses muestran al inicio las tareas `in_progress`/`review`/`blocked` y su dueño (máx. ~15 líneas para cuidar el presupuesto de contexto).
- **`RF-09` Regla de gobernanza**: la lista nativa (`TodoWrite`, `task.md` de Antigravity) se usa solo dentro de la sesión; al cerrar o pausar, el agente vuelca el estado a `TODO.md` con `backlog.py`.
- **`RF-10` REQ/PLAN compartidos**: un `REQ_`/`PLAN_` en `plans/` enlaza su tarea por `id`, y cualquiera de los dos agentes puede pasar a la fase siguiente.
- **`RF-11` Relevo por agotamiento de tokens (prioritario)**: cuando un agente se queda sin presupuesto (límite de uso, contexto lleno o fin de sesión), deja la tarea en `status=handoff` con una nota estructurada: objetivo, hecho, pendiente, rama, último commit, ficheros tocados y siguiente comando a ejecutar. Se dispara (a) a mano con `backlog.py handoff`, (b) desde el hook `Stop`/`PreCompact` de `aagy-ecc` y su equivalente en `aagy`, y (c) desde el guardrail de presupuesto de contexto existente cuando supera el umbral. El otro agente, al arrancar, ve primero las tareas en `handoff` y puede hacer `claim` y continuar sin preguntar a Master.
- **`RF-12` Modo simultáneo y modo relevo**: se admiten los dos. En simultáneo, cada agente trabaja en una tarea distinta y el `claim` impide coger la misma. En relevo, la tarea pasa de un agente a otro con `handoff` y se conserva la rama.
- **`RF-14` Épicas y comandos `epic-*`**: una tarea puede llevar `epic=<slug>` en sus metadatos, y una épica es un bloque `## Épica: <título>` en `TODO.md` con sus tareas debajo. Se implementan los comandos `epic-*` que ya citan las skills `dev-team` y `story-lifecycle`, pero sobre `backlog.py` (fichero, no GitHub): `/epic-decompose` (parte un REQ/objetivo en tareas de la épica), `/epic-claim` (coge la siguiente tarea libre de la épica), `/epic-sync` (resume avance, dueños y relevos) y `/epic-close` (archiva cuando todas están `done`). Existen como comandos en `aagy-ecc` y como workflows equivalentes en `aagy`. Las skills se corrigen para decir que la autoridad es `TODO.md`, no GitHub Issues.
- **`RF-13` Repos consumidores del home-lab**: el CLI y los scripts del ciclo funcionan en cualquier repo con `.governance/docs-map.json`. Si el repo no lo tiene, `backlog.py init` crea `doc/06-backlog/` mínimo y el `docs-map.json`. Ambos plugins traen los mismos scripts, así que no dependen de que el repo los copie.

### 3.1. Criterios de Aceptación

- [ ] **`CA-01`**: Dado que Claude hace `claim` de una tarea, cuando Antigravity ejecuta `next`, entonces no la recibe y `list` la muestra con `owner=claude`.
- [ ] **`CA-02`**: Dado un `handoff` de Claude a agy, cuando agy arranca sesión, entonces ve la tarea asignada con la nota de traspaso y la rama.
- [ ] **`CA-03`**: Dos `claim` simultáneos sobre la misma tarea producen exactamente un ganador.
- [ ] **`CA-04`**: Un `TODO.md` actual sin metadatos se lee sin errores y `archive_todo.py` sigue funcionando igual.
- [ ] **`CA-05`**: `sync_aagy_ecc.py --check` y `audit_plugin_parity.py` pasan con los scripts nuevos espejados.
- [ ] **`CA-06`**: Cobertura de tests ≥ 80 % en `backlog.py`.
- [ ] **`CA-07`**: Dado que Claude agota sus tokens en mitad de una tarea, cuando se abre una sesión de agy en la misma carpeta, entonces agy ve la tarea en `handoff` con la nota, hace `claim` y continúa en la misma rama.
- [ ] **`CA-09`**: Dado un REQ aprobado, cuando Claude ejecuta `/epic-decompose`, entonces `TODO.md` contiene la épica con sus tareas en `todo`, y agy puede hacer `/epic-claim` sobre ella.
- [ ] **`CA-08`**: En un repo del home-lab sin `doc/06-backlog/`, `backlog.py init` lo crea y `list` funciona desde los dos plugins.

---

## 4. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión | ¿Impactado? | Riesgo | Detalle |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Solo harness. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Estado en markdown (opción A). |
| **Ingress Único (`cluster-lb`)** | `NO` | - | - |
| **Resolución Split-DNS** | `NO` | - | - |
| **Restricciones de Hardware** | `NO` | Bajo | Script corto, sin proceso residente. |
| **Variables `.env` / Secretos** | `NO` | - | Opción B necesitaría token de `gh`, ya presente en FRACTAL. |

---

## 5. Retrocompatibilidad

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva**: metadatos en comentario HTML opcional (invisible al render y a `markdownlint`); entradas antiguas válidas por defecto; scripts existentes no cambian su interfaz.

---

## 6. Rendimiento y Presupuesto de Contexto

- `list`/`next` en O(n) sobre `TODO.md`; resumen de arranque acotado a ~15 líneas.
- Sin dependencias nuevas (stdlib de Python).

---

## 7. Threat Modeling

| Amenaza | Riesgo | Mitigación |
| :--- | :---: | :--- |
| **Inyección en notas de handoff** | Bajo | Las notas se tratan como texto; nunca se ejecutan ni se interpolan en comandos. |
| **Path Traversal en `id`** | Bajo | `id` validado con `^[a-z0-9]+(-[a-z0-9]+)*$`, máx. 64. |
| **Lock huérfano** | Medio | Lock con PID + timestamp y expiración; `release --force`. |
| **Prompt injection vía backlog** | Medio | La regla en `AGENTS.md` trata el contenido de tareas como datos, no como órdenes de seguridad. |

---

## 8. Respuestas de Master (2026-11-21)

1. **Dónde**: los dos en el mismo PC (FRACTAL), misma carpeta. → Opción A.
2. **Modo**: los dos, simultáneo y por relevos, sobre todo cuando uno se queda sin tokens. → `RF-11`, `RF-12`.
3. **Alcance**: también los repos del home-lab. → `RF-13`.
4. **Comandos `epic-*`**: una épica es un objetivo grande partido en tareas pequeñas. Master decidió mantenerlos y usarlos. → `RF-14`, implementados sobre `TODO.md` (no GitHub Issues).
5. **TTL del `claim`**: 4 h sin actualizar, confirmado. → `RF-03`.
