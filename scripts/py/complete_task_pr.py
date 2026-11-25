#!/usr/bin/env python3
"""
Fase 4 (complete_task_pr.py): revisión previa, gate de calidad, commit, push y PR.

Motor único de los dos plugins. Se lanza con ``aagy complete-task-pr`` (lanzador
``scripts/ps1/aagy.ps1`` o ``scripts/sh/aagy.sh``) y ``aagy-ecc`` lo trae en
``scripts/py/`` (sync_aagy_ecc.py), así que
funciona en cualquier repo con solo los scripts del plugin (CA-06).

1. Valida la rama (``<tipo>/<proyecto>/<nombre>``) y detecta la issue
   (``--issue``, rama ``gh-<N>`` o ``.governance/active-issue.json``).
2. Muestra la revisión previa; ``--review-only`` para aquí.
3. Gate: ``ci_local.py run`` y los ``checks`` que declare el repo en
   ``.governance/docs-map.json`` (RF-15), sin que el plugin los conozca.
4. Archiva las tareas ``[x]`` y, en ramas ``fix/*``, genera el postmortem.
5. Commit, push y PR con las secciones comunes y ``Closes #N``.
6. Sin auto-merge: solo fusiona con ``--merge`` (una persona lo pide) y después
   recicla el worktree del agente o vuelve a la rama destino.

Uso::

    python complete_task_pr.py --review-only [--issue N]
    python complete_task_pr.py --yes --title "[feat]-[aagy]: ..." [--body ...] [--merge]
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
from typing import Callable, List, Optional, Sequence, Tuple

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from validate_branch import validate_branch_name  # noqa: E402

ENCODING = "utf-8"
PY = sys.executable or "python"
ACTIVE_ISSUE_REL = Path(".governance") / "active-issue.json"
DOCS_MAP_REL = Path(".governance") / "docs-map.json"
CHECKS_KEY = "checks"
WORKTREE_ROLES = ("agy", "claude")
EXIT_DIRTY_WORKTREE = 3
_ISSUE_IN_BRANCH = re.compile(r"(?:gh|issue)-(\d+)(?:-|$)")
_COMPLETED = re.compile(r"^[\s*\-]*\[x\]", re.MULTILINE | re.IGNORECASE)
_CLOSES = r"\b(closes|fixes|resolves)\s+#{n}\b"
_TYPED_TITLE = re.compile(r"^\[[a-z]+\]-\[[^\]]+\]:\s")

Runner = Callable[[Sequence[str], Path], Tuple[int, str]]


def default_runner(argv: Sequence[str], cwd: Path) -> Tuple[int, str]:
    """Ejecuta un comando y devuelve (código, stdout); la salida de error va a la consola."""
    try:
        proc = subprocess.run(list(argv), cwd=str(cwd), stdout=subprocess.PIPE, text=True,  # noqa: S603
                              encoding=ENCODING, errors="replace", check=False)
    except OSError as exc:
        return 127, str(exc)
    return proc.returncode, (proc.stdout or "").strip()


def passthrough_runner(argv: Sequence[str], cwd: Path) -> Tuple[int, str]:
    """Como default_runner, pero con la salida en la consola (gates largos)."""
    try:
        return subprocess.call(list(argv), cwd=str(cwd)), ""  # noqa: S603
    except OSError as exc:
        return 127, str(exc)


@dataclass
class Plan:
    branch: str
    target: str
    title: str
    body: str
    issue: int = 0
    completed_todos: bool = False
    changes: List[str] = field(default_factory=list)


class PhaseError(Exception):
    """Error que para la fase 4 con un mensaje para el usuario."""


def _script(name: str) -> str:
    return str(_HERE / name)


def current_branch(root: Path, run: Runner) -> str:
    code, out = run(["git", "branch", "--show-current"], root)
    branch = out.strip() if code == 0 else ""
    branch = branch or os.environ.get("GITHUB_HEAD_REF", "") or os.environ.get("GITHUB_REF_NAME", "")
    if not branch:
        raise PhaseError("HEAD desacoplado: no se puede determinar la rama de trabajo.")
    return branch


def detect_issue(branch: str, root: Path, explicit: int = 0) -> int:
    if explicit > 0:
        return explicit
    match = _ISSUE_IN_BRANCH.search(branch)
    if match:
        return int(match.group(1))
    try:
        data = json.loads((root / ACTIVE_ISSUE_REL).read_text(encoding=ENCODING))
        return int(data.get("issue") or 0)
    except (OSError, ValueError, TypeError, AttributeError):
        return 0


def default_body(branch: str, target: str) -> str:
    """Cuerpo con las secciones comunes de issues, PR y TODO (#93)."""
    return (
        f"## 1. Motivación\n\n- Tarea terminada en la rama `{branch}`.\n\n"
        "## 2. Issues\n\n"
        "## 3. Criterios de aceptación\n\n- [x] `python scripts/py/ci_local.py run` en verde.\n\n"
        "## 4. Paridad aagy ↔ aagy-ecc\n\n- [ ] Igual en los dos plugins o asimetría declarada.\n\n"
        "## 5. Artefactos\n\n- Ver los ficheros de la PR.\n\n"
        f"## 6. Rollback\n\n- `git revert` del squash en `{target}`.\n"
    )


def with_closes(body: str, issue: int) -> str:
    if issue <= 0 or re.search(_CLOSES.format(n=issue), body, re.IGNORECASE):
        return body
    if "## 2. Issues" in body:
        return body.replace("## 2. Issues\n", f"## 2. Issues\n\n- Closes #{issue}\n", 1)
    return f"{body.rstrip()}\n\n## 2. Issues\n\n- Closes #{issue}\n"


def _todo_path(root: Path) -> Optional[Path]:
    try:
        from docs_map import resolve_doc_path  # noqa: PLC0415

        return resolve_doc_path(root, "todo")
    except (ImportError, ValueError, KeyError):
        return None


def build_plan(root: Path, run: Runner, title: str = "", body: str = "", target: str = "main",
               issue: int = 0) -> Plan:
    branch = current_branch(root, run)
    valid, _reason = validate_branch_name(branch)
    if not valid:
        raise PhaseError(f"Gobernanza de ramas rechazada para '{branch}' (usa <tipo>/<proyecto>/<nombre>).")
    if not title:
        code, last = run(["git", "log", "-1", "--pretty=format:%s"], root)
        title = last if code == 0 and _TYPED_TITLE.match(last) else ""
    if not title:
        raise PhaseError("Falta --title con el formato [type]-[projects]: <título>.")
    number = detect_issue(branch, root, issue)
    todo = _todo_path(root)
    completed = bool(todo and todo.is_file() and _COMPLETED.search(todo.read_text(encoding=ENCODING)))
    _, status = run(["git", "status", "--short"], root)
    return Plan(branch=branch, target=target, title=title, issue=number, completed_todos=completed,
                body=with_closes(body or default_body(branch, target), number),
                changes=[line for line in status.splitlines() if line.strip()][:15])


def review_lines(plan: Plan) -> List[str]:
    lines = [
        "=======================================================",
        "       AVISO DE REVISIÓN MANUAL PREVIA A EJECUCIÓN     ",
        "=======================================================",
        f"Rama origen:  {plan.branch}",
        f"Rama destino: {plan.target}",
        f"Título:       {plan.title}",
    ]
    if plan.issue:
        lines.append(f"Issue:        #{plan.issue}")
    if plan.completed_todos:
        lines.append("Tareas [x]:   se archivarán antes del commit")
    lines += ["", "Cambios:", *(plan.changes or ["(sin cambios locales)"]), "", "Cuerpo:", plan.body]
    return lines


def declared_checks(root: Path) -> List[List[str]]:
    """``checks`` de docs-map.json: comandos de pre-merge propios del repo (RF-15)."""
    try:
        data = json.loads((root / DOCS_MAP_REL).read_text(encoding=ENCODING))
    except (OSError, ValueError):
        return []
    raw = data.get(CHECKS_KEY) if isinstance(data, dict) else None
    return [shlex.split(str(cmd)) for cmd in raw if str(cmd).strip()] if isinstance(raw, list) else []


def quality_gate(root: Path, run: Runner) -> None:
    commands = [[PY, _script("ci_local.py"), "--repo", str(root), "run"], *declared_checks(root)]
    for argv in commands:
        print(f"[+] {' '.join(argv)}")
        code, _ = run(argv, root)
        if code != 0:
            raise PhaseError(f"El gate de calidad falló en: {' '.join(argv)}")


def prepare_tree(plan: Plan, root: Path, run: Runner) -> None:
    if plan.completed_todos:
        run([PY, _script("archive_todo.py"), "--repo-root", str(root), "--all-completed"], root)
    if plan.branch.startswith("fix/"):
        run([PY, _script("generate_postmortem.py"), "--repo-root", str(root), "--branch", plan.branch], root)
    _, dirty = run(["git", "status", "--porcelain"], root)
    if dirty:
        run(["git", "add", "-A"], root)
        code, _ = run(["git", "commit", "-m", plan.title, "-m", plan.body], root)
        if code != 0:
            raise PhaseError("git commit falló (revisa los hooks de pre-commit).")


def _issue_meta_args(plan: Plan, root: Path, run: Runner) -> List[str]:
    if plan.issue <= 0:
        return []
    code, raw = run(["gh", "issue", "view", str(plan.issue), "--json", "labels,milestone,projectItems"], root)
    try:
        meta = json.loads(raw) if code == 0 else {}
    except ValueError:
        meta = {}
    args: List[str] = []
    for label in meta.get("labels") or []:
        args += ["--label", str(label.get("name"))]
    if (meta.get("milestone") or {}).get("title"):
        args += ["--milestone", str(meta["milestone"]["title"])]
    for item in meta.get("projectItems") or []:
        args += ["--project", str(item.get("title"))]
    return args


def publish(plan: Plan, root: Path, run: Runner) -> str:
    """Push y PR (crea la PR si no existe). Devuelve su número."""
    if run(["git", "push", "-u", "origin", "HEAD"], root)[0] != 0:
        raise PhaseError("git push falló.")
    lookup = ["gh", "pr", "list", "--head", plan.branch, "--base", plan.target, "--json", "number", "--jq", ".[0].number"]
    number = run(lookup, root)[1]
    if number:
        return number
    base = ["gh", "pr", "create", "--base", plan.target, "--head", plan.branch, "--title", plan.title,
            "--body", plan.body, "--assignee", "@me"]
    if run(base + _issue_meta_args(plan, root, run), root)[0] != 0 and run(base, root)[0] != 0:
        raise PhaseError("gh pr create falló.")
    number = run(lookup, root)[1]
    if not number:
        raise PhaseError("No encuentro la PR recién creada.")
    return number


def merge_and_sync(plan: Plan, number: str, root: Path, run: Runner) -> None:
    """Solo con --merge: squash, borrar la rama y dejar el checkout al día."""
    if run(["gh", "pr", "merge", number, "--squash", "--delete-branch"], root)[0] != 0:
        raise PhaseError(f"No se pudo fusionar la PR #{number} (¿checks o revisiones pendientes?).")
    (root / ACTIVE_ISSUE_REL).unlink(missing_ok=True)
    role = run([PY, _script("agent_worktree.py"), "where"], root)[1].strip()
    if role in WORKTREE_ROLES:
        code, _ = run([PY, _script("agent_worktree.py"), "recycle", "--agent", role, "--if-merged", "--wait", "120"], root)
        if code == EXIT_DIRTY_WORKTREE:
            print("[!] El worktree tiene trabajo sin guardar: no se ha reciclado.")
        return
    if run(["git", "checkout", plan.target], root)[0] != 0:
        raise PhaseError(f"No se pudo volver a '{plan.target}': hay cambios locales. La PR ya está fusionada.")
    run(["git", "pull", "origin", plan.target], root)
    run(["git", "branch", "-D", plan.branch], root)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fase 4: revisión, gate, commit, push y PR (sin auto-merge).")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--title", default="")
    parser.add_argument("--body", default="")
    parser.add_argument("--target", default="main")
    parser.add_argument("--issue", type=int, default=0)
    parser.add_argument("--review-only", action="store_true")
    parser.add_argument("--yes", action="store_true", help="No pedir confirmación.")
    parser.add_argument("--merge", action="store_true", help="Fusionar la PR (solo si una persona lo pide).")
    parser.add_argument("--skip-gate", action="store_true", help="No ejecutar el gate (ya pasó en pre-push).")
    return parser.parse_args(argv)


def run_phase(args: argparse.Namespace, run: Runner = default_runner, gate_run: Runner = passthrough_runner,
              ask: Callable[[str], str] = input) -> int:
    root = args.repo.resolve()
    plan = build_plan(root, run, args.title, args.body, args.target, args.issue)
    print("\n".join(review_lines(plan)))
    if args.review_only:
        print("[OK] Modo --review-only: revisión completada sin cambios.")
        return 0
    if not args.yes and ask("¿Commit, push y PR? (s/N): ").strip().lower() not in ("s", "y", "si", "sí", "yes"):
        print("[CANCELADO] Operación cancelada por el usuario.")
        return 0
    if not args.skip_gate:
        quality_gate(root, gate_run)
    prepare_tree(plan, root, run)
    number = publish(plan, root, run)
    print(f"[OK] PR #{number} lista para revisión.")
    if args.merge:
        merge_and_sync(plan, number, root, run)
        print(f"[OK] PR #{number} fusionada en '{plan.target}'.")
    else:
        print("[i] Sin auto-merge: la PR la fusiona una persona (o vuelve a ejecutar con --merge si te lo pide).")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding=ENCODING)
    try:
        return run_phase(parse_args(argv))
    except PhaseError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
