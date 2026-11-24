#!/usr/bin/env python3
"""
/aagy-doctor: diagnóstico de la instalación de aagy en Google Antigravity / Gemini (aagy_doctor.py).

Revisa el plugin global (~/.gemini/config/plugins/aagy), el repo aagy de origen
y el proyecto actual con el catálogo común DOC-01..DOC-15 de doctor_core.py,
el mismo que usa /aagy-ecc-doctor en Claude Code (paridad 1:1).

Solo lectura por defecto. Con --fix propone arreglos seguros y los aplica tras
confirmarlos (--yes para no preguntar).

Uso:
  python scripts/py/aagy_doctor.py
  python scripts/py/aagy_doctor.py --json
  python scripts/py/aagy_doctor.py --fix
  python scripts/py/aagy_doctor.py --plugin-dir D:\\otro\\aagy --only DOC-05,DOC-09
"""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import shlex
import sys
from typing import Dict, List, Optional, Sequence, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import doctor_core as core  # noqa: E402
from install_manifest import InstallManifest, read_manifest  # noqa: E402

TARGET_NAME = "aagy (Antigravity)"
PLUGIN_NAME = "aagy"
RUNTIME_BINARY = "antigravity"
DIR_SKILLS = "skills"
DIR_AGENTS = "agents"
DIR_RULES = "rules"
FILE_PLUGIN_JSON = "plugin.json"
KEY_VERSION = "version"
DIR_SCRIPTS = "scripts"
PWSH_NO_PROFILE = "-NoProfile"
FILE_HOOKS_JSON = "hooks.json"
FILE_RULES = "AGENTS.md"
FILE_SKILL = "SKILL.md"
DOCTOR_SKILL = "aagy-doctor"
DATA_SUBDIR = ".data"
ENV_PLUGIN_DATA = "AGY_PLUGIN_DATA"
DEFAULT_PHASE = "generic"
PHASE_ALL = "all"
MIN_PYTHON = (3, 10, 0)
MIN_PWSH = (7, 0, 0)
SAFETY_PROBE_DENY = "rm -rf / "
SAFETY_PROBE_ALLOW = "ls"
SCRIPT_EXTENSIONS = (".ps1", ".py", ".sh")
LEGACY_MARKERS = ("ecc", "everything-claude-code")

MSG_NO_PLUGIN = "No hay plugin instalado que revisar."
MSG_NO_REPO = "Sin repo aagy de origen (usa --repo-root o reinstala para crear el manifiesto)."


@dataclass(frozen=True)
class AgyContext:
    home: Path
    plugin_dir: Path
    repo_root: Optional[Path]
    project_dir: Path
    manifest: Optional[InstallManifest]

    @property
    def installed(self) -> bool:
        return self.plugin_dir.is_dir()

    @property
    def phase(self) -> str:
        return (self.manifest.profile if self.manifest and self.manifest.profile else DEFAULT_PHASE)


# --------------------------------------------------------------------------- #
# Construcción del contexto
# --------------------------------------------------------------------------- #
def default_plugin_dir(home: Path) -> Path:
    return home / ".gemini" / "config" / "plugins" / PLUGIN_NAME


def resolve_repo_root(explicit: Optional[Path], manifest: Optional[InstallManifest], project_dir: Path) -> Optional[Path]:
    """--repo-root, después el repo de origen del manifiesto, después el repo que contiene el proyecto o este script."""
    if explicit is not None:
        return explicit.expanduser().resolve()
    if manifest and manifest.source_repo and core.find_repo_root(Path(manifest.source_repo)):
        return Path(manifest.source_repo).resolve()
    return core.find_repo_root(project_dir.resolve()) or core.find_repo_root(Path(_SCRIPT_DIR))


def build_context(args) -> AgyContext:
    home = (args.home or Path.home()).expanduser()
    plugin_dir = (args.plugin_dir or default_plugin_dir(home)).expanduser()
    project_dir = (args.project or Path.cwd()).expanduser()
    manifest = read_manifest(plugin_dir)
    return AgyContext(home, plugin_dir, resolve_repo_root(args.repo_root, manifest, project_dir), project_dir, manifest)


