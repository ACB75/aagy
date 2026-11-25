# Postmortem 5W: fix/aagy/local-model-env-fallback

> **ID de Tarea**: `fix/aagy/local-model-env-fallback`
> **Fecha**: `2026-11-25T22:06:41Z` | **Autor/Rol**: `ACB75`
> **Estado**: `BORRADOR | REVISADO`
> **Ubicación en el repo**: `<carpeta de postmortems>/PM_<rama>_<fecha>.md`

Sin culpables: el objetivo es reforzar sistemas, guardrails y procesos.

---

## 0. Estado actual

- **Entorno afectado**: `LOCAL / DEV`
- **Severidad**: `SEV-1 | SEV-2 | SEV-3`
- **Cambios (git diff)**: `aagy-ecc/agents/lifecycle-coordinator.md           |   2 +-
 aagy-ecc/agents/sync-aligner.md                    |   6 +-
 aagy-ecc/agents/todo-archiver.md                   |   4 +-
 aagy-ecc/commands/resume-session.md                |   2 +-
 .../skills/agent-introspection-debugging/SKILL.md  |   2 +-
 .../packs/extras/skills/configure-aagy/SKILL.md    |   2 +-
 .../packs/extras/skills/gemini-deep-ops/SKILL.md   |   6 +-
 .../gemini-deep-ops/templates/gemini-mcp/README.md |   6 +-
 .../references/aagy-release-checklist.md           | 211 ---------------------
 aagy-ecc/packs/extras/skills/skill-scout/SKILL.md  |   2 +-
 .../packs/extras/skills/story-lifecycle/SKILL.md   |   2 +-
 .../extras/skills/workspace-health-audit/SKILL.md  |   8 +-
 .../packs/shared/skills/sre-reliability/SKILL.md   |   4 +-
 aagy-ecc/rules/AGENTS.md                           |  40 ++--
 aagy-ecc/scripts/py/aagy_config.py                 |  20 ++
 aagy-ecc/scripts/py/local_model.py                 |   1 +
 aagy-ecc/skills/agent-self-evaluation/SKILL.md     |  14 +-
 .../references/hook-integration.md                 |   8 +-
 aagy-ecc/skills/agent-worktrees/SKILL.md           |   2 +-
 aagy-ecc/skills/engineering-lifecycle/SKILL.md     |  10 +-
 aagy-ecc/skills/git-workflow/SKILL.md              |   6 +-
 aagy-ecc/skills/shared-backlog/SKILL.md            |   6 +-
 aagy-ecc/skills/sonarqube-quality-gate/SKILL.md    |   4 +-
 aagy-ecc/skills/todo-lifecycle/SKILL.md            |   8 +-
 agents/lifecycle-coordinator.md                    |   2 +-
 agents/sync-aligner.md                             |   6 +-
 agents/todo-archiver.md                            |   4 +-
 doc/06-backlog/TODO.md                             |  27 +++
 rules/AGENTS.md                                    |  40 ++--
 scripts/py/aagy_config.py                          |  20 ++
 scripts/py/local_model.py                          |   1 +
 scripts/py/tests/test_local_model.py               |   1 +
 skills/aagy-doctor/SKILL.md                        |   8 +-
 skills/aagy-local/SKILL.md                         |   6 +-
 skills/aagy-ui/SKILL.md                            |   2 +-
 skills/agent-introspection-debugging/SKILL.md      |   2 +-
 skills/agent-self-evaluation/SKILL.md              |  14 +-
 .../references/hook-integration.md                 |   8 +-
 skills/agent-worktrees/SKILL.md                    |   2 +-
 skills/configure-aagy/SKILL.md                     |   2 +-
 skills/engineering-lifecycle/SKILL.md              |  10 +-
 skills/gemini-deep-ops/SKILL.md                    |   6 +-
 .../gemini-deep-ops/templates/gemini-mcp/README.md |   6 +-
 skills/git-workflow/SKILL.md                       |   6 +-
 .../references/aagy-release-checklist.md           | 211 ---------------------
 skills/shared-backlog/SKILL.md                     |   6 +-
 skills/skill-scout/SKILL.md                        |   2 +-
 skills/sonarqube-quality-gate/SKILL.md             |   4 +-
 skills/sre-reliability/SKILL.md                    |   4 +-
 skills/story-lifecycle/SKILL.md                    |   2 +-
 skills/todo-lifecycle/SKILL.md                     |   8 +-
 skills/workspace-health-audit/SKILL.md             |   8 +-
 52 files changed, 223 insertions(+), 571 deletions(-)`

## 1. Contexto y objetivos

- **Problema**: qué falló y cómo se detectó.
- **Objetivo**: que no vuelva a pasar.
- **Alcance**: componentes afectados.
- **Fuera de alcance**: lo que no tuvo que ver.

## 2. Las 5W

- **Who**: componentes y dependencias implicados.
- **What**: síntomas e impacto.
- **When**: detección, diagnóstico, corrección y resolución (UTC).
- **Where**: módulos, endpoints o consultas.
- **Why / How**: mecanismo del fallo y por qué no se contuvo.

## 3. Causa raíz (5 porqués)

1. ¿Por qué falló? ->
2. ¿Por qué ocurrió esa condición? ->
3. ¿Por qué no lo detectaron los tests? ->
4. ¿Por qué no había un guardrail? ->
5. ¿Por qué el diseño permitió que se propagara? -> causa raíz

## 4. Acciones

| Tipo | Acción | Responsable | Prioridad | Estado |
| :--- | :--- | :--- | :--- | :--- |
| Mitigación | Corrección en `fix/aagy/local-model-env-fallback` | `ACB75` | P0 | Resuelto |
| Prevención | Test de regresión | `<responsable>` | P1 | Planificado |

## 5. Criterios de aceptación

- [ ] **CA-01**: el test de regresión falla sin la corrección y pasa con ella.

## 6. Paridad aagy ↔ aagy-ecc

Si el fallo afecta a un plugin, comprobar el otro.

## 7. Preguntas abiertas

- **P-01**: `<pregunta>`. Por defecto: `<valor>`.

## 8. Referencias

- `<PR, issues, logs>`
