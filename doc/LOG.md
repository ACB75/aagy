# Registro Histórico de Decisiones y Cambios Materiales | AAGY / `aagy` Ecosystem

> **Espina Dorsal de Gobernanza Documental**: [ACB75/aagy](https://github.com/ACB75/aagy) (`aagy` -> `aagy`)  
> **Versión Canónica**: `4.1.0`

---

## 2026-11-21: Comandos de Diagnóstico `/aagy-doctor` y `/aagy-ecc-doctor`

### Hitos y Decisiones Materiales

1. **Dos doctors con paridad 1:1**: [`aagy_doctor.py`](../scripts/py/aagy_doctor.py) (Antigravity) y [`aagy_ecc_doctor.py`](../aagy-ecc/scripts/py/aagy_ecc_doctor.py) (Claude Code) implementan el catálogo común `DOC-01..14` de [`doctor_core.py`](../scripts/py/doctor_core.py). [`audit_plugin_parity.py`](../scripts/py/audit_plugin_parity.py) falla si sus IDs divergen.
2. **Solo lectura por defecto**: `--fix` muestra el plan y aplica cada arreglo tras confirmarlo (`--yes` para no preguntar). Salida humana o `--json`; exit `0`/`1`/`2`.
3. **Manifiesto de instalación**: los instaladores escriben `.aagy-install.json` (harness, fase, versión, commit, repo de origen) con [`install_manifest.py`](../scripts/py/install_manifest.py).
4. **Puntos de entrada**: skill [`aagy-doctor`](../skills/aagy-doctor/SKILL.md) (añadida a la fase `generic` y excluida del espejo de aagy-ecc) y comando [`/aagy-ecc-doctor`](../aagy-ecc/commands/aagy-ecc-doctor.md). Wrappers en `scripts/ps1/` y `scripts/sh/`. Requisitos y plan en [`doc/06-backlog/plans/`](06-backlog/plans/REQ_aagy_doctor_commands.md); manual en [`MANUAL_aagy_doctor.md`](04-operations/runbooks/MANUAL_aagy_doctor.md).

---

## 2026-11-20: Paridad Real `aagy-ecc` para Claude Code (Espejo, Hooks Python y Auditoría Estricta)

### Hitos y Decisiones Materiales

1. **Espejo generado dentro del plugin**: Claude Code solo carga archivos de la carpeta del plugin, así que [`sync_aagy_ecc.py`](../scripts/py/sync_aagy_ecc.py) copia `skills/` (169), `agents/` (49), `rules/AGENTS.md` y los motores Python de self-improve en `aagy-ecc/`. Wrappers `scripts/ps1/sync-aagy-ecc.ps1` y `scripts/sh/sync-aagy-ecc.sh`.
2. **Hooks reescritos**: el `hooks.json` heredado llamaba a ~25 scripts Node inexistentes. Sustituido por hooks Python stdlib equivalentes a los de `aagy`: `SessionStart` (inyecta `rules/AGENTS.md`), `PreToolUse` safety gate, `PostToolUse` markdownlint y `Stop` self-improve.
3. **Limpieza**: retirados restos de otros harnesses (`hermes`, `codex`, `qoder`, `cursor`, `memory-persistence`, `agent.yaml`, `SOUL.md`, `.claude/` generado) y 50 comandos que dependían de scripts, skills o subagentes inexistentes. `CLAUDE.md` pasa a [`project-template/`](../aagy-ecc/project-template/CLAUDE.md).
4. **Auditoría de paridad estricta**: [`audit_plugin_parity.py`](../scripts/py/audit_plugin_parity.py) ya no cuenta las skills de la raíz cuando falta `aagy-ecc/skills/`; ahora detecta deriva de contenido, scripts de hooks ausentes, versión y marketplace.
5. **Frontmatter**: corregidas 5 skills con `description` YAML inválido (`module-regression`, `change-impact`, `context-and-decisions`, `prompt-caching-strategy`, `recursive-decision-ledger`). Versión `4.1.0` alineada en `plugin.json` raíz y `aagy-ecc`.

---

## 2026-11-20: Cierre Maestro — Migración a `/aagy` (`Anything Antigravity`), Nuevo `README.md`, Sincronización `aagy-ecc` y Reinstalación Limpia (`Tarea 5.1`)

### Hitos y Decisiones Materiales

1. **Nuevo `README.md` Raíz y Sincronización `aagy-ecc/`**:
   - Regenerado [`README.md`](../README.md) de raíz reflejando la arquitectura definitiva (`aagy` + `aagy-ecc/`, `/doc` v2 con `.governance/docs-map.json`, `scripts/{py,ps1,sh}/tests/`, motor `self_improve.py`, instalación manual `install.ps1` / `install.sh` y paridad CLI 1-a-1).
   - Sincronizados [`aagy-ecc/README.md`](../aagy-ecc/README.md) y [`aagy-ecc/project-template/CLAUDE.md`](../aagy-ecc/project-template/CLAUDE.md) con paridad verificada al 100% mediante [`audit_plugin_parity.py`](../scripts/py/audit_plugin_parity.py).
2. **Cutover a `c:\Workspace\projects\aagy` Conservando Historial Git y Reinstalación Limpia del Plugin**:
   - Construido y sincronizado `c:\Workspace\projects\aagy` conservando el historial Git íntegro y el remoto renombrado `https://github.com/ACB75/aagy.git`.
   - Reinstalado limpiamente el plugin global en `~/.gemini/config/plugins/aagy` mediante `install.ps1 -Target agy -Profile minimal` y superadas todas las compuertas (`pytest` 154/154, `audit-workspace.ps1 -Clean`, `audit-plugin-parity.ps1`, `map-docs.ps1`, `audit-docs.py`, `lint-markdown.ps1 -CheckOnly`, SonarQube Rating A).

---

## 2026-11-20: Limpieza de Raíz, Consolidación Final de `scripts/`, Compactación de `rules/AGENTS.md` (< 12 KB) y Paridad `aagy-ecc` (`Tarea 0.4`)

### Hitos y Decisiones Materiales

1. **Consolidación Final de `scripts/{py,ps1,sh}/tests/` y Purga de Raíz**:
   - Eliminados los directorios proxy heredados `scripts/bin/` y `scripts/aagy/`, junto con los scripts `scripts/*.js` y `scripts/lib/` del antiguo instalador Node.js.
   - Purgados en raíz `manifests/`, `schemas/`, `templates/` (reubicando la plantilla opcional Gemini MCP en [`skills/gemini-deep-ops/templates/gemini-mcp/`](../skills/gemini-deep-ops/templates/gemini-mcp/README.md)), `.gemini/GEMINI.md`, `plugin.json`, `VERSION`, `package-lock.json` y `.vscode/aagy.code-workspace`.
   - Trasladados `aagy-sync.ps1` y `aagy-sync.sh` a [`scripts/ps1/aagy-sync.ps1`](../scripts/ps1/aagy-sync.ps1) y [`scripts/sh/aagy-sync.sh`](../scripts/sh/aagy-sync.sh), manteniendo en raíz [`install.ps1`](../install.ps1) e [`install.sh`](../install.sh).
2. **Compactación de `rules/AGENTS.md` (< 12 KB), `AGENTS.md` Raíz y Retiro de Copia Duplicada `aagy`**:
   - Fusionada `rules/pr-automerge-lifecycle.md` dentro de [`rules/AGENTS.md`](../rules/AGENTS.md) y compactado el archivo único a `< 12 KB` (~7.8 KB / ~2.050 tokens) delegando tutoriales a skills *lazy-loaded*.
   - Reducido [`AGENTS.md`](../AGENTS.md) de raíz a 14 líneas (~1 KB) preservando el marcador de Prompt Caching y retirada la copia duplicada `~/.gemini/config/plugins/aagy` dejando únicamente `~/.gemini/config/plugins/aagy`.
3. **Renombrado y Paridad Total `aagy-ecc/`**:
   - Renombrado `aagy/` a `aagy-ecc/`, actualizados [`package.json`](../package.json) (`workspaces: ["aagy-ecc"]`), [`aagy-ecc/package.json`](../aagy-ecc/package.json), [`aagy-ecc/.claude-plugin/plugin.json`](../aagy-ecc/.claude-plugin/plugin.json) y [`audit_plugin_parity.py`](../scripts/py/audit_plugin_parity.py).

---

## 2026-11-20: Motor Unificado de Autodescubrimiento, Instintos a Doble Nivel y Automejora con Budget Gate (`Tarea 0.3`)

### Hitos y Decisiones Materiales

1. **Motor Unificado y Agnóstico (`scripts/py/self_improve.py` + `instinct_manager.py`)**:
   - Unificación de `auto-evolve.ps1`/`.sh`, `instinct_manager.py` y `agent-self-evaluation` en [`scripts/py/self_improve.py`](../scripts/py/self_improve.py) eliminando todo acoplamiento hardcodeado a `home-lab` (`RF-05`).
   - Captura híbrida zero-overhead (`RF-01`): hook pasivo `Stop` en [`hooks.json`](../hooks.json) (`< 500 ms`, timeout `5s`, `0` tokens en prompt, retorno `{}` con aislamiento de fallos) y CLI manual (`--discover`, `--review`, `--promote`, `--capture-stop`, `--evaluate`).
   - Persistencia a doble nivel (`RF-02`): `<repo>/.agents/instincts/` (nivel proyecto) y `$PLUGIN_DATA/instincts/` (resuelto vía `AGY_PLUGIN_DATA`, `CLAUDE_PLUGIN_DATA` o `~/.gemini/config/plugins/aagy/.data`).
2. **Sanitización AgentShield, Redacción de Secretos y Promoción por 4 Compuertas (`RF-03` & `RF-04`)**:
   - Redacción automática de credenciales (`Bearer`, `API_KEY`, `password`, GitHub/AWS/Google keys $\rightarrow$ `[REDACTED]`) y bloqueo de vectores de *prompt injection* antes de persistir o promover.
   - Promoción controlada por 4 compuertas (AgentShield, Hard Gate de presupuesto de [`workspace_audit.py`](../scripts/py/workspace_audit.py), *smoke-test* en directorio efímero y confirmación explícita `--confirm`).
3. **Consolidación de Skills Redundantes y Documentación**:
   - Consolidadas `continuous-learning`, `continuous-learning-v2` y `eval-harness` dentro de [`skills/agent-self-evaluation/SKILL.md`](../skills/agent-self-evaluation/SKILL.md) (descripción $\le 140$ caracteres) y [`eval-driven-development.md`](../skills/agent-self-evaluation/references/eval-driven-development.md).
   - Manual operativo en [`MANUAL_unified_self_improvement.md`](04-operations/runbooks/MANUAL_unified_self_improvement.md) y suite [`test_self_improve.py`](../scripts/py/tests/test_self_improve.py) (154/154 tests pasando, SonarQube Rating A).

---

## 2026-11-20: Estructura Documental `/doc` v2, `.governance/docs-map.json` y Paridad 1-a-1 Manual

### Hitos y Decisiones Materiales

1. **Nueva Arquitectura `/doc` v2 y Purga de Planes Obsoletos (`ADR-0003`)**:
   - Raíz de [`doc/`](INDEX.md) saneada a 4 archivos vivos (`INDEX.md`, [`CONTEXT.md`](CONTEXT.md), [`STATUS.md`](STATUS.md), [`LOG.md`](LOG.md)), eliminando la duplicidad de `doc/README.md`.
   - Creación de jerarquía numerada (`00-governance/` a `06-backlog/`) y convención transversal `<folder>/dgrms/` separando `.mmd`, `.puml` ([`UC_aagy_lifecycle_parity.puml`](03-domain-and-flows/dgrms/UC_aagy_lifecycle_parity.puml)) y `.bpmn` ([`BP_aagy_task_delivery.bpmn`](03-domain-and-flows/dgrms/BP_aagy_task_delivery.bpmn)).
   - Consolidación de `TEMPLATE_ADR.md` y `TEMPLATE_POSTMORTEM.md` en [`00-governance/templates/`](00-governance/templates/README.md), preservación de [`the-security-guide.md`](00-governance/references/the-security-guide.md) y renombre de `STACK_MODERNO_GOOGLE.md` a [`google-modern-stack.md`](00-governance/references/google-modern-stack.md).
2. **Resolvedor Parametrizado `docs_map.py` y Retrocompatibilidad `home-lab`**:
   - Implementado [`scripts/py/docs_map.py`](../scripts/py/docs_map.py) con esquema `.governance/docs-map.json` v2, bloqueo estricto contra *path traversal* y *fallback* automático transparente hacia rutas heredadas de `home-lab`.
   - Parametrizados todos los scripts (`archive_todo.py`, `sync_ideas_todo.py`, `new_lifecycle_task.py`, `generate_postmortem.py`, `map_docs.py`, `workspace_audit.py`, `complete-task-pr.ps1`/`.sh` y wrappers `.ps1`/`.sh`).
3. **Flujo Flexible y Paridad Manual 1-a-1 (`MANUAL_WORKFLOW.md`)**:
   - Habilitados los 4 puntos de entrada `[IDEAS -> REQ -> PLAN -> TODO]` en `new_lifecycle_task.py --phase` y completados wrappers Linux faltantes (`sync-ideas-todo.sh`, `generate-postmortem.sh`, `map-docs.sh`).
   - Documentados estándares en [`DOC_STANDARDS.md`](00-governance/DOC_STANDARDS.md) y matriz completa de terminal en [`MANUAL_WORKFLOW.md`](00-governance/MANUAL_WORKFLOW.md).

---

## 2026-11-20: Optimización Máxima de Tokens, Purga de Artefactos Muertos y Reestructuración `scripts/`

### Hitos y Decisiones Materiales

1. **Poda y Lazy-Loading de Reglas**:
   - Deduplicado `AGENTS.md` raíz (< 1 KB) como puntero ligero con marcador de Prompt Caching, consolidando `rules/` en `AGENTS.md` + `AGENTS.md` y migrando 37 reglas de stack a skills *on-demand* (incl. `typescript-patterns`).
2. **Reorganización Multi-Runtime `scripts/{py,ps1,sh}/tests/`**:
   - Separación limpia por runtime con suites dedicadas (`120/120` tests) y proxies retrocompatibles en `scripts/ps1/` y `scripts/py/`. Ver [`MANUAL_scripts_and_token_optimization.md`](04-operations/runbooks/MANUAL_scripts_and_token_optimization.md).

---

## 2026-11-20: Cierre Maestro — Migración a Anything Antigravity (aagy) y Paridad con Claude Code

### Hitos y Decisiones Materiales

1. **Rebranding Maestro a Anything Antigravity (`aagy`)**:
   - Rebranding estructural del ecosistema unificado a **Anything Antigravity (`aagy`)**, manteniendo el historial Git completo (`git log` intacto).
   - Consolidación del subplugin para Anthropic Claude Code en `aagy/aagy/`, garantizando una arquitectura multi-harness coordinada y sin acoplamientos.
   - Actualización de identificadores en `plugin.json` (`name: aagy`, `displayName: Anything Antigravity (aagy)`).
2. **Linter Automático de Paridad de Plugins (`audit_plugin_parity.py`)**:
   - Analizador de simetría estructural y de capacidades entre el plugin raíz `aagy` y el subplugin `aagy/`.
   - Verificación de consistencia de manifiestos, coincidencia de nombres e integración en el paso 7.6 de `complete-task-pr.ps1` y `complete-task-pr.sh`.
   - Wrappers `scripts/ps1/audit-plugin-parity.ps1` y `audit-plugin-parity.sh`.
3. **Calidad y Documentación**:
   - Manual operativo [`doc/manual/MANUAL_aagy_ecc_parity_and_migration.md`](01-architecture/MANUAL_aagy_ecc_parity_and_migration.md).
   - Suite de pruebas `test_audit_plugin_parity.py` con cobertura completa.
   - SonarQube Rating A (0 violaciones), markdownlint 100% compliant.

---

## 2026-11-20: Automatización de Despliegue Tagged y Sondas de Salud en git-flow-helper

### Hitos y Decisiones Materiales

1. **Pipeline de Despliegue Multi-Tier (`git-flow-helper.ps1` y `git-flow-helper.sh`)**:
   - Integración de los parámetros `-Deploy`, `-Environment [sandbox|live]` y `-DryRun` en la acción `promote`.
   - Soporte para despliegue físico desatendido en los hosts de Home-Lab: FRACTAL (`192.168.1.100`) para SANDBOX y NEO (`192.168.1.200`) para LIVE.
   - Verificación de sondas de salud (liveness probes con 3 reintentos x 5s) sobre contenedores recién recreados.
   - Protocolo de rollback automático desatendido en $< 2\text{ minutos}$ hacia el commit/tag anterior ante fallos en sondas.
2. **Ergonomía y Calidad**:
   - Modo de simulación `-DryRun` para comprobar el plan de ejecución sin mutaciones físicas.
   - Manual operativo [`doc/manual/MANUAL_multitier_deployment.md`](04-operations/runbooks/MANUAL_multitier_deployment.md).
   - Suite de pruebas [`scripts/py/tests/test_git_flow_deploy.py`](../scripts/py/tests/test_git_flow_deploy.py) con 3/3 tests pasando (total 111/111 superados al 100%).
   - SonarQube Rating A (0 violaciones), markdownlint 100% compliant.

---

## 2026-11-20: Validador de Congruencia Ingress Traefik, Split-DNS y Catálogo Portal

### Hitos y Decisiones Materiales

1. **Validador Trilateral de Congruencia (`validate_ingress_routes.py`)**:
   - Extracción léxica de hostnames en etiquetas Traefik (`docker-compose*.yml`), registros Split-DNS (`Corefile` de CoreDNS) y servicios catalogados en `/portal` (`cluster/cmd/server/main.go`).
   - Detección de subdominios huérfanos sin entrada en DNS o sin visibilidad en el portal.
   - Generador de sugerencias exactas de configuración (`--fix`) para Corefile y código Go.
   - Omisión limpia (`SKIPPED`, exit code 0) en repositorios sin infraestructura compose ni CoreDNS.
2. **Ergonomía CLI e Integración en Lifecycle**:
   - Wrappers multiplataforma [`scripts/ps1/validate-ingress-routes.ps1`](../scripts/ps1/validate-ingress-routes.ps1) y `validate-ingress-routes.sh` con flags `--fix`, `--json` y `--no-strict`.
   - Integración como compuerta de validación previa en el paso 7.5 de [`complete-task-pr.ps1`](../scripts/ps1/complete-task-pr.ps1) y `complete-task-pr.sh`.
3. **Calidad y Documentación**:
   - Manual operativo [`doc/manual/MANUAL_ingress_routes_validator.md`](04-operations/runbooks/MANUAL_ingress_routes_validator.md).
   - Suite de pruebas [`scripts/py/tests/test_validate_ingress_routes.py`](../scripts/py/tests/test_validate_ingress_routes.py) con 6/6 tests pasando (total 108/108 superados al 100%).
   - SonarQube Rating A (0 violaciones), markdownlint 100% compliant.

---

## 2026-11-20: Analizador Estático de Bloqueos DDL y Concurrencia en PostgreSQL LTS

### Hitos y Decisiones Materiales

1. **Analizador Estático de Bloqueos DDL (`audit_pg_locks.py`)**:
   - Clasificación léxica de sentencias SQL en tres niveles de riesgo (`HIGH`, `MEDIUM`, `LOW`).
   - Detección de bloqueos críticos `ACCESS EXCLUSIVE` y reescritura de tablas (`DROP TABLE`, `TRUNCATE`, `DROP COLUMN`, `ALTER COLUMN TYPE`, `ADD CONSTRAINT` sin `NOT VALID`, y `DEFAULT` volátiles).
   - Detección de bloqueos `SHARE` sobre escrituras (`CREATE INDEX` y `DROP INDEX` sin `CONCURRENTLY`).
   - Sugerencias inmediatas de remediación segura para garantizar disponibilidad en PostgreSQL LTS multitenant.
   - Exclusión automática de directorios internos (`.git`, `node_modules`, `skills`, `.agents`) en escaneos de árbol.
2. **Ergonomía CLI e Integración en Lifecycle**:
   - Wrappers multiplataforma [`scripts/ps1/audit-pg-locks.ps1`](../scripts/ps1/audit-pg-locks.ps1) y `audit-pg-locks.sh` con flags `--file`, `--dir`, `--json` y `--no-strict`.
   - Integración en la compuerta de validación previa en el paso 7.4 de [`complete-task-pr.ps1`](../scripts/ps1/complete-task-pr.ps1) y `complete-task-pr.sh`.
3. **Calidad y Documentación**:
   - Manual operativo [`doc/manual/MANUAL_audit_pg_locks.md`](04-operations/runbooks/MANUAL_audit_pg_locks.md).
   - Suite de pruebas [`scripts/py/tests/test_audit_pg_locks.py`](../scripts/py/tests/test_audit_pg_locks.py) con 8/8 tests pasando (total 102/102 superados al 100%).
   - SonarQube Rating A (0 violaciones), markdownlint 100% compliant.

---

## 2026-11-20: Linter de Paridad Estática de Contratos entre Microservicios y SDK

### Hitos y Decisiones Materiales

1. **Analizador Estático de Paridad (`audit_sdk_parity.py`)**:
   - Extracción léxica de endpoints REST en controladores backend: Go (Gin, Chi, gorilla/mux), Python (FastAPI/Flask) y Java (Spring Boot `@GetMapping`, `@PostMapping`, etc.).
   - Extracción de rutas y métodos en clientes polyglot de `home-lab-sdk/` (TypeScript, Go, Python, Java).
   - Exclusión automática de endpoints internos de infraestructura (`/metrics`, `/health`, `/livez`, `/readyz`, `/debug/*`, `/ping`, `/favicon.ico`).
   - Omisión elegante (`SKIPPED`, exit code 0) en repositorios sin carpetas `services/` ni `home-lab-sdk/`.
2. **Ergonomía CLI e Integración en Lifecycle**:
   - Wrappers multiplataforma [`scripts/ps1/audit-sdk-parity.ps1`](../scripts/ps1/audit-sdk-parity.ps1) y `audit-sdk-parity.sh` con flags `--json` y `--no-strict`.
   - Integración como compuerta de validación previa en el paso 7.3 de [`complete-task-pr.ps1`](../scripts/ps1/complete-task-pr.ps1).
3. **Calidad y Documentación**:
   - Manual operativo [`doc/manual/MANUAL_sdk_parity_audit.md`](04-operations/runbooks/MANUAL_sdk_parity_audit.md).
   - Suite de pruebas [`scripts/py/tests/test_audit_sdk_parity.py`](../scripts/py/tests/test_audit_sdk_parity.py) con 6/6 tests pasando (total 94/94 pasando al 100%).
   - SonarQube Rating A (0 violaciones), markdownlint 100% compliant.

---

## 2026-11-20: Reubicación y Estandarización de Plantillas Documentales (ADR y Post-Mortem)

### Hitos y Decisiones Materiales

1. **Estandarización de Ubicaciones y Nombres Canónicos**:
   - `doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` trasladado canónicamente a [`doc/adr/TEMPLATE_ADR.md`](00-governance/templates/TEMPLATE_ADR.md).
   - `doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md` renombrado canónicamente a [`doc/post-mortem/TEMPLATE_POSTMORTEM.md`](00-governance/templates/TEMPLATE_POSTMORTEM.md).
2. **Refactorización de Referencias en Código y Documentación**:
   - Actualizadas referencias en `scripts/py/generate_postmortem.py` y `scripts/ps1/generate-postmortem.ps1` con retrocompatibilidad ante templates existentes.
   - Actualizadas referencias en `README.md`, `doc/INDEX.md`, `doc/README.md`, `.gemini/GEMINI.md`, `rules/common/development-workflow.md` y planes históricos.
3. **Calidad y Verificación**:
   - Suite [`scripts/py/tests/test_generate_postmortem.py`](../scripts/py/tests/test_generate_postmortem.py) con test específico de path por defecto.
   - 88/88 tests pasando, markdownlint 100% compliant, SonarQube Rating A.

---

## 2026-11-20: Promoción On-Demand de Skills Tier-2 a Tier-1

### Hitos y Decisiones Materiales

1. **Gestor de Promoción On-Demand (`skill_promotion.py`)**:
   - Copia dinámica de skills especializadas de `skills/<name>` a `~/.gemini/config/plugins/aagy/skills/<name>`.
   - Validación estricta de frontmatter (`description` $\le 140$ caracteres).
   - Protección de skills core de Tier 1 frente a sobreescritura o eliminación accidental.
   - Registro transaccional en `.active_promotions.json`.
2. **Utilidades de Ergonomía CLI (`scripts/ps1/`)**:
   - `enable-skill.ps1` y `enable-skill.sh` (promoción y flag `-List`).
   - `disable-skill.ps1` y `disable-skill.sh` (retirada limpia de skills temporales).
3. **Calidad y Documentación**:
   - Manual operativo [`doc/manual/MANUAL_skill_promotion.md`](04-operations/setup-guides/MANUAL_skill_promotion.md).
   - Suite [`scripts/py/tests/test_skill_promotion.py`](../scripts/py/tests/test_skill_promotion.py) con 87/87 tests pasando (100%).
   - SonarQube Rating A (0 violaciones), markdownlint 100% compliant.

---

## 2026-11-20: Telemetría Proactiva de Presupuesto en Sesión y Política de Compactación

### Hitos y Decisiones Materiales

1. **Monitor de Telemetría de Sesión (`session_token_monitor.py`)**:
   - Detección automática del transcript activo `transcript.jsonl` en la estructura de Antigravity brain.
   - Cálculo estandarizado de tokens acumulados (ratio $3.8\text{ chars/token}$) sobre inputs de usuario, respuestas del modelo, thinking y llamadas a herramientas.
   - Banderas CLI `--threshold <n>`, `--json` y `--alert-only`.
2. **Integración en Flujo de CI/PR (`complete-task-pr.ps1`)**:
   - Invocación automática al término de la integración de PR alertando con advertencia si la conversación supera los 45.000 tokens recomendando ejecutar `/compact`.
3. **Calidad y Documentación**:
   - Manual operativo [`doc/manual/MANUAL_session_token_telemetry.md`](04-operations/runbooks/MANUAL_session_token_telemetry.md).
   - Suite [`scripts/py/tests/test_session_token_monitor.py`](../scripts/py/tests/test_session_token_monitor.py) con 86/86 tests pasando (100%).
   - SonarQube Rating A (0 violaciones), markdownlint 100% compliant.

---

## 2026-11-20: Git Hooks Nativos e Instalador Determinista

### Hitos y Decisiones Materiales

1. **Hooks Git Locales (`scripts/py/hooks/`)**:
   - `pre-commit`: Hook POSIX sh que filtra archivos `.md` staged e invoca `lint-markdown.ps1 -CheckOnly` o `lint-markdown.sh --check-only`, impidiendo confirms con sintaxis rota.
   - `commit-msg`: Hook POSIX sh que invoca `format_commit.py --validate-file <path> --strict`, exigiendo Conventional Commits y cuerpo explicativo $\ge 20$ caracteres.
   - Soporte para variable de bypass de emergencia `GIT_HOOKS_BYPASS=1` y estándar Git `--no-verify`.
2. **Instalador Idempotente (`scripts/ps1/`)**:
   - `install-git-hooks.ps1` y `install-git-hooks.sh` con instalación determinista y soporte para desinstalación limpia con `-Uninstall` / `--uninstall`.
3. **Documentación y Calidad**:
   - Manual operativo [`doc/manual/MANUAL_git_hooks.md`](04-operations/setup-guides/MANUAL_git_hooks.md).
   - Suite [`scripts/py/tests/test_git_hooks.py`](../scripts/py/tests/test_git_hooks.py) con 83/83 tests pasando (100%).
   - SonarQube Rating A (0 violaciones), markdownlint 100% compliant.

---

## 2026-11-20: Optimización de Prompt Caching de Gemini 3.8 y Reordenamiento Estático de Reglas

### Hitos y Decisiones Materiales

1. **Reestructuración Binaria de `AGENTS.md` y `rules/AGENTS.md`**:
   - Separación formal en Bloque Estático Invariable (Google 5-Pillar, SRE, Security, Quality, Multi-Stack Standards, Microservice SDK Parity) y Bloque Contextual / Dinámico (Lifecycle 4-fases, Commit PR automation, TODO lifecycle, Archival, Token Exhaustion).
   - Inclusión de marcador canónico `<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->`.
   - Sincronización exacta con el plugin global `~/.gemini/config/plugins/aagy/rules/AGENTS.md`.
2. **Documentación Técnica**:
   - Creado [`doc/manual/MANUAL_gemini_prompt_caching.md`](04-operations/setup-guides/MANUAL_gemini_prompt_caching.md) detallando el mecanismo de coincidencia de prefijos determinista y directrices para desarrolladores.
3. **Calidad y Verificación**:
   - Test unitario `test_static_prompt_caching_prefix_invariance` incorporado en [`test_workspace_audit.py`](../scripts/py/tests/test_workspace_audit.py).
   - 79/79 tests superados (100%), SonarQube Rating A (0 violaciones), markdownlint 100% compliant.

---

## 2026-11-20: Hooks Nativos, Auditoría AgentShield e Instintos por Proyecto

### Hitos y Decisiones Materiales

1. **Hooks Nativos Deterministas (`hooks.json`)**:
   - Incorporado [`hooks.json`](../hooks.json) para intercepción de seguridad en `PreToolUse` (safety guard de comandos de riesgo vía `safety-check.ps1` / `.sh`) y formateo automático de Markdown en `PostToolUse` (`hook-post-write.ps1` / `.sh`).
2. **Suite de Seguridad AgentShield (`security_audit.py`)**:
   - Auditoría estática de sintaxis, timeouts ($\le 30\text{ s}$) y comandos de riesgo en `hooks.json`.
   - Detección de secretos en texto plano en `mcp_config.json` exigiendo `${ENV_VAR}`.
   - Prevención de patrones de *prompt injection* o jailbreaks en `skills/`.
3. **Motor de Instintos por Proyecto (`instinct_manager.py`)**:
   - CLI [`instinct_manager.py`](../scripts/py/instinct_manager.py) y wrappers `manage-instincts.ps1` / `.sh` para capturar y consultar directivas operacionales en `.agents/instincts/*.md` sin inflar `AGENTS.md`.
4. **Calidad y Tests**:
   - Suite [`test_agentshield_instincts.py`](../scripts/py/tests/test_agentshield_instincts.py) con 78/78 tests pasando (100%).
   - SonarQube Rating A (0 violaciones, Complejidad Cognitiva $\le 10$).

---

## 2026-11-20: Integración Zero-Overhead de Gemini MCP y Skill Gemini Deep Ops

### Hitos y Decisiones Materiales

1. **Plantilla Aislada con Guardrail en Reposo (`skills/gemini-deep-ops/templates/gemini-mcp/`)**:
   - Manifiestos `plugin.json` y `mcp_config.json` con `"disabled": true` por defecto para garantizar 0 tokens en reposo.
   - Parametrización segura de credenciales vía `${GEMINI_API_KEY}` sin claves en texto plano.
   - Utilidad de alternancia idempotente [`toggle_gemini_mcp.py`](../scripts/py/toggle_gemini_mcp.py) y wrappers `.ps1` / `.sh`.
2. **Skill Tier 2 `gemini-deep-ops` y CLI Multimodal**:
   - Creada [`skills/gemini-deep-ops/SKILL.md`](../skills/gemini-deep-ops/SKILL.md) con descripción $\le 140$ caracteres y carga bajo demanda.
   - Implementado motor de diagnóstico [`gemini_deep_ops.py`](../scripts/py/gemini_deep_ops.py) y wrappers `.ps1` / `.sh` con análisis heurístico de caídas OOMKilled, bloqueos PostgreSQL y latencia.
   - Guía operacional en [`doc/manual/MANUAL_gemini_deep_ops_multimodal.md`](04-operations/runbooks/MANUAL_gemini_deep_ops_multimodal.md).
3. **Calidad y Tests Unitarios**:
   - Pruebas unitarias en [`test_gemini_deep_ops.py`](../scripts/py/tests/test_gemini_deep_ops.py) con 74/74 tests superados (100%).
   - SonarQube Quality Gate Rating A (0 violaciones).

---

## 2026-11-20: Hard Gate de Presupuesto de Contexto en Harness (Rules, Customizations y MCPs)

### Hitos y Decisiones Materiales

1. **Guardrail Bloqueante de Presupuesto (`feat/aagy/workspace-audit-budget-hard-gate`)**:
   - Extendido [`workspace_audit.py`](../scripts/py/workspace_audit.py) con funciones `audit_rules()` y `audit_mcps()`.
   - Límite por archivo de reglas: $\le 24.000$ bytes (24 KB) por archivo Markdown.
   - Techo seguro de reglas agregadas: $\le 16.000$ tokens (frente al defaultRulesBudget de 20.000 tokens de Antigravity).
   - Auditoría de configuración MCP: detección de servidores pesados (`gemini-mcp`) exigiendo `"disabled": true` para garantizar 0 tokens en reposo.
   - Presupuesto eager en plugins activos: $\le 3.000$ tokens en reposo para Tier 1.
   - Integración automática del plugin global `~/.gemini/config/plugins/aagy` en la auditoría.
2. **Validación y Tests Unitarios (TDD)**:
   - Añadidos tests unitarios exhaustivos en [`test_workspace_audit.py`](../scripts/py/tests/test_workspace_audit.py) cubriendo archivos sobredimensionados, exceso de tokens de reglas, detección de MCPs pesados activos vs desactivados y desbordamiento eager.
   - Cobertura completa con 69/69 tests pasando al 100%.
   - SonarQube Quality Gate Rating A alcanzado (0 violaciones, Complejidad Cognitiva $\le 10$).

---

## 2026-11-20: Formalización del Workflow de Ingeniería de 4 Fases y Acoplamiento Home-Lab

### Hitos y Decisiones Materiales

1. **Plantillas Estandarizadas de 4 Fases (`doc/templates/`)**:
   - Fase 1: [`01_TOMA_REQUISITOS_E_IMPACTO.md`](00-governance/templates/01_TOMA_REQUISITOS_E_IMPACTO.md): Requisitos funcionales, criterios de aceptación (Given/When/Then), matriz de impacto en Home-Lab (paridad `home-lab-sdk`, PostgreSQL LTS lock safety, Ingress único `cluster-lb` y Split-DNS, SRE memory throttling) y política estricta de *Zero-Breaking Changes*.
   - Fase 2: [`02_PLAN_ACCION_ARQUITECTURA.md`](00-governance/templates/02_PLAN_ACCION_ARQUITECTURA.md): Inventario DRY de reutilización, sincronización previa del SDK, topología Mermaid, TDD (`RED` -> `GREEN` -> `REFACTOR` -> `VERIFY`) y plan de Fast-Rollback (<2 min: `git revert` y `down-migration.sql`).
   - Fase 3: [`03_DOCUMENTACION_Y_RELEASE_NOTES.md`](00-governance/templates/03_DOCUMENTACION_Y_RELEASE_NOTES.md): Generación previa de Notas de la Versión SemVer (`vX.Y.Z`), matriz de promoción multi-tier (`LOCAL` -> `SANDBOX` -> `LIVE`), actualización de espina documental (`STATUS.md`, `LOG.md`, ADRs) y autopsia 5W para incidentes.
   - Fase 4: [`04_PROPUESTA_COMMITS_PR.md`](00-governance/templates/04_PROPUESTA_COMMITS_PR.md): Commits atómicos convencionales `[type]-[projects]: <title>`, Pre-Flight Review Notice con diff completo de código + docs, compuertas de calidad SonarQube Rating A y orquestación de PR con squash-automerge.
2. **Skill `engineering-lifecycle` y Subagente `lifecycle-coordinator`**:
   - Creada skill [`skills/engineering-lifecycle/SKILL.md`](../skills/engineering-lifecycle/SKILL.md) e incorporada al catálogo Tier 1 (`generic`).
   - Creado subagente auditor [`agents/lifecycle-coordinator.md`](../agents/lifecycle-coordinator.md).
3. **Herramienta CLI de Scaffolding de Tareas (`new-lifecycle-task`)**:
   - Desarrollado [`scripts/py/new_lifecycle_task.py`](../scripts/py/new_lifecycle_task.py) y wrappers [`new-lifecycle-task.ps1`](../scripts/ps1/new-lifecycle-task.ps1) / `new-lifecycle-task.sh`.
   - Incorporada suite de tests unitarios (`test_new_lifecycle_task.py`) alcanzando 66/66 tests passing (100%).
4. **Actualización de Reglas de Gobernanza (`rules/AGENTS.md`)**:
   - Incorporado el workflow de 4 fases como regla obligatoria en la sección 1 de `rules/AGENTS.md` y `AGENTS.md`.

---

## 2026-11-08: Consolidación Final, Harness de Gobernanza y Optimización Two-Tier

### Hitos y Decisiones Materiales

1. **Arquitectura Two-Tier y Reducción del 98.25% de Tokens** (PR #9, PR #10 | Commit `352c079`):
   - Adopción de la arquitectura Two-Tier: Tier 1 Global Plugin (`~/.gemini/config/plugins/aagy`) con 21 skills nucleares transversales consumiendo ~701 tokens (reducido de 40.000 tokens iniciales).
   - Barrido y purgado del repositorio: eliminación de 147 skills y 27 agentes redundantes o no relacionados con los stacks autorizados (Java 25/Spring Boot 4, Angular 21/TS, Go/Microservices, Python/FastAPI, PyTorch/RecSys y automatización de oficina).
   - Normalización de 169 skills en Tier 2 con frontmatter $\le 140$ caracteres y 48 subagentes con $\le 120$ caracteres.

2. **Desacoplamiento Agnóstico y Saneamiento de Submódulos** (PR #11 | Commit `0106e39`):
   - Erradicación del subdirectorio anidado duplicado `aagy/` (530 archivos duplicados purgados).
   - Consolidación del plugin agnóstico `aagy` / `aagy` directamente en la raíz de `ACB75/aagy`.
   - Ajuste de `package.json` y `plugin.json` eliminando dependencias obsoletas.

3. **Pipeline Automatizado de Ingesta IDEAS -> TODO y CLI de Mapeo Documental** (PR #12 | Commit `8877291`):
   - Implementación del motor de ingesta [`sync_ideas_todo.py`](../scripts/py/sync_ideas_todo.py) con Meta-Prompt de 7 Fases.
   - Creación de la utilidad CLI [`map_docs.py`](../scripts/py/map_docs.py) y validación de enlaces relativos ignorando bloques de código.
   - Creación de plantilla canónica [`doc/IDEAS.md`](06-backlog/IDEAS.md).

4. **Estandarización de Política de Ramas de Incidencias en el Harness** (PR #13 | Commit `2bef381`):
   - Implementación de [`validate_branch.py`](../scripts/py/validate_branch.py) enforcing prefijos `fix/<id>`, `feat/*`, `refactor/*`, `infra/*`, `chore/*`, `docs/*`, `test/*`.
   - Bloqueo sistemático de commits y PRs directas en ramas protegidas (`main`, `master`).

5. **Generador Automatizado de Post-Mortem SRE 5W** (PR #14 | Commit `30b89e5`):
   - Creación de plantilla SRE [`doc/post-mortem/TEMPLATE_POSTMORTEM.md`](00-governance/templates/TEMPLATE_POSTMORTEM.md) con análisis Who, What, When, Where, Why/How.
   - Desarrollo del generador [`generate_postmortem.py`](../scripts/py/generate_postmortem.py) e integración automática en el cierre de ramas `fix/*`.

6. **Consolidación de Cierre Atómico, Auto-PR y Pre-Flight Review** (PR #15, PR #16 | Commits `ef04125`, `23c40d9`):
   - Fortalecimiento de [`complete-task-pr.ps1`](../scripts/ps1/complete-task-pr.ps1) y [`complete-task-pr.sh`](../scripts/sh/complete-task-pr.sh).
   - Auto-archivo sincronizado de tareas completadas (`- [x]`) de `doc/TODO.md` a `doc/TODO_DONE/` a write-time con `lint-markdown.ps1 -Fix`.
   - Pre-merge Quality Gate estricto: markdownlint, suite `pytest` (61 tests) y SonarQube Rating A.
   - Manejo determinista de colecciones bajo `Set-StrictMode -Version Latest`.

7. **Normalización de la Espina Dorsal Documental y Limpieza Final**:
   - Reorganización de planes de trabajo sueltos hacia [`doc/plan/`](06-backlog/plans/REQ_aagy_unified_self_improvement.md).
   - Registro de mapeo documental en [`.governance/docs-map.json`](../.governance/docs-map.json).
   - Creación de estado operativo [`doc/STATUS.md`](STATUS.md) e histórico [`doc/LOG.md`](LOG.md).
