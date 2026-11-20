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

## The 4 Canonical Phases

### Phase 1: Requisitos & Impacto (`doc/templates/01_TOMA_REQUISITOS_E_IMPACTO.md`)

1. Define functional requirements (`RF-xxx`) and testable acceptance criteria (`CA-xxx` Given/When/Then).
2. Complete the **Home-Lab Impact Matrix**:
   - `home-lab-sdk` client parity (Java, Go, Python, TypeScript).
   - PostgreSQL LTS multitenant lock safety (`CREATE INDEX CONCURRENTLY`, zero long table locks).
   - Reverse Proxy Ingress (`cluster-lb`) and Split-DNS (`CoreDNS`, `*.home.lab`).
   - SRE limits: `GOMEMLIMIT=80%` on Go runtimes, JVM cgroup limits, log caps (`max-size: 10m`).
3. Enforce **Zero-Breaking Changes Policy**: strictly non-breaking by default.

### Phase 2: Plan de Acción & TDD (`doc/templates/02_PLAN_ACCION_ARQUITECTURA.md`)

1. Audit existing code to reuse modules/components before writing net-new code (DRY first).
2. Synchronize models and clients in `home-lab-sdk/` first if contracts changed.
3. Establish Mermaid architecture and data flow topology.
4. Execute TDD workflow: `RED` (failing tests) -> `GREEN` (minimal clean implementation) -> `REFACTOR` (clean code, cognitive complexity $\le 15$) -> `VERIFY` (Quality Gate Rating A).
5. Define Fast-Rollback plan ($< 2$ minutes: `git revert <sha>` and `down-migration.sql`).

### Phase 3: Documentación & Release Notes (`doc/templates/03_DOCUMENTACION_Y_RELEASE_NOTES.md`)

*Must precede Phase 4 so that all documentation is staged and committed atomically with the code.*

1. Draft SemVer Release Notes (`vX.Y.Z`) certifying retrocompatibility.
2. Define Multi-Tier Promotion Matrix (`LOCAL` on main, `SANDBOX` on `vX.Y.Z-sandbox`, `LIVE` on `vX.Y.Z`).
3. Update Docs Spine:
   - Architecture Decision Records in `doc/adr/` if high-impact architectural choice.
   - Technical manuals in `doc/manual/` and Mermaid diagrams in `doc/diagrams/`.
   - Metrics in `doc/STATUS.md` and material decisions in `doc/LOG.md`.
   - Post-Mortem SRE 5W in `doc/post-mortem/` if fixing an incident (`fix/*`).

### Phase 4: Propuesta de Commits, Pre-Flight Review & PR (`doc/templates/04_PROPUESTA_COMMITS_PR.md`)

1. Validate branch naming with `scripts/ecc-agy/validate_branch.py`.
2. Format commit title: `[type]-[projects]: <title>` (e.g. `[feat]-[kakebo,sdk]: export csv and sync sdk`).
3. Generate structured Pre-Flight Review notice using `complete-task-pr.ps1 -ReviewOnly`.
4. Run pre-merge Quality Gate (markdownlint, unit tests, SonarQube Rating A, security audit).
5. Execute atomic commit, push, PR creation, conflict auto-resolution, and squash-automerge:

   ```powershell
   pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -Yes -Title "[type]-[projects]: <title>"
   ```

6. Promote to Sandbox / Live via `git-flow-helper.ps1 -Action promote -Tag ...`.

## Scaffolding Tooling

Initialize all 4 templates for a task:

```powershell
pwsh -File scripts/bin/ecc-agy/new-lifecycle-task.ps1 -TaskId "feat/kakebo/export-csv"
```

Or in Linux / WSL:

```bash
bash scripts/bin/ecc-agy/new-lifecycle-task.sh --task-id "feat/kakebo/export-csv"
```
