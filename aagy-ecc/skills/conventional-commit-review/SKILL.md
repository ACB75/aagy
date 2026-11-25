---
name: conventional-commit-review
description: "Draft and review [type]-[projects]: <title> commits with body comments."
metadata:
  origin: AAGY
---

# Conventional Commit & Message Review

Review staged git diffs and draft commit messages that strictly follow the workspace standard:
`[type]-[projects]: <title>` accompanied by a mandatory explanatory body comment (`msg comment`).

## Cuándo usarlo

Draft and review [type]-[projects]: <title> commits with body comments.

## Uso

Se carga sola cuando la tarea encaja con su `description`, o al pedirla por su nombre: `conventional-commit-review`.

## Standard Commit Format

### 1. Title Structure: `[type]-[projects]: <title>`

- **`[type]`**: Conventional Commit type: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `perf`, `build`, `ci`, `sec` (or `security`).
- **`-`**: Mandatory delimiter between type and affected projects.
- **`[projects]`**: One or more affected projects or modules, as declared in `projects` of the repo's `.governance/aagy.json` (any lowercase slug if it declares none), e.g. `[api]`, `[web]`, `[scripts]`, `[doc]` (or comma-separated `[api,web]` for cross-cutting changes).
- **`: <title>`**: Colon followed by a concise, imperative title in lowercase without a trailing period.

### 2. Mandatory Explanatory Body Comment (`msg comment`)

Single-line commits are strictly prohibited. Every commit must include an explanatory body comment detailing:

1. **Motivation & Context**: Why this change is necessary and what problem it solves.
2. **Affected Components**: Modules, contracts, or configuration files touched.
3. **Architectural Decisions**: Trade-offs, design patterns, or hardening applied.
4. **Verification**: Tests executed, exit codes, and quality gate results.

## Workflow

1. Run `git diff --staged` (or `git diff` if nothing staged) to inspect changes.
2. Identify the commit type and impacted project(s).
3. Draft the title: `[type]-[projects]: <title>`.
4. Draft the structured explanatory body comment.
5. Present the drafted message for user review. Never commit or push without explicit confirmation.

## Canonical Examples

```gitcommit
feat-[cluster]: implement tenant storage manager and quota enforcement

Introduce isolated storage telemetry and directory quotas per tenant.
- Package cluster/internal/storage with multi-OS support (Linux/Windows).
- Enforce hermetic environments (LOCAL, SANDBOX, LIVE) in cluster inventory.
- Tests: 100% unit tests passing in manager_test.go and storage_test.go.
```

```gitcommit
fix-[auth]: resolve ed25519 public key parsing in jwks endpoint

Fix cryptographic key decoding failure under RFC 7517 verification.
- Normalize base64url padding and validate curve parameters at startup.
- Prevent intermittent 500 errors when rotating refresh tokens.
- Tests: verified via auth/health and pytest integration suites (code 0).
```

## Anti-Patterns

- Single-line commits without an explanatory body.
- Using standard parentheses `feat(scope):` instead of `[type]-[projects]: <title>`.
- Executing `git commit` or `git push` autonomously without explicit user confirmation.

## Paridad

Claude Code: el mismo skill `conventional-commit-review` en el núcleo de `aagy-ecc`, espejado desde la raíz por `sync_aagy_ecc.py`.
