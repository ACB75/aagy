#!/usr/bin/env python3
"""
Guarda PreToolUse de los worktrees por agente.

Si el repo activó los worktrees por agente (marcador `$(git common dir)/aagy-worktrees.json`,
lo crea `agent_worktree.py init`), cada agente solo puede escribir en su worktree:
se deniegan escrituras y comandos que modifican el checkout principal de Master o el
worktree del otro agente, y los `git worktree add|remove|move` a mano. El worktree nativo
de Claude Code (EnterWorktree, `claude --worktree`) se deniega siempre.

Solo mira el sistema de ficheros (sin llamar a git) para responder en milisegundos.
"""

from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent_worktree_base import AGENT_LABELS, ROLE_MAIN, Layout, find_layout, is_within

GUARD_TAG = "[WORKTREE-GUARD]"
FMT_AGY = "agy"
CD_WORDS = frozenset({"cd", "set-location", "sl", "pushd", "chdir"})

# Comandos que se pueden ejecutar en una carpeta ajena porque solo leen.
READONLY_COMMANDS = frozenset(
    {
        "ls", "dir", "cat", "type", "head", "tail", "less", "more", "grep", "rg", "find", "wc",
        "pwd", "echo", "which", "where", "file", "stat", "tree", "du", "df", "diff", "sort", "uniq",
        "get-childitem", "gci", "get-content", "gc", "select-string", "sls", "get-location",
        "get-item", "test-path", "resolve-path", "write-output", "write-host", "measure-object",
        "popd", "true", "exit",
    }
) | CD_WORDS
READONLY_GIT = frozenset(
    {
        "status", "log", "diff", "show", "fetch", "blame", "rev-parse", "ls-files", "ls-remote",
        "describe", "shortlog", "grep", "remote", "config", "for-each-ref", "cat-file", "rev-list",
        "merge-base", "reflog", "help", "version", "--version",
    }
)
GIT_OPTS_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree"})
WRITE_HINTS = re.compile(
    r"(>>?|\btee\b|\brm\b|\brmdir\b|\bdel\b|\bmv\b|\bcp\b|\bmkdir\b|\btouch\b|\bsed\s+-i|"
    r"remove-item|set-content|add-content|out-file|new-item|copy-item|move-item|rename-item|"
    r"\bri\b|\bni\b|\bcpi\b|\bmi\b)",
    re.IGNORECASE,
)
GIT_BRANCH_READ = re.compile(r"\s(--list|-l|-a|-r|-v|-vv|--show-current|--contains)\b|branch\s*$")
GIT_STASH_READ = re.compile(r"\sstash\s+(list|show)\b")
SEGMENT_SPLIT = re.compile(r"\s*(?:&&|\|\||;|\||\r?\n)\s*")
CD_TARGET = re.compile(r"^(?:cd|chdir|pushd|set-location|sl)\s+(?:-path\s+)?(?P<path>.+?)\s*$", re.IGNORECASE)
GIT_C_TARGET = re.compile(r"(?:^|\s)git(?:\.exe)?\s+(?:-C\s+|--work-tree[= ])(?P<path>\"[^\"]+\"|'[^']+'|\S+)")
WORKTREE_CMD = re.compile(r"(?:^|\s)git(?:\.exe)?\s+(?:-C\s+\S+\s+)?worktree\s+(?:add|remove|move)\b")
NATIVE_WORKTREE = re.compile(r"(?:^|\s)claude(?:\.exe|\.cmd)?\s+(?:[^|;&]*\s)?(?:--worktree|-w)\b")
SELF_SCRIPT = re.compile(r"agent[_-]worktree\.(?:py|ps1|sh)", re.IGNORECASE)
# Redirecciones que no escriben ficheros: 2>&1, >$null, 2>/dev/null, >NUL.
HARMLESS_REDIRECT = re.compile(r"\d?>&\d|\d?>>?\s*(?:\$null|/dev/null|nul)\b", re.IGNORECASE)
# Worktrees nativos que crea la app de Claude Code (sesiones de escritorio y Remote Control):
# son checkouts aislados, no el principal de Master.
NATIVE_WORKTREES_REL = Path(".claude") / "worktrees"
PATH_TOKEN = re.compile(r"^([A-Za-z]:[\\/]|/|~|\.\.?[\\/])")

MSG_NATIVE = f"{GUARD_TAG} No uses el worktree nativo de Claude Code: cada agente tiene su worktree fijo (agent_worktree.py where)."
MSG_MANUAL = f"{GUARD_TAG} No crees ni borres worktrees a mano: usa agent_worktree.py init|recycle."
CLAUDE_FILE_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})
CLAUDE_SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
AGY_PATH_KEYS = ("TargetFile", "Path", "AbsolutePath", "FilePath")


