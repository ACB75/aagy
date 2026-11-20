#!/usr/bin/env python3
"""
ECC Workspace Auditor & Context Token Budget Engine (stdlib pura).

Audita y optimiza de forma recurrente:
  1. Higiene del workspace:
     - Archivos backup/temporales (.bak, .old, .orig, .tmp, .swp)
     - Cachés de ejecución (__pycache__, .pytest_cache, .mypy_cache, .ruff_cache)
     - Directorios vacíos
  2. Presupuesto de tokens y cumplimiento de frontmatter:
     - skills description <= 140 chars
     - agents description <= 120 chars
     - agents model in {flash, inherit}
     - cero tools de mutación en agentes read-only
  3. Detección de duplicados, redundancias y artefactos muertos:
     - Carpetas de skills huérfanas sin SKILL.md
     - Agentes sin frontmatter o descripción
     - Reglas vacías (0 bytes)
  4. Delegación a SonarQube (sonar_audit.py) y Seguridad (security_audit.py)

Uso:
  python workspace_audit.py [--root <path>] [--clean] [--optimize] [--skip-sonar] [--skip-security]
"""

from __future__ import annotations

import argparse
import collections
import json
import logging
import math
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

_SCRIPT_DIR: str = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from docs_map import DOCS_MAP_REL, validate_docs_map_targets

logger: logging.Logger = logging.getLogger("workspace-audit")

MAX_SKILL_DESC: int = 140
MAX_AGENT_DESC: int = 120
MAX_RULE_FILE_BYTES: int = 24_000
MAX_RULES_TOTAL_TOKENS: int = 16_000
MAX_EAGER_CUSTOMIZATION_TOKENS: int = 3_000
ACTIVE_MCP_BASE_TOKENS: int = 1_500
HEAVY_MCP_SERVERS: frozenset[str] = frozenset({"gemini-mcp"})
HEAVY_MCP_TOKENS: int = 4_500

ALLOWED_MODELS: frozenset[str] = frozenset({"flash", "inherit"})
CHARS_PER_TOKEN: float = 3.8

SKILL_FILE_NAME: str = "SKILL.md"
README_FILE: str = "README.md"
PLUGIN_NAME_ECC_AGY: str = "aagy"
DESC_KEY: str = "description"
MODEL_KEY: str = "model"

IGNORED_DIRS: frozenset[str] = frozenset({
    ".git", "node_modules", ".angular", "target", "dist",
    "brain", "conversations", "implicit", "code_tracker",
    "browser_recordings", "antigravity-browser-profile", "extensions",
})
CACHE_DIRS: frozenset[str] = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"})
BAK_REGEX: re.Pattern[str] = re.compile(r"\.(bak|old|orig|tmp|swp)$", re.IGNORECASE)
READ_ONLY_AGENT_REGEX: re.Pattern[str] = re.compile(
    r"(architect|planner|reviewer|troubleshooter|hunter|analyzer|evaluator|scout)",
    re.IGNORECASE,
)
WRITE_TOOLS_REGEX: re.Pattern[str] = re.compile(r"(write_to_file|replace_file_content|write_file|edit_file)")
FRONTMATTER_REGEX: re.Pattern[str] = re.compile(r"^---\s*\r?\n(.*?)\r?\n---", re.DOTALL)


@dataclass(frozen=True)
class AgentTarget:
    """Directorio con skills/agents a auditar."""
    label: str
    directory: Path
    include_rules: bool = False
    is_plugin: bool = False


@dataclass(frozen=True)
class HygieneReport:
    backups: Tuple[Path, ...]
    caches: Tuple[Path, ...]
    empty_dirs: Tuple[Path, ...]

    def all_targets(self) -> Tuple[Path, ...]:
        return self.backups + self.caches + self.empty_dirs


@dataclass(frozen=True)
class BudgetReport:
    skill_count: int = 0
    agent_count: int = 0
    skills_desc_chars: int = 0
    agents_desc_chars: int = 0
    rules_chars: int = 0
    rules_tokens: int = 0
    mcp_count: int = 0
    mcp_active_count: int = 0
    mcp_tokens: int = 0
    violations: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def estimated_tokens(self) -> int:
        skills_agents = math.ceil((self.skills_desc_chars + self.agents_desc_chars) / CHARS_PER_TOKEN)
        return self.rules_tokens + skills_agents + self.mcp_tokens

    @property
    def eager_customization_tokens(self) -> int:
        skills_agents = math.ceil((self.skills_desc_chars + self.agents_desc_chars) / CHARS_PER_TOKEN)
        return skills_agents + self.mcp_tokens


