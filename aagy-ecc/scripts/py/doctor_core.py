#!/usr/bin/env python3
"""
Núcleo común de los doctors de aagy (doctor_core.py).

Define el catálogo único de checks DOC-01..DOC-17 que comparten
/aagy-doctor (Antigravity) y /aagy-ecc-doctor (Claude Code), el modelo de
resultados, el runner con límite de tiempo por check, la salida humana y
JSON, los códigos de salida y el plan de arreglos (--fix) con confirmación.

Cada doctor registra exactamente una implementación por ID del catálogo:
si falta o sobra alguno, el runner falla. Así los dos doctors son
independientes pero no pueden divergir en qué comprueban (paridad 1:1).

Python 3 stdlib pura. Se espeja en aagy-ecc/scripts/py/ mediante
sync_aagy_ecc.py; se edita aquí, nunca en el espejo.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_FAIL = "FAIL"
STATUS_SKIP = "SKIP"
STATUSES: Tuple[str, ...] = (STATUS_PASS, STATUS_WARN, STATUS_FAIL, STATUS_SKIP)

SCOPE_INSTALL = "instalación"
SCOPE_REPO = "repo"
SCOPE_PROJECT = "proyecto"

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_INTERNAL = 2

DEFAULT_CHECK_TIMEOUT_S = 5.0
REPO_CHECK_TIMEOUT_S = 30.0
MANIFEST_FILE = ".aagy-install.json"
MAX_SKILL_DESC = 140
MAX_AGENT_DESC = 120
MAX_RULE_FILE_BYTES = 24_000
MAX_RULES_TOKENS = 16_000
CHARS_PER_TOKEN = 3.8
SKILL_FILE = "SKILL.md"
ENCODING = "utf-8"

# .agents/ guarda instintos y observaciones locales de self-improve: dato del workspace, no del plugin.
IGNORED_TREE_NAMES = frozenset({"__pycache__", ".pytest_cache", ".DS_Store", "Thumbs.db", ".agents", MANIFEST_FILE})
IGNORED_TREE_SUFFIXES = (".pyc", ".pyo")
FRONTMATTER_REGEX = re.compile(r"^---\s*\r?\n(.*?)\r?\n---", re.DOTALL)

_COLORS = {
    STATUS_PASS: "\033[92m",
    STATUS_WARN: "\033[93m",
    STATUS_FAIL: "\033[91m",
    STATUS_SKIP: "\033[90m",
}
_RESET = "\033[0m"


@dataclass(frozen=True)
class CheckSpec:
    """Entrada del catálogo común: igual en los dos doctors.

    ``min_timeout_s`` sube el límite de los checks que recorren el repo entero (en
    Windows, leer todos los ficheros tarda bastante más que en Linux).
    """
    check_id: str
    name: str
    scope: str
    min_timeout_s: float = 0.0


DOC_CATALOG: Tuple[CheckSpec, ...] = (
    CheckSpec("DOC-01", "Runtime del harness", SCOPE_INSTALL),
    CheckSpec("DOC-02", "Plugin instalado", SCOPE_INSTALL),
    CheckSpec("DOC-03", "Manifiestos", SCOPE_INSTALL),
    CheckSpec("DOC-04", "Versión y manifiesto de instalación", SCOPE_INSTALL),
    CheckSpec("DOC-05", "Reglas Tier 1", SCOPE_INSTALL),
    CheckSpec("DOC-06", "Skills y agentes", SCOPE_INSTALL),
    CheckSpec("DOC-07", "Deriva frente al repo", SCOPE_INSTALL),
    CheckSpec("DOC-08", "Comandos y puntos de entrada", SCOPE_INSTALL),
    CheckSpec("DOC-09", "Destinos de los hooks", SCOPE_INSTALL),
    CheckSpec("DOC-10", "Intérpretes", SCOPE_INSTALL),
    CheckSpec("DOC-11", "Smoke test de hooks", SCOPE_INSTALL),
    CheckSpec("DOC-12", "Datos y legado", SCOPE_INSTALL),
    CheckSpec("DOC-13", "Proyecto", SCOPE_PROJECT),
    CheckSpec("DOC-14", "Repo", SCOPE_REPO, min_timeout_s=REPO_CHECK_TIMEOUT_S),
    CheckSpec("DOC-15", "Worktrees de agente", SCOPE_REPO),
    CheckSpec("DOC-16", "Modelo local", SCOPE_PROJECT),
    CheckSpec("DOC-17", "Configuración externa", SCOPE_PROJECT),
)
CATALOG_IDS: Tuple[str, ...] = tuple(spec.check_id for spec in DOC_CATALOG)
_CATALOG_BY_ID: Dict[str, CheckSpec] = {spec.check_id: spec for spec in DOC_CATALOG}


@dataclass(frozen=True)
class FixAction:
    """
    Arreglo propuesto por un check. El check solo lo describe: el núcleo lo
    muestra, pide confirmación y lo ejecuta. Un check nunca escribe en disco.
    """
    description: str
    argv: Tuple[str, ...] = ()
    func: Optional[Callable[[], None]] = field(default=None, compare=False, hash=False)

    @property
    def key(self) -> Tuple[str, Tuple[str, ...]]:
        return self.description, self.argv

    def display(self) -> str:
        if self.argv:
            return " ".join(_quote(arg) for arg in self.argv)
        return self.description


@dataclass(frozen=True)
class CheckResult:
    """Resultado de un check."""
    check_id: str
    status: str
    message: str
    evidence: Tuple[str, ...] = ()
    fix: Optional[FixAction] = None

    def to_dict(self) -> Dict[str, object]:
        spec = _CATALOG_BY_ID.get(self.check_id)
        return {
            "id": self.check_id,
            "name": spec.name if spec else "",
            "scope": spec.scope if spec else "",
            "status": self.status,
            "message": self.message,
            "evidence": list(self.evidence),
            "fix": self.fix.display() if self.fix else None,
        }


@dataclass(frozen=True)
class Report:
    """Informe completo de un doctor."""
    target: str
    plugin_dir: str
    version: str
    results: Tuple[CheckResult, ...]

    def summary(self) -> Dict[str, int]:
        counts = {status: 0 for status in STATUSES}
        for result in self.results:
            counts[result.status] = counts.get(result.status, 0) + 1
        return counts

    def to_dict(self) -> Dict[str, object]:
        return {
            "target": self.target,
            "plugin_dir": self.plugin_dir,
            "version": self.version,
            "summary": self.summary(),
            "checks": [result.to_dict() for result in self.results],
        }


CheckFunc = Callable[[object], CheckResult]


def result(check_id: str, status: str, message: str, *evidence: str, fix: Optional[FixAction] = None) -> CheckResult:
    """Atajo para construir un CheckResult con evidencias variables."""
    return CheckResult(check_id, status, message, tuple(e for e in evidence if e), fix)


def validate_registry(registry: Dict[str, CheckFunc]) -> None:
    """Exige que el doctor implemente exactamente los IDs del catálogo (paridad 1:1)."""
    missing = [cid for cid in CATALOG_IDS if cid not in registry]
    extra = sorted(cid for cid in registry if cid not in _CATALOG_BY_ID)
    if missing or extra:
        raise ValueError(f"Registro de checks incompleto: faltan {missing}, sobran {extra}")


def _run_one(check_id: str, func: CheckFunc, ctx: object, timeout_s: float) -> CheckResult:
    box: Dict[str, CheckResult] = {}

    def target() -> None:
        try:
            box["r"] = func(ctx)
        except Exception as exc:  # un check roto no debe tumbar al doctor
            box["r"] = result(check_id, STATUS_FAIL, f"Error interno del check: {exc.__class__.__name__}: {exc}")

    worker = threading.Thread(target=target, name=f"doctor-{check_id}", daemon=True)
    worker.start()
    worker.join(timeout_s)
    if worker.is_alive() or "r" not in box:
        return result(check_id, STATUS_FAIL, f"Timeout: el check superó {timeout_s:g} s.")
    outcome = box["r"]
    if outcome.check_id != check_id or outcome.status not in STATUSES:
        return result(check_id, STATUS_FAIL, "El check devolvió un resultado inválido.")
    return outcome


def select_ids(only: Sequence[str] = (), skip: Sequence[str] = ()) -> Tuple[str, ...]:
    """Filtra el catálogo con --only / --skip, conservando su orden."""
    wanted = {cid.strip().upper() for cid in only if cid.strip()}
    unwanted = {cid.strip().upper() for cid in skip if cid.strip()}
    return tuple(cid for cid in CATALOG_IDS if (not wanted or cid in wanted) and cid not in unwanted)


def run_checks(
    registry: Dict[str, CheckFunc],
    ctx: object,
    ids: Optional[Sequence[str]] = None,
    timeout_s: float = DEFAULT_CHECK_TIMEOUT_S,
) -> Tuple[CheckResult, ...]:
    """Ejecuta los checks seleccionados en el orden del catálogo, cada uno con su límite de tiempo."""
    validate_registry(registry)
    selected = CATALOG_IDS if ids is None else tuple(ids)
    return tuple(_run_one(cid, registry[cid], ctx, check_timeout(cid, timeout_s)) for cid in selected)


def check_timeout(check_id: str, timeout_s: float = DEFAULT_CHECK_TIMEOUT_S) -> float:
    """Límite de un check: el pedido, o el mínimo de su entrada del catálogo si es mayor."""
    spec = _CATALOG_BY_ID.get(check_id)
    return max(timeout_s, spec.min_timeout_s if spec else 0.0)


def exit_code(report: Report, strict: bool = False) -> int:
    """0 sin FAIL (WARN permitidos salvo --strict), 1 con algún FAIL."""
    counts = report.summary()
    if counts[STATUS_FAIL] or (strict and counts[STATUS_WARN]):
        return EXIT_FAILED
    return EXIT_OK


def _paint(text: str, status: str, color: bool) -> str:
    return f"{_COLORS[status]}{text}{_RESET}" if color else text


def render_text(report: Report, color: bool = False, verbose: bool = False) -> str:
    """Salida legible en español: una línea por check y un resumen final."""
    lines = [
        "=" * 63,
        f" DOCTOR {report.target}".upper(),
        "=" * 63,
        f"Plugin:  {report.plugin_dir or 'N/A'}",
        f"Versión: {report.version or 'N/A'}",
        "",
    ]
    for res in report.results:
        name = _CATALOG_BY_ID[res.check_id].name if res.check_id in _CATALOG_BY_ID else ""
        tag = _paint(f"[{res.status}]", res.status, color)
        lines.append(f"{tag} {res.check_id} {name}: {res.message}")
        if verbose or res.status in (STATUS_WARN, STATUS_FAIL):
            lines.extend(f"         · {item}" for item in res.evidence)
        if res.fix and res.status in (STATUS_WARN, STATUS_FAIL):
            lines.append(f"         → Arreglo: {res.fix.display()}")
    counts = report.summary()
    lines.append("")
    lines.append(" · ".join(f"{counts[s]} {s}" for s in STATUSES) + f"  ({len(report.results)} checks)")
    return "\n".join(lines)


def render_json(report: Report) -> str:
    return json.dumps(report.to_dict(), indent=2, ensure_ascii=False)


def catalog_json() -> str:
    """Catálogo para la auditoría de paridad (--list-checks --json)."""
    return json.dumps(
        [{"id": s.check_id, "name": s.name, "scope": s.scope} for s in DOC_CATALOG],
        indent=2,
        ensure_ascii=False,
    )


# --------------------------------------------------------------------------- #
# Arreglos (--fix)
# --------------------------------------------------------------------------- #
def collect_fixes(results: Iterable[CheckResult]) -> List[FixAction]:
    """Arreglos de los WARN/FAIL, sin duplicados y en orden de aparición."""
    seen = set()
    fixes: List[FixAction] = []
    for res in results:
        if res.fix is None or res.status not in (STATUS_WARN, STATUS_FAIL):
            continue
        if res.fix.key in seen:
            continue
        seen.add(res.fix.key)
        fixes.append(res.fix)
    return fixes


def _execute_fix(fix: FixAction, timeout_s: float) -> Tuple[bool, str]:
    if fix.func is not None:
        try:
            fix.func()
            return True, "hecho"
        except OSError as exc:
            return False, str(exc)
    if not fix.argv:
        return False, "sin acción ejecutable"
    try:
        proc = subprocess.run(list(fix.argv), capture_output=True, text=True, timeout=timeout_s, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    if proc.returncode == 0:
        return True, "hecho"
    return False, (proc.stderr or proc.stdout or f"exit {proc.returncode}").strip()[:300]


def apply_fixes(
    fixes: Sequence[FixAction],
    assume_yes: bool,
    ask: Callable[[str], str] = input,
    out: Callable[[str], None] = print,
    timeout_s: float = 300.0,
) -> int:
    """
    Muestra el plan y aplica cada arreglo tras confirmarlo (o todos con --yes).
    Sin TTY y sin --yes no aplica nada. Devuelve cuántos arreglos fallaron.
    """
    if not fixes:
        out("No hay arreglos que aplicar.")
        return 0
    out("Plan de arreglos:")
    for idx, fix in enumerate(fixes, 1):
        out(f"  {idx}. {fix.description}: {fix.display()}")
    interactive = sys.stdin is not None and sys.stdin.isatty()
    if not assume_yes and not interactive:
        out("Sin terminal interactiva: no se aplica nada. Repite con --fix --yes para aplicarlos.")
        return 0
    failures = 0
    for fix in fixes:
        if not assume_yes:
            answer = ask(f"¿Aplicar «{fix.description}»? [s/N] ").strip().lower()
            if answer not in ("s", "si", "sí", "y", "yes"):
                out("  omitido")
                continue
        ok, detail = _execute_fix(fix, timeout_s)
        out(f"  {'OK' if ok else 'ERROR'}: {fix.description} ({detail})")
        failures += 0 if ok else 1
    return failures


# --------------------------------------------------------------------------- #
# Utilidades compartidas por los dos doctors
# --------------------------------------------------------------------------- #
def load_json(path: Path) -> Optional[object]:
    """JSON parseado, o None si no existe o es inválido."""
    try:
        return json.loads(path.read_text(encoding=ENCODING))
    except (OSError, ValueError):
        return None


def load_json_dict(path: Path) -> Optional[Dict[str, object]]:
    data = load_json(path)
    return data if isinstance(data, dict) else None


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding=ENCODING, errors="replace")
    except OSError:
        return ""


def frontmatter_value(content: str, key: str) -> Optional[str]:
    """Valor de una clave del frontmatter YAML simple, o None."""
    match = FRONTMATTER_REGEX.match(content)
    if not match:
        return None
    found = re.search(rf"^{re.escape(key)}:\s*(.+)$", match.group(1), re.MULTILINE)
    return found.group(1).strip().strip("'\"") if found else None


def normalized_bytes(path: Path) -> bytes:
    """Contenido con CRLF normalizado a LF."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def list_tree(base: Path) -> Dict[str, Path]:
    """Ficheros de un árbol (rutas relativas POSIX), sin cachés ni el manifiesto de instalación."""
    if not base.is_dir():
        return {}
    files: Dict[str, Path] = {}
    for path in sorted(base.rglob("*")):
        rel = path.relative_to(base)
        ignored = any(part in IGNORED_TREE_NAMES for part in rel.parts) or path.suffix in IGNORED_TREE_SUFFIXES
        if path.is_file() and not ignored:
            files[rel.as_posix()] = path
    return files