def _strip_quotes(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    return text


def _words(segment: str) -> List[str]:
    try:
        return [_strip_quotes(w) for w in shlex.split(segment, posix=False)]
    except ValueError:
        return segment.split()


def _resolve(raw: str, cwd: Path) -> Path:
    path = Path(os.path.expanduser(os.path.expandvars(_strip_quotes(raw))))
    return Path(os.path.normpath(str(path if path.is_absolute() else cwd / path)))


def _first_word(words: List[str]) -> str:
    if not words:
        return ""
    word = words[0].lower().replace("\\", "/").rsplit("/", 1)[-1]
    return word[:-4] if word.endswith(".exe") else word


def _git_subcommand(words: List[str]) -> Optional[str]:
    i = 1
    while i < len(words):
        word = words[i]
        if word in GIT_OPTS_WITH_VALUE:
            i += 2
        elif word.startswith("-") and word != "--version":
            i += 1
        else:
            return word.lower()
    return None


def _git_is_readonly(segment: str, words: List[str]) -> bool:
    sub = _git_subcommand(words)
    if sub == "branch":
        return bool(GIT_BRANCH_READ.search(segment))
    if sub == "stash":
        return bool(GIT_STASH_READ.search(segment))
    return sub in READONLY_GIT


def is_readonly(segment: str) -> bool:
    words = _words(segment)
    word = _first_word(words)
    if not word:
        return True
    if word not in CD_WORDS and WRITE_HINTS.search(HARMLESS_REDIRECT.sub(" ", segment)):
        return False
    if word == "git":
        return _git_is_readonly(segment, words)
    return word in READONLY_COMMANDS


def _paths_in(segment: str, cwd: Path) -> List[Path]:
    paths: List[Path] = []
    for token in _words(segment)[1:]:
        paths.extend(_resolve(piece, cwd) for piece in re.split(r"[=,]", token) if PATH_TOKEN.match(piece))
    return paths


def _deny_reason(agent: str, layout: Layout, target: Path) -> str:
    own = layout.worktrees[agent]
    role = layout.role(target)
    whose = "el checkout principal de Master" if role == ROLE_MAIN else f"el worktree de {AGENT_LABELS.get(role, '?')}"
    return (
        f"{GUARD_TAG} {AGENT_LABELS[agent]} trabaja solo en {own}. {target} es {whose}: no puedes escribir ahí. "
        f"Cambia a tu worktree (cd \"{own}\"); para leer usa Read/Grep. "
        "Gestiona los worktrees solo con agent_worktree.py."
    )


def _is_protected(layout: Layout, agent: str, target: Path) -> bool:
    if is_within(target, layout.main / NATIVE_WORKTREES_REL):
        return False
    return any(is_within(target, p) for p in layout.protected_for(agent))


def _active_layout(*starts: Path) -> Optional[Layout]:
    for start in starts:
        layout = find_layout(start, use_git=False)
        if layout is not None:
            return layout if layout.active else None
    return None


def guard_file(agent: str, cwd: Path, target_raw: str) -> Optional[str]:
    if not target_raw:
        return None
    target = _resolve(target_raw, cwd)
    layout = _active_layout(target if target.exists() else target.parent, cwd)
    if layout is not None and _is_protected(layout, agent, target):
        return _deny_reason(agent, layout, target)
    return None


def _segment_targets(segment: str, current: Path) -> List[Path]:
    match = GIT_C_TARGET.search(segment)
    targets = [_resolve(match.group("path"), current)] if match else [current]
    return targets + _paths_in(segment, current)


def _scan_segments(agent: str, layout: Layout, cwd: Path, command: str) -> Optional[str]:
    current = cwd
    for segment in filter(str.strip, SEGMENT_SPLIT.split(command)):
        cd = CD_TARGET.match(segment.strip())
        if cd:
            current = _resolve(cd.group("path"), current)
            continue
        if is_readonly(segment):
            continue
        hit = next((t for t in _segment_targets(segment, current) if _is_protected(layout, agent, t)), None)
        if hit is not None:
            return _deny_reason(agent, layout, hit)
    return None


def guard_command(agent: str, cwd: Path, command: str) -> Optional[str]:
    if not command.strip():
        return None
    if NATIVE_WORKTREE.search(command):
        return MSG_NATIVE
    layout = _active_layout(cwd)
    if layout is None or SELF_SCRIPT.search(command):
        return None
    if WORKTREE_CMD.search(command):
        return MSG_MANUAL
    return _scan_segments(agent, layout, cwd, command)


def _guard_agy(agent: str, payload: Dict[str, Any]) -> Optional[str]:
    call = payload.get("toolCall") or {}
    args = call.get("args") or {}
    cwd = Path(str(args.get("Cwd") or payload.get("cwd") or os.getcwd()))
    if args.get("CommandLine"):
        return guard_command(agent, cwd, str(args["CommandLine"]))
    target = next((args[k] for k in AGY_PATH_KEYS if args.get(k)), None)
    return guard_file(agent, cwd, str(target)) if target else None


def _guard_claude(agent: str, payload: Dict[str, Any]) -> Optional[str]:
    name = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    cwd = Path(str(payload.get("cwd") or os.getcwd()))
    if name == "EnterWorktree":
        return MSG_NATIVE
    if name in CLAUDE_SHELL_TOOLS:
        return guard_command(agent, cwd, str(tool_input.get("command") or ""))
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if name in CLAUDE_FILE_TOOLS and target:
        return guard_file(agent, cwd, str(target))
    return None


def guard_payload(agent: str, payload: Dict[str, Any], fmt: str) -> Optional[str]:
    """Interpreta el payload PreToolUse de Claude Code (`claude`) o de Antigravity (`agy`)."""
    return _guard_agy(agent, payload) if fmt == FMT_AGY else _guard_claude(agent, payload)


def guard_response(reason: Optional[str], fmt: str) -> Dict[str, Any]:
    if fmt == FMT_AGY:
        return {"decision": "deny", "reason": reason} if reason else {"decision": "allow"}
    if not reason:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def session_notice(agent: str, cwd: Path) -> str:
    """Aviso de arranque si la sesión no está en el worktree del agente (vacío si todo está bien)."""
    layout = _active_layout(cwd)
    if layout is None:
        return ""
    own = layout.worktrees[agent]
    if layout.role(cwd) == agent:
        return f"Worktree de {AGENT_LABELS[agent]}: {own}. Trabaja solo aquí; el checkout principal {layout.main} es de Master."
    return (
        f"AVISO: esta sesión está en {cwd}, pero {AGENT_LABELS[agent]} solo puede escribir en su worktree {own}. "
        f"Pide a Master que abra la sesión allí o trabaja con cd \"{own}\"."
    )
