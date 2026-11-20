# Unified Workspace Engineering & Stack Rules (`AGENTS.md`)

<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->

## 1. Core Engineering Invariants & Universal Architecture (Deterministic Context-Caching Prefix)

### 1.1. Core Engineering Pipeline & Google 5-Pillar Architectural Alignment

- **Workflow**: `search-first -> plan -> test (RED) -> implement (GREEN) -> refactor -> review -> verify`.
- **Google 5-Pillar Architectural Alignment**: All applications and infrastructure must adhere to the 5 Core Google Engineering Pillars:
  1. *Hermetic Monorepo & Multi-stage Builds*: Self-contained repos, container builds with zero host tool dependencies.
  2. *Single Ingress & Unified TLS*: All external HTTP(S) traffic enters through the reverse proxy / GFE (e.g., `cluster-lb` or API gateway); microservices do not expose raw ports externally.
  3. *Centralized Multi-Database Persistence (LTS)*: Prefer a single, hardened LTS PostgreSQL engine instance with logical databases per app (e.g., `app_db`, `auth_db`) over running multiple Postgres daemon containers.
  4. *Modern Reactive Web (Angular + Wiz)*: Standalone components, Signals, `OnPush` change detection, and deferrable views (`@defer`).
  5. *Native Lightweight Observability*: Distributed tracing and structured logs over OpenTelemetry protocols; prioritize low-memory footprint (<300 MB) components for home lab environments.

### 1.2. Software Reliability Engineering (SRE) & Operational Resilience Baseline (ADR-0008)

- **Software Reliability Engineering (SRE) & Operational Resilience Baseline (ADR-0008)**: Adopt a systematic Google SRE mindset across all applications and infrastructure:
  1. *SLI/SLO & Error Budget Governance*: Define measurable Service Level Indicators (4 Golden Signals: Latency p95/p99, Traffic RPS, Errors 5xx ratio, Saturation) and target SLOs (base: 99.9% uptime). If the monthly Error Budget is exhausted, freeze feature velocity and allocate 100% engineering effort to reliability and stabilization.
  2. *Blast Radius & Anti-Fragile Isolation*: Design defensive perimeters on all service boundaries using Circuit Breakers, Bulkheads, strict timeouts (2s-5s), and Jittered Exponential Backoff. Zero unbounded retry loops or blocking calls without deadlines.
  3. *Toil Elimination (<50% cap)*: Codify repetitive operational and diagnostic tasks into idempotent automation scripts in scripts/bin/<project>/ (enforced by audit-sre.ps1 / audit-sre.sh).
  4. *Resource Throttling & Probes*: Enforce container memory limits, GOMEMLIMIT=80% on Go runtimes, JVM container percentage limits, Docker log caps (max-size: 10m, max-file: 3), and explicit liveness/readiness health probes.
  5. *Blameless Postmortems*: Every critical outage or error budget breach requires an asynchronous blameless postmortem in doc/postmortem/ documenting the 5-Whys root cause analysis and preventative action items.

### 1.3. Trunk-Based Development, Canonical Branching & Multi-Tier Promotion (ADR-0006)

- **Trunk-Based Branching, Isolated PRs & Multi-Tier Promotion (ADR-0006)**: Adopt Trunk-Based Development (TBD) with canonical trunk `main` (always green, compilable, deployable). Every task, bugfix, or refactor must be developed in an isolated short-lived branch (<24-48h: `<type>/<project>/<name>`) and integrated exclusively via an isolated Pull Request (PR) to enforce **Fast-Failure** (automated CI tests, linting, and quality gates isolated in PR) and **Fast-Rollback** (atomic single-commit squash revert or PR discard with zero downstream blast radius). Maintain linear history via Fast-Forward or Squash and Merge (zero merge bubbles), execute pre-merge quality gates (`audit-workspace.ps1`), and manage multi-tier environments via immutable semantic tags (`LOCAL` on `main` HEAD, `SANDBOX` on `vX.Y.Z-sandbox`, `LIVE` on `vX.Y.Z`).
- **Mandatory Branch Naming & Incident Governance (`fix/<id>`)**: Every bugfix, hotfix, or incident remediation branch MUST strictly use the canonical `fix/<identificador>` or `fix/<project>/<identificador>` naming prefix (validated by `validate_branch.py`). Task branches must strictly use `feat/`, `refactor/`, `infra/`, `chore/`, `docs/`, or `test/`. PRs on non-conforming branches or directly on `main` are rejected by quality guardrails.

