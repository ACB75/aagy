#!/usr/bin/env python3
"""
Módulo de auditoría de paridad multi-harness entre Anything Antigravity (aagy)
y el subplugin para Claude Code (aagy-ecc) (audit_plugin_parity.py).

Verifica la simetría y coherencia estructural entre el arnés Antigravity/Gemini
y el arnés Claude Code para garantizar capacidades equivalentes sin deriva.
Cumple con SonarQube Quality Gate A (S3776 <= 15, S1192 sin duplicados).
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from sync_aagy_ecc import compare as sync_compare  # noqa: E402
import workflow_skeleton  # noqa: E402

# Constantes de Estado y Literales para SonarQube (S1192)
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_SKIPPED = "SKIPPED"

PLUGIN_NAME_AAGY = "aagy"
PLUGIN_NAME_AAGY_ECC = "aagy-ecc"

FILE_PLUGIN_JSON = "plugin.json"
FILE_MARKETPLACE_JSON = "marketplace.json"
DIR_SKILLS = "skills"
DIR_AGENTS = "agents"
DIR_AAGY_ECC = "aagy-ecc"
PLUGIN_ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)")
DIR_SCRIPTS_PY = Path("scripts", "py")
DOCTOR_AAGY = DIR_SCRIPTS_PY / "aagy_doctor.py"
DOCTOR_AAGY_ECC = Path(DIR_AAGY_ECC) / DIR_SCRIPTS_PY / "aagy_ecc_doctor.py"
DOCTOR_CATALOG = DIR_SCRIPTS_PY / "doctor_core.py"
DOCTOR_REGISTRY_ID = re.compile(r'^\s*"(DOC-\d{2})"\s*:', re.MULTILINE)
DOCTOR_CATALOG_ID = re.compile(r'CheckSpec\("(DOC-\d{2})"')

# Configuración de codificación UTF-8
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("audit-plugin-parity")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError) as exc:
        logger.debug("sys.stdout reconfigure skipped: %s", exc)


@dataclass(frozen=True)
class ParityAuditResult:
    """Resultado estructurado de la auditoría de paridad multi-harness."""
    status: str
    is_valid: bool
    root_plugin_name: str
    claude_plugin_name: str
    skills_count: int
    claude_skills_count: int
    discrepancies: Tuple[str, ...]
    agents_count: int = 0
    claude_agents_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario."""
        return asdict(self)


def _load_json_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """Carga y parsea un archivo JSON de forma segura."""
    if not file_path.is_file():
        return None
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
        return None
    except Exception:
        return None


def _check_root_plugin(repo_root: Path, discrepancies: List[str]) -> str:
    """Valida el manifiesto plugin.json del plugin raíz Antigravity."""
    root_manifest = repo_root / FILE_PLUGIN_JSON
    root_data = _load_json_file(root_manifest)
    if not root_data:
        discrepancies.append(f"No se encontró o es inválido '{FILE_PLUGIN_JSON}' en la raíz del repositorio.")
        return ""

    root_name = str(root_data.get("name", "")).strip()
    if root_name != PLUGIN_NAME_AAGY:
        discrepancies.append(
            f"El nombre del plugin raíz ('{root_name}') no coincide con '{PLUGIN_NAME_AAGY}'."
        )
    return root_name


def _count_dirs(base: Path) -> int:
    return sum(1 for p in base.iterdir() if p.is_dir()) if base.is_dir() else 0


def _count_md(base: Path) -> int:
    return sum(1 for p in base.glob("*.md") if p.is_file()) if base.is_dir() else 0


def _load_claude_manifest(claude_dir: Path, discrepancies: List[str]) -> Dict[str, Any]:
    claude_data = _load_json_file(claude_dir / ".claude-plugin" / FILE_PLUGIN_JSON)
    if claude_data:
        return claude_data
    pkg_data = _load_json_file(claude_dir / "package.json")
    if pkg_data:
        return pkg_data
    discrepancies.append(f"No se encontró manifiesto válido de plugin en '{claude_dir.name}/.claude-plugin/' ni 'package.json'.")
    return {}