def installed_version(ctx: AgyContext) -> str:
    data = core.load_json_dict(ctx.plugin_dir / FILE_PLUGIN_JSON) or {}
    return str(data.get(KEY_VERSION, ""))


def sync_fix(ctx: AgyContext) -> Optional[core.FixAction]:
    """Re-sincroniza el plugin global desde el repo con la fase instalada."""
    if ctx.repo_root is None:
        return None
    pwsh = core.which("pwsh")
    if pwsh:
        script = ctx.repo_root / DIR_SCRIPTS / "ps1" / "aagy-sync.ps1"
        argv: Tuple[str, ...] = (pwsh, PWSH_NO_PROFILE, "-File", str(script), "-Phase", ctx.phase, "-Clean")
    else:
        script = ctx.repo_root / DIR_SCRIPTS / "sh" / "aagy-sync.sh"
        argv = (core.which("bash") or "bash", str(script), ctx.phase, str(ctx.plugin_dir))
    return core.FixAction(f"Re-sincronizar aagy (fase '{ctx.phase}') desde el repo", argv)


# --------------------------------------------------------------------------- #
# DOC-01 .. DOC-04
# --------------------------------------------------------------------------- #
def check_runtime(ctx: AgyContext) -> core.CheckResult:
    found = core.which(RUNTIME_BINARY)
    if not found:
        return core.result("DOC-01", core.STATUS_SKIP, f"'{RUNTIME_BINARY}' no está en el PATH.")
    return core.result("DOC-01", core.STATUS_PASS, f"Antigravity localizado: {found}")


def check_plugin_installed(ctx: AgyContext) -> core.CheckResult:
    if ctx.installed:
        return core.result("DOC-02", core.STATUS_PASS, f"Plugin instalado en {ctx.plugin_dir}")
    return core.result("DOC-02", core.STATUS_FAIL, f"No existe {ctx.plugin_dir}", fix=sync_fix(ctx))


