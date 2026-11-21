#!/usr/bin/env python3
"""
Motor Unificado de Autodescubrimiento, Autoevaluación y Automejora para aagy / aagy (stdlib pura).

Unifica auto-evolve, instinct_manager y agent-self-evaluation con:
  1. Captura Híbrida Zero-Overhead (RF-01): Hook Stop (< 500 ms, 0 tokens, {}) + CLI manual.
  2. Persistencia a Doble Nivel (RF-02): <repo>/.agents/instincts/ y $PLUGIN_DATA/instincts/.
  3. Detección, Deduplicación y Redacción de Secretos / AgentShield (RF-03).
  4. Promoción Controlada con 4 Compuertas (RF-04): AgentShield, Budget Gate, Smoke-Test y Confirmación.
  5. Desacoplamiento Agnóstico (RF-05): Operación sobre cualquier repositorio (--repo-root).
"""
from __future__ import annotations

import argparse
from collections import Counter
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
import datetime
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

_SCRIPT_DIR: str = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from instinct_manager import (
    DEFAULT_DOMAIN,
    ENV_AGY_PLUGIN_DATA,
    SCOPE_ALL,
    SCOPE_GLOBAL,
    SCOPE_PROJECT,
    VALID_SCOPES,
    Instinct,
    check_prompt_injection,
    list_instincts,
    redact_secrets,
    resolve_plugin_data_dir,
    sanitize_slug,
    save_instinct,
)
from security_audit import scan_agentshield_hooks, scan_agentshield_skills
from workspace_audit import (
    MAX_RULE_FILE_BYTES,
    MAX_SKILL_DESC,
    audit_rules,
    audit_skills,
)

logger: logging.Logger = logging.getLogger("self-improve")

TIER_SKILL: str = "skill"
TIER_SCRIPT: str = "script"
TIER_HOOK: str = "hook"
TIER_RULE: str = "rule"
TIER_AGENT: str = "agent"
VALID_TIERS: Tuple[str, ...] = (TIER_SKILL, TIER_SCRIPT, TIER_HOOK, TIER_RULE, TIER_AGENT)

STATUS_PROMOTED: str = "PROMOTED"
STATUS_PENDING_CONFIRMATION: str = "PENDING_CONFIRMATION"
STATUS_GATE_FAILED: str = "GATE_FAILED"
STATUS_NOT_FOUND: str = "NOT_FOUND"

DIR_AGENTS: str = ".agents"
DIR_INSTINCTS: str = "instincts"
OBSERVATIONS_FILENAME: str = "observations.jsonl"
PROPOSALS_SUBDIR: str = "proposals"
SKILL_MD_FILENAME: str = "SKILL.md"
DEFAULT_MIN_OCCURRENCES: int = 2
DEFAULT_LIMIT: int = 5

KEY_CANDIDATE_ID: str = "candidate_id"
KEY_TRIGGER: str = "trigger"
KEY_LEARNING: str = "learning"
KEY_DOMAIN: str = "domain"
KEY_SCOPE: str = "scope"
KEY_OCCURRENCES: str = "occurrences"
KEY_CONFIDENCE: str = "confidence"
KEY_SOURCES: str = "sources"


@dataclass(frozen=True)
class PromotionCandidate:
    candidate_id: str
    trigger: str
    learning: str
    domain: str
    scope: str
    occurrences: int
    confidence: float
    recommended_tier: str
    sources: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PromotionResult:
    candidate_id: str
    target_tier: str
    promoted: bool
    gate_passed: bool
    smoke_test_passed: bool
    status: str
    target_path: str
    proposal_path: str
    violations: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AxisEvaluation:
    name: str
    score: int
    evidence: Tuple[str, ...]
    improvement: str = ""


@dataclass(frozen=True)
class EvaluationReport:
    overall_score: float
    verdict: str
    axes: Tuple[AxisEvaluation, ...]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@contextmanager