def _check_marketplace(claude_dir: Path, discrepancies: List[str]) -> None:
    market = _load_json_file(claude_dir / ".claude-plugin" / FILE_MARKETPLACE_JSON)
    if market is None:
        return
    names = [str(p.get("name", "")) for p in market.get("plugins", []) if isinstance(p, dict)]
    if PLUGIN_NAME_AAGY_ECC not in names:
        discrepancies.append(
            f"'{FILE_MARKETPLACE_JSON}' no publica un plugin llamado '{PLUGIN_NAME_AAGY_ECC}' (encontrado: {names})."
        )


def _check_hook_targets(claude_dir: Path, discrepancies: List[str]) -> None:
    """Cada script referenciado con ${CLAUDE_PLUGIN_ROOT} en hooks.json debe existir dentro del plugin."""
    hooks_file = claude_dir / "hooks" / "hooks.json"
    if not hooks_file.is_file():
        discrepancies.append(f"No se encontró '{DIR_AAGY_ECC}/hooks/hooks.json'.")
        return
    text = hooks_file.read_text(encoding="utf-8")
    for rel in sorted(set(PLUGIN_ROOT_REF.findall(text))):
        if not (claude_dir / rel).is_file():
            discrepancies.append(f"El hook referencia '{rel}', que no existe dentro de '{DIR_AAGY_ECC}/'.")


def _check_mirror(repo_root: Path, discrepancies: List[str]) -> None:
    report = sync_compare(repo_root)
    if report.in_sync:
        return
    discrepancies.append(
        f"Espejo de '{DIR_AAGY_ECC}/' desincronizado: {len(report.missing)} faltan, "
        f"{len(report.changed)} distintos, {len(report.extra)} sobrantes. "
        "Ejecuta scripts/ps1/sync-aagy-ecc.ps1 (o scripts/sh/sync-aagy-ecc.sh)."
    )


def _doctor_ids(path: Path, pattern: "re.Pattern[str]") -> Tuple[str, ...]:
    return tuple(sorted(set(pattern.findall(path.read_text(encoding="utf-8")))))


def _check_doctor_parity(repo_root: Path, discrepancies: List[str]) -> None:
    """/aagy-doctor y /aagy-ecc-doctor deben implementar exactamente los mismos checks del catálogo (1:1)."""
    doctors = {"aagy_doctor.py": repo_root / DOCTOR_AAGY, "aagy_ecc_doctor.py": repo_root / DOCTOR_AAGY_ECC}
    present = {name: path for name, path in doctors.items() if path.is_file()}
    if not present:
        return
    if len(present) != len(doctors):
        missing = sorted(set(doctors) - set(present))
        discrepancies.append(f"Falta el doctor hermano {missing}: los dos doctors deben existir a la vez.")
        return
    catalog_file = repo_root / DOCTOR_CATALOG
    catalog = _doctor_ids(catalog_file, DOCTOR_CATALOG_ID) if catalog_file.is_file() else ()
    ids = {name: _doctor_ids(path, DOCTOR_REGISTRY_ID) for name, path in present.items()}
    if len(set(ids.values())) != 1:
        discrepancies.append(f"Los doctors implementan checks distintos: {ids}.")
    for name, found in ids.items():
        if catalog and found != catalog:
            discrepancies.append(f"'{name}' no implementa el catálogo DOC-* de doctor_core.py: {found} != {catalog}.")


