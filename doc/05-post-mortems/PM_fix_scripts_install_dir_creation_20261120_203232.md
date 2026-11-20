# Autopsia Post-Incidente (Post-Mortem 5W): fix/scripts/install-dir-creation

> **Guía de Gobernanza SRE (ADR-0008):**
>
> - Esta autopsia es estrictamente **sin culpables (blameless)**. Su propósito es fortalecer los sistemas, guardrails y procesos defensivos de ingeniería.
> - Se genera automáticamente tras la resolución de ramas `fix/*`.

---

## 1. Metadatos del Incidente

- **Identificador de Rama / Incidente**: `fix/scripts/install-dir-creation`
- **Fecha y Hora de Cierre (UTC)**: `2026-11-20T20:32:32Z`
- **Ingeniero Responsable / Autor**: `ACB75`
- **Entorno Afectado**: `LOCAL / DEV`
- **Severidad Preliminar**: `SEV-2 (Degradación Parcial)`
- **Impacto en Error Budget (SLO)**: `Agotamiento < 0.1% del presupuesto mensual`
- **Resumen de Cambios (Git Diff)**:
  `doc/INDEX.md                                       |   1 +
 doc/LOG.md                                         |  19 ++
 doc/STATUS.md                                      |   7 +-
 doc/TODO.md                                        |  95 ++++++---
 ...acklog_migrar_aagy_a_aagy_Any_20261120_213030.md |  50 +++++
 doc/manual/MANUAL_aagy_ecc_parity_and_migration.md |  84 ++++++++
 .../DOCS_aagy_clean_docs_and_repo_migration.md     |  38 ++++
 .../PLAN_aagy_clean_docs_and_repo_migration.md     | 110 +++++++++++
 doc/plan/REQ_aagy_unified_self_improvement.md      |  83 ++++++++
 .../REVIEW_aagy_clean_docs_and_repo_migration.md   |  58 ++++++
 .../.claude-plugin/PLUGIN_SCHEMA_NOTES.md          |   0
 {aagy-ecc => aagy}/.claude-plugin/README.md       |   0
 .../.claude-plugin/marketplace.json                |   0
 {aagy-ecc => aagy}/.claude-plugin/plugin.json     |   0
 .../.claude/commands/add-language-rules.md         |   0
 .../.claude/commands/database-migration.md         |   0
 .../.claude/commands/feature-development.md        |   0
 {aagy-ecc => aagy}/.claude/aagy-tools.json         |   0
 {aagy-ecc => aagy}/.claude/enterprise/controls.md |   0
 .../instincts/inherited/aagy-instincts.yaml         |   0
 {aagy-ecc => aagy}/.claude/identity.json          |   0
 {aagy-ecc => aagy}/.claude/package-manager.json   |   0
 .../.claude/research/aagy-research-playbook.md      |   0
 .../.claude/rules/aagy-guardrails.md                |   0
 {aagy-ecc => aagy}/.claude/rules/node.md          |   0
 .../.claude/team/aagy-team-config.json              |   0
 .../.claude/workflows/aagy-pro-security-roadmap.js  |   0
 {aagy-ecc => aagy}/CLAUDE.md                      |   0
 {aagy-ecc => aagy}/README.md                      |   0
 {aagy-ecc => aagy}/SOUL.md                        |   0
 {aagy-ecc => aagy}/agent.yaml                     |   0
 {aagy-ecc => aagy}/commands/aside.md              |   0
 {aagy-ecc => aagy}/commands/astra-review.md       |   0
 {aagy-ecc => aagy}/commands/auto-update.md        |   0
 {aagy-ecc => aagy}/commands/build-fix.md          |   0
 {aagy-ecc => aagy}/commands/checkpoint.md         |   0
 {aagy-ecc => aagy}/commands/code-review.md        |   0
 {aagy-ecc => aagy}/commands/cost-report.md        |   0
 {aagy-ecc => aagy}/commands/cpp-build.md          |   0
 {aagy-ecc => aagy}/commands/cpp-review.md         |   0
 {aagy-ecc => aagy}/commands/cpp-test.md           |   0
 {aagy-ecc => aagy}/commands/aagy-guide.md          |   0
 {aagy-ecc => aagy}/commands/epic-claim.md         |   0
 {aagy-ecc => aagy}/commands/epic-decompose.md     |   0
 {aagy-ecc => aagy}/commands/epic-publish.md       |   0
 {aagy-ecc => aagy}/commands/epic-review.md        |   0
 {aagy-ecc => aagy}/commands/epic-sync.md          |   0
 {aagy-ecc => aagy}/commands/epic-unblock.md       |   0
 {aagy-ecc => aagy}/commands/epic-validate.md      |   0
 {aagy-ecc => aagy}/commands/evolve.md             |   0
 {aagy-ecc => aagy}/commands/fastapi-review.md     |   0
 {aagy-ecc => aagy}/commands/feature-dev.md        |   0
 {aagy-ecc => aagy}/commands/flutter-build.md      |   0
 {aagy-ecc => aagy}/commands/flutter-review.md     |   0
 {aagy-ecc => aagy}/commands/flutter-test.md       |   0
 {aagy-ecc => aagy}/commands/gan-build.md          |   0
 {aagy-ecc => aagy}/commands/gan-design.md         |   0
 {aagy-ecc => aagy}/commands/go-build.md           |   0
 {aagy-ecc => aagy}/commands/go-review.md          |   0
 {aagy-ecc => aagy}/commands/go-test.md            |   0
 {aagy-ecc => aagy}/commands/gradle-build.md       |   0
 {aagy-ecc => aagy}/commands/harness-audit.md      |   0
 {aagy-ecc => aagy}/commands/hookify-configure.md  |   0
 {aagy-ecc => aagy}/commands/hookify-help.md       |   0
 {aagy-ecc => aagy}/commands/hookify-list.md       |   0
 {aagy-ecc => aagy}/commands/hookify.md            |   0
 {aagy-ecc => aagy}/commands/instinct-export.md    |   0
 {aagy-ecc => aagy}/commands/instinct-import.md    |   0
 {aagy-ecc => aagy}/commands/instinct-status.md    |   0
 {aagy-ecc => aagy}/commands/jira.md               |   0
 {aagy-ecc => aagy}/commands/kotlin-build.md       |   0
 {aagy-ecc => aagy}/commands/kotlin-review.md      |   0
 {aagy-ecc => aagy}/commands/kotlin-test.md        |   0
 {aagy-ecc => aagy}/commands/learn-eval.md         |   0
 {aagy-ecc => aagy}/commands/learn.md              |   0
 {aagy-ecc => aagy}/commands/loop-start.md         |   0
 {aagy-ecc => aagy}/commands/loop-status.md        |   0
 {aagy-ecc => aagy}/commands/marketing-campaign.md |   0
 {aagy-ecc => aagy}/commands/model-route.md        |   0
 {aagy-ecc => aagy}/commands/multi-backend.md      |   0
 {aagy-ecc => aagy}/commands/multi-execute.md      |   0
 {aagy-ecc => aagy}/commands/multi-frontend.md     |   0
 {aagy-ecc => aagy}/commands/multi-plan.md         |   0
 {aagy-ecc => aagy}/commands/multi-workflow.md     |   0
 {aagy-ecc => aagy}/commands/orch-add-feature.md   |   0
 {aagy-ecc => aagy}/commands/orch-build-mvp.md     |   0
 .../commands/orch-change-feature.md                |   0
 {aagy-ecc => aagy}/commands/orch-fix-defect.md    |   0
 {aagy-ecc => aagy}/commands/orch-refine-code.md   |   0
 {aagy-ecc => aagy}/commands/orch-review.md        |   0
 {aagy-ecc => aagy}/commands/plan-canvas.md        |   0
 {aagy-ecc => aagy}/commands/plan-prd.md           |   0
 {aagy-ecc => aagy}/commands/plan.md               |   0
 {aagy-ecc => aagy}/commands/pm2.md                |   0
 {aagy-ecc => aagy}/commands/pr.md                 |   0
 {aagy-ecc => aagy}/commands/project-init.md       |   0
 {aagy-ecc => aagy}/commands/projects.md           |   0
 {aagy-ecc => aagy}/commands/promote.md            |   0
 {aagy-ecc => aagy}/commands/prp-commit.md         |   0
 {aagy-ecc => aagy}/commands/prp-implement.md      |   0
 {aagy-ecc => aagy}/commands/prp-plan.md           |   0
 {aagy-ecc => aagy}/commands/prp-pr.md             |   0
 {aagy-ecc => aagy}/commands/prp-prd.md            |   0
 {aagy-ecc => aagy}/commands/prune.md              |   0
 {aagy-ecc => aagy}/commands/python-review.md      |   0
 {aagy-ecc => aagy}/commands/quality-gate.md       |   0
 {aagy-ecc => aagy}/commands/react-build.md        |   0
 {aagy-ecc => aagy}/commands/react-review.md       |   0
 {aagy-ecc => aagy}/commands/react-test.md         |   0
 {aagy-ecc => aagy}/commands/refactor-clean.md     |   0
 {aagy-ecc => aagy}/commands/resume-session.md     |   0
 {aagy-ecc => aagy}/commands/review-pr.md          |   0
 {aagy-ecc => aagy}/commands/rust-build.md         |   0
 {aagy-ecc => aagy}/commands/rust-review.md        |   0
 {aagy-ecc => aagy}/commands/rust-test.md          |   0
 {aagy-ecc => aagy}/commands/santa-loop.md         |   0
 {aagy-ecc => aagy}/commands/save-session.md       |   0
 {aagy-ecc => aagy}/commands/security-scan.md      |   0
 {aagy-ecc => aagy}/commands/sessions.md           |   0
 {aagy-ecc => aagy}/commands/setup-pm.md           |   0
 {aagy-ecc => aagy}/commands/skill-create.md       |   0
 {aagy-ecc => aagy}/commands/skill-health.md       |   0
 {aagy-ecc => aagy}/commands/skill-host-compat.md  |   0
 {aagy-ecc => aagy}/commands/test-coverage.md      |   0
 {aagy-ecc => aagy}/commands/token-card.md         |   0
 {aagy-ecc => aagy}/commands/update-codemaps.md    |   0
 {aagy-ecc => aagy}/commands/update-docs.md        |   0
 {aagy-ecc => aagy}/commands/vue-review.md         |   0
 {aagy-ecc => aagy}/hooks/README.md                |   0
 {aagy-ecc => aagy}/hooks/codex-hooks.json         |   0
 .../hooks/hermes/check-console-log.py              |   0
 .../hooks/hermes/config-protection.py              |   0
 {aagy-ecc => aagy}/hooks/hooks.json               |   0
 {aagy-ecc => aagy}/hooks/hooks.metadata.json      |   0
 .../hooks/memory-persistence/README.md             |   0
 .../hooks/memory-persistence/hooks.json            |   0
 {aagy-ecc => aagy}/hooks/qoder-hooks.json         |   0
 {aagy-ecc => aagy}/package.json                   |   4 +-
 .../scaffolds/cursor/aagy-agent-data.json           |   0
 {aagy-ecc => aagy}/scaffolds/cursor/hooks.json    |   0
 .../scaffolds/cursor/rules/aagy-agent-data-home.mdc |   0
 install.ps1                                        |  12 +-
 install.sh                                         |  10 +-
 package.json                                       |   8 +-
 plugin.json                                        |   8 +-
 scripts/pwsh/audit-plugin-parity.ps1        |  40 ++++
 scripts/sh/audit-plugin-parity.sh         |  19 ++
 scripts/pwsh/complete-task-pr.ps1           |  10 +
 scripts/sh/complete-task-pr.sh            |   5 +
 scripts/py/audit_plugin_parity.py             | 213 +++++++++++++++++++++
 scripts/py/format_commit.py                   |   2 +-
 scripts/py/security_audit.py                  |   2 +-
 scripts/py/sonar_audit.py                     |   2 +-
 scripts/py/tests/test_audit_plugin_parity.py  | 103 ++++++++++
 154 files changed, 934 insertions(+), 49 deletions(-)`

