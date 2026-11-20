#!/usr/bin/env python3
"""
Gestor de Instintos y Aprendizajes a Doble Nivel (Proyecto + PLUGIN_DATA) para aagy / aagy (stdlib pura).

Permite capturar, sanitizar (AgentShield + redacción de secretos), almacenar y exportar
instintos en <repo>/.agents/instincts/*.md (nivel proyecto) y $PLUGIN_DATA/instincts/*.md
(nivel global plugin) desacoplados del prompt principal para no inflar AGENTS.md.
"""
from __future__ import annotations

import argparse
import datetime
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

_SCRIPT_DIR: str = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from security_audit import PROMPT_INJECTION_PATTERN

logger: logging.Logger = logging.getLogger("instinct-manager")

INSTINCTS_SUBDIR: str = ".agents/instincts"
DEFAULT_DOMAIN: str = "general"
SCOPE_PROJECT: str = "project"
SCOPE_GLOBAL: str = "global"
SCOPE_ALL: str = "all"
VALID_SCOPES: Tuple[str, ...] = (SCOPE_PROJECT, SCOPE_GLOBAL, SCOPE_ALL)

ENV_AGY_PLUGIN_DATA: str = "AGY_PLUGIN_DATA"
ENV_CLAUDE_PLUGIN_DATA: str = "CLAUDE_PLUGIN_DATA"
REDACTED_TOKEN: str = "[REDACTED]"
ARG_SCOPE: str = "--scope"
HELP_ROOT: str = "Raíz del repositorio."
HELP_SCOPE: str = "Ámbito de instintos: project, global o all."

FRONTMATTER_REGEX: re.Pattern[str] = re.compile(
    r"^---\s*\r?\n(.*?)\r?\n---\s*\r?\n?(.*)$",
    re.DOTALL,
)

SECRET_REDACTION_PATTERNS: Tuple[Tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\b(Bearer)\s+[A-Za-z0-9\-._~+/]+=*", re.IGNORECASE),
        f"\\1 {REDACTED_TOKEN}",
    ),
    (
        re.compile(r"\b(ghp_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
        REDACTED_TOKEN,
    ),
    (
        re.compile(r"\b(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z\-_]{20,}|sk-[A-Za-z0-9\-_]{20,})\b"),
        REDACTED_TOKEN,
    ),
    (
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
            re.DOTALL,
        ),
        REDACTED_TOKEN,
    ),
    (
        re.compile(
            r"""(\b(?:api[_-]?key|secret[_-]?key|access[_-]?token|auth[_-]?token|password|passwd|pwd|secret)\s*[:=]\s*)(['"]?)[^'"\s,;]{6,}\2""",
            re.IGNORECASE,
        ),
        f"\\1{REDACTED_TOKEN}",
    ),
)