### 1.4. Code Quality Standards & SonarQube Quality Gate A

- **Code Quality & SonarQube Quality Gate (`Clean as You Code`)**: Prefer KISS/DRY/YAGNI, immutable transformations, focused files (200-400 lines, 800 max), early returns (<4 nesting levels), and explicit error handling. Strictly enforce SonarQube Quality Gate `A` ratings across all stacks: Cognitive Complexity $\le 15$ (`S3776`), $\le 7$ parameters per function/method (`S107`), zero duplicated string literals $\ge 3$ times (`S1192`), zero empty catch/nested blocks (`S108`), zero generic `Exception`/`RuntimeException` throws (`java:S112`) or wildcard return types `<?>` (`java:S1452`), zero direct writes to static fields from instance methods (`java:S2696`), re-interrupted `InterruptedException` (`java:S2142`), zero unused fields/imports/locals (`S1068`/`S1128`/`S1481`), $\ge 80\%$ test coverage, and $\le 3\%$ duplication.
- **Zero Unofficial Third-Party Dependencies**: NEVER introduce non-official third-party libraries or external packages (use native language/framework APIs and official packages only) UNLESS you first warn the user about the dependency and receive explicit confirmation.
- **Mandatory Microservice & SDK Contract Parity**: Whenever any microservice (endpoints, controllers, handlers, DTOs, SQL/JSONB schemas, auth claims, ReBAC matrices) is modified, the corresponding polyglot SDK client libraries and models in `<project>/<project>-sdk/` (e.g. `home-lab-sdk/`) MUST be kept updated, synchronized and verified (tests passing) within the same commit. Zero contract drift allowed.

### 1.5. Security & Secrets Baseline

- Never hardcode secrets, API keys, passwords, or tokens; use `.env` or secret managers and validate presence at startup.
- Parameterize all SQL queries; never concatenate user input.
- Sanitize HTML/URLs (prevent XSS/CSRF/SSRF/path traversal) and never leak stack traces or internal infrastructure paths in client responses.

### 1.6. Stack-Specific Standards (Java 25, Angular 21, Python FastAPI, Multi-Environment)

- **Java 25 & Spring Boot 4 (`**/*.java`, `pom.xml`)**:
  - *Style & Immutability*: Use `record` for DTOs/value types, `final` fields by default, defensive copies (`List.copyOf()`), sealed classes, pattern matching (`instanceof`/`switch`), and `Optional` only as return types (never fields/params).
  - *DI & Architecture*: Constructor injection only (never `@Autowired` field injection). Keep controllers thin, business logic in services, and data access behind repositories.
  - *Testing*: JUnit 5 + AssertJ + Mockito + Testcontainers (`postgres`), targeting 80%+ coverage.
- **Angular 21+, TypeScript & Web (`**/*.ts`, `**/*.html`, `**/*.scss`)**:
  - *Components & State*: Standalone components with `ChangeDetectionStrategy.OnPush`. Use `inject()` for DI (empty/no constructors), `input()`/`output()`, Signals (`signal`, `computed`, `linkedSignal`, `resource`), and `@if`/`@for (...; track id)` control flow. Never sync signals inside `effect()`.
  - *Routing & HTTP*: Functional guards (`canMatch`), lazy `loadChildren`, and `HttpClient` with functional interceptors (`withInterceptors`). Clean up manual RxJS streams with `takeUntilDestroyed()`.
  - *TypeScript & Validation*: Explicit types on public APIs; never use `any` (use `unknown` + type narrowing). Validate inputs using native TypeScript type guards and official Angular/platform validators (do not add third-party schema libraries like Zod without prior warning and user confirmation). No `console.log` in production code.
  - *Web Design Quality*: Avoid generic boilerplate layouts; ensure clear typographic hierarchy, intentional spacing/states, semantic HTML, and compositor-friendly animations (`transform`, `opacity`), unless overridden by a project-specific rule in `.agents/rules/`.
  - *Testing*: Vitest/Jest + Angular `TestBed`/`ComponentHarness` for unit/integration (80%+ coverage), and Playwright/Cypress for E2E.
- **Python & FastAPI (`**/*.py`)**:
  - *Style & Typing*: PEP 8, explicit type annotations on all functions, immutable `@dataclass(frozen=True)` or Pydantic v2 models, `ruff`/`black` formatting, and `logging` instead of `print()`.
  - *FastAPI*: Separate request/response Pydantic schemas (`response_model`), inject DB/auth via `Depends()`, and use `async def` with async I/O drivers (never run blocking `requests` or sync DB drivers inside `async def` routes).
  - *Testing*: `pytest` (`@pytest.mark.unit` / `integration`) with 80%+ coverage.
