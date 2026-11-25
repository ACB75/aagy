# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | AAGY ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Resuelve las tareas en el orden de este fichero y respeta `deps=` (números de issue que tienen que estar cerrados antes). Las épicas #103, #80 y #91 están cerradas; queda la validación de la UI en Windows (#122).
> 2. **Flujo Git:** Una rama `<type>/<project>/<name>` y un PR por tarea, con tests unitarios/e2e en verde. Sin `auto-merge`: el merge lo hace una persona.
> 3. **Tarea Final Obligatoria:** Cada ronda de épicas termina con una tarea que revisa toda la documentación y borra lo desfasado (como #97). Depende de todas las demás: cualquier épica o tarea nueva se añade a su `deps=`.
> 4. **Paridad issues ↔ TODO:** Toda issue abierta tiene aquí su tarea con `issue=<N>`, y toda tarea con `issue=` apunta a una issue abierta. Las ideas en `Draft` de `IDEAS.md` no necesitan issue. Lo comprueba `python scripts/py/backlog.py gh-sync --check`; issues, PR y tareas comparten secciones (Motivación, Criterios de aceptación, Paridad, Artefactos).

---

## 1. Backlog Activo

## Épica: UI de Claude Code y Antigravity (#116)

> Status line, avisos de escritorio, `ccusage` opcional y extensiones de VS Code (#116, PR #119), con paridad hasta donde Antigravity lo permite. Runbook: doc/04-operations/runbooks/MANUAL_ui.md

- [ ] **Validar la UI en Windows 11 (status line, toast y CI local)**
  <!-- aagy-task: id=ui-windows-validation epic=ui-de-claude-code-y-antigravity-116 issue=122 deps=116 -->
  - Pendiente, no se hace todavía: cerrar las sesiones de Claude, `git pull --ff-only origin main`,
    `aagy-sync.ps1 generic -Hard`, reinstalar aagy-ecc (sale de la caché 4.4.0), abrir una sesión nueva y
    pasar `/aagy-doctor` y `/aagy-ecc-doctor` antes de revisar los criterios.

## Épica: Plugin autónomo, automejora coste/rendimiento y modos de operación

> Evolución del plugin agnóstico para auto-detectar el stack del repo, optimizar tareas según historial de sesiones (coste/rendimiento) y soportar modo `auto` vs `manual`.

- [ ] **Auto-escaneo de stack del repositorio en el plugin (`aagy-sync --auto` / `SessionStart`)**
  <!-- aagy-task: id=auto-repo-scan epic=plugin-autonomo-y-modos -->
  - **Motivación**: Que al incorporar el plugin en cualquier repo sin configuración previa, detecte automáticamente el stack (`pom.xml`/`build.gradle`, `angular.json`, `go.mod`, `pyproject.toml`, `Dockerfile`/K8s, etc.) y active solo las skills y agentes necesarios.
  - **Criterios de aceptación**: Detección determinista en `repo_profiles.py`, respeto a `.governance/aagy-profiles.json` cuando exista, 0 escritura no autorizada en el repo, tests unitarios en verde.
  - **Paridad**: Mismo motor Python compartido en `aagy` y `aagy-ecc`.
  - **Artefactos**: `scripts/py/repo_profiles.py`, `scripts/py/tests/test_repo_profiles.py`, `doc/02-adr/`.

- [ ] **Automejora y autodescubrimiento orientado a balance coste/rendimiento desde historial de sesiones**
  <!-- aagy-task: id=self-improve-cost-perf epic=plugin-autonomo-y-modos -->
  - **Motivación**: Analizar el historial de sesiones y observaciones para proponer e implementar nuevas skills, agentes o hooks optimizando el balance coste (tokens en catálogo/contexto) vs rendimiento (ahorro de tiempo/pasos repetidos).
  - **Criterios de aceptación**: Scoring coste/rendimiento en `self_improve.py --discover`, filtro automático de `consumer_refs` y rutas absolutas locales, síntesis de artefactos pasando los 4 gates (`AgentShield`, `Budget Gate`, `Smoke-Test`, confirmación según modo).
  - **Paridad**: Mismo motor Python en `aagy` y `aagy-ecc`.
  - **Artefactos**: `scripts/py/self_improve.py`, `scripts/py/tests/test_self_improve.py`, `skills/agent-self-evaluation/SKILL.md`.

- [ ] **Integrar dos modos de operación: `auto` (commit + PR + auto-merge en verde) y `manual` (guardrails por acción)**
  <!-- aagy-task: id=operation-modes-auto-manual epic=plugin-autonomo-y-modos -->
  - **Motivación**: Permitir alternar por configuración (`aagy_config.py`: `workflow.mode` / `AAGY_WORKFLOW_MODE`) entre flujo totalmente autónomo y flujo supervisado.
  - **Criterios de aceptación**:
    - **Modo `auto`**: los flujos de TODO/issues ejecutan commit, creación de PR y auto-merge automáticamente **solo** si todos los tests y quality gates pasan en verde (`exit 0`).
    - **Modo `manual`** (por defecto): salta un guardrail explícito de confirmación ante cada commit, PR, push o acción destructiva.
  - **Paridad**: Misma configuración y hooks en `aagy` y `aagy-ecc`.
  - **Artefactos**: `scripts/py/aagy_config.py`, `scripts/py/complete_task_pr.py`, `scripts/py/hook_safety.py`, `rules/AGENTS.md`, tests unitarios.

## Épica: Flujo GitHub Issues y Projects v2 (cerrada 2026-11-21 por agy)
