#!/usr/bin/env python3
"""
Módulo de validación de nombres de rama Git en AAGY (validate_branch.py).
Enforza la convención canónica de ramas de tarea e incidencias (fix/*).
Cumple con SonarQube Quality Gate A (S3776 <= 15, S1192 sin duplicados).
"""

import argparse
import re
import shlex
import subprocess
import sys
from typing import Callable, List, Optional, Sequence, Tuple

MSG_OK = "OK"
MSG_RESERVED_BRANCH = "Rama 'main' o 'master' no permitida directamente para desarrollo de tareas."
MSG_INVALID_BRANCH = (
    "Nombre de rama no cumple la convención canónica: "
    "debe seguir <tipo>/<nombre> o <tipo>/<proyecto>/<nombre> "
    "(tipos permitidos: fix, feat, refactor, infra, chore, docs, test)."
)

# Regex canónica de ramas de tarea
BRANCH_REGEX = re.compile(
    r"^(?P<type>fix|feat|refactor|infra|chore|docs|test)/"
    r"(?P<segment1>[a-zA-Z0-9._-]+)"
    r"(?:/(?P<segment2>[a-zA-Z0-9._-]+))?$"
)


def is_fix_branch(branch_name: str) -> bool:
    """Determina si una rama corresponde a una incidencia o corrección."""
    return branch_name.strip().startswith("fix/")


def validate_branch_name(branch_name: str, allow_main: bool = False) -> Tuple[bool, str]:
    """
    Valida si el nombre de rama cumple la política estricta de gobernanza Git.
    Retorna tupla (es_valido, mensaje_error).
    """
    cleaned = branch_name.strip()
    if cleaned in ("main", "master"):
        if allow_main:
            return True, MSG_OK
        return False, MSG_RESERVED_BRANCH

    if " " in cleaned or cleaned.endswith("/") or "//" in cleaned:
        return False, MSG_INVALID_BRANCH

    match = BRANCH_REGEX.match(cleaned)
    if not match:
        return False, MSG_INVALID_BRANCH

    branch_type = match.group("type")
    # Para ramas no-fix, requerir minúsculas consistentes
    if branch_type != "fix":
        if any(c.isupper() for c in cleaned):
            return False, MSG_INVALID_BRANCH

    return True, MSG_OK


# --- Detección de ramas creadas o publicadas por un comando git (hooks PreToolUse) ---

_SEGMENT_SPLIT = re.compile(r"&&|\|\||[;|\n]")
_GIT_GLOBAL_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
_CREATE_FLAGS = {
    "checkout": {"-b", "-B", "--orphan"},
    "switch": {"-c", "-C", "--create", "--force-create"},
}
_BRANCH_SAFE_FLAGS = {"-f", "--force", "-t", "--track", "--no-track"}
_BRANCH_RENAME_FLAGS = {"-m", "-M", "--move"}
_PUSH_SKIP_FLAGS = {"-d", "--delete", "--tags", "--mirror", "--all", "--prune"}
_PUSH_OPTS_WITH_VALUE = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
REMOTE_HEADS_PREFIX = "refs/heads/"
_TAG_LIKE = re.compile(r"^v?\d+(\.\d+)+")