def _check_claude_plugin(repo_root: Path, root_version: str, discrepancies: List[str]) -> Tuple[str, int, int]:
    """Valida el subplugin aagy-ecc para Claude Code."""
    claude_dir = repo_root / DIR_AAGY_ECC
    if not claude_dir.is_dir():
        discrepancies.append(f"No se encontró el subdirectorio del plugin Claude Code '{DIR_AAGY_ECC}/'.")
        return "", 0, 0

    claude_data = _load_claude_manifest(claude_dir, discrepancies)
    claude_name = str(claude_data.get("name", "")).strip()
    if claude_name and claude_name != PLUGIN_NAME_AAGY_ECC:
        discrepancies.append(f"El nombre del plugin Claude Code ('{claude_name}') no es '{PLUGIN_NAME_AAGY_ECC}'.")

    claude_version = str(claude_data.get("version", "")).strip()
    if claude_data and root_version and claude_version != root_version:
        discrepancies.append(
            f"Versión de '{PLUGIN_NAME_AAGY_ECC}' ('{claude_version}') distinta de la de '{PLUGIN_NAME_AAGY}' ('{root_version}')."
        )

    if not (claude_dir / DIR_SKILLS).is_dir():
        discrepancies.append(f"No existe '{DIR_AAGY_ECC}/{DIR_SKILLS}/': Claude Code no cargaría ninguna skill.")

    _check_marketplace(claude_dir, discrepancies)
    _check_hook_targets(claude_dir, discrepancies)
    if (repo_root / DIR_SKILLS).is_dir():
        _check_mirror(repo_root, discrepancies)

    return claude_name, _count_dirs(claude_dir / DIR_SKILLS), _count_md(claude_dir / DIR_AGENTS)


CI_TEMPLATE = Path("templates") / "github-actions" / "ci-quality-gate.yml"
_RUN_LINE = re.compile(r"^\s*(?:-\s*)?run:\s*(\|)?\s*(.*)$")
_ALLOWED_RUN = re.compile(r"^(npm install|python -m pip install|pip install|python scripts/py/ci_local\.py run)")
_PAID_HINT = re.compile(r"(EXA_API_KEY|FIRECRAWL_API_KEY|exa MCP|firecrawl)", re.IGNORECASE)


def _template_commands(text: str) -> List[str]:
    """Comandos de los pasos ``run:`` de un workflow (una línea o bloque ``|``)."""
    commands: List[str] = []
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        match = _RUN_LINE.match(line)
        if not match:
            continue
        if match.group(2):
            commands.append(match.group(2).strip())
            continue
        indent = len(line) - len(line.lstrip())
        for nxt in lines[idx + 1:]:
            if nxt.strip() and len(nxt) - len(nxt.lstrip()) <= indent:
                break
            if nxt.strip():
                commands.append(nxt.strip())
    return commands


def _check_ci_template(repo_root: Path, discrepancies: List[str]) -> None:
    """La plantilla de Actions solo puede llamar a ci_local.py (paridad con el pre-push local)."""
    template = repo_root / CI_TEMPLATE
    if not template.is_file():
        return
    text = template.read_text(encoding="utf-8", errors="replace")
    extra = [cmd for cmd in _template_commands(text) if not _ALLOWED_RUN.match(cmd)]
    if extra:
        discrepancies.append(f"'{CI_TEMPLATE.as_posix()}' ejecuta pasos que ci_local.py no ejecuta: {extra[0]}")
    if "ci_local.py run" not in text:
        discrepancies.append(f"'{CI_TEMPLATE.as_posix()}' no llama a 'python scripts/py/ci_local.py run'.")