@dataclass(frozen=True)
class DuplicateReport:
    global_shadowed_skills: Tuple[Tuple[str, str, Path], ...]
    cross_project_duplicate_skills: Tuple[Tuple[str, Tuple[str, ...]], ...]
    cross_project_duplicate_agents: Tuple[Tuple[str, Tuple[str, ...]], ...]

    @property
    def has_redundancies(self) -> bool:
        return bool(self.global_shadowed_skills)


@dataclass(frozen=True)
class DeadArtifactReport:
    orphan_skill_dirs: Tuple[Path, ...]
    invalid_agents: Tuple[Tuple[Path, str], ...]
    empty_rules: Tuple[Path, ...]

    @property
    def total_issues(self) -> int:
        return len(self.orphan_skill_dirs) + len(self.invalid_agents) + len(self.empty_rules)


# --------------------------------------------------------------------------- #
# [1] Higiene
# --------------------------------------------------------------------------- #
def scan_hygiene(root: Path, max_depth: int = 5) -> HygieneReport:
    """Recorre el árbol detectando backups, cachés y directorios vacíos."""
    backups: List[Path] = []
    caches: List[Path] = []
    empty_dirs: List[Path] = []

    def walk(directory: Path, depth: int) -> None:
        if depth > max_depth or directory.name in IGNORED_DIRS:
            return
        try:
            entries = list(os.scandir(directory))
        except OSError:
            return
        if not entries:
            empty_dirs.append(directory)
            return
        for entry in entries:
            if entry.is_symlink():
                continue
            path = Path(entry.path)
            if entry.is_dir():
                if entry.name in CACHE_DIRS:
                    caches.append(path)
                else:
                    walk(path, depth + 1)
            elif entry.is_file() and BAK_REGEX.search(entry.name):
                backups.append(path)

    walk(root, 0)
    return HygieneReport(tuple(backups), tuple(caches), tuple(empty_dirs))


def clean_targets(targets: Sequence[Path]) -> None:
    """Elimina los objetivos detectados con manejo seguro de excepciones."""
    for target in targets:
        try:
            if target.is_dir():
                shutil.rmtree(target)
            else:
                target.unlink()
            logger.info("  [CLEANED] %s", target)
        except OSError as exc:
            logger.warning("  [SKIPPED] %s (%s)", target, exc.strerror or exc)


# --------------------------------------------------------------------------- #
# [2] Presupuesto de tokens / frontmatter
# --------------------------------------------------------------------------- #
def read_frontmatter(content: str) -> str:
    match = FRONTMATTER_REGEX.match(content)
    return match.group(1) if match else ""


def frontmatter_field(frontmatter: str, key: str) -> Optional[str]:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", frontmatter, re.MULTILINE)
    if not match:
        return None
    val = match.group(1).strip()
    return val.strip("'\"")


def audit_skills(skills_dir: Path) -> Tuple[int, int, List[str]]:
    count, chars, violations = 0, 0, []
    if not skills_dir.is_dir():
        return count, chars, violations
    for skill_md in sorted(skills_dir.glob(f"*/{SKILL_FILE_NAME}")):
        count += 1
        content = skill_md.read_text(encoding="utf-8", errors="replace")
        desc = frontmatter_field(read_frontmatter(content), DESC_KEY)
        if desc is None:
            violations.append(f"Skill '{skill_md.parent.name}' is missing description in frontmatter")
            continue
        chars += len(desc)
        if len(desc) > MAX_SKILL_DESC:
            violations.append(
                f"Skill '{skill_md.parent.name}' description is {len(desc)} chars (>{MAX_SKILL_DESC} max)"
            )
    return count, chars, violations


def check_agent(name: str, frontmatter: str) -> Tuple[int, List[str]]:
    violations: List[str] = []
    desc = frontmatter_field(frontmatter, DESC_KEY) or ""
    if not desc:
        violations.append(f"Agent '{name}' is missing description in frontmatter")
    elif len(desc) > MAX_AGENT_DESC:
        violations.append(f"Agent '{name}' description is {len(desc)} chars (>{MAX_AGENT_DESC} max)")
    
    model = frontmatter_field(frontmatter, MODEL_KEY)
    if model is not None and model not in ALLOWED_MODELS:
        violations.append(f"Agent '{name}' uses non-optimal model '{model}' (expected 'flash' or 'inherit')")
    
    if READ_ONLY_AGENT_REGEX.search(name) and WRITE_TOOLS_REGEX.search(frontmatter):
        violations.append(f"Read-only agent '{name}' has write tools in frontmatter")
    return len(desc), violations