def _plugin_data_env(plugin_data_dir: Optional[Path]) -> Iterator[None]:
    prev_env = os.environ.get(ENV_AGY_PLUGIN_DATA)
    if plugin_data_dir is not None:
        os.environ[ENV_AGY_PLUGIN_DATA] = str(plugin_data_dir)
    try:
        yield
    finally:
        if plugin_data_dir is not None:
            if prev_env is None:
                os.environ.pop(ENV_AGY_PLUGIN_DATA, None)
            else:
                os.environ[ENV_AGY_PLUGIN_DATA] = prev_env


def _observations_file(repo_root: Path, scope: str, plugin_data_dir: Optional[Path]) -> Path:
    if scope == SCOPE_GLOBAL:
        base = resolve_plugin_data_dir(plugin_data_dir) / DIR_INSTINCTS
    else:
        base = repo_root / DIR_AGENTS / DIR_INSTINCTS
    base.mkdir(parents=True, exist_ok=True)
    return base / OBSERVATIONS_FILENAME


def _fingerprint_pattern(trigger: str, learning: str) -> str:
    tokens = re.findall(r"[a-z0-9]{3,}", f"{trigger} {learning}".lower())
    core = " ".join(sorted(set(tokens))[:12])
    return hashlib.sha256(core.encode("utf-8")).hexdigest()[:10]