---

## 2. Resumen Ejecutivo (Blameless Summary)

Breve resumen descriptivo del fallo observado, cómo fue detectado por las sondas o tests, y la estrategia aplicada para mitigar y solventar la anomalía.

---

## 3. Análisis Exhaustivo de las 5W

### 3.1. Who (Quién / Qué Componentes)

- **Microservicios afectados**: Componentes o módulos involucrados en la degradación.
- **Actores y dependencias**: Clientes, proxies Ingress, colas o bases de datos que interactuaron con el fallo.

### 3.2. What (Qué Ocurrió)

- **Síntomas observables**: Códigos de error HTTP 5xx, timeouts, memory leaks o excepciones no controladas.
- **Impacto**: Número de peticiones degradadas o impacto en la experiencia de usuario.

### 3.3. When (Cronología de Eventos UTC)

- `HH:MM:SS UTC` - **Detección**: Activación de alarma o fallo en tests de integración.
- `HH:MM:SS UTC` - **Diagnóstico**: Aislamiento del componente causante y reproducción del error.
- `HH:MM:SS UTC` - **Mitigación / Fix**: Commit correctivo en rama `fix/*` y validación de tests.
- `HH:MM:SS UTC` - **Resolución**: Fusión en `main` y verificación verde del Ingress.