def is_local_tag(name: str) -> bool:
    """True si `name` es un tag local (git push origin <tag> no publica una rama)."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "-q", "--verify", f"refs/tags/{name}"],
            capture_output=True,
            text=True,
            check=False,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return res.returncode == 0


def _git_subcommand(tokens: List[str]) -> Tuple[str, List[str]]:
    """Devuelve (subcomando, argumentos) si los tokens son una llamada a git; ('', []) si no."""
    if not tokens or _exe_name(tokens[0]) not in ("git", "git.exe"):
        return "", []
    idx = 1
    while idx < len(tokens) and tokens[idx].startswith("-"):
        idx += 2 if tokens[idx] in _GIT_GLOBAL_OPTS_WITH_VALUE else 1
    if idx >= len(tokens):
        return "", []
    return tokens[idx], tokens[idx + 1:]


def _exe_name(token: str) -> str:
    """Nombre base de un ejecutable (git, /usr/bin/git, C:\\Git\\git.exe)."""
    return re.split(r"[\\/]", token)[-1].lower()


def _flag_value(args: List[str], flags: set) -> List[str]:
    found = []
    for i, arg in enumerate(args):
        if arg in flags and i + 1 < len(args):
            found.append(args[i + 1])
        else:
            for flag in flags:
                if flag.startswith("--") and arg.startswith(flag + "="):
                    found.append(arg.split("=", 1)[1])
    return found


def _branch_targets(args: List[str]) -> List[str]:
    positional = [a for a in args if not a.startswith("-")]
    flags = [a for a in args if a.startswith("-")]
    if any(f in _BRANCH_RENAME_FLAGS for f in flags):
        return positional[-1:]
    if any(f not in _BRANCH_SAFE_FLAGS for f in flags):
        return []  # listar, borrar, copiar, --show-current, etc.
    return positional[:1]


def _push_positional(args: List[str]) -> List[str]:
    """Argumentos posicionales de git push (remoto y refspecs), sin opciones ni sus valores."""
    positional: List[str] = []
    skip_next = False
    for arg in args:
        if skip_next:
            skip_next = False
        elif arg in _PUSH_OPTS_WITH_VALUE:
            skip_next = True
        elif not arg.startswith("-"):
            positional.append(arg)
    return positional


def _refspec_target(spec: str, current_branch: Callable[[], str]) -> str:
    """Rama remota que publica un refspec, o '' si borra, es un tag u otra ref."""
    spec = spec.lstrip("+")
    if spec.startswith(":"):
        return ""
    dst = spec.split(":", 1)[1] if ":" in spec else spec
    if dst.startswith(REMOTE_HEADS_PREFIX):
        return dst[len(REMOTE_HEADS_PREFIX):]
    if dst.startswith("refs/") or _TAG_LIKE.match(dst):
        return ""
    if dst == "HEAD":
        return current_branch()
    return "" if is_local_tag(dst) else dst


def _push_targets(args: List[str], current_branch: Callable[[], str]) -> List[str]:
    if any(a in _PUSH_SKIP_FLAGS for a in args):
        return []
    refspecs = _push_positional(args)[1:]
    if not refspecs:
        return [current_branch()]
    return [_refspec_target(spec, current_branch) for spec in refspecs]


def branches_in_command(command: str, current_branch: Callable[[], str] = None) -> List[str]:
    """
    Ramas que un comando de shell crea, renombra o publica con git
    (checkout -b, switch -c, branch, branch -m, push). Ignora borrados, tags y listados.
    """
    resolve = current_branch or get_current_git_branch
    found: List[str] = []
    for segment in _SEGMENT_SPLIT.split(command or ""):
        try:
            tokens = shlex.split(segment, posix=True)
        except ValueError:
            continue
        sub, args = _git_subcommand(tokens)
        if sub in _CREATE_FLAGS:
            found.extend(_flag_value(args, _CREATE_FLAGS[sub]))
        elif sub == "branch":
            found.extend(_branch_targets(args))
        elif sub == "push":
            found.extend(_push_targets(args, resolve))
    return [b for b in found if b]


def invalid_branches_in_command(command: str, current_branch: Callable[[], str] = None) -> List[str]:
    """Ramas de `branches_in_command` que no cumplen la convención (main/master se permiten)."""
    return [
        b for b in branches_in_command(command, current_branch)
        if not validate_branch_name(b, allow_main=True)[0]
    ]


def get_current_git_branch() -> str:
    """Obtiene el nombre de la rama activa en el directorio actual."""
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return ""


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parsea argumentos de línea de comandos."""
    parser = argparse.ArgumentParser(description="Validador canónico de nombres de rama Git en AAGY.")
    parser.add_argument("--branch", type=str, default="", help="Nombre de la rama a validar (por defecto la activa).")
    parser.add_argument("--allow-main", action="store_true", help="Permite 'main' como rama válida.")
    parser.add_argument(
        "--git-command",
        type=str,
        default=None,
        help="Valida las ramas que crea o publica este comando de shell (uso desde hooks PreToolUse).",
    )
    return parser.parse_args(argv)


def command_rejection(command: str, current_branch: Callable[[], str] = None) -> str:
    """Mensaje de rechazo para un comando que crea o publica ramas fuera de convención, o '' si es válido."""
    try:
        invalid = invalid_branches_in_command(command, current_branch)
    except Exception:  # noqa: BLE001 - los hooks son fail-open
        return ""
    if not invalid:
        return ""
    names = ", ".join(f"'{b}'" for b in invalid)
    return (
        f"[BRANCH-GUARD] Rama {names} fuera de convención. {MSG_INVALID_BRANCH} "
        "Usa por ejemplo 'git switch -c fix/<proyecto>/<nombre>', renombra con "
        "'git branch -m <tipo>/<proyecto>/<nombre>' o publica con "
        "'git push -u origin HEAD:<tipo>/<proyecto>/<nombre>'."
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada CLI."""
    args = parse_args(argv)
    if args.git_command is not None:
        reason = command_rejection(args.git_command)
        if reason:
            print(reason)
            return 1
        return 0
    branch = args.branch or get_current_git_branch()
    if not branch:
        print("[ERROR] No se pudo determinar el nombre de la rama.")
        return 1

    valid, msg = validate_branch_name(branch, allow_main=args.allow_main)
    if not valid:
        print(f"[REJECT] Rama '{branch}' inválida: {msg}")
        return 1

    fix_note = " (Incidencia / Corrección)" if is_fix_branch(branch) else ""
    print(f"[PASS] Rama '{branch}' cumple la convención canónica{fix_note}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