def record_observation(
    repo_root: Path,
    pattern_id: str,
    trigger: str,
    learning: str,
    domain: str = DEFAULT_DOMAIN,
    scope: str = SCOPE_PROJECT,
    plugin_data_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Registra una observación sanitizada en observations.jsonl."""
    combined = f"{trigger}\n{learning}"
    if check_prompt_injection(combined):
        logger.warning("[AGENTSHIELD] Observación rechazada por patrón de inyección: %s", pattern_id)
        return None

    clean_trigger, _ = redact_secrets(trigger.strip())
    clean_learning, _ = redact_secrets(learning.strip())
    clean_id = sanitize_slug(pattern_id)
    norm_scope = scope if scope in (SCOPE_PROJECT, SCOPE_GLOBAL) else SCOPE_PROJECT

    obs_path = _observations_file(repo_root, norm_scope, plugin_data_dir)
    entry: Dict[str, Any] = {
        "id": clean_id,
        "fingerprint": _fingerprint_pattern(clean_trigger, clean_learning),
        KEY_TRIGGER: clean_trigger,
        KEY_LEARNING: clean_learning,
        KEY_DOMAIN: domain,
        KEY_SCOPE: norm_scope,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    try:
        with obs_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        logger.debug("No se pudo escribir observación en %s: %s", obs_path, exc)
        return None

    return entry


def _ingest_single_learning(
    item: Dict[str, Any],
    repo_root: Path,
    plugin_data_dir: Optional[Path],
) -> None:
    lid = str(item.get("id") or item.get("pattern_id") or "session-learning")
    trig = str(item.get(KEY_TRIGGER) or "session stop observation")
    text = str(item.get(KEY_LEARNING) or "").strip()
    dom = str(item.get(KEY_DOMAIN) or DEFAULT_DOMAIN)
    scp = str(item.get(KEY_SCOPE) or SCOPE_PROJECT)
    if not text or check_prompt_injection(f"{trig}\n{text}"):
        return
    record_observation(repo_root, lid, trig, text, dom, scp, plugin_data_dir)
    save_instinct(repo_root, lid, trig, text, dom, 0.9, scp)


def _ingest_explicit_learnings(
    learnings: Any,
    repo_root: Path,
    plugin_data_dir: Optional[Path],
) -> None:
    if not isinstance(learnings, list):
        return
    with _plugin_data_env(plugin_data_dir):
        for item in learnings:
            if isinstance(item, dict):
                _ingest_single_learning(item, repo_root, plugin_data_dir)


def _ingest_repeated_items(
    items: Any,
    prefix: str,
    domain: str,
    repo_root: Path,
    plugin_data_dir: Optional[Path],
) -> None:
    if not isinstance(items, list):
        return
    normalized = [str(x).strip() for x in items if isinstance(x, str) and str(x).strip()]
    counts = Counter(normalized)
    for text, count in counts.items():
        if count < DEFAULT_MIN_OCCURRENCES:
            continue
        short_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]
        pat_id = f"{prefix}-{short_hash}"
        for _ in range(count):
            record_observation(
                repo_root=repo_root,
                pattern_id=pat_id,
                trigger=f"Repeated {prefix} ({count}x)",
                learning=f"Recurring pattern detected: {text}",
                domain=domain,
                scope=SCOPE_PROJECT,
                plugin_data_dir=plugin_data_dir,
            )


TRANSCRIPT_TAIL_BYTES: int = 2 * 1024 * 1024
TRANSCRIPT_TEXT_MAX: int = 200
SHELL_TOOL_NAMES: Tuple[str, ...] = ("Bash", "PowerShell", "run_command")


def _first_line(text: str) -> str:
    stripped = text.strip()
    return stripped.splitlines()[0][:TRANSCRIPT_TEXT_MAX] if stripped else ""


def _tool_result_text(block: Dict[str, Any]) -> str:
    content = block.get("content")
    if isinstance(content, list):
        content = " ".join(str(c.get("text") or "") for c in content if isinstance(c, dict))
    return _first_line(str(content or ""))


def _read_transcript_tail(transcript: Path) -> List[str]:
    with transcript.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        size = handle.tell()
        handle.seek(max(0, size - TRANSCRIPT_TAIL_BYTES))
        raw = handle.read().decode("utf-8", errors="replace")
    lines = raw.splitlines()
    return lines[1:] if size > TRANSCRIPT_TAIL_BYTES else lines


def _collect_from_block(block: Dict[str, Any], commands: List[str], errors: List[str]) -> None:
    kind = block.get("type")
    if kind == "tool_use" and block.get("name") in SHELL_TOOL_NAMES:
        tool_input = block.get("input")
        cmd = _first_line(str(tool_input.get("command") or "")) if isinstance(tool_input, dict) else ""
        if cmd:
            commands.append(cmd)
    elif kind == "tool_result" and block.get("is_error") is True:
        err = _tool_result_text(block)
        if err:
            errors.append(err)


def extract_transcript_signals(transcript_path: str) -> Tuple[List[str], List[str]]:
    """Extrae comandos de shell y errores de herramientas del transcript JSONL (Claude Code)."""
    commands: List[str] = []
    errors: List[str] = []
    path = Path(transcript_path).expanduser() if transcript_path else None
    if path is None or not path.is_file():
        return commands, errors
    for line in _read_transcript_tail(path):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = record.get("message") if isinstance(record, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    _collect_from_block(block, commands, errors)
    return commands, errors


def _payload_signals(data: Dict[str, Any]) -> Tuple[Any, Any]:
    commands = data.get("commands")
    errors = data.get("errors")
    if commands is None and errors is None:
        commands, errors = extract_transcript_signals(str(data.get("transcript_path") or ""))
    return commands, errors


def capture_stop_event(
    payload: Optional[Dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
    plugin_data_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Hook pasivo Stop (RF-01 / CA-01):
    Ejecución sub-segundo (< 500 ms), 0 tokens en prompt, aislamiento total de fallos (devuelve {}).
    """
    data = payload if isinstance(payload, dict) else {}
    cwd_str = str(data.get("cwd") or "").strip()
    target_root = repo_root or (Path(cwd_str) if cwd_str else Path.cwd())

    try:
        if not target_root.is_dir():
            return {}
        _ingest_explicit_learnings(data.get("learnings"), target_root, plugin_data_dir)
        commands, errors = _payload_signals(data)
        _ingest_repeated_items(commands, "cmd", "workflow", target_root, plugin_data_dir)
        _ingest_repeated_items(errors, "err", "debugging", target_root, plugin_data_dir)
    except Exception as exc:
        logger.debug("Aislamiento de fallo en hook Stop: %s", exc)

    return {}


def _parse_observation_file(obs_file: Path) -> List[Dict[str, Any]]:
    if not obs_file.is_file():
        return []
    try:
        lines = obs_file.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []

    records: List[Dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
            if isinstance(parsed, dict):
                records.append(parsed)
        except json.JSONDecodeError:
            continue
    return records


def _load_observations(repo_root: Path, scope: str, plugin_data_dir: Optional[Path]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    if scope in (SCOPE_PROJECT, SCOPE_ALL):
        records.extend(_parse_observation_file(repo_root / DIR_AGENTS / DIR_INSTINCTS / OBSERVATIONS_FILENAME))
    if scope in (SCOPE_GLOBAL, SCOPE_ALL):
        records.extend(
            _parse_observation_file(resolve_plugin_data_dir(plugin_data_dir) / DIR_INSTINCTS / OBSERVATIONS_FILENAME)
        )
    return records


def _recommend_tier(domain: str, learning: str) -> str:
    lowered = f"{domain} {learning}".lower()
    if "hook" in lowered or "pretooluse" in lowered or "posttooluse" in lowered:
        return TIER_HOOK
    if "script" in lowered or "cli" in lowered or "automat" in lowered:
        return TIER_SCRIPT
    return TIER_SKILL


def _merge_observations_into_buckets(
    observations: Sequence[Dict[str, Any]],
    grouped: Dict[str, Dict[str, Any]],
) -> None:
    for obs in observations:
        cid = sanitize_slug(str(obs.get("id") or "candidate"))
        bucket = grouped.setdefault(
            cid,
            {
                KEY_CANDIDATE_ID: cid,
                KEY_TRIGGER: str(obs.get(KEY_TRIGGER) or DEFAULT_DOMAIN),
                KEY_LEARNING: str(obs.get(KEY_LEARNING) or ""),
                KEY_DOMAIN: str(obs.get(KEY_DOMAIN) or DEFAULT_DOMAIN),
                KEY_SCOPE: str(obs.get(KEY_SCOPE) or SCOPE_PROJECT),
                KEY_OCCURRENCES: 0,
                KEY_CONFIDENCE: 0.75,
                KEY_SOURCES: set(),
            },
        )
        bucket[KEY_OCCURRENCES] += 1
        bucket[KEY_CONFIDENCE] = min(0.98, round(bucket[KEY_CONFIDENCE] + 0.05, 2))
        bucket[KEY_SOURCES].add(OBSERVATIONS_FILENAME)


def _merge_instincts_into_buckets(
    instincts: Sequence[Instinct],
    grouped: Dict[str, Dict[str, Any]],
) -> None:
    for inst in instincts:
        bucket = grouped.setdefault(
            inst.instinct_id,
            {
                KEY_CANDIDATE_ID: inst.instinct_id,
                KEY_TRIGGER: inst.trigger,
                KEY_LEARNING: inst.learning,
                KEY_DOMAIN: inst.domain,
                KEY_SCOPE: inst.scope,
                KEY_OCCURRENCES: 0,
                KEY_CONFIDENCE: inst.confidence,
                KEY_SOURCES: set(),
            },
        )
        bucket[KEY_OCCURRENCES] = max(bucket[KEY_OCCURRENCES], inst.occurrences)
        bucket[KEY_CONFIDENCE] = max(bucket[KEY_CONFIDENCE], inst.confidence)
        bucket[KEY_SOURCES].add(inst.file_path.name)


def discover_candidates(
    repo_root: Path,
    scope: str = SCOPE_ALL,
    min_occurrences: int = DEFAULT_MIN_OCCURRENCES,
    limit: int = DEFAULT_LIMIT,
    tier_filter: Optional[str] = None,
    plugin_data_dir: Optional[Path] = None,
) -> List[PromotionCandidate]:
    """Analiza observaciones e instintos, deduplicando patrones recurrentes (>= min_occurrences)."""
    grouped: Dict[str, Dict[str, Any]] = {}
    _merge_observations_into_buckets(_load_observations(repo_root, scope, plugin_data_dir), grouped)

    with _plugin_data_env(plugin_data_dir):
        instincts = list_instincts(repo_root, scope=scope)
    _merge_instincts_into_buckets(instincts, grouped)

    candidates: List[PromotionCandidate] = []
    for item in grouped.values():
        if item[KEY_OCCURRENCES] < min_occurrences:
            continue
        rec_tier = _recommend_tier(item[KEY_DOMAIN], item[KEY_LEARNING])
        if tier_filter and rec_tier != tier_filter:
            continue
        candidates.append(
            PromotionCandidate(
                candidate_id=item[KEY_CANDIDATE_ID],
                trigger=item[KEY_TRIGGER],
                learning=item[KEY_LEARNING],
                domain=item[KEY_DOMAIN],
                scope=item[KEY_SCOPE],
                occurrences=item[KEY_OCCURRENCES],
                confidence=item[KEY_CONFIDENCE],
                recommended_tier=rec_tier,
                sources=tuple(sorted(item[KEY_SOURCES])),
            )
        )

    candidates.sort(key=lambda c: (-c.occurrences, -c.confidence, c.candidate_id))
    return candidates[: max(1, limit)]


def _render_draft_artifact(
    candidate: PromotionCandidate,
    target_tier: str,
    custom_description: Optional[str] = None,
) -> str:
    if custom_description is not None:
        desc = custom_description
    else:
        raw_desc = f"Use when {candidate.trigger}. {candidate.learning}"
        desc = raw_desc[: MAX_SKILL_DESC - 3].rstrip() + "..." if len(raw_desc) > MAX_SKILL_DESC else raw_desc

    if target_tier == TIER_SKILL:
        return (
            f"---\n"
            f"name: {candidate.candidate_id}\n"
            f'description: "{desc}"\n'
            f"---\n\n"
            f"# {candidate.candidate_id}\n\n"
            f"## When to Activate\n\n"
            f"- Trigger: `{candidate.trigger}`\n"
            f"- Domain: `{candidate.domain}`\n\n"
            f"## Guidance\n\n"
            f"{candidate.learning}\n"
        )

    if target_tier == TIER_RULE:
        return (
            f"## Rule: {candidate.candidate_id} ({candidate.domain})\n\n"
            f"- **Trigger**: `{candidate.trigger}`\n"
            f"- **Directive**: {candidate.learning}\n"
        )

    if target_tier == TIER_HOOK:
        return json.dumps(
            {
                f"aagy-{candidate.candidate_id}": {
                    "Stop": [
                        {
                            "matcher": "*",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python scripts/py/self_improve.py --capture-stop",
                                    "timeout": 5,
                                }
                            ],
                        }
                    ]
                }
            },
            indent=2,
        )

    return (
        "#!/usr/bin/env python3\n"
        f'"""Auto-synthesized helper for {candidate.candidate_id}."""\n'
        "import sys\n\n"
        "def main() -> int:\n"
        "    return 0\n\n"
        'if __name__ == "__main__":\n'
        "    sys.exit(main())\n"
    )


def _smoke_test_rule_in_stage(repo_root: Path, stage_root: Path, draft_content: str) -> List[str]:
    r_dir = stage_root / "rules"
    r_dir.mkdir(parents=True, exist_ok=True)
    existing_rules_dir = repo_root / "rules"
    if existing_rules_dir.is_dir():
        for existing_rule in existing_rules_dir.glob("*.md"):
            (r_dir / existing_rule.name).write_text(
                existing_rule.read_text(encoding="utf-8", errors="replace"),
                encoding="utf-8",
            )
    target_rule = r_dir / "AGENTS.md"
    prior = target_rule.read_text(encoding="utf-8", errors="replace") if target_rule.is_file() else ""
    target_rule.write_text(prior + "\n" + draft_content, encoding="utf-8")
    _, _, rule_violations = audit_rules(stage_root, include_rules=True)
    if target_rule.stat().st_size > MAX_RULE_FILE_BYTES:
        rule_violations.append(f"Rule exceeds {MAX_RULE_FILE_BYTES} bytes limit")
    return rule_violations


def _validate_gates_and_smoketest(
    repo_root: Path,
    candidate: PromotionCandidate,
    target_tier: str,
    draft_content: str,
) -> Tuple[bool, bool, List[str]]:
    violations: List[str] = list(check_prompt_injection(draft_content))

    if target_tier == TIER_SKILL:
        sec_findings = scan_agentshield_skills(f"skills/{candidate.candidate_id}/SKILL.md", draft_content)
        violations.extend(f.message for f in sec_findings)
    elif target_tier == TIER_HOOK:
        hook_findings = scan_agentshield_hooks("hooks.json", draft_content)
        violations.extend(f.message for f in hook_findings)

    smoke_ok = False
    with tempfile.TemporaryDirectory() as tmp_str:
        stage_root = Path(tmp_str)
        if target_tier == TIER_SKILL:
            s_dir = stage_root / "skills" / candidate.candidate_id
            s_dir.mkdir(parents=True, exist_ok=True)
            (s_dir / SKILL_MD_FILENAME).write_text(draft_content, encoding="utf-8")
            _, _, skill_violations = audit_skills(stage_root / "skills")
            violations.extend(skill_violations)
            smoke_ok = len(skill_violations) == 0
        elif target_tier == TIER_RULE:
            rule_violations = _smoke_test_rule_in_stage(repo_root, stage_root, draft_content)
            violations.extend(rule_violations)
            smoke_ok = len(rule_violations) == 0
        elif target_tier == TIER_HOOK:
            smoke_ok = len(violations) == 0
        else:
            script_file = stage_root / f"{candidate.candidate_id}.py"
            script_file.write_text(draft_content, encoding="utf-8")
            try:
                compile(draft_content, str(script_file), "exec")
                smoke_ok = True
            except SyntaxError as exc:
                violations.append(f"Script syntax error: {exc}")

    gate_passed = len(violations) == 0 and smoke_ok
    return gate_passed, smoke_ok, violations


def _resolve_target_path(repo_root: Path, candidate_id: str, target_tier: str) -> Path:
    if target_tier == TIER_SKILL:
        return repo_root / "skills" / candidate_id / SKILL_MD_FILENAME
    if target_tier == TIER_RULE:
        return repo_root / "rules" / f"{candidate_id}.md"
    if target_tier == TIER_HOOK:
        return repo_root / DIR_AGENTS / DIR_INSTINCTS / PROPOSALS_SUBDIR / f"{candidate_id}.hooks.json"
    return repo_root / "scripts" / "py" / f"{candidate_id.replace('-', '_')}.py"


def promote_candidate(
    repo_root: Path,
    candidate_id: str,
    target_tier: Optional[str] = None,
    confirmed: bool = False,
    custom_description: Optional[str] = None,
    plugin_data_dir: Optional[Path] = None,
) -> PromotionResult:
    """
    Promoción controlada por 4 compuertas (RF-04 / CA-02 / CA-03):
      1. AgentShield & Secret Redaction
      2. Hard Gate de Presupuesto (workspace_audit.py)
      3. Smoke-Test automático
      4. Confirmación explícita del usuario (confirmed=True)
    """
    clean_id = sanitize_slug(candidate_id)
    candidates = discover_candidates(
        repo_root=repo_root,
        scope=SCOPE_ALL,
        min_occurrences=1,
        limit=100,
        plugin_data_dir=plugin_data_dir,
    )
    match = next((c for c in candidates if c.candidate_id == clean_id), None)
    if match is None:
        return PromotionResult(
            candidate_id=clean_id,
            target_tier=target_tier or TIER_SKILL,
            promoted=False,
            gate_passed=False,
            smoke_test_passed=False,
            status=STATUS_NOT_FOUND,
            target_path="",
            proposal_path="",
            violations=(f"Candidate '{clean_id}' not found.",),
        )

    chosen_tier = target_tier if target_tier in VALID_TIERS else match.recommended_tier
    draft = _render_draft_artifact(match, chosen_tier, custom_description=custom_description)

    proposals_dir = repo_root / DIR_AGENTS / DIR_INSTINCTS / PROPOSALS_SUBDIR
    proposals_dir.mkdir(parents=True, exist_ok=True)
    proposal_file = proposals_dir / f"{clean_id}.{chosen_tier}.draft.md"
    proposal_file.write_text(draft, encoding="utf-8")

    gate_passed, smoke_ok, violations = _validate_gates_and_smoketest(repo_root, match, chosen_tier, draft)
    target_path = _resolve_target_path(repo_root, clean_id, chosen_tier)

    if not gate_passed:
        return PromotionResult(
            candidate_id=clean_id,
            target_tier=chosen_tier,
            promoted=False,
            gate_passed=False,
            smoke_test_passed=smoke_ok,
            status=STATUS_GATE_FAILED,
            target_path=str(target_path),
            proposal_path=str(proposal_file),
            violations=tuple(violations),
        )

    if not confirmed:
        return PromotionResult(
            candidate_id=clean_id,
            target_tier=chosen_tier,
            promoted=False,
            gate_passed=True,
            smoke_test_passed=smoke_ok,
            status=STATUS_PENDING_CONFIRMATION,
            target_path=str(target_path),
            proposal_path=str(proposal_file),
            violations=(),
        )

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(draft, encoding="utf-8")
    return PromotionResult(
        candidate_id=clean_id,
        target_tier=chosen_tier,
        promoted=True,
        gate_passed=True,
        smoke_test_passed=smoke_ok,
        status=STATUS_PROMOTED,
        target_path=str(target_path),
        proposal_path=str(proposal_file),
        violations=(),
    )


def evaluate_agent_output(task: Optional[str], output: str) -> EvaluationReport:
    """Evalúa la respuesta del agente en los 5 ejes de agent-self-evaluation."""
    text = output.strip()
    words = len(text.split())

    acc_ev = ["+ Verified claims/tests"] if re.search(r"(?i)(passed|exit\s+code\s*0|verified)", text) else ["- No explicit test/exit code verification"]
    acc_ded = 1 if re.search(r"(?i)(should\s+work|probably|untested|TODO)", text) else 0
    acc_score = max(2, 5 - acc_ded - (0 if acc_ev[0].startswith("+") else 1))

    comp_ev = ["+ Edge cases/verification noted"] if re.search(r"(?i)(edge\s*case|error\s*handling|verified)", text) else ["- Minimal coverage evidence"]
    comp_score = 5 if comp_ev[0].startswith("+") else 4

    clar_ev = ["+ Structured markdown"] if re.search(r"(^#{1,3}\s+|```|^\s*[-*]\s+)", text, re.MULTILINE) else ["- Plain unstructured text"]
    clar_score = 5 if clar_ev[0].startswith("+") else 3

    act_ev = ["+ Actionable command or path"] if re.search(r"(?i)(run\s+|pwsh|python|pytest|PR\b)", text) else ["- No concrete next command"]
    act_score = 5 if act_ev[0].startswith("+") else 3

    task_words = len((task or "").split()) or 20
    conc_score = 3 if words > task_words * 25 else 5
    conc_ev = ["+ Concise information density"] if conc_score >= 4 else ["- Verbose relative to task"]

    axes = (
        AxisEvaluation("Accuracy", acc_score, tuple(acc_ev)),
        AxisEvaluation("Completeness", comp_score, tuple(comp_ev)),
        AxisEvaluation("Clarity", clar_score, tuple(clar_ev)),
        AxisEvaluation("Actionability", act_score, tuple(act_ev)),
        AxisEvaluation("Conciseness", conc_score, tuple(conc_ev)),
    )
    avg = round(sum(a.score for a in axes) / len(axes), 2)
    verdict = "Deliver as-is." if avg >= 4.0 else "Address weak axes before delivery."
    return EvaluationReport(overall_score=avg, verdict=verdict, axes=axes)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Motor Unificado de Autodescubrimiento y Automejora (aagy / aagy)."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Raíz del repositorio objetivo.")
    parser.add_argument("--plugin-data", type=Path, default=None, help="Ruta a PLUGIN_DATA global.")
    parser.add_argument("--discover", action="store_true", help="Descubre y deduplica patrones candidatos.")
    parser.add_argument("--review", type=str, default=None, help="Revisa un candidato y valida gates sin promover.")
    parser.add_argument("--promote", type=str, default=None, help="Promueve un candidato tras superar gates.")
    parser.add_argument("--confirm", action="store_true", help="Confirma explícitamente la escritura del artefacto.")
    parser.add_argument("--capture-stop", action="store_true", help="Modo pasivo para hook Stop (stdin JSON -> {}).")
    parser.add_argument("--evaluate", type=str, default=None, help="Evalúa un texto de salida en los 5 ejes.")
    parser.add_argument("--task", type=str, default=None, help="Descripción de tarea para --evaluate.")
    parser.add_argument("--scope", choices=list(VALID_SCOPES), default=SCOPE_ALL, help="Ámbito: project, global, all.")
    parser.add_argument("--tier", choices=list(VALID_TIERS), default=None, help="Filtra o fuerza el tier de artefacto.")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Máximo de candidatos a listar.")
    parser.add_argument("--min-occurrences", type=int, default=DEFAULT_MIN_OCCURRENCES, help="Ocurrencias mínimas.")
    parser.add_argument("--dry-run", action="store_true", help="Modo simulación sin escritura final.")
    parser.add_argument("--write", action="store_true", help="Alias legacy; requiere --confirm para escribir.")
    parser.add_argument("--json", action="store_true", help="Produce salida en formato JSON.")
    return parser.parse_args(argv)