def audit_agents(agents_dir: Path) -> Tuple[int, int, List[str]]:
    count, chars, violations = 0, 0, []
    if not agents_dir.is_dir():
        return count, chars, violations
    for agent_md in sorted(agents_dir.glob("*.md")):
        if agent_md.name == README_FILE:
            continue
        count += 1
        frontmatter = read_frontmatter(agent_md.read_text(encoding="utf-8", errors="replace"))
        desc_chars, agent_violations = check_agent(agent_md.name, frontmatter)
        chars += desc_chars
        violations.extend(agent_violations)
    return count, chars, violations


def _collect_rule_files(target_dir: Path) -> List[Path]:
    rules_dir = target_dir / "rules"
    if rules_dir.is_dir():
        files = [p for p in sorted(rules_dir.glob("*.md")) if p.name != README_FILE]
        if files:
            return files

    agents_root = target_dir / "AGENTS.md"
    return [agents_root] if agents_root.is_file() else []


def audit_rules(target_dir: Path, include_rules: bool = True) -> Tuple[int, int, List[str]]:
    """
    Audita archivos de reglas Markdown (.md):
    - Cada archivo individual <= MAX_RULE_FILE_BYTES (24.000 bytes / 24 KB).
    - Total de tokens de reglas <= MAX_RULES_TOTAL_TOKENS (16.000 tokens).
    Retorna: (total_chars, total_tokens, violations)
    """
    if not include_rules:
        return 0, 0, []

    total_chars = 0
    violations: List[str] = []
    rule_files = _collect_rule_files(target_dir)

    for r_file in rule_files:
        try:
            size = r_file.stat().st_size
        except OSError:
            continue
        if size > MAX_RULE_FILE_BYTES:
            violations.append(
                f"Rule file '{r_file.name}' is {size} bytes (>{MAX_RULE_FILE_BYTES} max limit of 24 KB)"
            )
        content = r_file.read_text(encoding="utf-8", errors="replace")
        total_chars += len(content)

    total_tokens = math.ceil(total_chars / CHARS_PER_TOKEN)
    if total_tokens > MAX_RULES_TOTAL_TOKENS:
        violations.append(
            f"Aggregated rules exceed safe budget: {total_tokens} tokens (>{MAX_RULES_TOTAL_TOKENS} ceiling, 20k absolute limit)"
        )

    return total_chars, total_tokens, violations


def _find_mcp_config_file(target_dir: Path) -> Optional[Path]:
    for candidate in (
        target_dir / "mcp_config.json",
        target_dir / ".gemini" / "mcp_config.json",
        target_dir / "gemini.json",
    ):
        if candidate.is_file():
            return candidate
    return None


def audit_mcps(target_dir: Path) -> Tuple[int, int, int, List[str]]:
    """
    Audita servidores MCP declarados en mcp_config.json:
    - Exige 'disabled: true' en servidores pesados (HEAVY_MCP_SERVERS).
    - Calcula la huella estimada de servidores activos en reposo.
    Retorna: (total_mcps, active_mcps, estimated_tokens, violations)
    """
    mcp_file = _find_mcp_config_file(target_dir)
    if not mcp_file:
        return 0, 0, 0, []

    try:
        data = json.loads(mcp_file.read_text(encoding="utf-8", errors="replace"))
    except (json.JSONDecodeError, OSError) as exc:
        return 0, 0, 0, [f"Invalid JSON in MCP configuration file '{mcp_file.name}': {exc}"]

    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict):
        return 0, 0, 0, []

    total_mcps = len(servers)
    active_mcps = 0
    mcp_tokens = 0
    violations: List[str] = []

    for name, config in servers.items():
        is_disabled = bool(config.get("disabled", False)) if isinstance(config, dict) else False

        if name in HEAVY_MCP_SERVERS and not is_disabled:
            violations.append(
                f"Heavy MCP server '{name}' is enabled by default. Must set '\"disabled\": true' to prevent context overflow."
            )

        if not is_disabled:
            active_mcps += 1
            server_tokens = HEAVY_MCP_TOKENS if name in HEAVY_MCP_SERVERS else ACTIVE_MCP_BASE_TOKENS
            mcp_tokens += server_tokens

    return total_mcps, active_mcps, mcp_tokens, violations


