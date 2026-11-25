# Fase 1: Toma de Requisitos — Plantilla genérica ampliable y paridad `aagy` ↔ `aagy-ecc`

> **ID de Tarea**: `docs/doc/generic-templates`
> **Fecha**: `2026-11-24` | **Autor/Rol**: `Claude (toma de requisitos) / Master (aprobación)`
> **Estado**: `BORRADOR` (P-02 y P-03 resueltas; P-01 y P-04 abiertas en la §7, con valor por defecto)
> **Ubicación en el repo**: `doc/06-backlog/plans/REQ_aagy_generic_templates.md`

---

## 0. Estado actual (hallazgos en `main` @ `59cda4b`)

| Pieza | Dónde | Hoy | Problema |
| :--- | :--- | :--- | :--- |
| Plantillas del lifecycle | `doc/00-governance/templates/01..04_*.md`, `TEMPLATE_ADR.md`, `TEMPLATE_POSTMORTEM.md` | Seis plantillas con estructuras distintas | Llevan contenido de app (`<repo>-sdk`, PostgreSQL, `lb`, `.<dominio-interno>`, `app`), que según la regla P-13 no puede vivir en el plugin. No hay una base común ni puntos de extensión. |
| REQ y PLAN reales | `doc/06-backlog/plans/REQ_*.md`, `PLAN_*.md` | Cada uno con su propio formato | No siguen `01_*` ni `02_*`. |
| Skills (workflows de Antigravity) | `skills/*/SKILL.md` (172) | Secciones libres (`Cuándo usarla`, `When to Activate`, `Reglas`...) | Sin esqueleto común ni comprobación. |
| Comandos de Claude Code | `aagy-ecc/commands/*.md` (26) | `Uso`, `Qué hacer`, `Reglas` en los propios; formato ECC en los heredados | Dos formatos mezclados. |
| Subagentes | `agents/*.md` | Formato libre | Igual. |
| Issues, PR y TODO | `.github/ISSUE_TEMPLATE/*`, `pull_request_template.md`, `TODO.md` (7 fases) | Tres esquemas de secciones distintos | Una issue y su tarea en `TODO.md` no comparten estructura, y nada comprueba que estén alineadas. |
| Fase 4 en `aagy-ecc` | `aagy-ecc/scripts/py/` | No incluye `complete-task-pr`, `generate_postmortem`, `sonar_audit`, `format_commit` ni `git-flow-helper` | Las reglas de `aagy-ecc` mandan a `scripts/ps1/aagy.ps1 complete-task-pr`, que no existe al instalar el plugin en otro proyecto. |
| Hooks | `hooks.json` y `aagy-ecc/hooks/hooks.json` | `aagy-ecc` tiene `SessionStart`, `PreCompact` y `SessionEnd`; `aagy` solo `Stop` | Antigravity no deja relevo (`handoff`) automático. |
| Docs desfasados | `aagy-ecc/hooks/README.md`, `aagy-ecc/commands/aagy-ecc-doctor.md`, directiva de `TODO.md` | "tres hooks"; "DOC-01..14"; "auto-merge continuo" | No reflejan el código (5 hooks, DOC-15, sin auto-merge y presupuesto 0 €). |

---

## 1. Contexto y objetivos

- **Problema**: cada documento y cada workflow tiene su propia forma, las plantillas tienen datos de un proyecto concreto y los dos plugins no hacen lo mismo en la fase 4 ni en los hooks.
- **Objetivo**: una sola plantilla base, genérica y ampliable, de la que salen todos los documentos y workflows del harness. Los dos plugins la usan igual, y un check la hace cumplir.
- **Alcance**: sacar del repo todo lo de app y aplicarlo allí con reinstalación y hard sync; plantillas de `doc/`, REQ/PLAN/ADR/postmortem/runbook, IDEAS/TODO, issues y PR, skills, comandos y subagentes; paridad de fase 4 y hooks; alineación issues ↔ `TODO.md`; revisión final de toda la documentación.
- **Fuera de alcance**: reescribir el contenido técnico de las 172 skills (solo se adapta su esqueleto); cambiar el flujo de 4 fases.

---

## 2. Requisitos funcionales

### 2.1. Plantilla base

