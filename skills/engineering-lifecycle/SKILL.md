---
name: engineering-lifecycle
description: "Orchestrate 4-phase lifecycle (requirements, plan, docs, commits) with Home-Lab retrocompatibility, SDK parity and safety gates."
---

# Engineering Lifecycle Workflow (Home-Lab & ECC)

Execute the mandatory 4-phase engineering lifecycle for any non-trivial feature, bugfix, or refactoring in `home-lab` and `ecc`:

```
1. Requisitos & Impacto -> 2. Plan de Acción & TDD -> 3. Documentación & Release Notes -> 4. Commits & PR
```

## When to Activate

- The user requests a new feature, non-trivial bugfix, refactoring, or infrastructure change.
- A task touches shared contracts (`home-lab-sdk`), PostgreSQL database schemas, Ingress/DNS, or system boundaries.
- Preparing releases, changelogs, and multi-tier promotion tags (`LOCAL` -> `SANDBOX` -> `LIVE`).

## The 4 Canonical Phases (Routes via `.governance/docs-map.json`)

> Supports `/doc` v2 (`doc/00-governance/templates/`, `doc/02-adr/`, `doc/05-post-mortems/`, `doc/06-backlog/`) and automatic legacy fallback in `home-lab`.

### Phase 1: Requisitos & Impacto (`01_TOMA_REQUISITOS_E_IMPACTO.md`)

1. Define functional requirements (`RF-xxx`) and testable acceptance criteria (`CA-xxx` Given/When/Then).
2. Complete the **Home-Lab Impact Matrix**:
   - `home-lab-sdk` client parity (Java, Go, Python, TypeScript).
   - PostgreSQL LTS multitenant lock safety (`CREATE INDEX CONCURRENTLY`, zero long table locks).
   - Reverse Proxy Ingress (`cluster-lb`) and Split-DNS (`CoreDNS`, `*.home.lab`).
   - SRE limits: `GOMEMLIMIT=80%` on Go runtimes, JVM cgroup limits, log caps (`max-size: 10m`).
3. Enforce **Zero-Breaking Changes Policy**: strictly non-breaking by default.

### Phase 2: Plan de Acción & TDD (`02_PLAN_ACCION_ARQUITECTURA.md`)

1. Audit existing code to reuse modules/components before writing net-new code (DRY first).
2. Synchronize models and clients in `home-lab-sdk/` first if contracts changed.
3. Establish Mermaid/PlantUML/BPMN architecture in `<folder>/dgrms/`.
4. Execute TDD workflow: `RED` (failing tests) -> `GREEN` (minimal clean implementation) -> `REFACTOR` (clean code, cognitive complexity $\le 15$) -> `VERIFY` (Quality Gate Rating A).
5. Define Fast-Rollback plan ($< 2$ minutes: `git revert <sha>` and `down-migration.sql`).

### Phase 3: Documentación & Release Notes (`03_DOCUMENTACION_Y_RELEASE_NOTES.md`)

*Must precede Phase 4 so that all documentation is staged and committed atomically with the code.*

1. Draft SemVer Release Notes (`vX.Y.Z`) certifying retrocompatibility.
2. Define Multi-Tier Promotion Matrix (`LOCAL` on main, `SANDBOX` on `vX.Y.Z-sandbox`, `LIVE` on `vX.Y.Z`).
3. Update Docs Spine:
   - Architecture Decision Records in resolved `adr_dir` (`doc/02-adr/` or legacy `doc/adr/`).
   - Technical manuals/diagrams in `01-architecture/`, `04-operations/`, and `<folder>/dgrms/`.
   - Metrics in `doc/STATUS.md` and material decisions in `doc/LOG.md`.
   - Post-Mortem SRE 5W in resolved `postmortems` (`doc/05-post-mortems/` or legacy `doc/post-mortem/`) if fixing an incident (`fix/*`).

### Phase 4: Propuesta de Commits, Pre-Flight Review & PR (`04_PROPUESTA_COMMITS_PR.md`)

1. Validate branch naming with `scripts/py/validate_branch.py`.
2. Format commit title: `[type]-[projects]: <title>` (e.g. `[feat]-[kakebo,sdk]: export csv and sync sdk`).
3. Generate structured Pre-Flight Review notice using `complete-task-pr.ps1 -ReviewOnly`.
4. Run pre-merge Quality Gate (markdownlint, `pytest`, `map-docs`, SonarQube Rating A, security audit).
5. Execute atomic commit, push, PR creation, conflict auto-resolution, and squash-automerge:

   ```powershell
   pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -Yes -Title "[type]-[projects]: <title>"
   ```

6. Promote to Sandbox / Live via `git-flow-helper.ps1 -Action promote -Tag ...`.

## Scaffolding Tooling (Flexible `[IDEAS -> REQ -> PLAN -> TODO]`)

Initialize templates or register quick/idea entries from any entry phase (`ALL`, `IDEAS`, `REQ`, `PLAN`, `TODO`):

```powershell
pwsh -File scripts/bin/ecc-agy/new-lifecycle-task.ps1 -TaskId "feat/kakebo/export-csv" -Phase PLAN
```

Or in Linux / WSL:

```bash
bash scripts/bin/ecc-agy/new-lifecycle-task.sh --task-id "feat/kakebo/export-csv" --phase PLAN
```