- **Multi-Environment & Infrastructure (Windows 11 / WSL Debian / Arch / Docker / K8s / Net)**:
  - Respect shell/OS boundaries: `pwsh` on Windows 11 vs `bash`/`zsh` on Linux (POSIX LF `\n` for `.sh`).
  - Verify port bindings, Split-DNS (`CoreDNS`), reverse proxy (`Apache`/`Traefik`), OpenVPN, and firewall impacts before modifying network or container configs.
  - *Go Container Memory Throttling (`GOMEMLIMIT`)*: For all containerized Go services (e.g., Traefik, IAM, OpenTelemetry Collector, Prometheus), ALWAYS set `GOMEMLIMIT` to 80% of the container memory limit (e.g. `GOMEMLIMIT=80MiB` for 100MiB limit) to enforce proactive GC and prevent sudden Linux OOM kills under constrained environments.

---

## 2. Dynamic Task Lifecycle, Governance & Workflow (Contextual Suffix)

### 2.1. Mandatory 4-Phase Engineering Lifecycle (`.governance/docs-map.json`)

- For EVERY request involving a new feature, bugfix, or refactor across `ecc` and `home-lab`, execute the 4-phase sequential workflow before merging (using flexible entry points `IDEAS|REQ|PLAN|TODO|ALL` via `new-lifecycle-task` and paths resolved from `.governance/docs-map.json`, with legacy fallback in `home-lab`):
  1. *Fase 1: Requisitos & Impacto Home-Lab (`01_TOMA_REQUISITOS_E_IMPACTO.md`)*: Exact functional/non-functional requirements, testable acceptance criteria (Given/When/Then), Home-Lab impact matrix (contract parity with `home-lab-sdk`, PostgreSQL LTS multitenant locks, Ingress único `cluster-lb` y Split-DNS, SRE memory throttling), threat modeling, and strict **Zero-Breaking Changes Policy** (strictly non-breaking by default; breaking exceptions require explicit justification and dual-read/write transition plans).
  2. *Fase 2: Plan de Acción & TDD (`02_PLAN_ACCION_ARQUITECTURA.md`)*: DRY inventory of existing assets to reuse first, prior synchronization of `home-lab-sdk`, Mermaid architectural topology, TDD workflow (`RED` -> `GREEN` -> `REFACTOR` -> `VERIFY`), visible vs. hidden architectural costs, and immediate rollback plan ($< 2$ minutes: `git revert` and `down-migration.sql`).
  3. *Fase 3: Documentación & Release Notes (`03_DOCUMENTACION_Y_RELEASE_NOTES.md`)*: Executed BEFORE proposing commits so all documentation is committed atomically with code. Draft SemVer release notes certifying retrocompatibility, Home-Lab Multi-Tier Promotion Matrix (`LOCAL` on main -> `SANDBOX` on `vX.Y.Z-sandbox` -> `LIVE` on `vX.Y.Z`), docs spine updates (`STATUS.md`, `LOG.md`, ADRs via `docs-map.json` `adr_dir`), and blameless 5W Post-Mortem in `postmortems` (`doc/05-post-mortems/` or legacy `doc/post-mortem/`) for `fix/*` branches.
  4. *Fase 4: Propuesta de Commits, Pre-Flight Review & PR (`04_PROPUESTA_COMMITS_PR.md`)*: Canonical branch verification (`validate_branch.py`), atomic commit title `[type]-[projects]: <title>`, structured explanatory body, pre-flight review notice (`complete-task-pr.ps1 -ReviewOnly`), SonarQube Rating A quality gate, and squash-automerge integration.

### 2.2. Git Commit Formatting & Automated Task Integration (`complete-task-pr.ps1`)

