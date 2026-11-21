# Hook Integration for Zero-Overhead Session-Stop Capture

The unified self-improvement engine wires a passive `Stop` hook in [`hooks.json`](../../hooks.json) that executes in $< 500\text{ ms}$ (timeout `5s`), consumes `0` prompt tokens, and isolates any runtime or permission error by returning `{}`:

```json
{
  "aagy-self-improve": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "python scripts/py/self_improve.py --capture-stop",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## Security & SRE Guarantees

1. **Zero Prompt Overhead**: Never echoes text into the conversation context or modifies `AGENTS.md` / `rules/` autonomously.
2. **Secret Redaction & AgentShield**: Scrubs `Bearer`, `API_KEY`, `password`, GitHub/AWS/Google keys (`[REDACTED]`) and rejects prompt-injection patterns before persisting to `<repo>/.agents/instincts/` or `$PLUGIN_DATA/instincts/`.
3. **Fault Isolation**: If stdin is empty, malformed JSON, or the filesystem is read-only, `--capture-stop` logs a debug note and exits `0` with `{}`.

## Standalone Evaluator & CLI Usage

```bash
# 5-axis rubric evaluator
python3 skills/agent-self-evaluation/scripts/evaluate.py --task task.txt --output response.txt

# Unified discovery and budget-gated promotion
python3 scripts/py/self_improve.py --discover --repo-root .
python3 scripts/py/self_improve.py --review <candidate-id> --repo-root .
python3 scripts/py/self_improve.py --promote <candidate-id> --confirm --repo-root .
```