def check_manifests(ctx: AgyContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-03", core.STATUS_SKIP, MSG_NO_PLUGIN)
    data = core.load_json_dict(ctx.plugin_dir / FILE_PLUGIN_JSON)
    if data is None:
        return core.result("DOC-03", core.STATUS_FAIL, f"'{FILE_PLUGIN_JSON}' falta o no es JSON válido.", fix=sync_fix(ctx))
    if data.get("name") != PLUGIN_NAME:
        return core.result("DOC-03", core.STATUS_FAIL, f"'{FILE_PLUGIN_JSON}' tiene name='{data.get('name')}', se esperaba '{PLUGIN_NAME}'.")
    return core.result("DOC-03", core.STATUS_PASS, f"'{FILE_PLUGIN_JSON}' válido.")


def _repo_version(repo_root: Optional[Path]) -> str:
    if repo_root is None:
        return ""
    data = core.load_json_dict(repo_root / FILE_PLUGIN_JSON) or {}
    return str(data.get(KEY_VERSION, ""))


def _ecc_version(repo_root: Optional[Path]) -> str:
    if repo_root is None:
        return ""
    data = core.load_json_dict(repo_root / "aagy-ecc" / ".claude-plugin" / FILE_PLUGIN_JSON) or {}
    return str(data.get(KEY_VERSION, ""))


def check_version(ctx: AgyContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-04", core.STATUS_SKIP, MSG_NO_PLUGIN)
    problems: List[str] = []
    if ctx.manifest is None:
        problems.append(f"Falta {core.MANIFEST_FILE}: no se sabe qué fase se instaló (se asume '{DEFAULT_PHASE}').")
    current = installed_version(ctx)
    repo_version = _repo_version(ctx.repo_root)
    if repo_version and current != repo_version:
        problems.append(f"Versión instalada '{current}' distinta de la del repo '{repo_version}'.")
    ecc_version = _ecc_version(ctx.repo_root)
    if repo_version and ecc_version and ecc_version != repo_version:
        problems.append(f"aagy-ecc está en '{ecc_version}' y aagy en '{repo_version}'.")
    if problems:
        return core.result("DOC-04", core.STATUS_WARN, problems[0], *problems[1:], fix=sync_fix(ctx))
    commit = ctx.manifest.commit[:7] if ctx.manifest and ctx.manifest.commit else "?"
    return core.result("DOC-04", core.STATUS_PASS, f"Versión {current}, fase '{ctx.phase}', commit {commit}.")


# --------------------------------------------------------------------------- #
# DOC-05 .. DOC-08
# --------------------------------------------------------------------------- #
def check_rules(ctx: AgyContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-05", core.STATUS_SKIP, MSG_NO_PLUGIN)
    rules_file = ctx.plugin_dir / DIR_RULES / FILE_RULES
    problems = core.rules_budget_problems(rules_file)
    if problems:
        return core.result("DOC-05", core.STATUS_FAIL, problems[0], *problems[1:], fix=sync_fix(ctx))
    repo_rules = ctx.repo_root / DIR_RULES / FILE_RULES if ctx.repo_root else None
    if repo_rules and repo_rules.is_file() and core.normalized_bytes(repo_rules) != core.normalized_bytes(rules_file):
        return core.result("DOC-05", core.STATUS_WARN, "rules/AGENTS.md difiere del repo.", fix=sync_fix(ctx))
    size_kb = rules_file.stat().st_size / 1024
    return core.result("DOC-05", core.STATUS_PASS, f"rules/AGENTS.md ({size_kb:.1f} KB) dentro del presupuesto.")


_PHASE_BLOCK = r"^\s*{phase}\)\s*\n\s*SKILLS=\(([^)]*)\)\s*\n\s*AGENTS=\(([^)]*)\)"


def expected_catalog(repo_root: Optional[Path], phase: str) -> Optional[Tuple[Tuple[str, ...], Tuple[str, ...]]]:
    """(skills, agentes) que la fase instala, leídos de scripts/sh/aagy-sync.sh; None si no se puede saber."""
    if repo_root is None:
        return None
    if phase == PHASE_ALL:
        skills = tuple(sorted(p.name for p in (repo_root / DIR_SKILLS).iterdir() if p.is_dir()))
        agents = tuple(sorted(p.name for p in (repo_root / DIR_AGENTS).glob("*.md")))
        return skills, agents
    text = core.read_text(repo_root / DIR_SCRIPTS / "sh" / "aagy-sync.sh")
    match = re.search(_PHASE_BLOCK.format(phase=re.escape(phase)), text, re.MULTILINE)
    if not match:
        return None
    available_skills = {p.name for p in (repo_root / DIR_SKILLS).iterdir() if p.is_dir()}
    available_agents = {p.name for p in (repo_root / DIR_AGENTS).glob("*.md")}
    skills = tuple(s for s in match.group(1).split() if s in available_skills)
    agents = tuple(a for a in match.group(2).split() if a in available_agents)
    return skills, agents


def _installed_names(ctx: AgyContext) -> Tuple[set, set]:
    skills_dir = ctx.plugin_dir / DIR_SKILLS
    agents_dir = ctx.plugin_dir / DIR_AGENTS
    skills = {p.name for p in skills_dir.iterdir() if p.is_dir()} if skills_dir.is_dir() else set()
    agents = {p.name for p in agents_dir.glob("*.md")} if agents_dir.is_dir() else set()
    return skills, agents


def check_catalog(ctx: AgyContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-06", core.STATUS_SKIP, MSG_NO_PLUGIN)
    problems = core.frontmatter_problems(ctx.plugin_dir / DIR_SKILLS, ctx.plugin_dir / DIR_AGENTS)
    skills, agents = _installed_names(ctx)
    expected = expected_catalog(ctx.repo_root, ctx.phase)
    if expected is not None:
        missing = [s for s in expected[0] if s not in skills] + [a for a in expected[1] if a not in agents]
        if missing:
            problems.insert(0, f"Faltan {len(missing)} elementos de la fase '{ctx.phase}': {', '.join(missing[:5])}")
    summary = f"{len(skills)} skills y {len(agents)} agentes instalados (fase '{ctx.phase}')."
    if problems:
        return core.result("DOC-06", core.STATUS_WARN, summary, *problems[:8], fix=sync_fix(ctx))
    return core.result("DOC-06", core.STATUS_PASS, summary)


def _expected_tree(ctx: AgyContext) -> Dict[str, Path]:
    """Ficheros del repo que deberían estar instalados (skills/agentes presentes + reglas + manifiestos)."""
    assert ctx.repo_root is not None
    skills, agents = _installed_names(ctx)
    expected: Dict[str, Path] = {}
    for name in sorted(skills):
        for rel, src in core.list_tree(ctx.repo_root / DIR_SKILLS / name).items():
            expected[f"{DIR_SKILLS}/{name}/{rel}"] = src
    for name in sorted(agents):
        src = ctx.repo_root / DIR_AGENTS / name
        if src.is_file():
            expected[f"{DIR_AGENTS}/{name}"] = src
    for rel in (f"{DIR_RULES}/{FILE_RULES}", FILE_PLUGIN_JSON, FILE_HOOKS_JSON):
        if (ctx.repo_root / rel).is_file():
            expected[rel] = ctx.repo_root / rel
    return expected


def check_drift(ctx: AgyContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-07", core.STATUS_SKIP, MSG_NO_PLUGIN)
    if ctx.repo_root is None:
        return core.result("DOC-07", core.STATUS_SKIP, MSG_NO_REPO)
    expected = _expected_tree(ctx)
    actual = {rel: path for rel, path in core.list_tree(ctx.plugin_dir).items() if rel in expected}
    diff = core.compare_trees(expected, actual)
    if diff.clean:
        return core.result("DOC-07", core.STATUS_PASS, f"{len(expected)} ficheros idénticos al repo.")
    return core.result("DOC-07", core.STATUS_WARN, f"Deriva frente al repo: {diff.summary()}.", *diff.sample(), fix=sync_fix(ctx))


def check_entry_points(ctx: AgyContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-08", core.STATUS_SKIP, MSG_NO_PLUGIN)
    skill_md = ctx.plugin_dir / DIR_SKILLS / DOCTOR_SKILL / FILE_SKILL
    desc = core.frontmatter_value(core.read_text(skill_md), "description")
    if desc is None:
        return core.result("DOC-08", core.STATUS_WARN, f"La skill '{DOCTOR_SKILL}' no está instalada.", fix=sync_fix(ctx))
    return core.result("DOC-08", core.STATUS_PASS, f"Skill '{DOCTOR_SKILL}' instalada.")


# --------------------------------------------------------------------------- #
# DOC-09 .. DOC-11: hooks e intérpretes
# --------------------------------------------------------------------------- #
def iter_hook_commands(hooks_data: Dict[str, object]) -> List[str]:
    """Comandos de un hooks.json de Antigravity ({grupo: {evento: [{matcher, hooks: [...]}]}})."""
    commands: List[str] = []
    for group in hooks_data.values():
        if not isinstance(group, dict):
            continue
        for entries in group.values():
            for entry in entries if isinstance(entries, list) else []:
                hooks = entry.get("hooks", []) if isinstance(entry, dict) else []
                commands.extend(str(h.get("command", "")) for h in hooks if isinstance(h, dict) and h.get("command"))
    return commands


def split_command(command: str) -> Tuple[str, List[str]]:
    """(intérprete, scripts referenciados) de un comando de hook."""
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    if not tokens:
        return "", []
    scripts = [t for t in tokens[1:] if t.lower().endswith(SCRIPT_EXTENSIONS)]
    return tokens[0], scripts


def _hook_script_problem(script: str, ctx: AgyContext) -> Optional[str]:
    path = Path(script)
    if path.is_absolute():
        return None if path.is_file() else f"'{script}' no existe."
    if (ctx.plugin_dir / path).is_file():
        return None
    return f"'{script}' es relativo y no está dentro del plugin: solo funciona en workspaces que lo contengan."


def check_hook_targets(ctx: AgyContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-09", core.STATUS_SKIP, MSG_NO_PLUGIN)
    hooks_file = ctx.plugin_dir / FILE_HOOKS_JSON
    if not hooks_file.is_file():
        return core.result("DOC-09", core.STATUS_WARN, f"No hay '{FILE_HOOKS_JSON}': el plugin no tiene hooks.", fix=sync_fix(ctx))
    data = core.load_json_dict(hooks_file)
    if data is None:
        return core.result("DOC-09", core.STATUS_FAIL, f"'{FILE_HOOKS_JSON}' no es JSON válido.", fix=sync_fix(ctx))
    commands = iter_hook_commands(data)
    problems: List[str] = []
    for command in commands:
        interpreter, scripts = split_command(command)
        if interpreter and not core.which(interpreter):
            problems.append(f"Intérprete '{interpreter}' no está en el PATH ({command}).")
        problems.extend(p for p in (_hook_script_problem(s, ctx) for s in scripts) if p)
    problems = list(dict.fromkeys(problems))
    if problems:
        return core.result("DOC-09", core.STATUS_WARN, f"{len(problems)} avisos en {len(commands)} hooks.", *problems)
    return core.result("DOC-09", core.STATUS_PASS, f"{len(commands)} hooks con destinos resolubles.")


def check_interpreters(ctx: AgyContext) -> core.CheckResult:
    py_ok, py_msg = core.required_interpreter(("python", "python3"), MIN_PYTHON, "Python")
    pwsh_ok, pwsh_msg = core.required_interpreter(("pwsh",), MIN_PWSH, "PowerShell")
    lint = core.which("markdownlint")
    notes = [py_msg, pwsh_msg, f"markdownlint {'disponible' if lint else 'no instalado (opcional)'}"]
    if not py_ok or not pwsh_ok:
        failed = py_msg if not py_ok else pwsh_msg
        return core.result("DOC-10", core.STATUS_FAIL, failed, *notes)
    return core.result("DOC-10", core.STATUS_PASS, f"{py_msg}; {pwsh_msg}.", notes[2])


def _safety_script(ctx: AgyContext) -> Optional[Path]:
    for base in (ctx.plugin_dir, ctx.repo_root):
        candidate = base / DIR_SCRIPTS / "ps1" / "safety-check.ps1" if base else None
        if candidate and candidate.is_file():
            return candidate
    return None


def check_hook_smoke(ctx: AgyContext) -> core.CheckResult:
    pwsh = core.which("pwsh")
    script = _safety_script(ctx)
    if not pwsh or script is None:
        return core.result("DOC-11", core.STATUS_SKIP, "Sin pwsh o sin safety-check.ps1 accesible para la prueba.")
    payload = '{"toolCall":{"args":{"CommandLine":"%s"}}}'
    _, deny_out, _ = core.run_capture([pwsh, PWSH_NO_PROFILE, "-File", str(script)], payload % SAFETY_PROBE_DENY, 2.2)
    _, allow_out, _ = core.run_capture([pwsh, PWSH_NO_PROFILE, "-File", str(script)], payload % SAFETY_PROBE_ALLOW, 2.2)
    if '"deny"' not in deny_out:
        return core.result("DOC-11", core.STATUS_FAIL, "El safety gate no bloqueó el comando de prueba.", deny_out.strip()[:200])
    if '"allow"' not in allow_out:
        return core.result("DOC-11", core.STATUS_FAIL, "El safety gate bloqueó un comando inocuo.", allow_out.strip()[:200])
    return core.result("DOC-11", core.STATUS_PASS, "safety-check.ps1 bloquea el comando de prueba y deja pasar 'ls'.")


# --------------------------------------------------------------------------- #
# DOC-12 .. DOC-14
# --------------------------------------------------------------------------- #
def data_dir(ctx: AgyContext) -> Path:
    env_val = os.environ.get(ENV_PLUGIN_DATA, "").strip()
    return Path(env_val).expanduser() if env_val else ctx.plugin_dir / DATA_SUBDIR


def legacy_entries(ctx: AgyContext) -> List[str]:
    """Plugins del legado ecc junto a aagy, y skills/agentes instalados que ya no existen en el repo."""
    found: List[str] = []
    plugins_root = ctx.plugin_dir.parent
    if plugins_root.is_dir():
        found.extend(
            f"Plugin heredado: {p.name}" for p in sorted(plugins_root.iterdir())
            if p.is_dir() and p.name != PLUGIN_NAME and any(m in p.name.lower() for m in LEGACY_MARKERS)
        )
    if ctx.repo_root is not None and ctx.installed:
        skills, agents = _installed_names(ctx)
        found.extend(f"Skill huérfana: {s}" for s in sorted(skills) if not (ctx.repo_root / DIR_SKILLS / s).is_dir())
        found.extend(f"Agente huérfano: {a}" for a in sorted(agents) if not (ctx.repo_root / DIR_AGENTS / a).is_file())
    return found


def check_data_and_legacy(ctx: AgyContext) -> core.CheckResult:
    target = data_dir(ctx)
    problems: List[str] = []
    fix = None
    if not core.writable_dir(target):
        problems.append(f"El directorio de datos {target} no es escribible.")
    elif not target.exists():
        fix = core.FixAction(f"Crear el directorio de datos {target}", func=lambda: target.mkdir(parents=True, exist_ok=True))
        problems.append(f"El directorio de datos {target} aún no existe.")
    problems.extend(legacy_entries(ctx))
    if problems:
        return core.result("DOC-12", core.STATUS_WARN, problems[0], *problems[1:9], fix=fix)
    instincts = len(list((target / "instincts").glob("*.md")))
    return core.result("DOC-12", core.STATUS_PASS, f"Datos en {target} ({instincts} instintos globales), sin legado.")


def check_project(ctx: AgyContext) -> core.CheckResult:
    agents_dir = ctx.project_dir / ".agents"
    if not agents_dir.is_dir():
        return core.result("DOC-13", core.STATUS_SKIP, f"{ctx.project_dir} no tiene .agents/.")
    problems = core.frontmatter_problems(agents_dir / DIR_SKILLS, agents_dir / DIR_AGENTS)
    for rules_file in sorted((agents_dir / DIR_RULES).glob("*.md")) if (agents_dir / DIR_RULES).is_dir() else []:
        problems.extend(core.rules_budget_problems(rules_file))
    global_skills, _ = _installed_names(ctx) if ctx.installed else (set(), set())
    local_skills = {p.name for p in (agents_dir / DIR_SKILLS).iterdir() if p.is_dir()} if (agents_dir / DIR_SKILLS).is_dir() else set()
    shadowed = sorted(local_skills & global_skills)
    if shadowed:
        problems.append(f"Skills locales que ocultan a las globales: {', '.join(shadowed)}")
    if problems:
        return core.result("DOC-13", core.STATUS_WARN, f"{len(problems)} avisos en .agents/ del proyecto.", *problems[:8])
    return core.result("DOC-13", core.STATUS_PASS, f".agents/ del proyecto válido ({len(local_skills)} skills locales).")


def git_hooks_installed(repo_root: Path) -> bool:
    code, out, _ = core.run_capture(["git", "-C", str(repo_root), "config", "--get", "core.hooksPath"], timeout_s=3.0)
    if code == 0 and out.strip():
        return True
    return (repo_root / ".git" / "hooks" / "pre-commit").is_file()


def check_repo(ctx: AgyContext) -> core.CheckResult:
    if ctx.repo_root is None:
        return core.result("DOC-14", core.STATUS_SKIP, MSG_NO_REPO)
    if not (ctx.repo_root / "aagy-ecc").is_dir():
        return core.result("DOC-14", core.STATUS_SKIP, f"{ctx.repo_root} no es el repo aagy: la paridad solo se comprueba allí.")
    from audit_plugin_parity import audit_parity  # import tardío: solo existe en el repo
    parity = audit_parity(ctx.repo_root)
    problems = list(parity.discrepancies)
    if not git_hooks_installed(ctx.repo_root):
        problems.append("Git hooks del repo no instalados (scripts/ps1/install-git-hooks.ps1).")
    if problems:
        return core.result("DOC-14", core.STATUS_WARN, problems[0], *problems[1:6])
    return core.result("DOC-14", core.STATUS_PASS, f"Paridad PASS y git hooks instalados en {ctx.repo_root}.")


def check_agent_worktrees(ctx) -> core.CheckResult:
    """DOC-15: worktree fijo por agente (<repo>-aagy / <repo>-aagy-ecc), si el repo lo usa."""
    if ctx.repo_root is None:
        return core.result("DOC-15", core.STATUS_SKIP, MSG_NO_REPO)
    try:
        import agent_worktree  # noqa: PLC0415 - mismo directorio que el doctor
    except ImportError:
        return core.result("DOC-15", core.STATUS_SKIP, "agent_worktree.py no está instalado junto al doctor.")
    status, message, evidence = agent_worktree.doctor_findings(ctx.repo_root)
    fix = None
    if status == core.STATUS_WARN and "Falta el worktree" in message:
        fix = core.FixAction("Crear los worktrees que faltan (agent_worktree.py init)", agent_worktree.init_argv(ctx.repo_root))
    return core.result("DOC-15", status, message, *evidence, fix=fix)


def check_external_config(ctx) -> core.CheckResult:
    """DOC-17: capas de configuración externa (.governance/aagy.json y AAGY_ENV_DIR)."""
    try:
        import aagy_config  # noqa: PLC0415 - mismo directorio que el doctor
    except ImportError:
        return core.result("DOC-17", core.STATUS_SKIP, "aagy_config.py no está instalado junto al doctor.")
    status, message, evidence = aagy_config.doctor_findings(ctx.project_dir)
    return core.result("DOC-17", status, message, *evidence)


REGISTRY: Dict[str, core.CheckFunc] = {
    "DOC-01": check_runtime,
    "DOC-02": check_plugin_installed,
    "DOC-03": check_manifests,
    "DOC-04": check_version,
    "DOC-05": check_rules,
    "DOC-06": check_catalog,
    "DOC-07": check_drift,
    "DOC-08": check_entry_points,
    "DOC-09": check_hook_targets,
    "DOC-10": check_interpreters,
    "DOC-11": check_hook_smoke,
    "DOC-12": check_data_and_legacy,
    "DOC-13": check_project,
    "DOC-14": check_repo,
    "DOC-15": check_agent_worktrees,
    "DOC-17": check_external_config,
}


def parse_args(args: Optional[Sequence[str]] = None):
    parser = core.build_parser("Diagnóstico de la instalación de aagy en Antigravity / Gemini (/aagy-doctor).")
    parser.add_argument("--plugin-dir", type=Path, default=None, help="Plugin a revisar (por defecto ~/.gemini/config/plugins/aagy).")
    return parser.parse_args(args)


def main(args: Optional[Sequence[str]] = None) -> int:
    core.configure_stdout()
    parsed = parse_args(args)
    if parsed.list_checks:
        print(core.catalog_json())
        return core.EXIT_OK
    try:
        ctx = build_context(parsed)
        ids = core.select_ids(core.split_ids(parsed.only), core.split_ids(parsed.skip))
        results = core.run_checks(REGISTRY, ctx, ids, timeout_s=parsed.timeout)
        report = core.Report(TARGET_NAME, str(ctx.plugin_dir), installed_version(ctx), results)
    except Exception as exc:  # error del propio doctor, no de la instalación
        print(f"[aagy-doctor] Error interno: {exc}", file=sys.stderr)
        return core.EXIT_INTERNAL
    return core.finish(report, parsed)


if __name__ == "__main__":
    sys.exit(main())
