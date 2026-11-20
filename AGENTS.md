# Anything Antigravity (`aagy`) Workspace Rules (`AGENTS.md`)

<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->

## 1. Core Engineering Invariants & Universal Architecture (Deterministic Context-Caching Prefix)

- **Source of Truth**: This repository (`aagy`) authors the canonical rules in [rules/AGENTS.md](file:///c:/Workspace/projects/ecc/rules/AGENTS.md) and [rules/pr-automerge-lifecycle.md](file:///c:/Workspace/projects/ecc/rules/pr-automerge-lifecycle.md).
- **Two-Tier Architecture**: Global agents and harnesses consume `rules/AGENTS.md` from the installed `aagy` plugin to avoid prompt duplication.
- **Google 5-Pillars & SRE**: All workflows adhere to Hermetic Builds, Single Ingress, Centralized Persistence, Modern Reactive Web, and Native Lightweight Observability.

## 2. Dynamic Task Lifecycle, Governance & Workflow (Contextual Suffix)

- **Lifecycle & Governance**: For task lifecycle, branch naming (`fix/<id>`, `feat/*`, `refactor/*`), automated PR lifecycle, and SonarQube quality gates, consult [rules/AGENTS.md](file:///c:/Workspace/projects/ecc/rules/AGENTS.md).
- **Automated Task Integration**: Automated integration to `main` is handled by `complete-task-pr.ps1` with atomic conventional commit messages `[type]-[projects]: <title>`.
