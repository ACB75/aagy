#!/usr/bin/env python3
"""
CI local de aagy (ci_local.py): la única fuente de las comprobaciones de calidad.

Presupuesto 0 $: las comprobaciones se ejecutan en el equipo, en el hook
``pre-push`` (scripts/py/hooks/pre-push), no en GitHub Actions. Las Actions son
opcionales, están apagadas por defecto y solo existen como plantillas en
``templates/github-actions/``; la plantilla de calidad solo llama a este script,
así que no puede divergir de lo local (audit_plugin_parity.py lo comprueba).

Pasos por defecto (cada uno se salta si su herramienta o su script no existen):
markdownlint, pytest, workspace_audit, sonar_audit, security_audit, espejo de
aagy-ecc y paridad de plugins. Un repo consumidor puede declarar los suyos en
``ci.steps`` de ``.governance/aagy.json`` (lista de comandos).

Uso::

    python ci_local.py run [--fast] [--only pytest,sonar]
    python ci_local.py list
    python ci_local.py actions status|on|off

Solo stdlib. Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
from typing import Callable, List, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import aagy_config  # noqa: E402

ENCODING = "utf-8"
TEMPLATES_REL = Path("templates") / "github-actions"
WORKFLOWS_REL = Path(".github") / "workflows"
TEMPLATE_MARKER = "# aagy-template:"
PY = sys.executable or "python"
STATUS_OK = "OK"
STATUS_FAIL = "FAIL"
STATUS_SKIP = "SKIP"


@dataclass(frozen=True)
class Step:
    name: str
    argv: Tuple[str, ...]
    fast: bool = True
    needs: Tuple[str, ...] = ()


def repo_root(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for folder in (current, *current.parents):
        if (folder / ".git").exists():
            return folder
    return current


def _script(root: Path, name: str) -> str:
    return str(root / "scripts" / "py" / name)


def _markdownlint() -> Tuple[str, ...]:
    if shutil.which("markdownlint-cli2"):
        return ("markdownlint-cli2", "doc/**/*.md", "README.md")
    if shutil.which("markdownlint"):
        return ("markdownlint", "--config", ".markdownlint.json", "doc/**/*.md", "README.md")
    return ()


def default_steps(root: Path) -> List[Step]:
    tests = [d for d in ("scripts/py/tests", "scripts/ps1/tests", "scripts/sh/tests") if (root / d).is_dir()]
    steps = [
        Step("markdownlint", _markdownlint(), needs=(".markdownlint.json",)),
        Step("pytest", (PY, "-m", "pytest", "-q", *tests), fast=False, needs=tuple(tests[:1])),
        Step("workspace_audit", (PY, _script(root, "workspace_audit.py"), "--skip-sonar", "--skip-security"),
             needs=("scripts/py/workspace_audit.py",)),
        Step("sonar", (PY, _script(root, "sonar_audit.py")), needs=("scripts/py/sonar_audit.py",)),
        Step("security", (PY, _script(root, "security_audit.py")), needs=("scripts/py/security_audit.py",)),
        Step("mirror", (PY, _script(root, "sync_aagy_ecc.py"), "--check"), needs=("scripts/py/sync_aagy_ecc.py",)),
        Step("parity", (PY, _script(root, "audit_plugin_parity.py")), needs=("scripts/py/audit_plugin_parity.py",)),
    ]
    return steps


def configured_steps(root: Path) -> List[Step]:
    """``ci.steps`` del proyecto (lista de comandos) o los pasos por defecto."""
    raw = aagy_config.get("ci.steps", None, root)
    if not isinstance(raw, list) or not raw:
        return default_steps(root)
    return [Step(f"step-{i + 1}", tuple(shlex.split(str(cmd)))) for i, cmd in enumerate(raw)]


def _skip_reason(step: Step, root: Path) -> str:
    if not step.argv:
        return "herramienta no instalada"
    missing = [n for n in step.needs if not (root / n).exists()]
    if missing:
        return f"falta {missing[0]}"
    if step.name == "pytest" and subprocess.call([PY, "-c", "import pytest"], stdout=subprocess.DEVNULL,  # noqa: S603
                                                 stderr=subprocess.DEVNULL) != 0:
        return "pytest no instalado"
    return ""


Runner = Callable[[Sequence[str], Path], int]


def _default_runner(argv: Sequence[str], cwd: Path) -> int:
    return subprocess.call(list(argv), cwd=str(cwd))  # noqa: S603 - comandos del propio repo


def run_steps(steps: Sequence[Step], root: Path, fast: bool = False, only: Sequence[str] = (),
              runner: Runner = _default_runner) -> List[Tuple[str, str, float]]:
    results: List[Tuple[str, str, float]] = []
    for step in steps:
        if (only and step.name not in only) or (fast and not step.fast):
            continue
        reason = _skip_reason(step, root)
        if reason:
            results.append((step.name, f"{STATUS_SKIP} ({reason})", 0.0))
            continue
        started = time.monotonic()
        code = runner(step.argv, root)
        results.append((step.name, STATUS_OK if code == 0 else STATUS_FAIL, time.monotonic() - started))
    return results


# --------------------------------------------------------------------------- Actions opcionales

def templates_dir(root: Path) -> Path:
    local = root / TEMPLATES_REL
    return local if local.is_dir() else _HERE.parent.parent / TEMPLATES_REL


def template_files(root: Path) -> List[Path]:
    folder = templates_dir(root)
    return sorted(folder.glob("*.yml")) if folder.is_dir() else []


def active_templates(root: Path) -> List[Path]:
    folder = root / WORKFLOWS_REL
    if not folder.is_dir():
        return []
    return sorted(p for p in folder.glob("*.yml") if TEMPLATE_MARKER in p.read_text(encoding=ENCODING, errors="replace"))


def actions_on(root: Path) -> List[Path]:
    target = root / WORKFLOWS_REL
    target.mkdir(parents=True, exist_ok=True)
    copied = []
    for template in template_files(root):
        dest = target / template.name
        if dest.exists() and TEMPLATE_MARKER not in dest.read_text(encoding=ENCODING, errors="replace"):
            continue  # nunca pisar un workflow propio del repo
        dest.write_text(template.read_text(encoding=ENCODING), encoding=ENCODING)
        copied.append(dest)
    return copied


def actions_off(root: Path) -> List[Path]:
    removed = active_templates(root)
    for path in removed:
        path.unlink()
    return removed


def _cmd_run(args: argparse.Namespace, root: Path) -> int:
    only = tuple(x for x in (args.only or "").split(",") if x)
    results = run_steps(configured_steps(root), root, args.fast, only)
    failed = [name for name, status, _ in results if status == STATUS_FAIL]
    for name, status, seconds in results:
        print(f"[ci-local] {status:<4} {name}" + (f" ({seconds:.1f} s)" if seconds else ""))
    print(f"[ci-local] {'FALLA: ' + ', '.join(failed) if failed else 'Todo en verde.'}")
    return 1 if failed else 0


def _cmd_list(_args: argparse.Namespace, root: Path) -> int:
    for step in configured_steps(root):
        print(f"{step.name}: {' '.join(step.argv) or '(sin herramienta)'}")
    return 0


def _cmd_actions(args: argparse.Namespace, root: Path) -> int:
    if args.state == "on":
        changed = actions_on(root)
        print(f"[ci-local] Actions activadas: {', '.join(p.name for p in changed) or 'ninguna'}. "
              "En un repo privado gastan minutos de pago.")
    elif args.state == "off":
        changed = actions_off(root)
        print(f"[ci-local] Actions quitadas: {', '.join(p.name for p in changed) or 'ninguna'}.")
    else:
        active = active_templates(root)
        print(f"[ci-local] Actions {'activas: ' + ', '.join(p.name for p in active) if active else 'apagadas'}.")
    return 0


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CI local de aagy (pre-push).")
    parser.add_argument("--repo", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    p_run = sub.add_parser("run", help="Ejecuta las comprobaciones.")
    p_run.add_argument("--fast", action="store_true", help="Sin la suite de tests.")
    p_run.add_argument("--only", default="", help="Pasos separados por comas.")
    sub.add_parser("list", help="Muestra los pasos.")
    p_act = sub.add_parser("actions", help="Plantillas opcionales de GitHub Actions.")
    p_act.add_argument("state", choices=("status", "on", "off"), nargs="?", default="status")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding=ENCODING)
    args = parse_args(argv)
    root = repo_root(args.repo)
    if os.environ.get("AAGY_CI_SKIP") == "1" and args.command == "run":
        print("[ci-local] AAGY_CI_SKIP=1: comprobaciones omitidas.")
        return 0
    handler = {"run": _cmd_run, "list": _cmd_list, "actions": _cmd_actions}[args.command]
    return handler(args, root)


if __name__ == "__main__":
    sys.exit(main())