- **RF-01**: `doc/00-governance/templates/TEMPLATE_BASE.md` define el esqueleto común: cabecera (id, fecha, autor/rol, estado, ubicación), `0. Estado actual`, `1. Contexto y objetivos`, cuerpo propio del tipo, `Criterios de aceptación`, `Paridad aagy ↔ aagy-ecc`, `Preguntas abiertas` y `Referencias`.
- **RF-02**: cada tipo de documento (REQ, PLAN, DOCS, PR, ADR, POSTMORTEM, RUNBOOK, IDEA, TODO) es una plantilla que hereda la base y solo añade su cuerpo propio.
- **RF-03**: puntos de extensión declarados. Un proyecto consumidor añade secciones (por ejemplo, la matriz de impacto de app) en su propio repo, declaradas en `.governance/docs-map.json` (`template_extensions`), sin tocar el plugin. Mismo patrón que los perfiles de stack de ADR-0004.
- **RF-04**: las plantillas del plugin no contienen nombres de proyectos, hosts, dominios ni usuarios (regla P-13). Lo de app se va a su repo (RF-14); el plugin solo trae una extensión de ejemplo genérica.

### 2.2. Workflows

- **RF-05**: esqueleto común para skills, comandos y subagentes: frontmatter (`name`/`description` dentro del presupuesto de tokens), `Cuándo usarlo`, `Uso`, `Qué hacer`, `Reglas`, `Paridad`. Secciones extra permitidas después de las comunes.
- **RF-06**: un mismo workflow tiene el mismo nombre de sección y el mismo orden en `aagy` (skill) y en `aagy-ecc` (comando o skill). La sección `Paridad` nombra su equivalente en el otro plugin. Todo workflow de un plugin se porta al otro si el harness lo permite; si no, la sección declara la asimetría (P-03).

### 2.3. Issues ↔ TODO

- **RF-07**: issues, PR y tareas de `TODO.md` usan las mismas secciones que la plantilla base (motivación, criterios, paridad, artefactos).
- **RF-08**: toda issue abierta tiene su tarea en `TODO.md` con `issue=<N>`, y toda tarea abierta con `issue=` apunta a una issue abierta. Las ideas en `Draft` no necesitan issue.
- **RF-09**: `backlog.py gh-sync --check` (o un check del doctor) informa de las diferencias sin cambiar nada.

### 2.4. Paridad de plugins

- **RF-10**: la fase 4 tiene un motor Python único (`complete_task_pr.py` y los scripts que usa) que se copia a `aagy-ecc` con `sync_aagy_ecc.py`; los `.ps1` y `.sh` quedan como envoltorios finos. Las reglas de `aagy-ecc` apuntan a la ruta del plugin.
- **RF-11**: los hooks de los dos plugins cubren los mismos momentos (inicio, antes de herramienta, después de escribir, fin de turno, compactación, fin de sesión) donde el harness lo permita. Si Antigravity no tiene el evento, la asimetría queda documentada en `MANUAL_aagy_ecc_parity_and_migration.md`.
- **RF-12**: `audit_plugin_parity.py` y los doctores comprueban RF-05, RF-06, RF-10 y RF-11.

### 2.5. Fuera app y hard sync

- **RF-14**: en este repo no queda nada de app ni de otro proyecto consumidor: código, skills, agentes, packs, plantillas, ADR, runbooks y ejemplos. Antes de borrar, lo que es de app (`audit_sdk_parity`, `audit_pg_locks`, `validate_ingress_routes`, matriz de impacto, runbooks, perfil de stack) se mueve a su repo.
- **RF-15**: gancho genérico: el repo consumidor declara sus checks de pre-merge y sus secciones de plantilla en `.governance/docs-map.json` (`checks`, `template_extensions`), y la fase 4 los ejecuta sin conocerlos. Un check falla si reaparece una referencia a un proyecto consumidor.
- **RF-16**: `.aagy-install.json` guarda la lista de ficheros instalados con su hash. `aagy-sync --hard` sobrescribe solo esos, borra los que el plugin ya no trae y nunca toca lo propio del proyecto; si un fichero se editó a mano, avisa y no lo pisa salvo `--force`. Tiene `--dry-run`.
- **RF-17**: la forma de aplicar los cambios en app (y en cualquier consumidor) es reinstalar el plugin y hacer una hard sync, seguida del doctor.

### 2.6. Revisión final (última tarea)

- **RF-13**: revisar y actualizar toda la documentación (`doc/`, `README.md`, `AGENTS.md`, skills, comandos, agentes, READMEs de `aagy-ecc`) contra el código, pasarla a la plantilla y actualizar o borrar lo desfasado. Es la última tarea de todo el backlog, no solo de esta épica: depende también de las épicas #80 (modelo local) y #103 (plugin agnóstico).

---

## 3. Criterios de aceptación