def audit_target_budget(target: AgentTarget) -> BudgetReport:
    rules_chars, rules_tokens, rules_violations = audit_rules(target.directory, target.include_rules)
    skill_count, skill_chars, skill_violations = audit_skills(target.directory / "skills")
    agent_count, agent_chars, agent_violations = audit_agents(target.directory / "agents")
    mcp_count, mcp_active, mcp_tokens, mcp_violations = audit_mcps(target.directory)

    violations = list(rules_violations + skill_violations + agent_violations + mcp_violations)

    if target.is_plugin:
        eager_tokens = math.ceil((skill_chars + agent_chars) / CHARS_PER_TOKEN) + mcp_tokens
        if eager_tokens > MAX_EAGER_CUSTOMIZATION_TOKENS:
            violations.append(
                f"Eager customizations in plugin '{target.label}' exceed budget: ~{eager_tokens} tokens (>{MAX_EAGER_CUSTOMIZATION_TOKENS} max)"
            )

    return BudgetReport(
        skill_count=skill_count,
        agent_count=agent_count,
        skills_desc_chars=skill_chars,
        agents_desc_chars=agent_chars,
        rules_chars=rules_chars,
        rules_tokens=rules_tokens,
        mcp_count=mcp_count,
        mcp_active_count=mcp_active,
        mcp_tokens=mcp_tokens,
        violations=tuple(violations),
    )


# --------------------------------------------------------------------------- #
# [3] Duplicados y artefactos muertos
# --------------------------------------------------------------------------- #
def _scan_target_orphan_skills(target: AgentTarget) -> List[Path]:
    orphans: List[Path] = []
    skills_dir = target.directory / "skills"
    if skills_dir.is_dir():
        for s_dir in skills_dir.iterdir():
            if s_dir.is_dir() and not (s_dir / SKILL_FILE_NAME).is_file():
                orphans.append(s_dir)
    return orphans


def _scan_target_invalid_agents(target: AgentTarget) -> List[Tuple[Path, str]]:
    invalid: List[Tuple[Path, str]] = []
    agents_dir = target.directory / "agents"
    if agents_dir.is_dir():
        for a_file in agents_dir.glob("*.md"):
            if a_file.name == README_FILE:
                continue
            txt = a_file.read_text(encoding="utf-8", errors="replace")
            fm = read_frontmatter(txt)
            if not fm:
                invalid.append((a_file, "missing frontmatter"))
            elif not frontmatter_field(fm, DESC_KEY):
                invalid.append((a_file, "missing description"))
    return invalid


def _scan_target_empty_rules(target: AgentTarget) -> List[Path]:
    empty: List[Path] = []
    rules_dir = target.directory / "rules"
    if rules_dir.is_dir():
        for r_file in rules_dir.glob("*.md"):
            if r_file.stat().st_size == 0 or not r_file.read_text(encoding="utf-8", errors="replace").strip():
                empty.append(r_file)
    return empty


def scan_dead_artifacts(targets: Sequence[AgentTarget]) -> DeadArtifactReport:
    orphan_skills: List[Path] = []
    invalid_agents: List[Tuple[Path, str]] = []
    empty_rules: List[Path] = []

    for target in targets:
        if target.directory.is_dir():
            orphan_skills.extend(_scan_target_orphan_skills(target))
            invalid_agents.extend(_scan_target_invalid_agents(target))
            empty_rules.extend(_scan_target_empty_rules(target))

    return DeadArtifactReport(
        orphan_skill_dirs=tuple(orphan_skills),
        invalid_agents=tuple(invalid_agents),
        empty_rules=tuple(empty_rules),
    )


# --------------------------------------------------------------------------- #
# CLI y Ejecución Principal
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ECC Workspace hygiene and token budget audit.")
    parser.add_argument("--root", type=Path, default=None, help="Raíz del repositorio.")
    parser.add_argument("--clean", action="store_true", help="Elimina backups y cachés detectados.")
    parser.add_argument("--optimize", action="store_true", help="Poda redundancias y optimiza descripciones.")
    parser.add_argument("--skip-sonar", action="store_true", help="Omite auditoría estática SonarQube.")
    parser.add_argument("--skip-security", action="store_true", help="Omite auditoría de seguridad.")
    return parser.parse_args(argv)


def _audit_targets_budget(targets: Sequence[AgentTarget]) -> int:
    logger.info("\n=== [2/4] PRESUPUESTO DE TOKENS Y FRONTMATTER ===")
    total_violations = 0
    for target in targets:
        report = audit_target_budget(target)
        rules_info = f", Rules={report.rules_chars}c (~{report.rules_tokens}t)" if target.include_rules else ""
        mcp_info = f", MCPs={report.mcp_active_count}/{report.mcp_count} (~{report.mcp_tokens}t)" if report.mcp_count > 0 else ""
        logger.info(
            "• %s: Skills=%d (%dc), Agents=%d (%dc)%s%s => ~%d tokens",
            target.label,
            report.skill_count,
            report.skills_desc_chars,
            report.agent_count,
            report.agents_desc_chars,
            rules_info,
            mcp_info,
            report.estimated_tokens,
        )
        for v in report.violations:
            total_violations += 1
            logger.warning("  [VIOLATION] %s", v)
    return total_violations


