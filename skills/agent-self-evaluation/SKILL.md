---
name: agent-self-evaluation
description: "Unified 5-axis self-evaluation, instinct discovery, and budget-gated self-improvement via Stop hook and CLI. Not for raw rule edits."
origin: AAGY
---

# Unified Agent Self-Evaluation & Continuous Self-Improvement (`aagy` / `aagy`)

Combines post-task 5-axis quality evaluation, passive `Stop` hook instinct capture (`0` prompt tokens, $< 500\text{ ms}$), dual-level instinct persistence (`<repo>/.agents/instincts/` + `$PLUGIN_DATA/instincts/`), Eval-Driven Development (`pass@k` / `pass^k`), and budget-gated artifact promotion (`scripts/py/self_improve.py`).

## When to Activate

- After completing code changes spanning 3+ files or a multi-step engineering lifecycle (`implement -> test -> review`)
- When capturing or reviewing project-scoped (`.agents/instincts/`) and global (`$PLUGIN_DATA/instincts/`) instincts
- When running pattern discovery (`--discover`), candidate gate review (`--review`), or controlled promotion (`--promote --confirm`)
- When defining capability/regression evals (`pass@k` / `pass^k`) for harness or skill improvements (see [`references/eval-driven-development.md`](references/eval-driven-development.md))
- At session end via the passive `Stop` hook in `hooks.json` (see [`references/hook-integration.md`](references/hook-integration.md))

## 1. The 5 Evaluation Axes

| Axis | Question | What It Catches |
| :--- | :--- | :--- |
| **Accuracy** | Are claims, APIs, and outputs verified by tool evidence? | Hallucinations, unverified claims, wrong syntax |
| **Completeness** | Did it cover all requirements and critical edge cases? | Missed requirements, unhandled error paths |
| **Clarity** | Is the output structured, scannable, and unambiguous? | Wall-of-text paragraphs, unexplained jargon |
| **Actionability** | Can the user or CI act immediately on the deliverable? | Vague suggestions, missing commands or file links |
| **Conciseness** | Did it use the minimum tokens needed? | Filler, meta-commentary, repeated statements |

### Scoring Scale & Evidence Rule

- `5` — Exceptional: verified with concrete tool outputs, no substantive improvement needed
- `4` — Good: minor nits only
- `3` — Adequate: meets request but has a notable gap on at least one axis
- `2` — Weak: clear gap affecting correctness or usability
- `1` — Poor: fundamentally misses the request

Every score below `5` MUST cite concrete evidence (**"Show the gap, don't just name it"**).

## 2. Unified Self-Discovery & Self-Improvement Architecture

```text
Session / CLI Activity
  │
  ├─► Passive Stop Hook (hooks.json -> self_improve.py --capture-stop, <500ms, 0 tokens, returns {})
  └─► Manual CLI (auto-evolve.ps1/.sh | manage-instincts.ps1/.sh | self_improve.py)
        │
        ▼
  Sanitization Layer (AgentShield Prompt-Injection Check + Secret Redaction [REDACTED])
        │
        ├─► Project Level: <repo>/.agents/instincts/{*.md, observations.jsonl}
        └─► Global Plugin Level: $PLUGIN_DATA/instincts/{*.md, observations.jsonl}
              │
              ▼
  Pattern Discovery & Deduplication (--discover, >= 2 occurrences, prefers Tier-2 skill/script/hook)
              │
              ▼
  Controlled Promotion (--review / --promote <id> --confirm)
    1. AgentShield Security Gate (0 injections, 0 secrets)
    2. Context Budget Hard Gate (workspace_audit.py: skill <=140c, agent <=120c, rule <=24KB / <=16k tokens)
    3. Isolated Smoke-Test (exit code 0)
    4. Explicit Human Confirmation (--confirm required before writing to skills/, rules/, or scripts/)
```

## 3. CLI Parity Commands (`pwsh` / `bash` / `python`)

```powershell
# 1. Discover recurring patterns (>= 2 occurrences) across project + global scopes
pwsh -NoProfile -File scripts/ps1/auto-evolve.ps1 -Discover

# 2. Review candidate against AgentShield, Budget Gate, and Smoke-Test (no write)
pwsh -NoProfile -File scripts/ps1/auto-evolve.ps1 -Review "pg-lock-safety" -Tier skill

# 3. Promote candidate ONLY with explicit confirmation after passing all gates
pwsh -NoProfile -File scripts/ps1/auto-evolve.ps1 -Promote "pg-lock-safety" -Tier skill -Confirm

# 4. Manage instincts directly at project or global ($PLUGIN_DATA) scope
pwsh -NoProfile -File scripts/ps1/manage-instincts.ps1 list --scope all
pwsh -NoProfile -File scripts/ps1/manage-instincts.ps1 save --id pg-lock --trigger "DDL migration" --learning "Use CONCURRENTLY" --scope project

# 5. Run 5-axis output evaluation via CLI
python scripts/py/self_improve.py --evaluate "All 146 tests passed (exit code 0)." --task "Verify suite"
```

## References & Templates

- [`references/hook-integration.md`](references/hook-integration.md) — Passive `Stop` hook configuration and non-blocking contract
- [`references/evaluation-criteria.md`](references/evaluation-criteria.md) — Detailed 5-axis rubric
- [`references/eval-driven-development.md`](references/eval-driven-development.md) — Eval-Driven Development (`pass@k`, `pass^k`, Code/Model/Human graders)
- [`templates/evaluation-report.md`](templates/evaluation-report.md) — Standard evaluation report template
