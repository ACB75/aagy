# Eval-Driven Development (EDD) & Grader Framework

Consolidates capability and regression evaluation (`pass@k` and `pass^k`) into the unified `agent-self-evaluation` workflow.

## 1. Eval Types

- **Capability Evals**: Verify that a new skill, hook, or code change solves a previously unmet capability (`pass@3 >= 0.90`).
- **Regression Evals**: Verify that existing tests, quality gates (`workspace_audit.py`, `sonar_audit.py`, `security_audit.py`), and hooks continue passing without degradation (`pass^3 = 1.00`).

## 2. Grader Types

1. **Code-Based Grader (Deterministic)**: `pytest`, `aagy workspace-audit`, `lint-markdown.ps1 -CheckOnly`, `self_improve.py --review`.
2. **Model-Based Grader (5-Axis Rubric)**: `skills/agent-self-evaluation/scripts/evaluate.py` or `self_improve.py --evaluate`.
3. **Human Grader (Mandatory Confirmation Gate)**: Required before promoting any candidate to `skills/`, `rules/`, or `scripts/` (`--confirm`).

## 3. Reliability Metrics

- **`pass@k`**: At least one success in $k$ attempts (capability discovery target: `pass@3 >= 90%`).
- **`pass^k`**: All $k$ consecutive trials succeed (release & safety gate target: `pass^3 = 100%`).