def _run_delegated_checks(root: Path, skip_sonar: bool, skip_security: bool) -> int:
    script_dir = Path(__file__).resolve().parent
    delegated_code = 0
    if not skip_sonar:
        sonar_script = script_dir / "sonar_audit.py"
        if sonar_script.is_file():
            logger.info("\n=== [4/4] AUDITORÍA SONARQUBE QUALITY GATE A ===")
            res = subprocess.run([sys.executable, str(sonar_script), "--root", str(root)], check=False)
            if res.returncode != 0:
                delegated_code = res.returncode

    if not skip_security:
        sec_script = script_dir / "security_audit.py"
        if sec_script.is_file():
            logger.info("\n=== VERIFICACIÓN DE SEGURIDAD ESTÁTICA ===")
            res = subprocess.run([sys.executable, str(sec_script), "--root", str(root)], check=False)
            if res.returncode != 0:
                delegated_code = res.returncode
    return delegated_code


def _audit_docs_map_integrity(root: Path) -> List[str]:
    """Valida rutas declaradas en .governance/docs-map.json cuando el archivo existe."""
    if not (root / DOCS_MAP_REL).is_file():
        return []
    return validate_docs_map_targets(root)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve() if args.root else Path(__file__).resolve().parent.parent.parent
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)

    logger.info("==================================================================")
    logger.info("           AUDITORÍA DE TOKENS, HIGIENE Y HARNESS (ECC)          ")
    logger.info("==================================================================")
    logger.info("Raíz de trabajo: %s\n", root)

    # 1. Higiene
    logger.info("=== [1/4] HIGIENE DEL WORKSPACE ===")
    hygiene = scan_hygiene(root)
    logger.info("Backups detectados: %d", len(hygiene.backups))
    logger.info("Cachés detectadas: %d", len(hygiene.caches))
    logger.info("Directorios vacíos: %d", len(hygiene.empty_dirs))
    if args.clean and hygiene.all_targets():
        logger.info("Limpiando elementos temporales...")
        clean_targets(hygiene.all_targets())

    # 2. Objetivos de tokens
    targets = [AgentTarget("ECC Root", root, include_rules=True)]
    global_plugin = Path.home() / ".gemini" / "config" / "plugins" / PLUGIN_NAME_ECC_AGY
    if global_plugin.is_dir():
        targets.append(AgentTarget(f"Global Plugin ({PLUGIN_NAME_ECC_AGY})", global_plugin, include_rules=True, is_plugin=True))
    elif (root / PLUGIN_NAME_ECC_AGY).is_dir():
        targets.append(AgentTarget(f"{PLUGIN_NAME_ECC_AGY} distribution", root / PLUGIN_NAME_ECC_AGY, include_rules=True, is_plugin=True))

    total_violations = _audit_targets_budget(targets)

    # 2.5 Integridad de docs-map.json si existe
    docs_map_issues = _audit_docs_map_integrity(root)
    for dm_issue in docs_map_issues:
        total_violations += 1
        logger.warning("  [DOCS-MAP] %s", dm_issue)

    # 3. Artefactos muertos
    logger.info("\n=== [3/4] ARTEFACTOS MUERTOS O HUÉRFANOS ===")
    dead_report = scan_dead_artifacts(targets)
    logger.info("Skills huérfanas / Agentes inválidos / Reglas vacías: %d", dead_report.total_issues)
    for orphan in dead_report.orphan_skill_dirs:
        logger.warning("  [DEAD SKILL] %s", orphan)
    for agent_path, reason in dead_report.invalid_agents:
        logger.warning("  [INVALID AGENT] %s: %s", agent_path, reason)
    for rule in dead_report.empty_rules:
        logger.warning("  [EMPTY RULE] %s", rule)

    exit_code = 1 if (total_violations > 0 or dead_report.total_issues > 0) else 0

    delegated_code = _run_delegated_checks(root, args.skip_sonar, args.skip_security)
    if delegated_code != 0:
        exit_code = delegated_code

    if exit_code == 0:
        logger.info("\n[PASS] Todas las comprobaciones de higiene y presupuesto de tokens cumplen exitosamente.")
    else:
        logger.error("\n[FAIL] Se detectaron violaciones en las reglas de calidad del workspace.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