- [ ] **CA-01**: dado un documento nuevo creado con `new-lifecycle-task --phase <X>`, cuando se abre, entonces tiene las secciones comunes de `TEMPLATE_BASE.md` en el orden fijado.
- [ ] **CA-02**: dado un repo consumidor con `template_extensions` en `docs-map.json`, cuando crea un REQ, entonces aparece su sección extra y el plugin no cambia.
- [ ] **CA-03**: `grep` de `app`, `<dominio-interno>` y `app` en las plantillas del plugin no devuelve nada.
- [ ] **CA-04**: el check de esqueleto pasa en todas las skills, comandos y agentes de los dos plugins (exit `0`).
- [ ] **CA-05**: `backlog.py gh-sync --check` no muestra diferencias entre issues abiertas y `TODO.md`.
- [ ] **CA-06**: con `aagy-ecc` instalado en un repo que no es `aagy`, la fase 4 funciona solo con los scripts del plugin.
- [ ] **CA-07**: `audit-plugin-parity` da `[PASS]` incluyendo hooks y fase 4.
- [ ] **CA-08**: tras la revisión final, ningún documento cita scripts, checks, rutas o flujos que no existan.
- [ ] **CA-09**: `grep -ri` de `app`, `<dominio-interno>`, `app` y `app` en el repo no devuelve nada, salvo el historial (`git log`, `doc/LOG.md`, `doc/06-backlog/done/`) y este REQ mientras siga abierto.
- [ ] **CA-10**: en app, tras reinstalar y `aagy-sync --hard`, el doctor no da FAIL y ningún fichero propio de app se ha borrado ni cambiado.

---

## 4. Paridad `aagy` ↔ `aagy-ecc`

- Las plantillas viven en `doc/00-governance/templates/` y se copian a los dos plugins con `sync_aagy_ecc.py`.
- Los checks nuevos van en `doctor_core.py` (común) y en `audit_plugin_parity.py`.
- Coste: 0 €, sin servicios de pago, sin dependencias nuevas.

---

## 5. Impacto y retrocompatibilidad

- Los documentos existentes siguen siendo válidos: el check empieza en modo aviso (`WARN`) y pasa a `FAIL` cuando la revisión final (RF-13) termine.
- Los nombres de fichero actuales (`01..04_*`, `TEMPLATE_ADR.md`, `TEMPLATE_POSTMORTEM.md`) se mantienen para no romper `new_lifecycle_task.py` ni enlaces.
- Rollback: `git revert` del squash de cada tarea.

---

## 6. Tareas (épica)

1. Plantilla base genérica y puntos de extensión (RF-01..RF-04).
2. Plantillas de issues, PR, IDEAS y TODO alineadas con la base, y check de paridad issues ↔ TODO (RF-07..RF-09).
3. Esqueleto común de workflows y su check (RF-05, RF-06, RF-12).
4. Fase 4 con motor Python único en los dos plugins (RF-10).
5. Paridad del safety gate y guardrails agnósticos (#108, PR #102).
6. Paridad de hooks con un solo motor Python (RF-11; incluye los hooks de P5 de #103).
7. Sacar del repo todo lo referente a app (RF-14, RF-15; incluye P2 y P3 de #103, con los datos en las capas de `aagy_config` de #104).
8. Hard sync con lista de ficheros instalados (RF-16, RF-17).
9. **Última de todo el backlog**: revisar y actualizar toda la documentación y actualizar o borrar lo desfasado (RF-13).

---

## 7. Preguntas abiertas (con valor por defecto)

- **P-01**: ¿el check de esqueleto aplica también a las skills heredadas de ECC que no son del lifecycle? Por defecto: sí, solo al esqueleto, no al contenido.
- **P-02**: ~~¿la extensión de app se mueve ya o queda como ejemplo?~~ Resuelta 2026-11-24: en este repo no queda nada de app. Se mueve a su repo y se aplica allí reinstalando el plugin y con una hard sync (RF-14..RF-17).
- **P-03**: ~~¿los comandos heredados de ECC sin equivalente en `aagy` se portan o se marcan como asimetría?~~ Resuelta 2026-11-24: se portan a `aagy` siempre que se pueda; si Antigravity no lo permite, se marca la asimetría en su sección `Paridad`.
- **P-04**: ¿lo desfasado se borra o se archiva? Por defecto: se borra (queda en el historial de git), salvo ADRs, que se marcan `Superseded`.

---

## 8. Referencias

- `rules/AGENTS.md` §2, `skills/engineering-lifecycle/SKILL.md`, `doc/00-governance/DOC_STANDARDS.md`
- ADR-0003 (estructura `/doc` v2), ADR-0004 (perfiles declarados por el repo consumidor)
- `scripts/py/new_lifecycle_task.py`, `scripts/py/backlog.py`, `scripts/py/sync_aagy_ecc.py`, `scripts/py/audit_plugin_parity.py`