def _check_paid_skills(repo_root: Path, discrepancies: List[str]) -> None:
    """Toda skill que dependa de una API de pago declara ``cost: paid`` (presupuesto 0 $)."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import aagy_config  # noqa: PLC0415

    for skill_md in sorted((repo_root / DIR_SKILLS).glob("*/SKILL.md")):
        name = skill_md.parent.name
        head = skill_md.read_text(encoding="utf-8", errors="replace")[:600]
        if _PAID_HINT.search(head) and aagy_config.skill_cost(skill_md) != "paid":
            discrepancies.append(f"La skill '{name}' usa una API de pago y no declara 'cost: paid' en su frontmatter.")


def _check_workflow_skeleton(repo_root: Path, discrepancies: List[str]) -> None:
    """RF-05/RF-06: los workflows propios cumplen el esqueleto; los heredados solo avisan."""
    findings = workflow_skeleton.audit(repo_root)
    for item in findings:
        if item.level == workflow_skeleton.LEVEL_FAIL:
            discrepancies.append(f"El workflow '{item.key}' no sigue el esqueleto común: {'; '.join(item.problems)}")
    warns = sum(1 for f in findings if f.level == workflow_skeleton.LEVEL_WARN)
    if warns:
        logger.warning("[WARN] %d workflows heredados sin esqueleto completo (python scripts/py/workflow_skeleton.py --verbose).", warns)


def audit_parity(repo_root: Path) -> ParityAuditResult:
    """
    Ejecuta la auditoría de paridad completa entre Anything Antigravity y Claude Code.
    """
    discrepancies: List[str] = []

    root_name = _check_root_plugin(repo_root, discrepancies)
    root_data = _load_json_file(repo_root / FILE_PLUGIN_JSON) or {}
    root_version = str(root_data.get("version", "")).strip()
    claude_name, claude_skills_count, claude_agents_count = _check_claude_plugin(repo_root, root_version, discrepancies)
    _check_doctor_parity(repo_root, discrepancies)
    _check_ci_template(repo_root, discrepancies)
    _check_paid_skills(repo_root, discrepancies)
    _check_workflow_skeleton(repo_root, discrepancies)

    root_skills_count = _count_dirs(repo_root / DIR_SKILLS)
    root_agents_count = _count_md(repo_root / DIR_AGENTS)

    is_valid = len(discrepancies) == 0
    status = STATUS_PASS if is_valid else STATUS_FAIL

    return ParityAuditResult(
        status=status,
        is_valid=is_valid,
        root_plugin_name=root_name,
        claude_plugin_name=claude_name,
        skills_count=root_skills_count,
        claude_skills_count=claude_skills_count,
        discrepancies=tuple(discrepancies),
        agents_count=root_agents_count,
        claude_agents_count=claude_agents_count,
    )


def print_report(result: ParityAuditResult) -> None:
    """Muestra el reporte legible de paridad."""
    color_code = "\033[92m" if result.is_valid else "\033[91m"
    reset_code = "\033[0m"

    logger.info("=======================================================")
    logger.info("   AUDITORIA DE PARIDAD MULTI-HARNESS (aagy <-> aagy-ecc)   ")
    logger.info("=======================================================")
    logger.info(f"Estado de Paridad:        {color_code}[{result.status}]{reset_code}")
    logger.info(f"Plugin Raíz Antigravity:  {result.root_plugin_name or 'N/A'}")
    logger.info(f"Subplugin Claude Code:    {result.claude_plugin_name or 'N/A'}")
    logger.info(f"Habilidades Antigravity:  {result.skills_count}")
    logger.info(f"Habilidades Claude Code:  {result.claude_skills_count}")
    logger.info(f"Subagentes Antigravity:   {result.agents_count}")
    logger.info(f"Subagentes Claude Code:   {result.claude_agents_count}")

    if result.discrepancies:
        logger.info("\nDiscrepancias Detectadas:")
        for disc in result.discrepancies:
            logger.info(f"  - {disc}")
    logger.info("=======================================================\n")


def parse_args(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Auditoría de paridad multi-harness entre Anything Antigravity (aagy) y Claude Code (aagy-ecc)."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path("."),
        help="Ruta raíz del repositorio (por defecto actual)."
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Solo verifica y retorna código de salida 0 o 1 sin reporte verboso."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en formato JSON estructurado."
    )
    return parser.parse_args(args)


def main(args: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada principal."""
    parsed = parse_args(args)
    repo_root = parsed.repo_root.resolve()

    result = audit_parity(repo_root)

    if parsed.json:
        print(json.dumps(result.to_dict(), indent=2))
    elif not parsed.check_only:
        print_report(result)

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