EXTRA_INJECTION_REGEX: re.Pattern[str] = re.compile(
    r"(override\s+system\s+prompt|disregard\s+all\s+prior|rm\s+-rf\s+/|curl\s+[^|\n]+\|\s*(?:bash|sh))",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Instinct:
    instinct_id: str
    trigger: str
    learning: str
    domain: str
    confidence: float
    file_path: Path
    scope: str = SCOPE_PROJECT
    occurrences: int = 1


def resolve_plugin_data_dir(plugin_data_dir: Optional[Path] = None) -> Path:
    """Resuelve el directorio global PLUGIN_DATA para instintos transversales de aagy/aagy."""
    if plugin_data_dir is not None:
        return plugin_data_dir.resolve()

    for env_key in (ENV_AGY_PLUGIN_DATA, ENV_CLAUDE_PLUGIN_DATA):
        env_val = os.environ.get(env_key, "").strip()
        if env_val:
            return Path(env_val).expanduser().resolve()

    return (Path.home() / ".gemini" / "config" / "plugins" / "aagy" / ".data").resolve()


def redact_secrets(text: str) -> Tuple[str, int]:
    """Filtra credenciales, tokens Bearer, API keys y passwords antes de persistir."""
    sanitized = text
    redactions = 0
    for pattern, replacement in SECRET_REDACTION_PATTERNS:
        sanitized, count = pattern.subn(replacement, sanitized)
        redactions += count
    return sanitized, redactions


def check_prompt_injection(text: str) -> List[str]:
    """Valida que un texto no contenga vectores de prompt injection o comandos destructivos."""
    findings: List[str] = []
    for match in PROMPT_INJECTION_PATTERN.finditer(text):
        findings.append(f"AgentShield prompt-injection pattern detected: '{match.group(0)}'")
    for match in EXTRA_INJECTION_REGEX.finditer(text):
        findings.append(f"AgentShield unsafe directive detected: '{match.group(0)}'")
    return findings


def sanitize_slug(raw_id: str) -> str:
    """Normaliza un identificador de instinto en formato slug seguro."""
    cleaned = re.sub(r"[^a-zA-Z0-9_\-]", "_", raw_id).strip("_").lower()
    return cleaned or "instinct"


def _resolve_storage_dir(repo_root: Path, scope: str) -> Path:
    if scope == SCOPE_GLOBAL:
        return resolve_plugin_data_dir() / "instincts"
    return repo_root / ".agents" / "instincts"


def _parse_frontmatter_field(fm: str, key: str) -> Optional[str]:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", fm, re.MULTILINE)
    if not match:
        return None
    return match.group(1).strip().strip("'\"")


def _read_existing_occurrences(target_file: Path) -> int:
    if not target_file.is_file():
        return 0
    try:
        raw = target_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    match = FRONTMATTER_REGEX.match(raw)
    if not match:
        return 1
    occ_str = _parse_frontmatter_field(match.group(1), "occurrences")
    try:
        return max(1, int(occ_str)) if occ_str else 1
    except ValueError:
        return 1


def save_instinct(
    repo_root: Path,
    instinct_id: str,
    trigger: str,
    learning: str,
    domain: str = DEFAULT_DOMAIN,
    confidence: float = 0.9,
    scope: str = SCOPE_PROJECT,
) -> Instinct:
    """Guarda o actualiza un instinto sanitizado en nivel proyecto (.agents/instincts) o global (PLUGIN_DATA)."""
    normalized_scope = scope if scope in (SCOPE_PROJECT, SCOPE_GLOBAL) else SCOPE_PROJECT
    combined_text = f"{trigger}\n{learning}"
    injection_issues = check_prompt_injection(combined_text)
    if injection_issues:
        raise ValueError("; ".join(injection_issues))

    clean_trigger, _ = redact_secrets(trigger.strip())
    clean_learning, _ = redact_secrets(learning.strip())
    clean_id = sanitize_slug(instinct_id)

    instincts_dir = _resolve_storage_dir(repo_root, normalized_scope)
    instincts_dir.mkdir(parents=True, exist_ok=True)

    target_file = instincts_dir / f"{clean_id}.md"
    occurrences = _read_existing_occurrences(target_file) + 1
    today = datetime.date.today().isoformat()
    bounded_conf = round(min(1.0, max(0.1, float(confidence))), 2)

    content = f"""---
id: "{clean_id}"
trigger: "{clean_trigger}"
domain: "{domain}"
scope: "{normalized_scope}"
confidence: {bounded_conf}
occurrences: {occurrences}
created_at: "{today}"
---

# Instinto: {clean_id}

> **Disparador Operativo**: `{clean_trigger}` | **Dominio**: `{domain}` | **Ámbito**: `{normalized_scope}`

{clean_learning}
"""
    target_file.write_text(content, encoding="utf-8")
    logger.info("[OK] Instinto guardado (%s) en: %s", normalized_scope, target_file)

    return Instinct(
        instinct_id=clean_id,
        trigger=clean_trigger,
        learning=clean_learning,
        domain=domain,
        confidence=bounded_conf,
        file_path=target_file,
        scope=normalized_scope,
        occurrences=occurrences,
    )


def _load_instincts_from_dir(instincts_dir: Path, default_scope: str) -> List[Instinct]:
    if not instincts_dir.is_dir():
        return []

    loaded: List[Instinct] = []
    for file_path in sorted(instincts_dir.glob("*.md")):
        if file_path.name == "README.md":
            continue
        inst = _parse_instinct_file(file_path, default_scope)
        if inst is not None:
            loaded.append(inst)
    return loaded


def _parse_instinct_file(file_path: Path, default_scope: str) -> Optional[Instinct]:
    try:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None

    match = FRONTMATTER_REGEX.match(raw)
    if not match:
        return None

    fm, body = match.group(1), match.group(2)
    inst_id = _parse_frontmatter_field(fm, "id") or file_path.stem
    trigger = _parse_frontmatter_field(fm, "trigger") or DEFAULT_DOMAIN
    domain = _parse_frontmatter_field(fm, "domain") or DEFAULT_DOMAIN
    scope = _parse_frontmatter_field(fm, "scope") or default_scope
    conf_str = _parse_frontmatter_field(fm, "confidence") or "0.9"
    occ_str = _parse_frontmatter_field(fm, "occurrences") or "1"

    try:
        confidence = float(conf_str)
    except ValueError:
        confidence = 0.9
    try:
        occurrences = max(1, int(occ_str))
    except ValueError:
        occurrences = 1

    return Instinct(
        instinct_id=inst_id,
        trigger=trigger,
        learning=body.strip(),
        domain=domain,
        confidence=confidence,
        file_path=file_path,
        scope=scope,
        occurrences=occurrences,
    )


def list_instincts(repo_root: Path, scope: str = SCOPE_PROJECT) -> List[Instinct]:
    """Lista los instintos registrados según el ámbito ('project', 'global' o 'all')."""
    normalized_scope = scope if scope in VALID_SCOPES else SCOPE_PROJECT
    results: List[Instinct] = []

    if normalized_scope in (SCOPE_PROJECT, SCOPE_ALL):
        results.extend(_load_instincts_from_dir(_resolve_storage_dir(repo_root, SCOPE_PROJECT), SCOPE_PROJECT))

    if normalized_scope in (SCOPE_GLOBAL, SCOPE_ALL):
        global_dir = _resolve_storage_dir(repo_root, SCOPE_GLOBAL)
        seen_ids = {i.instinct_id for i in results}
        for g_inst in _load_instincts_from_dir(global_dir, SCOPE_GLOBAL):
            if g_inst.instinct_id not in seen_ids:
                results.append(g_inst)

    return results


def export_instincts(repo_root: Path, scope: str = SCOPE_PROJECT) -> str:
    """Genera un resumen en Markdown de los instintos activos para el ámbito solicitado."""
    instincts = list_instincts(repo_root, scope=scope)
    if not instincts:
        return "No hay instintos registrados en este proyecto."

    lines = [
        "# Catálogo de Instintos del Proyecto",
        "",
        "| ID | Disparador | Dominio | Ámbito | Confianza | Archivo |",
        "| :--- | :--- | :---: | :---: | :---: | :--- |",
    ]
    for inst in instincts:
        lines.append(
            f"| `{inst.instinct_id}` | {inst.trigger} | {inst.domain} | {inst.scope} | {inst.confidence:.2f} | `{inst.file_path.name}` |"
        )

    lines.append("\n## Directivas Detalladas\n")
    for inst in instincts:
        lines.append(f"### `{inst.instinct_id}` ({inst.domain} / {inst.scope})")
        lines.append(f"- **Trigger**: {inst.trigger}")
        lines.append(f"- **Aprendizaje**: {inst.learning}\n")

    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gestor de Instintos a Doble Nivel (.agents/instincts/ + PLUGIN_DATA).")
    subparsers = parser.add_subparsers(dest="subcommand", help="Comandos disponibles")

    p_save = subparsers.add_parser("save", help="Guarda un nuevo instinto.")
    p_save.add_argument("--id", required=True, help="ID o slug del instinto.")
    p_save.add_argument("--trigger", required=True, help="Palabra clave o disparador.")
    p_save.add_argument("--learning", required=True, help="Texto del aprendizaje o directriz.")
    p_save.add_argument("--domain", default=DEFAULT_DOMAIN, help="Dominio (database, backend, frontend, sre).")
    p_save.add_argument("--confidence", type=float, default=0.9, help="Nivel de confianza (0.0 a 1.0).")
    p_save.add_argument(ARG_SCOPE, choices=list(VALID_SCOPES[:2]), default=SCOPE_PROJECT, help=HELP_SCOPE)
    p_save.add_argument("--root", type=Path, default=None, help=HELP_ROOT)

    p_list = subparsers.add_parser("list", help="Lista los instintos existentes.")
    p_list.add_argument(ARG_SCOPE, choices=list(VALID_SCOPES), default=SCOPE_PROJECT, help=HELP_SCOPE)
    p_list.add_argument("--root", type=Path, default=None, help=HELP_ROOT)

    p_exp = subparsers.add_parser("export", help="Exporta instintos en formato Markdown.")
    p_exp.add_argument(ARG_SCOPE, choices=list(VALID_SCOPES), default=SCOPE_PROJECT, help=HELP_SCOPE)
    p_exp.add_argument("--root", type=Path, default=None, help=HELP_ROOT)

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)

    root = getattr(args, "root", None)
    repo_root = root.resolve() if root else Path(__file__).resolve().parent.parent.parent
    scope = getattr(args, "scope", SCOPE_PROJECT)

    if args.subcommand == "save":
        save_instinct(
            repo_root=repo_root,
            instinct_id=args.id,
            trigger=args.trigger,
            learning=args.learning,
            domain=args.domain,
            confidence=args.confidence,
            scope=scope,
        )
        return 0

    if args.subcommand == "list" or not args.subcommand:
        instincts = list_instincts(repo_root, scope=scope)
        logger.info("=== INSTINTOS REGISTRADOS (%d) ===", len(instincts))
        for inst in instincts:
            logger.info("  • [%s/%s] %s: %s", inst.scope, inst.domain, inst.instinct_id, inst.trigger)
        return 0

    if args.subcommand == "export":
        summary = export_instincts(repo_root, scope=scope)
        logger.info("%s", summary)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
