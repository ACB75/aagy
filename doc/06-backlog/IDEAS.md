# Catálogo de Propuestas e Ideas de Ingeniería (`IDEAS.md`)

> **Protocolo de Ingesta:**
>
> 1. Añade propuestas con el formato estructurado a continuación.
> 2. Cuando una propuesta sea aprobada para desarrollo, cambia su estado a `- Status: Approved`.
> 3. Ejecuta `pwsh -File scripts/ps1/aagy.ps1 sync-ideas-todo` para transformarla mediante la metodología de 7 fases e inyectarla en `doc/06-backlog/TODO.md`.

---

## Plantilla de Propuesta

```markdown
## Idea N: Nombre Conciso de la Propuesta

- Status: Draft | Approved
- Sector: <Dominio / Stack>
- DataType: <Formatos de datos / Artefactos>
- Objective: <Objetivo medible>
- Description: <Detalle del problema y solución planteada>

```

---

## Idea 1: Telemetría para autodescubrimiento y automejora

- Status: Draft
- Sector: <Dominio / Stack>
- DataType: <Formatos de datos / Artefactos>
- Objective: <Implementar un sistema de telemetría que permita el autodescubrimiento y la automejora del clúster>
- Description: <Implementar un sistema de telemetría que permita el autodescubrimiento y la automejora del clúster.>

## Idea 2: Quitar los workflows de GitHub Actions que cuesten dinero

- Status: Approved (2026-11-24, issue #105 de la épica #103: Actions opcionales, apagadas por defecto y con paridad con la CI local)
- Sector: CI/CD / GitHub Actions
- DataType: `.github/workflows/*.yml`
- Objective: Que el repo no consuma minutos de pago de GitHub Actions.
- Description: Revisar los workflows actuales (`ci-quality-gate.yml`, `project-auto-sync.yml`) y quitar o sustituir los que gasten minutos facturables. Las comprobaciones que aporten valor pueden pasar a hooks locales (pre-commit / PreToolUse) o ejecutarse en local con los scripts de `scripts/`.

## Idea 3: Quitar `gh` de los nombres de ramas y PRs

- Status: Draft
- Sector: Gobernanza Git / Lifecycle scripts
- DataType: Nombres de rama, títulos de PR, `.governance/active-issue.json`
- Objective: Que ramas y PRs no lleven el prefijo `gh-<N>`.
- Description: Hoy `new_lifecycle_task.py` crea ramas `<type>/<project>/gh-<N>-<slug>`, y `aagy complete-task-pr` y `backlog.py` (`GH_ID_RE`, `gh-sync`) detectan la issue a partir de ese `gh-<N>`. Hay que quitar `gh` del nombre y mantener el vínculo con la issue por otra vía (por ejemplo `.governance/active-issue.json` o `Closes #N` en el cuerpo del PR), con paridad en `aagy-ecc`.