def _read_stdin_nonblocking(timeout_sec: float = 0.05) -> str:
    if sys.stdin is None or sys.stdin.isatty():
        return ""
    if isinstance(sys.stdin, io.TextIOBase) and not hasattr(sys.stdin, "fileno"):
        return sys.stdin.read()

    buf: List[str] = []

    def _reader() -> None:
        try:
            buf.append(sys.stdin.read())
        except Exception as exc:
            logger.debug("Lectura stdin interrumpida: %s", exc)

    worker = threading.Thread(target=_reader, daemon=True)
    worker.start()
    worker.join(timeout=timeout_sec)
    return buf[0] if buf else ""


def _handle_capture_stop_cli(repo_root: Path, plugin_data: Optional[Path]) -> int:
    payload: Dict[str, Any] = {}
    try:
        raw = _read_stdin_nonblocking()
        if raw and raw.strip():
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                payload = parsed
    except Exception as exc:
        logger.debug("Stdin no JSON en --capture-stop: %s", exc)

    res = capture_stop_event(payload=payload, repo_root=repo_root, plugin_data_dir=plugin_data)
    print(json.dumps(res))
    return 0


def _run_promote_or_review_cli(args: argparse.Namespace, repo_root: Path, target_id: str) -> int:
    is_confirmed = bool(args.confirm and args.promote and not args.dry_run)
    result = promote_candidate(
        repo_root=repo_root,
        candidate_id=target_id,
        target_tier=args.tier,
        confirmed=is_confirmed,
        plugin_data_dir=args.plugin_data,
    )
    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.gate_passed else 1

    logger.info("[%s] Candidato '%s' (%s) -> %s", result.status, result.candidate_id, result.target_tier, result.target_path)
    for violation in result.violations:
        logger.warning("  [GATE] %s", violation)
    return 0 if result.gate_passed else 1


