#!/usr/bin/env python3
"""
Un git worktree fijo por agente (Claude Code / aagy-ecc y Antigravity / aagy).

Para un clon principal `<padre>/<repo>` (el de Master) se mantienen dos worktrees
hermanos del mismo clon:

- `<padre>/<repo>-aagy`      → Antigravity (agy)
- `<padre>/<repo>-aagy-ecc`  → Claude Code (claude)

Comandos:

- `init`     crea los worktrees que falten, desacoplados en `origin/<base>`.
- `where`    dice si la carpeta actual es el principal, el worktree de un agente u otra.
- `status`   estado de los tres checkouts.
- `recycle`  tras fusionarse la PR: limpia el worktree en sitio (o lo recrea si no se
             puede), copia la configuración (.env) del principal, regenera las
             dependencias y actualiza el principal con --ff-only si está limpio en main.
             Nunca borra trabajo sin guardar: si lo hay, bloquea y avisa.
- `guard`    hook PreToolUse: impide que un agente escriba fuera de su worktree.
- `notice`   aviso de arranque de sesión.

El marcador `$(git common dir)/aagy-worktrees.json` activa la guarda; sin él, el repo
sigue como siempre. Ver doc/04-operations/runbooks/MANUAL_agent_worktrees.md.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from agent_worktree_base import (  # noqa: E402
    AGENT_LABELS,
    AGENT_SUFFIXES,
    DEFAULT_BASE,
    ENCODING,
    EXIT_BLOCKED,
    EXIT_ERROR,
    EXIT_NO_GH,
    EXIT_NOT_MERGED,
    EXIT_OK,
    G_DETACH,
    G_REV_LIST,
    G_REV_PARSE,
    G_WORKTREE,
    REMOTE,
    ROLE_MAIN,
    Layout,
    WorktreeError,
    base_branch,
    current_branch,
    find_layout,
    git,
    git_out,
    is_within,
    load_config,
    norm,
    registered_worktrees,
    resolve_agent,
    run,
    short_head,
    status_lines,
    utc_iso,
    worktree_lock,
)
from agent_worktree_provision import config_files_to_copy, install_plan, provision  # noqa: E402,F401

__all__ = [
    "EXIT_BLOCKED", "EXIT_ERROR", "EXIT_NO_GH", "EXIT_NOT_MERGED", "EXIT_OK", "DEFAULT_BASE",
    "Layout", "WorktreeError", "config_files_to_copy", "find_layout", "install_plan", "load_config",
    "op_init", "op_recycle", "op_status", "doctor_findings", "main",
]

GH_TIMEOUT = 20
MERGED = "MERGED"
CMD_RECYCLE = "recycle"
OPT_AGENT = "--agent"
OPT_JSON = "--json"
OPT_NO_INSTALL = "--no-install"
FLAG = "store_true"
AGENT_CHOICES = sorted(AGENT_SUFFIXES)


# --------------------------------------------------------------------------- init / status


def _origin(base: str) -> str:
    return f"{REMOTE}/{base}"


def _fetch(layout: Layout, base: str) -> None:
    res = git(layout.main, "fetch", "--prune", REMOTE, base)
    if not res.ok:
        raise WorktreeError(f"git fetch {REMOTE} {base} falló: {res.err}")


def _add_worktree(layout: Layout, path: Path, base: str) -> None:
    res = git(layout.main, G_WORKTREE, "add", G_DETACH, str(path), _origin(base))
    if not res.ok:
        raise WorktreeError(f"No se pudo crear {path}: {res.err}")


def write_marker(layout: Layout, base: str) -> None:
    data = {"version": 1, "base": base, "updated": utc_iso(), **layout.to_dict()}
    data.pop("active", None)
    layout.marker.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding=ENCODING)


def op_init(layout: Layout, install: bool = True, fetch: bool = True) -> List[str]:
    config = load_config(layout.main)
    base = base_branch(layout.main)
    messages: List[str] = []
    with worktree_lock(layout):
        if fetch:
            _fetch(layout, base)
        registered = registered_worktrees(layout)
        for agent, path in layout.worktrees.items():
            label = AGENT_LABELS[agent]
            if norm(path) in registered:
                messages.append(f"{label}: {path} ya existe.")
                continue
            if path.exists():
                raise WorktreeError(f"{path} existe pero no es un worktree de {layout.main}. Muévelo o bórralo.")
            _add_worktree(layout, path, base)
            messages.append(f"{label}: creado {path} en {_origin(base)}.")
            messages.extend(provision(layout.main, path, config, install))
        write_marker(layout, base)
    messages.append(f"Activado. El checkout principal {layout.main} queda para Master.")
    return messages


def worktree_state(path: Path) -> Dict[str, Any]:
    if not path.is_dir():
        return {"exists": False}
    return {"exists": True, "branch": current_branch(path), "head": short_head(path), "dirty": len(status_lines(path))}


def op_status(layout: Layout) -> Dict[str, Any]:
    data: Dict[str, Any] = {"active": layout.active, ROLE_MAIN: {"path": str(layout.main), **worktree_state(layout.main)}}
    for agent, path in layout.worktrees.items():
        data[agent] = {"path": str(path), **worktree_state(path)}
    return data


# --------------------------------------------------------------------------- recycle


@dataclass
class PrInfo:
    state: str
    head_oid: Optional[str]
    number: Optional[int]

    @property
    def label(self) -> str:
        return f"PR #{self.number} {self.state.lower()}"


def pr_info(cwd: Path, branch: str) -> Optional[PrInfo]:
    """PR más reciente de la rama, o None si no hay PR. Sin gh lanza EXIT_NO_GH."""
    if shutil.which("gh") is None:
        raise WorktreeError("Falta gh (GitHub CLI): sin él no se puede saber si la PR está fusionada.", EXIT_NO_GH)
    res = run(
        ["gh", "pr", "list", "--head", branch, "--state", "all", "--limit", "1", OPT_JSON, "state,headRefOid,number"],
        cwd, GH_TIMEOUT,
    )
    if not res.ok:
        raise WorktreeError(f"gh no pudo consultar la PR de {branch}: {res.err}", EXIT_NO_GH)
    try:
        items = json.loads(res.out or "[]")
    except ValueError:
        items = []
    if not items:
        return None
    item = items[0]
    return PrInfo(state=str(item.get("state") or "").upper(), head_oid=item.get("headRefOid"), number=item.get("number"))


def wait_for_merge(cwd: Path, branch: str, seconds: int) -> Optional[PrInfo]:
    deadline = time.monotonic() + max(0, seconds)
    pr = pr_info(cwd, branch)
    while pr is not None and pr.state == "OPEN" and time.monotonic() < deadline:
        time.sleep(5)
        pr = pr_info(cwd, branch)
    return pr


def _count(path: Path, rev_range: str) -> str:
    return git_out(path, G_REV_LIST, "--count", rev_range) or "0"


def _unpushed(path: Path, branch: str, pr: Optional[PrInfo], base: str) -> List[str]:
    if pr is not None and pr.state == MERGED:
        if not pr.head_oid or not git(path, "cat-file", "-e", f"{pr.head_oid}^{{commit}}").ok:
            return [f"No encuentro en local el último commit de la PR #{pr.number}; no puedo asegurar que no haya trabajo nuevo."]
        count = _count(path, f"{pr.head_oid}..HEAD")
        return [f"{count} commit(s) posteriores a la PR #{pr.number} sin publicar."] if count != "0" else []
    upstream = git_out(path, G_REV_PARSE, "--abbrev-ref", "--symbolic-full-name", "@{u}")
    count = _count(path, f"{'@{u}' if upstream else _origin(base)}..HEAD")
    return [f"{count} commit(s) sin push en {branch}."] if count != "0" else []


def _detached_orphans(path: Path, base: str) -> List[str]:
    if git(path, "merge-base", "--is-ancestor", "HEAD", _origin(base)).ok:
        return []
    if git_out(path, "branch", "-r", "--contains", "HEAD"):
        return []
    return ["HEAD desacoplado con commits que no están en ninguna rama remota."]


def unsaved_work(path: Path, branch: Optional[str], pr: Optional[PrInfo], base: str) -> List[str]:
    """Lista legible de lo que se perdería al reciclar. Vacía = seguro."""
    problems: List[str] = []
    lines = status_lines(path)
    if lines:
        problems.append(f"{len(lines)} fichero(s) sin commit: " + ", ".join(line[3:] for line in lines[:5]))
    if not branch:
        return problems + _detached_orphans(path, base)
    stashes = (git_out(path, "stash", "list") or "").splitlines()
    mine = [s for s in stashes if f"on {branch}:" in s.lower()]
    if mine:
        problems.append(f"{len(mine)} stash(es) de la rama {branch}.")
    return problems + _unpushed(path, branch, pr, base)


def _clean_in_place(path: Path, base: str) -> Tuple[bool, str]:
    for args in (("switch", G_DETACH, _origin(base)), ("reset", "--hard", _origin(base))):
        res = git(path, *args)
        if not res.ok:
            return False, res.err
    res = git(path, "clean", "-ffdx")
    failed = [line for line in (res.err + "\n" + res.out).splitlines() if "failed to remove" in line.lower()]
    if not res.ok or failed:
        return False, "\n".join(failed) or res.err
    return True, ""


def _recreate(layout: Layout, path: Path, base: str) -> None:
    git(layout.main, G_WORKTREE, "remove", "--force", str(path))
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    if path.exists():
        raise WorktreeError(
            f"No se puede borrar {path}: algún programa (IDE, terminal, servidor de desarrollo) lo tiene abierto. "
            "Ciérralo y repite el reciclado."
        )
    git(layout.main, G_WORKTREE, "prune")
    _add_worktree(layout, path, base)


def update_main(layout: Layout, base: str) -> str:
    branch = current_branch(layout.main)
    if branch != base:
        return f"AVISO: tu checkout principal está en '{branch or 'HEAD desacoplado'}', no en {base}; no lo toco."
    if status_lines(layout.main, "--untracked-files=no"):
        return "AVISO: tu checkout principal tiene cambios sin commit; no lo actualizo. Haz git pull cuando quieras."
    res = git(layout.main, "merge", "--ff-only", _origin(base))
    if not res.ok:
        detail = res.err.splitlines()[-1] if res.err else "?"
        return f"AVISO: tu checkout principal no avanza en fast-forward ({detail}); no lo toco."
    return f"Checkout principal actualizado a {_origin(base)} ({short_head(layout.main) or '?'})."


def _release_backlog(layout: Layout, path: Path, branch: Optional[str], agent: str) -> Optional[str]:
    try:
        import backlog  # noqa: PLC0415 - dependencia opcional del mismo directorio
    except ImportError:
        return None
    repo = backlog.locate_repo(layout.main)
    key = backlog.K_AGENT_WORKTREE
    touched: List[str] = []
    try:
        with backlog.state_lock(repo):
            state = backlog.load_state(repo)
            for tid, entry in state.get("tasks", {}).items():
                same_wt = bool(entry.get(key)) and is_within(Path(entry[key]), path)
                same_branch = bool(branch) and entry.get("branch") == branch and entry.get("owner") == agent
                if same_wt or same_branch:
                    entry.pop(key, None)
                    backlog.record(entry, agent, CMD_RECYCLE, "worktree reciclado tras el merge")
                    touched.append(tid)
            if touched:
                backlog.save_state(repo, state)
    except Exception as exc:  # noqa: BLE001 - el backlog no debe impedir el reciclado
        return f"AVISO: no se pudo actualizar el backlog: {exc}"
    return f"Backlog: liberado el worktree de {', '.join(touched)}." if touched else None


def _check_merged(path: Path, branch: str, if_merged: bool, wait_s: int) -> Tuple[Optional[PrInfo], Optional[List[str]]]:
    """(PR, None) si se puede seguir; (None, mensajes) si hay que parar sin error."""
    pr = wait_for_merge(path, branch, wait_s) if wait_s else pr_info(path, branch)
    if pr is not None and pr.state == MERGED:
        return pr, None
    state = "sin PR" if pr is None else pr.label
    if not if_merged:
        raise WorktreeError(f"La rama {branch} no está fusionada ({state}). No se recicla.", EXIT_NOT_MERGED)
    later = f"La rama {branch} aún no está fusionada ({state}); se reciclará en el próximo claim o inicio de sesión."
    return None, [later] if wait_s else []


def _reset_worktree(layout: Layout, path: Path, branch: Optional[str], base: str, hard_recreate: bool) -> List[str]:
    messages: List[str] = []
    ok, detail = (False, "") if hard_recreate else _clean_in_place(path, base)
    if not ok:
        if not hard_recreate:
            first = detail.splitlines()[0] if detail else "?"
            messages.append(f"La limpieza en sitio no fue posible ({first}); recreo el worktree.")
        _recreate(layout, path, base)
    messages.append(f"{path} limpio en {_origin(base)}.")
    if branch:
        git(layout.main, "branch", "-D", branch)
        messages.append(f"Rama local {branch} borrada.")
    git(layout.main, G_WORKTREE, "prune")
    return messages


def _is_clean_at_base(path: Path, branch: Optional[str], base: str) -> bool:
    head = git_out(path, G_REV_PARSE, "HEAD")
    return branch is None and head is not None and head == git_out(path, G_REV_PARSE, _origin(base))


def op_recycle(
    layout: Layout,
    agent: str,
    if_merged: bool = False,
    hard_recreate: bool = False,
    install: bool = True,
    wait_s: int = 0,
) -> List[str]:
    config = load_config(layout.main)
    base = base_branch(layout.main)
    path = layout.worktrees[agent]
    if norm(path) not in registered_worktrees(layout):
        raise WorktreeError(f"{path} no es un worktree de {layout.main}. Ejecuta init.")
    branch = current_branch(path)
    pr: Optional[PrInfo] = None
    if branch:
        pr, stop = _check_merged(path, branch, if_merged, wait_s)
        if stop is not None:
            return stop
    with worktree_lock(layout):
        os.chdir(str(layout.main))  # en Windows no se puede borrar la carpeta en la que está el proceso
        _fetch(layout, base)
        problems = unsaved_work(path, branch, pr, base)
        if problems:
            raise WorktreeError(
                f"No reciclo {path}: hay trabajo sin guardar.\n- " + "\n- ".join(problems)
                + "\nHaz commit y push (o descártalo tú) y repite.",
                EXIT_BLOCKED,
            )
        if _is_clean_at_base(path, branch, base) and not hard_recreate:
            messages = [f"{path} ya está limpio en {_origin(base)}."]
        else:
            messages = _reset_worktree(layout, path, branch, base, hard_recreate)
            messages.extend(provision(layout.main, path, config, install))
        note = _release_backlog(layout, path, branch, agent)
        messages.extend([note] if note else [])
        messages.append(update_main(layout, base))
    return messages


# --------------------------------------------------------------------------- doctor (DOC-15)


def _layout_problems(layout: Layout, base: str) -> List[str]:
    registered = registered_worktrees(layout)
    problems: List[str] = []
    for agent, path in layout.worktrees.items():
        entry = registered.get(norm(path))
        if entry is None:
            problems.append(f"Falta el worktree de {AGENT_LABELS[agent]}: {path}.")
        elif entry.get("branch") == f"refs/heads/{base}":
            problems.append(f"El worktree de {AGENT_LABELS[agent]} tiene {base} en checkout; debe estar desacoplado o en una rama de tarea.")
    if registered.get(norm(layout.main), {}).get("detached"):
        problems.append(f"El checkout principal {layout.main} está desacoplado.")
    legacy = layout.main.parent / f"{layout.main.name}.wt"
    if legacy.is_dir():
        problems.append(f"Quedan worktrees por tarea en {legacy} (backlog.py --worktree).")
    return problems


def doctor_findings(start: Path) -> Tuple[str, str, List[str]]:
    """Estado (PASS/WARN/SKIP), mensaje y evidencias del check DOC-15 de los dos doctors."""
    layout = find_layout(start)
    if layout is None:
        return "SKIP", f"{start} no es un repositorio git con checkout principal.", []
    if not layout.active:
        return "SKIP", "Worktrees por agente no activados en este repo (agent_worktree.py init).", []
    problems = _layout_problems(layout, base_branch(layout.main))
    if problems:
        return "WARN", problems[0], problems[1:6]
    return "PASS", f"Worktrees de agente correctos: {', '.join(str(p) for p in layout.worktrees.values())}.", []


def init_argv(start: Path) -> Tuple[str, ...]:
    return (sys.executable or "python", str(Path(__file__).resolve()), "--repo", str(start), "init")


# --------------------------------------------------------------------------- CLI


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Un git worktree fijo por agente (aagy / aagy-ecc).")
    parser.add_argument("--repo", default=".", help="Cualquier carpeta del repositorio (por defecto, la actual).")
    parser.add_argument("--quiet", action=FLAG, help="No imprime nada si no hay nada que hacer.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init", help="Crea los worktrees de los agentes.")
    p.add_argument(OPT_NO_INSTALL, action=FLAG)
    p.add_argument("--no-fetch", action=FLAG)
    for name, text in (("where", "Rol de la carpeta actual."), ("status", "Estado de los tres checkouts.")):
        sub.add_parser(name, help=text).add_argument(OPT_JSON, action=FLAG)
    p = sub.add_parser(CMD_RECYCLE, help="Recicla el worktree del agente tras el merge.")
    p.add_argument(OPT_AGENT, choices=AGENT_CHOICES)
    p.add_argument("--if-merged", action=FLAG, help="Sale sin error si la PR aún no está fusionada.")
    p.add_argument("--hard-recreate", action=FLAG, help="Borra y recrea el worktree en vez de limpiarlo.")
    p.add_argument(OPT_NO_INSTALL, action=FLAG)
    p.add_argument("--wait", type=int, default=0, help="Segundos a esperar a que la PR se fusione.")
    p = sub.add_parser("guard", help="Hook PreToolUse: lee el payload por stdin.")
    p.add_argument(OPT_AGENT, required=True, choices=AGENT_CHOICES)
    p.add_argument("--format", choices=("claude", "agy"), default="claude")
    sub.add_parser("notice", help="Aviso de arranque de sesión.").add_argument(OPT_AGENT, required=True, choices=AGENT_CHOICES)
    return parser


def _read_stdin_json() -> Dict[str, Any]:
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _cmd_guard(args: argparse.Namespace) -> int:
    import agent_worktree_guard as guard  # noqa: PLC0415

    try:
        reason = guard.guard_payload(args.agent, _read_stdin_json(), args.format)
    except Exception:  # noqa: BLE001 - una guarda rota no debe bloquear el trabajo (fail-open)
        reason = None
    response = guard.guard_response(reason, args.format)
    if response:
        print(json.dumps(response, ensure_ascii=False))
    return EXIT_OK


def _cmd_notice(args: argparse.Namespace, start: Path) -> int:
    import agent_worktree_guard as guard  # noqa: PLC0415

    text = guard.session_notice(args.agent, Path(str(_read_stdin_json().get("cwd") or start)))
    if text:
        print(text)
    return EXIT_OK


def _print_status(data: Dict[str, Any]) -> None:
    for key in (ROLE_MAIN, *AGENT_SUFFIXES):
        item = data[key]
        state = "no existe" if not item.get("exists") else (
            f"{item.get('branch') or 'desacoplado'} @ {item.get('head')}, {item.get('dirty')} cambio(s)"
        )
        print(f"{key:7} {item['path']}: {state}")
    print("Guarda activa." if data["active"] else "Guarda inactiva (ejecuta init).")


def _run_command(args: argparse.Namespace, layout: Layout, start: Path) -> List[str]:
    if args.command == "init":
        return op_init(layout, install=not args.no_install, fetch=not args.no_fetch)
    if args.command == "where":
        data = layout.to_dict(start)
        return [json.dumps(data, ensure_ascii=False) if args.json else data["role"]]
    if args.command == "status":
        data = op_status(layout)
        if args.json:
            return [json.dumps(data, ensure_ascii=False, indent=2)]
        _print_status(data)
        return []
    agent = resolve_agent(args.agent, layout, start)
    return op_recycle(
        layout, agent, if_merged=args.if_merged, hard_recreate=args.hard_recreate,
        install=not args.no_install, wait_s=args.wait,
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    start = Path(args.repo).resolve()
    if args.command == "guard":
        return _cmd_guard(args)
    if args.command == "notice":
        return _cmd_notice(args, start)
    layout = find_layout(start)
    if layout is None or (args.command == CMD_RECYCLE and args.quiet and not layout.active):
        if args.quiet:
            return EXIT_OK  # hooks: repos que no usan worktrees por agente
        print(f"[agent-worktree] {start} no está en un repositorio git con checkout principal normal.", file=sys.stderr)
        return EXIT_ERROR
    try:
        lines = _run_command(args, layout, start)
    except WorktreeError as exc:
        if not (args.quiet and exc.code == EXIT_NO_GH):
            print(f"[agent-worktree] {exc}", file=sys.stderr)
        return exc.code
    for line in lines:
        print(line)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