@dataclass(frozen=True)
class TreeDiff:
    missing: Tuple[str, ...]
    changed: Tuple[str, ...]
    extra: Tuple[str, ...]

    @property
    def clean(self) -> bool:
        return not (self.missing or self.changed or self.extra)

    def summary(self) -> str:
        return f"{len(self.missing)} faltan, {len(self.changed)} distintos, {len(self.extra)} sobrantes"

    def sample(self, limit: int = 5) -> Tuple[str, ...]:
        items = [f"falta {p}" for p in self.missing] + [f"distinto {p}" for p in self.changed]
        items += [f"sobra {p}" for p in self.extra]
        return tuple(items[:limit])


def compare_trees(expected: Dict[str, Path], actual: Dict[str, Path]) -> TreeDiff:
    """Compara dos mapas {ruta relativa: fichero} normalizando finales de línea."""
    missing = [rel for rel in expected if rel not in actual]
    changed = [
        rel for rel, src in expected.items()
        if rel in actual and normalized_bytes(src) != normalized_bytes(actual[rel])
    ]
    extra = [rel for rel in actual if rel not in expected]
    return TreeDiff(tuple(sorted(missing)), tuple(sorted(changed)), tuple(sorted(extra)))


def rules_budget_problems(rules_file: Path) -> List[str]:
    """Problemas de presupuesto de un fichero de reglas (vacío, > 24 KB, > 16.000 tokens)."""
    text = read_text(rules_file)
    if not text.strip():
        return [f"'{rules_file.name}' falta o está vacío."]
    problems: List[str] = []
    size = len(text.encode(ENCODING))
    if size > MAX_RULE_FILE_BYTES:
        problems.append(f"'{rules_file.name}' ocupa {size} bytes (> {MAX_RULE_FILE_BYTES}).")
    tokens = int(len(text) / CHARS_PER_TOKEN) + 1
    if tokens > MAX_RULES_TOKENS:
        problems.append(f"'{rules_file.name}' estima {tokens} tokens (> {MAX_RULES_TOKENS}).")
    return problems


