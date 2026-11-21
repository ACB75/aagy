#!/usr/bin/env python3
"""
/aagy-ecc-doctor: diagnóstico de la instalación de aagy-ecc en Claude Code (aagy_ecc_doctor.py).

Revisa el plugin aagy-ecc instalado en Claude Code (marketplace, plugin
habilitado, copia en caché, hooks y comandos), el repo aagy de origen y el
proyecto actual con el catálogo común DOC-01..DOC-14 de doctor_core.py, el
mismo que usa /aagy-doctor en Antigravity (paridad 1:1).

Fuente propia de aagy-ecc (no es un espejo). doctor_core.py, install_manifest.py
e instinct_manager.py sí son espejos generados por sync_aagy_ecc.py.

Solo lectura por defecto. Con --fix propone arreglos seguros y los aplica tras
confirmarlos (--yes para no preguntar).

Uso:
  python "${CLAUDE_PLUGIN_ROOT}/scripts/py/aagy_ecc_doctor.py"
  python "${CLAUDE_PLUGIN_ROOT}/scripts/py/aagy_ecc_doctor.py" --json
  python "${CLAUDE_PLUGIN_ROOT}/scripts/py/aagy_ecc_doctor.py" --fix
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Dict, List, Optional, Sequence, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import doctor_core as core  # noqa: E402
from install_manifest import InstallManifest, read_manifest  # noqa: E402

TARGET_NAME = "aagy-ecc (Claude Code)"
PLUGIN_NAME = "aagy-ecc"
MARKETPLACE_NAME = "aagy-ecc"
PLUGIN_KEY = f"{PLUGIN_NAME}@{MARKETPLACE_NAME}"
RUNTIME_BINARY = "claude"
DIR_PLUGIN_META = ".claude-plugin"
DIR_PLUGINS = "plugins"
KEY_VERSION = "version"
KEY_TOOL_INPUT = "tool_input"
DIR_SCRIPTS = "scripts"
DIR_SKILLS = "skills"
DIR_AGENTS = "agents"
DIR_COMMANDS = "commands"
DIR_TEMPLATE = "project-template"
FILE_PLUGIN_JSON = "plugin.json"
FILE_MARKETPLACE_JSON = "marketplace.json"
FILE_RULES = "rules/AGENTS.md"
FILE_HOOKS = "hooks/hooks.json"
FILE_KNOWN_MARKETPLACES = "known_marketplaces.json"
FILE_INSTALLED_PLUGINS = "installed_plugins.json"
FILE_SETTINGS = "settings.json"
DOCTOR_COMMAND = "aagy-ecc-doctor.md"
ENV_CLAUDE_CONFIG_DIR = "CLAUDE_CONFIG_DIR"
MIN_PYTHON = (3, 10, 0)
SAFETY_PROBE_DENY = "rm -rf / "
SAFETY_PROBE_ALLOW = "ls"
LEGACY_MARKERS = ("everything-claude-code", "ecc")
PLUGIN_ROOT_REF = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_./-]+)")
PROJECT_TEMPLATE_FILES = ("CLAUDE.md", ".claude/rules/aagy-guardrails.md")

MSG_NO_PLUGIN = "No se encontró una copia instalada de aagy-ecc que revisar."
MSG_NO_REPO = "Sin repo aagy de origen (usa --repo-root o reinstala para crear el manifiesto)."
MSG_UNKNOWN_STATE = "No se pudo leer el estado de plugins de Claude Code"


@dataclass(frozen=True)
class EccContext:
    home: Path
    claude_home: Path
    install_path: Optional[Path]
    repo_root: Optional[Path]
    project_dir: Path
    manifest: Optional[InstallManifest]
    installed_entry: Dict[str, object] = field(default_factory=dict)

    @property
    def installed(self) -> bool:
        return self.install_path is not None and self.install_path.is_dir()

    @property
    def plugins_dir(self) -> Path:
        return self.claude_home / DIR_PLUGINS

    @property
    def repo_plugin(self) -> Optional[Path]:
        return self.repo_root / PLUGIN_NAME if self.repo_root else None


# --------------------------------------------------------------------------- #
# Estado de plugins de Claude Code (formato interno: lectura tolerante)
# --------------------------------------------------------------------------- #
def default_claude_home(home: Path) -> Path:
    env_val = os.environ.get(ENV_CLAUDE_CONFIG_DIR, "").strip()
    return Path(env_val).expanduser() if env_val else home / ".claude"


def plugin_entries(installed_data: Optional[Dict[str, object]]) -> Dict[str, List[Dict[str, object]]]:
    """Normaliza installed_plugins.json (v1: {clave: {...}}, v2: {clave: [{...}]}) a {clave: [entradas]}."""
    plugins = (installed_data or {}).get(DIR_PLUGINS, {})
    normalized: Dict[str, List[Dict[str, object]]] = {}
    if not isinstance(plugins, dict):
        return normalized
    for key, value in plugins.items():
        entries = value if isinstance(value, list) else [value]
        normalized[str(key)] = [e for e in entries if isinstance(e, dict)]
    return normalized


def looks_like_plugin(path: Path) -> bool:
    data = core.load_json_dict(path / DIR_PLUGIN_META / FILE_PLUGIN_JSON) or {}
    return data.get("name") == PLUGIN_NAME


def find_install_path(claude_home: Path, entries: List[Dict[str, object]]) -> Optional[Path]:
    """installPath de installed_plugins.json, después la caché, después la carpeta de este script."""
    for entry in entries:
        raw = str(entry.get("installPath", "")).strip()
        if raw and Path(raw).expanduser().is_dir():
            return Path(raw).expanduser()
    cache = claude_home / DIR_PLUGINS / "cache" / MARKETPLACE_NAME / PLUGIN_NAME
    if cache.is_dir():
        versions = sorted((p for p in cache.iterdir() if p.is_dir()), key=lambda p: p.stat().st_mtime)
        if versions:
            return versions[-1]
        if looks_like_plugin(cache):
            return cache
    own_root = Path(_SCRIPT_DIR).parent.parent
    return own_root if looks_like_plugin(own_root) else None


def resolve_repo_root(explicit: Optional[Path], manifest: Optional[InstallManifest], project_dir: Path) -> Optional[Path]:
    if explicit is not None:
        return explicit.expanduser().resolve()
    if manifest and manifest.source_repo and core.find_repo_root(Path(manifest.source_repo)):
        return Path(manifest.source_repo).resolve()
    return core.find_repo_root(project_dir.resolve()) or core.find_repo_root(Path(_SCRIPT_DIR))


def build_context(args) -> EccContext:
    home = (args.home or Path.home()).expanduser()
    claude_home = (args.claude_home or default_claude_home(home)).expanduser()
    entries = plugin_entries(core.load_json_dict(claude_home / DIR_PLUGINS / FILE_INSTALLED_PLUGINS)).get(PLUGIN_KEY, [])
    install_path = (args.plugin_dir.expanduser() if args.plugin_dir else find_install_path(claude_home, entries))
    manifest = read_manifest(install_path) if install_path else None
    project_dir = (args.project or Path.cwd()).expanduser()
    repo_root = resolve_repo_root(args.repo_root, manifest, project_dir)
    return EccContext(home, claude_home, install_path, repo_root, project_dir, manifest, entries[0] if entries else {})


def manifest_version(plugin_root: Optional[Path]) -> str:
    if plugin_root is None:
        return ""
    data = core.load_json_dict(plugin_root / DIR_PLUGIN_META / FILE_PLUGIN_JSON) or {}
    return str(data.get(KEY_VERSION, ""))


def _run_all(commands: Sequence[Sequence[str]]) -> None:
    for argv in commands:
        proc = subprocess.run(list(argv), capture_output=True, text=True, timeout=300, check=False)
        if proc.returncode != 0:
            raise OSError((proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()[:300])


def reinstall_fix(ctx: EccContext) -> Optional[core.FixAction]:
    """Refresca el marketplace local y (re)instala aagy-ecc desde el repo."""
    claude = core.which(RUNTIME_BINARY)
    if claude is None or ctx.repo_plugin is None:
        return None
    known = core.load_json_dict(ctx.plugins_dir / FILE_KNOWN_MARKETPLACES) or {}
    marketplace_cmd = (
        [claude, "plugin", "marketplace", "update", MARKETPLACE_NAME]
        if MARKETPLACE_NAME in known
        else [claude, "plugin", "marketplace", "add", str(ctx.repo_plugin)]
    )
    install_cmd = [claude, "plugin", "install", PLUGIN_KEY]
    shown = f"{' '.join(marketplace_cmd[1:])} && {' '.join(install_cmd[1:])}"
    return core.FixAction(f"Reinstalar aagy-ecc en Claude Code (claude {shown})", func=lambda: _run_all((marketplace_cmd, install_cmd)))


def sync_fix(ctx: EccContext) -> Optional[core.FixAction]:
    if ctx.repo_root is None:
        return None
    script = ctx.repo_root / DIR_SCRIPTS / "py" / "sync_aagy_ecc.py"
    return core.FixAction("Regenerar el espejo de aagy-ecc desde el repo", (sys.executable, str(script), "--repo-root", str(ctx.repo_root)))


# --------------------------------------------------------------------------- #
# DOC-01 .. DOC-04
# --------------------------------------------------------------------------- #
def check_runtime(ctx: EccContext) -> core.CheckResult:
    found = core.which(RUNTIME_BINARY)
    if not found:
        return core.result("DOC-01", core.STATUS_FAIL, "El CLI 'claude' no está en el PATH.")
    code, out, err = core.run_capture([found, "--version"], timeout_s=4.0)
    version = core.parse_version(out or err) if code == 0 else None
    label = ".".join(map(str, version)) if version else "versión desconocida"
    return core.result("DOC-01", core.STATUS_PASS, f"Claude Code {label} ({found})")


def check_plugin_installed(ctx: EccContext) -> core.CheckResult:
    known = core.load_json_dict(ctx.plugins_dir / FILE_KNOWN_MARKETPLACES)
    installed = core.load_json_dict(ctx.plugins_dir / FILE_INSTALLED_PLUGINS)
    if known is None and installed is None:
        if ctx.installed:
            return core.result("DOC-02", core.STATUS_WARN, f"{MSG_UNKNOWN_STATE}; hay una copia en {ctx.install_path}.")
        return core.result("DOC-02", core.STATUS_FAIL, f"{MSG_UNKNOWN_STATE} ni hay copia instalada.", fix=reinstall_fix(ctx))
    problems: List[str] = []
    if MARKETPLACE_NAME not in (known or {}):
        problems.append(f"Marketplace '{MARKETPLACE_NAME}' no registrado.")
    if PLUGIN_KEY not in plugin_entries(installed):
        problems.append(f"Plugin '{PLUGIN_KEY}' no instalado.")
    settings = core.load_json_dict(ctx.claude_home / FILE_SETTINGS) or {}
    enabled = settings.get("enabledPlugins", {})
    if isinstance(enabled, dict) and enabled.get(PLUGIN_KEY) is False:
        problems.append(f"Plugin '{PLUGIN_KEY}' deshabilitado en settings.json (claude plugin enable {PLUGIN_KEY}).")
    if problems:
        return core.result("DOC-02", core.STATUS_FAIL, problems[0], *problems[1:], fix=reinstall_fix(ctx))
    return core.result("DOC-02", core.STATUS_PASS, f"'{PLUGIN_KEY}' instalado y habilitado ({ctx.install_path}).")


def check_manifests(ctx: EccContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-03", core.STATUS_SKIP, MSG_NO_PLUGIN)
    meta = ctx.install_path / DIR_PLUGIN_META
    plugin = core.load_json_dict(meta / FILE_PLUGIN_JSON)
    if plugin is None or plugin.get("name") != PLUGIN_NAME:
        return core.result("DOC-03", core.STATUS_FAIL, f"'{FILE_PLUGIN_JSON}' falta, es inválido o no se llama '{PLUGIN_NAME}'.", fix=reinstall_fix(ctx))
    market_file = meta / FILE_MARKETPLACE_JSON
    if not market_file.is_file() and ctx.repo_plugin:
        market_file = ctx.repo_plugin / DIR_PLUGIN_META / FILE_MARKETPLACE_JSON
    market = core.load_json_dict(market_file)
    if market is None:
        return core.result("DOC-03", core.STATUS_WARN, f"No se pudo leer '{FILE_MARKETPLACE_JSON}'.")
    published = {str(p.get("name")): str(p.get(KEY_VERSION, "")) for p in market.get(DIR_PLUGINS, []) if isinstance(p, dict)}
    if PLUGIN_NAME not in published:
        return core.result("DOC-03", core.STATUS_FAIL, f"'{FILE_MARKETPLACE_JSON}' no publica '{PLUGIN_NAME}'.")
    if published[PLUGIN_NAME] and published[PLUGIN_NAME] != plugin.get(KEY_VERSION):
        return core.result("DOC-03", core.STATUS_WARN, f"marketplace.json dice {published[PLUGIN_NAME]} y plugin.json {plugin.get('version')}.")
    return core.result("DOC-03", core.STATUS_PASS, "plugin.json y marketplace.json válidos y coherentes.")


def _root_version(repo_root: Optional[Path]) -> str:
    data = core.load_json_dict(repo_root / FILE_PLUGIN_JSON) if repo_root else None
    return str((data or {}).get(KEY_VERSION, ""))


def check_version(ctx: EccContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-04", core.STATUS_SKIP, MSG_NO_PLUGIN)
    problems: List[str] = []
    if ctx.manifest is None:
        problems.append(f"Falta {core.MANIFEST_FILE} en la copia instalada (instala con install.ps1 / install.sh).")
    current = manifest_version(ctx.install_path)
    repo_version = manifest_version(ctx.repo_plugin)
    if repo_version and current != repo_version:
        problems.append(f"Versión instalada '{current}' distinta de la del repo '{repo_version}'.")
    root_version = _root_version(ctx.repo_root)
    if repo_version and root_version and repo_version != root_version:
        problems.append(f"aagy-ecc está en '{repo_version}' y aagy en '{root_version}'.")
    if problems:
        return core.result("DOC-04", core.STATUS_WARN, problems[0], *problems[1:], fix=reinstall_fix(ctx))
    commit = ctx.manifest.commit[:7] if ctx.manifest and ctx.manifest.commit else "?"
    return core.result("DOC-04", core.STATUS_PASS, f"Versión {current}, commit {commit}.")


# --------------------------------------------------------------------------- #
# DOC-05 .. DOC-08
# --------------------------------------------------------------------------- #
def check_rules(ctx: EccContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-05", core.STATUS_SKIP, MSG_NO_PLUGIN)
    rules_file = ctx.install_path / FILE_RULES
    problems = core.rules_budget_problems(rules_file)
    if problems:
        return core.result("DOC-05", core.STATUS_FAIL, problems[0], *problems[1:], fix=sync_fix(ctx) or reinstall_fix(ctx))
    repo_rules = ctx.repo_root / FILE_RULES if ctx.repo_root else None
    if repo_rules and repo_rules.is_file() and core.normalized_bytes(repo_rules) != core.normalized_bytes(rules_file):
        return core.result("DOC-05", core.STATUS_WARN, "Las reglas que inyecta SessionStart difieren del repo.", fix=reinstall_fix(ctx))
    size_kb = rules_file.stat().st_size / 1024
    return core.result("DOC-05", core.STATUS_PASS, f"SessionStart inyecta rules/AGENTS.md ({size_kb:.1f} KB) dentro del presupuesto.")


def _count(path: Path, dirs: bool) -> int:
    if not path.is_dir():
        return 0
    return sum(1 for p in path.iterdir() if p.is_dir()) if dirs else sum(1 for p in path.glob("*.md") if p.name != "README.md")


def check_catalog(ctx: EccContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-06", core.STATUS_SKIP, MSG_NO_PLUGIN)
    problems = core.frontmatter_problems(ctx.install_path / DIR_SKILLS, ctx.install_path / DIR_AGENTS)
    skills = _count(ctx.install_path / DIR_SKILLS, dirs=True)
    agents = _count(ctx.install_path / DIR_AGENTS, dirs=False)
    if ctx.repo_plugin is not None:
        want_skills = _count(ctx.repo_plugin / DIR_SKILLS, dirs=True)
        want_agents = _count(ctx.repo_plugin / DIR_AGENTS, dirs=False)
        if (skills, agents) != (want_skills, want_agents):
            problems.insert(0, f"El repo tiene {want_skills} skills y {want_agents} agentes.")
    summary = f"{skills} skills y {agents} agentes instalados."
    if problems:
        return core.result("DOC-06", core.STATUS_WARN, summary, *problems[:8], fix=reinstall_fix(ctx))
    return core.result("DOC-06", core.STATUS_PASS, summary)


def check_drift(ctx: EccContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-07", core.STATUS_SKIP, MSG_NO_PLUGIN)
    if ctx.repo_plugin is None:
        return core.result("DOC-07", core.STATUS_SKIP, MSG_NO_REPO)
    if ctx.install_path.resolve() == ctx.repo_plugin.resolve():
        return core.result("DOC-07", core.STATUS_PASS, "Claude Code usa directamente aagy-ecc/ del repo.")
    diff = core.compare_trees(core.list_tree(ctx.repo_plugin), core.list_tree(ctx.install_path))
    if diff.clean:
        return core.result("DOC-07", core.STATUS_PASS, "La copia en caché es idéntica a aagy-ecc/ del repo.")
    return core.result("DOC-07", core.STATUS_WARN, f"La copia instalada no refleja el repo: {diff.summary()}.", *diff.sample(), fix=reinstall_fix(ctx))


def _command_names(plugin_root: Path) -> List[str]:
    commands_dir = plugin_root / DIR_COMMANDS
    return sorted(p.stem for p in commands_dir.glob("*.md")) if commands_dir.is_dir() else []


def _other_plugin_roots(ctx: EccContext) -> Dict[str, Path]:
    roots: Dict[str, Path] = {}
    installed = plugin_entries(core.load_json_dict(ctx.plugins_dir / FILE_INSTALLED_PLUGINS))
    for key, entries in installed.items():
        if key == PLUGIN_KEY:
            continue
        for entry in entries:
            raw = str(entry.get("installPath", "")).strip()
            if raw and Path(raw).expanduser().is_dir():
                roots[key] = Path(raw).expanduser()
                break
    return roots


def check_entry_points(ctx: EccContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-08", core.STATUS_SKIP, MSG_NO_PLUGIN)
    commands_dir = ctx.install_path / DIR_COMMANDS
    problems = [
        f"Comando '/{p.stem}' sin description."
        for p in sorted(commands_dir.glob("*.md")) if not core.frontmatter_value(core.read_text(p), "description")
    ] if commands_dir.is_dir() else ["No hay carpeta commands/."]
    if not (commands_dir / DOCTOR_COMMAND).is_file():
        problems.insert(0, f"Falta el comando /{DOCTOR_COMMAND[:-3]}.")
    own = set(_command_names(ctx.install_path))
    for key, root in _other_plugin_roots(ctx).items():
        clashes = sorted(own & set(_command_names(root)))
        if clashes:
            problems.append(f"Comandos que también define '{key}': {', '.join(clashes[:5])}")
    if problems:
        return core.result("DOC-08", core.STATUS_WARN, f"{len(problems)} avisos en {len(own)} comandos.", *problems[:8], fix=reinstall_fix(ctx))
    return core.result("DOC-08", core.STATUS_PASS, f"{len(own)} comandos slash válidos, sin colisiones.")


# --------------------------------------------------------------------------- #
# DOC-09 .. DOC-11: hooks e intérpretes
# --------------------------------------------------------------------------- #
def check_hook_targets(ctx: EccContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-09", core.STATUS_SKIP, MSG_NO_PLUGIN)
    hooks_file = ctx.install_path / FILE_HOOKS
    data = core.load_json_dict(hooks_file)
    if data is None:
        return core.result("DOC-09", core.STATUS_FAIL, f"'{FILE_HOOKS}' falta o no es JSON válido.", fix=reinstall_fix(ctx))
    targets = sorted(set(PLUGIN_ROOT_REF.findall(json.dumps(data))))
    missing = [rel for rel in targets if not (ctx.install_path / rel).is_file()]
    if missing:
        return core.result("DOC-09", core.STATUS_FAIL, f"{len(missing)} hooks apuntan a scripts inexistentes.", *missing, fix=reinstall_fix(ctx))
    return core.result("DOC-09", core.STATUS_PASS, f"{len(targets)} destinos de hooks existen dentro del plugin.")


def hook_python() -> Optional[str]:
    """El Python que usan los hooks: `command -v python || command -v python3`."""
    for name in ("python", "python3"):
        found = core.which(name)
        if found:
            return found
    return None


def check_interpreters(ctx: EccContext) -> core.CheckResult:
    bash = core.which("bash")
    first = hook_python()
    notes = [f"bash: {bash or 'no encontrado'}", f"markdownlint {'disponible' if core.which('markdownlint') else 'no instalado (opcional)'}"]
    if not bash:
        return core.result("DOC-10", core.STATUS_FAIL, "Los hooks necesitan bash (en Windows, Git Bash en el PATH).", *notes)
    if first and core.is_windows_store_stub(first):
        return core.result("DOC-10", core.STATUS_FAIL, f"'{first}' es el alias de la Microsoft Store, no un Python real.", *notes)
    ok, message = core.required_interpreter(("python", "python3"), MIN_PYTHON, "Python")
    if not ok:
        return core.result("DOC-10", core.STATUS_FAIL, message, *notes)
    return core.result("DOC-10", core.STATUS_PASS, f"{message}; bash disponible.", notes[1])


def _run_hook(python: str, script: Path, payload: Dict[str, object], cwd: Path) -> Tuple[int, str]:
    code, out, err = core.run_capture([python, str(script)], json.dumps(payload), timeout_s=1.5, cwd=cwd)
    return code, out or err


def _smoke_problems(python: str, hooks_dir: Path, tmp: Path) -> List[str]:
    problems: List[str] = []
    code, out = _run_hook(python, hooks_dir / "session_start_rules.py", {"hook_event_name": "SessionStart"}, tmp)
    if code != 0 or "additionalContext" not in out:
        problems.append("session_start_rules.py no devolvió las reglas.")
    code, out = _run_hook(python, hooks_dir / "safety_check.py", {KEY_TOOL_INPUT: {"command": SAFETY_PROBE_DENY}}, tmp)
    if code != 0 or '"deny"' not in out:
        problems.append("safety_check.py no bloqueó el comando de prueba.")
    code, out = _run_hook(python, hooks_dir / "safety_check.py", {KEY_TOOL_INPUT: {"command": SAFETY_PROBE_ALLOW}}, tmp)
    if code != 0 or '"deny"' in out:
        problems.append("safety_check.py bloqueó un comando inocuo.")
    probe = tmp / "probe.txt"
    probe.write_text("x\n", encoding=core.ENCODING)
    code, _ = _run_hook(python, hooks_dir / "post_write_lint.py", {KEY_TOOL_INPUT: {"file_path": str(probe)}}, tmp)
    if code != 0:
        problems.append("post_write_lint.py terminó con error.")
    return problems


def check_hook_smoke(ctx: EccContext) -> core.CheckResult:
    if not ctx.installed:
        return core.result("DOC-11", core.STATUS_SKIP, MSG_NO_PLUGIN)
    python = hook_python()
    if python is None or core.is_windows_store_stub(python):
        return core.result("DOC-11", core.STATUS_SKIP, "Sin un Python real en el PATH para ejecutar los hooks.")
    with tempfile.TemporaryDirectory(prefix="aagy-ecc-doctor-") as tmp:
        problems = _smoke_problems(python, ctx.install_path / DIR_SCRIPTS / "hooks", Path(tmp))
    if problems:
        return core.result("DOC-11", core.STATUS_FAIL, problems[0], *problems[1:], fix=reinstall_fix(ctx))
    return core.result("DOC-11", core.STATUS_PASS, "SessionStart, safety gate y linter responden como se espera.")


# --------------------------------------------------------------------------- #
# DOC-12 .. DOC-14
# --------------------------------------------------------------------------- #
def data_dir() -> Path:
    """El mismo directorio que usa self_improve.py (instinct_manager.resolve_plugin_data_dir)."""
    from instinct_manager import resolve_plugin_data_dir  # espejo en aagy-ecc/scripts/py
    return resolve_plugin_data_dir()


def legacy_entries(ctx: EccContext) -> List[str]:
    known = core.load_json_dict(ctx.plugins_dir / FILE_KNOWN_MARKETPLACES) or {}
    installed = plugin_entries(core.load_json_dict(ctx.plugins_dir / FILE_INSTALLED_PLUGINS))
    found = [f"Plugin heredado instalado: {k}" for k in sorted(installed) if k != PLUGIN_KEY and _is_legacy(k)]
    found += [f"Marketplace heredado: {k}" for k in sorted(known) if k != MARKETPLACE_NAME and _is_legacy(k)]
    return found


def _is_legacy(name: str) -> bool:
    lowered = name.lower()
    return PLUGIN_NAME not in lowered and any(marker in lowered for marker in LEGACY_MARKERS)


def check_data_and_legacy(ctx: EccContext) -> core.CheckResult:
    target = data_dir()
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


def check_project(ctx: EccContext) -> core.CheckResult:
    present = [rel for rel in PROJECT_TEMPLATE_FILES if (ctx.project_dir / rel).is_file()]
    if not present:
        return core.result("DOC-13", core.STATUS_SKIP, f"{ctx.project_dir} no usa la plantilla de aagy-ecc.")
    template_root = (ctx.install_path or ctx.repo_plugin or Path()) / DIR_TEMPLATE
    if not template_root.is_dir():
        return core.result("DOC-13", core.STATUS_SKIP, "No se encontró project-template/ para comparar.")
    outdated = [
        rel for rel in present
        if (template_root / rel).is_file()
        and core.normalized_bytes(template_root / rel) != core.normalized_bytes(ctx.project_dir / rel)
    ]
    if outdated:
        return core.result("DOC-13", core.STATUS_WARN, "La plantilla del proyecto difiere de project-template/.", *outdated)
    return core.result("DOC-13", core.STATUS_PASS, f"Plantilla del proyecto al día ({', '.join(present)}).")


def _import_repo_module(repo_root: Path, name: str):
    scripts_dir = str(repo_root / DIR_SCRIPTS / "py")
    if scripts_dir not in sys.path:
        sys.path.append(scripts_dir)
    return __import__(name)


def check_repo(ctx: EccContext) -> core.CheckResult:
    if ctx.repo_root is None:
        return core.result("DOC-14", core.STATUS_SKIP, MSG_NO_REPO)
    report = _import_repo_module(ctx.repo_root, "sync_aagy_ecc").compare(ctx.repo_root)
    parity = _import_repo_module(ctx.repo_root, "audit_plugin_parity").audit_parity(ctx.repo_root)
    if not report.in_sync:
        detail = f"{len(report.missing)} faltan, {len(report.changed)} distintos, {len(report.extra)} sobrantes"
        return core.result("DOC-14", core.STATUS_WARN, f"Espejo de aagy-ecc desincronizado ({detail}).", *parity.discrepancies[:5], fix=sync_fix(ctx))
    if parity.discrepancies:
        return core.result("DOC-14", core.STATUS_WARN, parity.discrepancies[0], *parity.discrepancies[1:6])
    return core.result("DOC-14", core.STATUS_PASS, f"Espejo IN_SYNC y paridad PASS en {ctx.repo_root}.")


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
}


def parse_args(args: Optional[Sequence[str]] = None):
    parser = core.build_parser("Diagnóstico de la instalación de aagy-ecc en Claude Code (/aagy-ecc-doctor).")
    parser.add_argument("--claude-home", type=Path, default=None, help="Configuración de Claude Code (por defecto ~/.claude o CLAUDE_CONFIG_DIR).")
    parser.add_argument("--plugin-dir", type=Path, default=None, help="Copia instalada de aagy-ecc a revisar (por defecto, la de installed_plugins.json).")
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
        plugin_dir = str(ctx.install_path) if ctx.install_path else ""
        report = core.Report(TARGET_NAME, plugin_dir, manifest_version(ctx.install_path), results)
    except Exception as exc:  # error del propio doctor, no de la instalación
        print(f"[aagy-ecc-doctor] Error interno: {exc}", file=sys.stderr)
        return core.EXIT_INTERNAL
    return core.finish(report, parsed)


if __name__ == "__main__":
    sys.exit(main())