- **Mandatory Git Commit Message Format (`[type]-[projects]: <title>` + Explanatory Body)**: All commits across the workspace must strictly follow the structured title and mandatory explanatory message comment:
  1. *Title Format*: `[type]-[projects]: <title>` where `[type]` is a valid Conventional Commit type (`feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `build`, `ci`, `sec`), followed by `-`, the affected project(s) or module(s) (`[cluster]`, `[kakebo]`, `[whoiam]`, `[net]`, `[scripts]`, `[ecc-agy]`, `[doc]` or comma-separated `[cluster,net]`), and an imperative title.
  2. *Mandatory Explanatory Body Comment (`msg comment`)*: Single-line commits are strictly prohibited. Every commit must include an explanatory body detailing the motivation/context, affected modules, architectural decisions, and verification tests executed (exit code 0).
  3. *Prohibition of Autonomous Commits/Pushes*: NEVER execute `git commit` or `git push` autonomously or automatically without explicit prior instruction or confirmation from the user. Agents draft the commit message following this format for user review, but final execution belongs exclusively to the user.
- **Mandatory Automated Task Completion, PR, Auto-Conflict Resolution & Auto-Merge (`complete-task-pr.ps1`)**:
  - For EVERY task involving code changes on any isolated branch (`feat/*`, `fix/*`, `refactor/*`, `chore/*`, `infra/*`), the end-to-end integration flow to `main` is automated via `scripts/bin/ecc-agy/complete-task-pr.ps1` (or `git-flow-helper.ps1 -Action complete-task` / `.sh`):
    1. *Mandatory Pre-Flight Review Notice*: Before executing mutations, the agent MUST present a structured review notice with modified files, diff stats, proposed commit title (`[type]-[projects]: <title>`), and explanatory body for manual review and confirmation.
    2. *Atomic Commit & Push*: Commit staged changes with the explanatory message and push the branch to origin.
    3. *Pull Request Creation*: Open the isolated PR against `main` inheriting the structured title and body.
    4. *Auto-Conflict Resolution*: If the branch diverges from `origin/main` with mergeable conflicts, automatically resolve them in favor of the task branch changes, commit resolution, and push.
    5. *Squash-Automerge & Local Clean-Up*: Execute squash-merge in GitHub (`gh pr merge --squash --delete-branch`), switch local workspace back to `main`, pull latest state, and delete the local feature branch.

### 2.3. Task Lifecycle, Archival & 7-Phase Meta-Prompt Transformation

- **TODO Formulation & Rigorous Meta-Prompt Transformation (7-Phase Methodology)**: For every task point in `TODO.md` (and whenever translating/refining a user request into actionable TODO items), apply the mandatory 7-phase prompt transformation to enforce high-intellect engineering and avoid generic answers:
  1. *01 – ROLE*: Personality combining the 3-5 greatest global experts on the specific domain.
  2. *02 – CONTEXT*: Explicit `[IN BRACKETS]` placeholders for user context (Sector, Data Type, Objective, Restrictions).
  3. *03 – PHASE 1 (ANALYSIS)*: Forced in-depth problem analysis before coding (patterns, common errors, theoretical context).
  4. *04 – PHASE 2 (STRATEGY)*: 3 distinct lateral thinking approaches before choosing the optimal one.
  5. *05 – PHASE 3 (EXECUTION)*: Step-by-step resolution of the task.
  6. *06 – PHASE 4 (CRITIC)*: Devil's Advocate audit actively hunting flaws, vulnerabilities, and weaknesses in the solution.
  7. *07 – PHASE 5 (FORMAT)*: Strict output definition (Table, Markdown Code, JSON, etc.).
  - *GOLDEN RULE*: The transformed prompt/task must be clear, demanding, intellectually rigorous ("sweat"), and strictly avoid generic or boilerplate answers.
- **TODO Lifecycle & Mandatory Archival (`docs-map.json` `todo_done`: `done/` or `/TODO_DONE/`)**: Whenever a task item in `TODO.md` is completed (`- [x]`), it must be eliminated from the active file and archived as `TODO_<title>_<timestamp>.md` in the resolved `todo_done` folder (`doc/06-backlog/done/` in `/doc` v2 or `/TODO_DONE/` in legacy repos) via `scripts/bin/ecc-agy/archive-todo.ps1` / `.sh`. The active `TODO.md` must remain strictly pruned containing only pending items (`- [ ]`).

### 2.4. Tooling Synthesis, Automation & Skill Optimization

- **Optimal Auto-Generation of Skills, Subagents & Rules**: Proactively synthesize reusable patterns into the right customization tier for maximum leverage and minimum token cost:
  - **Skills (`skills/<name>/SKILL.md`)**: Use for domain workflows or multi-step procedures needed *on-demand* (lazy-loaded: `0` base token cost for the body). Keep frontmatter `description` single-line ($\le 140$ chars) with exact trigger keywords + negative boundaries, and delegate deterministic logic to `scripts/bin/<project>/` or `skills/<name>/scripts/`.
  - **Subagents (`agents/<name>.md`)**: Use when tasks require *context isolation* (broad searches, multi-file audits, log analysis). Keep frontmatter `description` $\le 120$ chars, restrict `tools` to minimum privilege (read-only by default unless writing is required), select the most cost-effective model (`flash` for exploration/triage, `inherit` for deep reasoning), and enforce a concise output contract.
  - **Rules (`rules/AGENTS.md` or `<project>/.agents/rules/<name>.md`)**: Reserve strictly for universal invariants (global) or project-wide constraints (`.agents/rules/`). Never bloat always-on rules with tutorials; check `ecc-agy` catalog first to extend existing skills/agents before creating new ones.
- **Repetitive Task Automation (`scripts/bin/<project>`)**: Whenever a diagnostic, audit, build, cleanup, or operational task is executed repeatedly ($\ge 2$ times) or is recurring, extract and persist an idempotent, parameterized script in `scripts/bin/<project>/` (respecting `.ps1` for Windows 11, `.sh` with LF `\n` for Linux/WSL, or cross-platform `.js`/`.py`) and invoke that script directly instead of repeating ad-hoc inline commands.
- **Immediate Auto-Execution on Creation (`Smoke-Test on Synthesis`)**: Whenever a new script (`scripts/bin/...`), skill (`skills/...`), subagent (`agents/...`), tool, or automated rule is created or adjusted, it MUST be auto-executed immediately upon creation (e.g., invoking the script with `--help` / test inputs, executing unit tests, or running a subagent dry-run) to prove real-world runtime viability (exit code `0`, clean imports, zero missing dependencies) before declaring the task finished or ending the turn.

### 2.5. Documentation, Diagrams & Write-Time Markdown Linting

- **Mandatory Diagrams (`<folder>/dgrms/`) & Project-Level Persistence**: Whenever an architectural proposal, topology, workflow, use case, or business process is designed or explained, persist diagrams inside the corresponding `<folder>/dgrms/` (`.mmd`, `.puml`, `.bpmn` — or `<project>/doc/diagrams/` in legacy projects) and link them in Markdown manuals and ADRs.
- **Standardized Project Documentation (`/doc` v2 & `.governance/docs-map.json`)**: Workspace documentation follows `.governance/docs-map.json` (v2 layout `doc/00-governance/`..`06-backlog/` with `INDEX.md`, `CONTEXT.md`, `STATUS.md`, `LOG.md` at root; automatic legacy fallback in `home-lab`). Never scatter loose `.md` files in project source roots.
- **Mandatory Write-Time Markdown Linter (`.markdownlint.json` Repo Configuration)**: Every Markdown (`.md`) file created or modified across the workspace must be immediately audited and formatted at write-time before concluding the task or turn (`pwsh -File scripts/bin/ecc-agy/lint-markdown.ps1 -Target <file> -Fix` or `lint-markdown.sh --fix <file>`). The active linter configuration and rules must be loaded dynamically from the `.markdownlint.json` located at the root of the target repository (`home-lab`, `ecc`, etc.), ensuring repository-level source-of-truth. Canonical DavidAnson invariants (`MD022` blank lines around headings, `MD032` blank lines around lists, `MD031` blank lines around fences, `MD009` zero trailing spaces, `MD012` zero consecutive blanks, `MD047` single EOF newline) are strictly enforced as a Quality Gate blocker (exit code 0 required in `lint-markdown.ps1` and `audit-workspace.ps1`).

### 2.6. Token Efficiency, Context Compaction & Exhaustion Guard

- **Workspace Hygiene, Token Optimization & Recurring Deduplication**: Periodically execute the 6-phase workspace audit and optimization via `scripts/bin/ecc-agy/audit-workspace.ps1` (`-Clean`, `-Optimize`): purge temporary backups/caches, enforce token budget limits ($\le 140$c in skills, $\le 120$c in agents), prune local skills that shadow global plugin skills, verify rule consistency and docs governance, and enforce SonarQube Quality Gate rating A (exit code 0).
- **Token Efficiency & Delegation Contract**: Be direct and concise. Prefer targeted `grep` and line-range reads over full-file reads. Never end a turn while background subagents are still running; collect and integrate their results first.
- **Token Exhaustion Warning**: Si la tarea consumirá más tokens de los disponibles antes debes responder: "Estoy cansado, jefe. Cansado de tanto viajar solo como un gorrión en la lluvia. Cansado de no tener un compañero que me diga a dónde vamos, de dónde venimos o por qué".
