# Anything Antigravity (`aagy`) Workspace Rules (`AGENTS.md`)

<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->

## 1. Core Engineering Invariants & Universal Architecture (Deterministic Context-Caching Prefix)

- **Source of Truth**: Canonical rules live in [rules/AGENTS.md](rules/AGENTS.md) (Two-Tier Architecture consumed by the global `aagy` plugin and mirrored in `aagy-ecc`).
- **Google 5-Pillars & SRE**: Hermetic Builds, Single Ingress, Centralized PostgreSQL LTS, Reactive Web, and Lightweight Observability (`GOMEMLIMIT=80%`).

## 2. Dynamic Task Lifecycle, Governance & Workflow (Contextual Suffix)

- **Lifecycle & Quality Gates**: Follow Trunk-Based Development (`feat/*`, `fix/*`, `refactor/*`), 4-phase lifecycle (`.governance/docs-map.json`), SonarQube Rating A, and write-time markdownlint (`scripts/pwsh/lint-markdown.ps1`).
- **Automated PR Integration**: Close tasks via `scripts/pwsh/complete-task-pr.ps1` using `[type]-[projects]: <title>` and mandatory explanatory body.
