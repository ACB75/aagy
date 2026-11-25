---
name: research-ops
description: "Evidence-first current-state research workflow for AAGY."
metadata:
  origin: AAGY
---

# Research Ops

Use this when the user asks to research something current, compare options, enrich people or companies, or turn repeated lookups into a monitored workflow.

## Uso

Se carga sola cuando la tarea encaja con su `description`, o al pedirla por su nombre: `research-ops`.

This is the operator wrapper around the repo's research stack. It coordinates native web search, local docs lookup, and durable knowledge capture without requiring paid search skills.

## Skill Stack

Pull these AAGY-native skills into the workflow when relevant:

- `documentation-lookup` for official API/framework documentation
- `search-first` to check existing local code, docs, and packages before external lookups
- `knowledge-ops` when the result should be stored in durable context afterward

## When to Use

- user says "research", "look up", "compare", "who should I talk to", or "what's the latest"
- the answer depends on current public information
- the user already supplied evidence and wants it factored into a fresh recommendation
- the task may be recurring enough that it should become a monitor instead of a one-off lookup

## Guardrails

- do not answer current questions from stale memory when fresh search is cheap
- separate:
  - sourced fact
  - user-provided evidence
  - inference
  - recommendation
- do not spin up a heavyweight research pass if the answer is already in local code or docs

## Workflow

### 1. Start from what the user already gave you

Normalize any supplied material into:

- already-evidenced facts
- needs verification
- open questions

Do not restart the analysis from zero if the user already built part of the model.

### 2. Classify the ask

Choose the right lane before searching:

- quick factual answer
- comparison or decision memo
- lead/enrichment pass
- recurring monitoring candidate

### 3. Take the lightest useful evidence path first

- check local code and docs first (`search-first`)
- use native web search or `documentation-lookup` for fast current-web discovery
- synthesize across multiple primary sources with explicit citations and dates when accuracy matters
- persist durable findings with `knowledge-ops` when the result will be reused

### 4. Report with explicit evidence boundaries

For important claims, say whether they are:

- sourced facts
- user-supplied context
- inference
- recommendation

Freshness-sensitive answers should include concrete dates.

### 5. Decide whether the task should stay manual

If the user is likely to ask the same research question repeatedly, say so explicitly and recommend a monitoring or workflow layer instead of repeating the same manual search forever.

## Output Format

```text
QUESTION TYPE
- factual / comparison / enrichment / monitoring

EVIDENCE
- sourced facts
- user-provided context

INFERENCE
- what follows from the evidence

RECOMMENDATION
- answer or next move
- whether this should become a monitor
```

## Pitfalls

- do not mix inference into sourced facts without labeling it
- do not ignore user-provided evidence
- do not use a heavy research lane for a question local repo context can answer
- do not give freshness-sensitive answers without dates

## Verification

- important claims are labeled by evidence type
- freshness-sensitive outputs include dates
- the final recommendation matches the actual research mode used

## Paridad

Claude Code: el mismo skill `research-ops` en el paquete `aagy-ecc-extras`, espejado desde la raíz por `sync_aagy_ecc.py`.