def frontmatter_problems(skills_dir: Path, agents_dir: Path) -> List[str]:
    """Skills sin SKILL.md o con descripción ausente/larga; agentes con descripción ausente/larga."""
    problems: List[str] = []
    for skill in sorted(p for p in skills_dir.iterdir() if p.is_dir()) if skills_dir.is_dir() else []:
        desc = frontmatter_value(read_text(skill / SKILL_FILE), "description")
        if desc is None:
            problems.append(f"Skill '{skill.name}' sin SKILL.md o sin description.")
        elif len(desc) > MAX_SKILL_DESC:
            problems.append(f"Skill '{skill.name}': description de {len(desc)} caracteres (> {MAX_SKILL_DESC}).")
    for agent in sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []:
        if agent.name == "README.md":
            continue
        desc = frontmatter_value(read_text(agent), "description")
        if not desc:
            problems.append(f"Agente '{agent.name}' sin description.")
        elif len(desc) > MAX_AGENT_DESC:
            problems.append(f"Agente '{agent.name}': description de {len(desc)} caracteres (> {MAX_AGENT_DESC}).")
    return problems


def which(name: str) -> Optional[str]:
    return shutil.which(name)


def run_capture(argv: Sequence[str], stdin: str = "", timeout_s: float = 4.0, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Ejecuta un comando con límite de tiempo. Devuelve (exit, stdout, stderr); -1 si no se pudo ejecutar."""
    try:
        proc = subprocess.run(
            list(argv),
            input=stdin,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
            cwd=str(cwd) if cwd else None,
            encoding=ENCODING,
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return -1, "", str(exc)
    return proc.returncode, proc.stdout or "", proc.stderr or ""


_VERSION_REGEX = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")


def parse_version(text: str) -> Optional[Tuple[int, int, int]]:
    match = _VERSION_REGEX.search(text or "")
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3) or 0)


def interpreter_version(binary: str, flag: str = "--version") -> Optional[Tuple[int, int, int]]:
    code, out, err = run_capture([binary, flag], timeout_s=4.0)
    return parse_version(out or err) if code == 0 else None


def required_interpreter(names: Sequence[str], minimum: Tuple[int, int, int], label: str) -> Tuple[bool, str]:
    for name in names:
        found = which(name)
        if not found or is_windows_store_stub(found):
            continue
        version = interpreter_version(found)
        if version and version >= minimum:
            return True, f"{label} {'.'.join(map(str, version))} ({found})"
        return False, f"{label} {'.'.join(map(str, version)) if version else '?'} en {found}, se necesita ≥ {'.'.join(map(str, minimum))}"
    return False, f"{label} no está en el PATH"


def is_windows_store_alias(path: str) -> bool:
    """True si la ruta apunta a WindowsApps (posible alias de la Microsoft Store)."""
    return "windowsapps" in path.replace("\\", "/").lower()


def is_windows_store_stub(path: str) -> bool:
    """True si apunta a WindowsApps y no responde como un intérprete real."""
    return is_windows_store_alias(path) and interpreter_version(path) is None


def writable_dir(path: Path) -> bool:
    """True si el directorio existe y se puede escribir, o si se podría crear."""
    probe = path
    while not probe.exists():
        if probe.parent == probe:
            return False
        probe = probe.parent
    return probe.is_dir() and os.access(probe, os.W_OK)


def find_repo_root(start: Path) -> Optional[Path]:
    """Sube desde start hasta encontrar el repo aagy (plugin.json raíz + aagy-ecc/)."""
    for directory in (start, *start.parents):
        manifest = load_json_dict(directory / "plugin.json")
        if manifest and manifest.get("name") == "aagy" and (directory / "aagy-ecc").is_dir():
            return directory
    return None


def _quote(arg: str) -> str:
    return f'"{arg}"' if (" " in arg or not arg) else arg


# --------------------------------------------------------------------------- #
# CLI común
# --------------------------------------------------------------------------- #
def build_parser(description: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--json", action="store_true", help="Salida JSON estructurada.")
    parser.add_argument("--strict", action="store_true", help="Un WARN cuenta como fallo (exit 1).")
    parser.add_argument("--only", default="", help="IDs a ejecutar, separados por comas (DOC-01,DOC-05).")
    parser.add_argument("--skip", default="", help="IDs a omitir, separados por comas.")
    parser.add_argument("--fix", action="store_true", help="Aplica los arreglos seguros tras confirmarlos.")
    parser.add_argument("--yes", action="store_true", help="Con --fix, aplica sin preguntar.")
    parser.add_argument("--verbose", action="store_true", help="Muestra también la evidencia de los PASS.")
    parser.add_argument("--list-checks", action="store_true", help="Imprime el catálogo de checks y sale.")
    parser.add_argument("--repo-root", type=Path, default=None, help="Raíz del repo aagy (activa los checks de repo).")
    parser.add_argument("--project", type=Path, default=None, help="Proyecto a revisar (por defecto, el directorio actual).")
    parser.add_argument("--home", type=Path, default=None, help="Directorio home alternativo (pruebas).")
    parser.add_argument("--timeout", type=float, default=DEFAULT_CHECK_TIMEOUT_S, help="Límite por check en segundos.")
    return parser


def split_ids(raw: str) -> List[str]:
    return [part for part in (raw or "").split(",") if part.strip()]


def configure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding=ENCODING, errors="replace")
        except (AttributeError, ValueError):
            return


def finish(report: Report, args: argparse.Namespace) -> int:
    """Imprime el informe, aplica --fix si procede y devuelve el código de salida."""
    if args.json:
        print(render_json(report))
    else:
        print(render_text(report, color=sys.stdout.isatty(), verbose=args.verbose))
    if args.fix:
        out = (lambda line: print(line, file=sys.stderr)) if args.json else print
        failures = apply_fixes(collect_fixes(report.results), assume_yes=args.yes, out=out)
        if failures:
            return EXIT_FAILED
    return exit_code(report, strict=args.strict)
