# Anything Antigravity (`aagy`) Workspace Rules (`AGENTS.md`)

<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->

## 1. Core Engineering Invariants & Universal Architecture (Deterministic Context-Caching Prefix)

- **Source of Truth**: Canonical rules live in [rules/AGENTS.md](rules/AGENTS.md) (Two-Tier Architecture consumed by the global `aagy` plugin and mirrored in `aagy-ecc`).
- **Google 5-Pillars & SRE**: Hermetic Builds, Single Ingress, Centralized PostgreSQL LTS, Reactive Web, and Lightweight Observability (`GOMEMLIMIT=80%`).

## 2. Dynamic Task Lifecycle, Governance & Workflow (Contextual Suffix)

- **Branch Naming**: Create and push only `<type>/<project>/<name>` branches (`fix`, `feat`, `refactor`, `infra`, `chore`, `docs`, `test`; e.g. `fix/aagy-ecc/branch-naming`), validated by `scripts/py/validate_branch.py`. The PreToolUse safety hooks of `aagy` and `aagy-ecc` deny `git checkout -b`, `git switch -c`, `git branch` and `git push` with any other name.
- **Lifecycle & Quality Gates**: Follow Trunk-Based Development (`feat/*`, `fix/*`, `refactor/*`), 4-phase lifecycle (`.governance/docs-map.json`), SonarQube Rating A, and write-time markdownlint (`scripts/ps1/lint-markdown.ps1`).
- **Automated PR Integration**: Close tasks via `python scripts/py/complete_task_pr.py` (wrappers `scripts/ps1/complete-task-pr.ps1`, `scripts/sh/complete-task-pr.sh`) using `[type]-[projects]: <title>` and mandatory explanatory body. No auto-merge.