def _run_discover_cli(args: argparse.Namespace, repo_root: Path) -> int:
    candidates = discover_candidates(
        repo_root=repo_root,
        scope=args.scope,
        min_occurrences=args.min_occurrences,
        limit=args.limit,
        tier_filter=args.tier,
        plugin_data_dir=args.plugin_data,
    )
    if args.json:
        print(json.dumps({"candidates": [c.to_dict() for c in candidates]}, indent=2))
        return 0

    logger.info("=== CANDIDATOS DE AUTOMEJORA DETECTADOS (%d) ===", len(candidates))
    for cand in candidates:
        logger.info(
            "  • [%s/%s] %s (%dx, conf=%.2f -> %s): %s",
            cand.scope,
            cand.domain,
            cand.candidate_id,
            cand.occurrences,
            cand.confidence,
            cand.recommended_tier,
            cand.trigger,
        )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)
    repo_root = args.repo_root.resolve()

    if args.capture_stop:
        return _handle_capture_stop_cli(repo_root, args.plugin_data)

    if args.evaluate is not None:
        report = evaluate_agent_output(args.task, args.evaluate)
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            logger.info("Overall Self-Evaluation Score: %.2f/5 — %s", report.overall_score, report.verdict)
        return 0

    target_id = args.promote or args.review
    if target_id:
        return _run_promote_or_review_cli(args, repo_root, target_id)

    return _run_discover_cli(args, repo_root)


if __name__ == "__main__":
    sys.exit(main())