### 3.4. Where (Dónde)

- **Localización técnica**: Módulos, controladores, endpoints o consultas SQL afectadas.
- **Entorno de ejecución**: Contenedores Docker, pods o servicios en red local `*.home.arpa`.

### 3.5. Why & How (Por Qué y Cómo)

- **Mecanismo de fallo**: Descripción técnica exacta de la condición de carrera, desbordamiento o excepción no capturada.
- **Propagación del blast radius**: Por qué el fallo no fue contenido por circuit breakers o bulkheads.

---

## 4. Análisis de Causa Raíz (5 Porqués / 5-Whys)

1. **¿Por qué falló el servicio?** ->
2. **¿Por qué ocurrió esa condición?** ->
3. **¿Por qué no se detectó en tests previos?** ->
4. **¿Por qué no existía un guardrail defensivo?** ->
5. **¿Por qué la arquitectura permitió la propagación?** -> *(Causa Raíz Fundamental)*

---

## 5. Acciones Preventivas y Correctivas

| Tipo | Acción Concreta | Responsable | Prioridad | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Mitigación** | Corrección aplicada en rama `fix/scripts/install-dir-creation` | `ACB75` | P0 | Resuelto |
| **Prevención** | Test de regresión automatizado añadido | Equipo Dev | P1 | Planificado |
| **Monitoreo** | Ajuste de métricas SLI y alertas tempranas | Equipo SRE | P1 | Planificado |
