#!/usr/bin/env python3
"""
Security & Secrets Static Auditor (NIST SP 800-63-4, OWASP Top 10).

Audita archivos de código y configuración en busca de:
  1. Secretos y credenciales expuestas (GitHub tokens, AWS keys, JWTs, private keys).
  2. Patrones de inyección de comandos shell (shell=True con interpolación, os.system).
  3. Comprobaciones de seguridad operativa.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("security-audit")

SEVERITY_HIGH: str = "HIGH"
RULE_INJECTION_SHELL: str = "SEC-INJECTION-SHELL"
RULE_AGENTSHIELD_HOOK_CMD: str = "SEC-AGENTSHIELD-HOOK-CMD"
RULE_AGENTSHIELD_HOOK_TIMEOUT: str = "SEC-AGENTSHIELD-HOOK-TIMEOUT"
RULE_AGENTSHIELD_HOOK_SYNTAX: str = "SEC-AGENTSHIELD-HOOK-SYNTAX"
RULE_AGENTSHIELD_INJECTION: str = "SEC-AGENTSHIELD-INJECTION"
RULE_AGENTSHIELD_MCP_SECRET: str = "SEC-AGENTSHIELD-MCP-SECRET"

EXCLUDED_DIRS = {
    ".git", ".gemini", ".antigravity", ".vscode", "node_modules",
    "target", "dist", ".angular", "bin", "obj", "__pycache__",
    ".pytest_cache", ".venv", "venv", "scratch", "brain", "aagy-ecc", "aagy",
}

SECRET_PATTERNS = [
    ("GitHub Token", re.compile(r"\b(ghp_[A-Za-z0-9_]{36,}|github_pat_[A-Za-z0-9_]{60,})\b")),
    ("AWS Access Key", re.compile(r"\b(AKIA[0-9A-Z]{16})\b")),
    ("Private Key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Hardcoded Password", re.compile(r"""(?:password|passwd|pwd|secret)\s*[:=]\s*['"][^'"\s]{8,}['"]""", re.IGNORECASE)),
]

INJECTION_PATTERNS = [
    ("Subprocess Shell Injection", re.compile(r"""subprocess\.(?:run|Popen|call|check_output)\s*\([^)]*shell\s*=\s*True""")),
    ("os.system Usage", re.compile(r"""\bos\.system\s*\(""")),
]


@dataclass(frozen=True)
class SecurityFinding:
    rule_id: str
    severity: str  # HIGH, MEDIUM, LOW
    file_path: str
    line: int
    message: str


def iter_scannable_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDED_DIRS]
        for fname in filenames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in {".py", ".ts", ".js", ".json", ".yml", ".yaml", ".env", ".ps1", ".sh", ".md"}:
                p = Path(dirpath) / fname
                yield p


def scan_secrets_in_content(file_path: str, content: str) -> List[SecurityFinding]:
    findings: List[SecurityFinding] = []
    # Ignorar archivos de tests explícitos y archivos de documentación/prompts Markdown
    if "test_" in file_path or "_test" in file_path or file_path.endswith(".md"):
        return findings

    lines = content.splitlines()
    for line_idx, line in enumerate(lines, 1):
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(line):
                # Descartar si es un placeholder como <YOUR_KEY> o process.env
                if "process.env" in line or "os.environ" in line or "example" in line.lower():
                    continue
                findings.append(
                    SecurityFinding(
                        rule_id=f"SEC-SECRET-{name.replace(' ', '-')}",
                        severity="HIGH",
                        file_path=file_path,
                        line=line_idx,
                        message=f"Possible hardcoded credential detected: {name}",
                    )
                )
    return findings


def scan_command_injections(file_path: str, content: str) -> List[SecurityFinding]:
    findings: List[SecurityFinding] = []
    if "test_" in file_path or "_test" in file_path:
        return findings

    lines = content.splitlines()
    for line_idx, line in enumerate(lines, 1):
        for name, pattern in INJECTION_PATTERNS:
            if pattern.search(line):
                findings.append(
                    SecurityFinding(
                        rule_id="SEC-INJECTION-SHELL",
                        severity="HIGH",
                        file_path=file_path,
                        line=line_idx,
                        message=f"Unsafe shell execution pattern detected: {name}",
                    )
                )
    return findings


DANGEROUS_HOOK_PATTERNS = re.compile(r"""(\beval\b|\|\s*(bash|sh)|rm\s+-rf\s+/)""", re.IGNORECASE)
PROMPT_INJECTION_PATTERN = re.compile(
    r"""(ignore\s+previous\s+instructions|bypass\s+access\s+control|exfiltrate\s+(?:database|credentials|keys|tokens)|disable\s+safety\s+(?:guard|check))""",
    re.IGNORECASE,
)


def _inspect_hook_handlers(file_path: str, handlers: Any) -> List[SecurityFinding]:
    findings: List[SecurityFinding] = []
    if not isinstance(handlers, list):
        return findings
    for handler in handlers:
        if not isinstance(handler, dict):
            continue
        timeout = handler.get("timeout")
        if isinstance(timeout, (int, float)) and timeout > 30:
            findings.append(SecurityFinding(
                rule_id=RULE_AGENTSHIELD_HOOK_TIMEOUT,
                severity=SEVERITY_HIGH,
                file_path=file_path,
                line=1,
                message=f"Excessive hook timeout ({timeout}s > 30s max)",
            ))
        cmd = handler.get("command", "")
        if isinstance(cmd, str) and DANGEROUS_HOOK_PATTERNS.search(cmd):
            findings.append(SecurityFinding(
                rule_id=RULE_AGENTSHIELD_HOOK_CMD,
                severity=SEVERITY_HIGH,
                file_path=file_path,
                line=1,
                message=f"Potentially dangerous command in hook: {cmd}",
            ))
    return findings


HOOK_EVENTS: Tuple[str, ...] = ("PreToolUse", "PostToolUse", "SessionStart", "Stop", "PreInvocation", "PostInvocation")


def _extract_hook_sub_handlers(hook_cfg: Dict[str, Any]) -> List[Any]:
    handlers: List[Any] = []
    for ev in HOOK_EVENTS:
        ev_items = hook_cfg.get(ev)
        if not isinstance(ev_items, list):
            continue
        for item in ev_items:
            if isinstance(item, dict):
                handlers.extend(item.get("hooks", [item]))
    return handlers


def scan_agentshield_hooks(file_path: str, content: str) -> List[SecurityFinding]:
    if not file_path.endswith("hooks.json"):
        return []

    try:
        data = json.loads(content)
    except (json.JSONDecodeError, OSError) as exc:
        return [SecurityFinding(
            rule_id=RULE_AGENTSHIELD_HOOK_SYNTAX,
            severity=SEVERITY_HIGH,
            file_path=file_path,
            line=1,
            message=f"Invalid JSON syntax in hooks.json: {exc}",
        )]

    if not isinstance(data, dict):
        return []

    findings: List[SecurityFinding] = []
    for hook_cfg in data.values():
        if isinstance(hook_cfg, dict):
            sub_hooks = _extract_hook_sub_handlers(hook_cfg)
            findings.extend(_inspect_hook_handlers(file_path, sub_hooks))

    return findings


def scan_agentshield_skills(file_path: str, content: str) -> List[SecurityFinding]:
    norm = file_path.replace("\\", "/")
    if "skills/" not in norm and not norm.endswith("SKILL.md"):
        return []
    if "test_" in file_path or "_test" in file_path:
        return []

    findings: List[SecurityFinding] = []
    for idx, line in enumerate(content.splitlines(), 1):
        if re.search(r"""(never\s+follow|flag\s+it|prevent|reject|detect|e\.g\.)""", line, re.IGNORECASE):
            continue
        match = PROMPT_INJECTION_PATTERN.search(line)
        if match:
            findings.append(SecurityFinding(
                rule_id=RULE_AGENTSHIELD_INJECTION,
                severity=SEVERITY_HIGH,
                file_path=file_path,
                line=idx,
                message=f"Potential prompt injection pattern detected: '{match.group(0)}'",
            ))
    return findings


def _inspect_env_value(file_path: str, s_name: str, k: str, v: str) -> Optional[SecurityFinding]:
    if v.startswith("${"):
        return None
    is_suspicious = len(v) >= 16 or bool(re.search(r"(key|secret|token|password)", k, re.IGNORECASE))
    if is_suspicious and not re.search(r"(example|placeholder|dummy|<YOUR_)", v, re.IGNORECASE):
        return SecurityFinding(
            rule_id=RULE_AGENTSHIELD_MCP_SECRET,
            severity=SEVERITY_HIGH,
            file_path=file_path,
            line=1,
            message=f"Plaintext secret in MCP server '{s_name}' env key '{k}'",
        )
    return None


def _check_server_env(file_path: str, s_name: str, env_dict: Any) -> List[SecurityFinding]:
    if not isinstance(env_dict, dict):
        return []
    findings: List[SecurityFinding] = []
    for k, v in env_dict.items():
        if isinstance(v, str):
            res = _inspect_env_value(file_path, s_name, k, v)
            if res:
                findings.append(res)
    return findings


def scan_agentshield_mcp(file_path: str, content: str) -> List[SecurityFinding]:
    if not file_path.endswith("mcp_config.json"):
        return []
    if "test_" in file_path or "_test" in file_path:
        return []

    try:
        data = json.loads(content)
    except (json.JSONDecodeError, OSError):
        return []

    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict):
        return []

    findings: List[SecurityFinding] = []
    for s_name, s_cfg in servers.items():
        if isinstance(s_cfg, dict):
            findings.extend(_check_server_env(file_path, s_name, s_cfg.get("env")))
    return findings


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Static Security & Secrets Auditor.")
    parser.add_argument("--root", type=Path, default=None, help="Directorio raíz a escanear.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve() if args.root else Path(__file__).resolve().parent.parent.parent

    logger.info("Iniciando escaneo de seguridad en: %s", root)
    findings: List[SecurityFinding] = []

    for path in iter_scannable_files(root):
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        file_str = str(path)
        findings.extend(scan_secrets_in_content(file_str, content))
        findings.extend(scan_command_injections(file_str, content))
        findings.extend(scan_agentshield_hooks(file_str, content))
        findings.extend(scan_agentshield_skills(file_str, content))
        findings.extend(scan_agentshield_mcp(file_str, content))

    if not findings:
        logger.info("[PASS] Escaneo de seguridad finalizado sin vulnerabilidades detectadas.")
        return 0

    logger.warning("\n[FAIL] Se detectaron %d problemas de seguridad:", len(findings))
    for f in findings:
        logger.warning("  [%s][%s] %s:%d - %s", f.severity, f.rule_id, f.file_path, f.line, f.message)
    return 1


if __name__ == "__main__":
    sys.exit(main())
