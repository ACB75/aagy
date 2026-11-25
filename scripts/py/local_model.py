#!/usr/bin/env python3
"""
Modelo local con Ollama para aagy y aagy-ecc (local_model.py).

Núcleo común del servidor MCP ``aagy-local`` (local_model_mcp.py), del comando
``/aagy-local`` y del doctor. Solo stdlib de Python. Sin Ollama, todo sigue
igual que sin este módulo: el modo ``auto`` se queda en ``off`` sin avisos.

Modos (``local_model.mode`` o ``AAGY_LOCAL_MODEL``):

- ``auto`` (por defecto): si Ollama responde y tiene el modelo de herramienta,
  se comporta como ``tool``; si no, como ``off``.
- ``off``: el servidor MCP no expone herramientas.
- ``tool``: como ``auto``, pero forzado; si Ollama no responde, el doctor falla.
- ``only``: sesión solo local (lanzadores ``claude-local`` y ``agy-local``).

Configuración (se lee con aagy_config; gana la primera capa que tenga la clave):

| Clave                      | Variable de atajo          | Por defecto              |
|----------------------------|----------------------------|--------------------------|
| ``local_model.mode``       | ``AAGY_LOCAL_MODEL``       | ``auto``                 |
| ``local_model.url``        | ``AAGY_OLLAMA_URL``        | ``http://localhost:11434`` |
| ``local_model.tool``       | ``AAGY_LOCAL_MODEL_NAME``  | (ninguno)                |
| ``local_model.only``       | ``AAGY_LOCAL_AGENT_MODEL`` | (ninguno)                |
| ``local_model.fim``        | ``AAGY_LOCAL_FIM_MODEL``   | (ninguno)                |
| ``local_model.num_ctx``    | ``AAGY_LOCAL_NUM_CTX``     | ``8192``                 |
| ``local_model.timeout_s``  | ``AAGY_LOCAL_TIMEOUT_S``   | ``120``                  |
| ``local_model.tasks``      | —                          | catálogo del plugin      |
| ``local_model.private_globs`` | —                       | ``[]``                   |

El plugin no trae nombres de modelo: van en la capa de entorno
(``<AAGY_ENV_DIR>/aagy/env.json``) o en la del proyecto.

Uso::

    python local_model.py status [--json]
    python local_model.py on | off | auto
    python local_model.py run summarize --path build.log
    python local_model.py only --harness claude|agy   # sesión solo local
    python local_model.py bench [--models a,b]   # precisión y tokens/s
    python local_model.py usage                  # resumen del registro de uso
    python local_model.py register-agy [--config <mcp_config.json>]
    python local_model.py setup --tool <m> --only <m> --fim <m> [--pull]  # configura la máquina

Se espeja en aagy-ecc/scripts/py/ mediante sync_aagy_ecc.py.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import fnmatch
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
import urllib.error
import urllib.request

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import aagy_config  # noqa: E402

ENCODING = "utf-8"
SERVER_NAME = "aagy-local"
KEY_ROOT = "local_model"

MODE_AUTO = "auto"
MODE_OFF = "off"
MODE_TOOL = "tool"
MODE_ONLY = "only"
MODES = (MODE_AUTO, MODE_OFF, MODE_TOOL, MODE_ONLY)

DEFAULT_URL = "http://localhost:11434"
DEFAULT_NUM_CTX = 8192
DEFAULT_TIMEOUT_S = 120
PROBE_TIMEOUT_S = 0.8
DEFAULT_MAX_CHARS = 24000

K_INSTRUCTION = "instruction"
K_PARAMS = "params"
K_DEFAULTS = "defaults"
K_FORMAT = "format"
K_MAX_CHARS = "max_chars"
K_NUM_CTX = "num_ctx"
K_CONTENT = "content"
K_DURATION = "duration_ms"

# Variables de atajo del REQ, además de las AAGY_LOCAL_MODEL_<CLAVE> de aagy_config.
ALIASES: Dict[str, str] = {
    "mode": "AAGY_LOCAL_MODEL",
    "url": "AAGY_OLLAMA_URL",
    "tool": "AAGY_LOCAL_MODEL_NAME",
    "only": "AAGY_LOCAL_AGENT_MODEL",
    "fim": "AAGY_LOCAL_FIM_MODEL",
    K_NUM_CTX: "AAGY_LOCAL_NUM_CTX",
    "timeout_s": "AAGY_LOCAL_TIMEOUT_S",
}

FORMAT_TEXT = "text"
FORMAT_JSON = "json"

# Catálogo por defecto (P-04): solo tareas sencillas y de una llamada. Son datos, no
# código; cada proyecto las amplía o quita en local_model.tasks (null quita una).
DEFAULT_TASKS: Dict[str, Dict[str, Any]] = {
    "classify": {
        K_INSTRUCTION: "Clasifica el texto en una sola de estas etiquetas: {labels}. Responde solo con la etiqueta.",
        K_PARAMS: ["labels"],
        K_FORMAT: FORMAT_TEXT,
        K_MAX_CHARS: 8000,
    },
    "summarize": {
        K_INSTRUCTION: "Resume el texto en español en {max_words} palabras como máximo. Sin preámbulos.",
        K_PARAMS: ["max_words"],
        K_DEFAULTS: {"max_words": "120"},
        K_FORMAT: FORMAT_TEXT,
        K_MAX_CHARS: DEFAULT_MAX_CHARS,
    },
    "extract": {
        K_INSTRUCTION: "Extrae del texto estos campos: {fields}. Responde solo con un objeto JSON con esas claves; usa null si falta un dato.",
        K_PARAMS: ["fields"],
        K_FORMAT: FORMAT_JSON,
        K_MAX_CHARS: DEFAULT_MAX_CHARS,
    },
    "translate": {
        K_INSTRUCTION: "Traduce el texto a {target_lang}. Mantén el formato Markdown y el código sin traducir. Responde solo con la traducción.",
        K_PARAMS: ["target_lang"],
        K_DEFAULTS: {"target_lang": "español"},
        K_FORMAT: FORMAT_TEXT,
        K_MAX_CHARS: 16000,
    },
    "complete": {
        K_INSTRUCTION: "Continúa el texto o el código de forma natural. Responde solo con la continuación.",
        K_PARAMS: [],
        K_FORMAT: FORMAT_TEXT,
        K_MAX_CHARS: 8000,
    },
}


class LocalModelError(RuntimeError):
    """Error controlado: se devuelve como resultado estructurado, nunca como excepción al agente."""


@dataclass(frozen=True)
class Settings:
    mode: str
    url: str
    tool_model: str
    only_model: str
    fim_model: str
    num_ctx: int
    timeout_s: float
    tasks: Mapping[str, Mapping[str, Any]]
    private_globs: Tuple[str, ...]
    project_file: Optional[Path]


@dataclass
class Status:
    mode: str
    effective: str
    url: str
    reachable: bool
    tool_model: str
    tool_model_present: bool
    models: List[str] = field(default_factory=list)
    reason: str = ""


# --------------------------------------------------------------------------- configuración

def _value(cfg: aagy_config.Config, key: str, environ: Mapping[str, str]) -> Any:
    alias = ALIASES.get(key)
    raw = environ.get(alias, "").strip() if alias else ""
    if raw:
        return raw
    return cfg.get(f"{KEY_ROOT}.{key}")


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def merge_tasks(overrides: Any) -> Dict[str, Dict[str, Any]]:
    """Catálogo del plugin más el del proyecto. ``null`` quita una tarea; un objeto la añade o la amplía."""
    tasks = {name: dict(spec) for name, spec in DEFAULT_TASKS.items()}
    if not isinstance(overrides, Mapping):
        return tasks
    for name, spec in overrides.items():
        if spec is None:
            tasks.pop(name, None)
        elif isinstance(spec, Mapping) and (name in tasks or spec.get(K_INSTRUCTION)):
            tasks[name] = {**tasks.get(name, {}), **spec}
    return tasks


def load_settings(start: Optional[Path] = None, environ: Optional[Mapping[str, str]] = None) -> Settings:
    env = dict(os.environ if environ is None else environ)
    cfg = aagy_config.load(start, env)
    mode = str(_value(cfg, "mode", env) or MODE_AUTO).lower()
    globs = _value(cfg, "private_globs", env) or []
    return Settings(
        mode=mode if mode in MODES else MODE_AUTO,
        url=str(_value(cfg, "url", env) or DEFAULT_URL).rstrip("/"),
        tool_model=str(_value(cfg, "tool", env) or ""),
        only_model=str(_value(cfg, "only", env) or ""),
        fim_model=str(_value(cfg, "fim", env) or ""),
        num_ctx=_as_int(_value(cfg, K_NUM_CTX, env), DEFAULT_NUM_CTX),
        timeout_s=float(_as_int(_value(cfg, "timeout_s", env), DEFAULT_TIMEOUT_S)),
        tasks=merge_tasks(_value(cfg, "tasks", env)),
        private_globs=tuple(str(g) for g in globs) if isinstance(globs, list) else (),
        project_file=cfg.project.path,
    )


# --------------------------------------------------------------------------- Ollama

def _http_json(url: str, payload: Optional[Mapping[str, Any]], timeout: float) -> Dict[str, Any]:
    data = json.dumps(payload).encode(ENCODING) if payload is not None else None
    request = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - URL de configuración local
            return json.loads(response.read().decode(ENCODING))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise LocalModelError(f"Ollama no responde en {url}: {exc}") from exc


def list_models(settings: Settings, timeout: float = PROBE_TIMEOUT_S) -> List[str]:
    data = _http_json(f"{settings.url}/api/tags", None, timeout)
    return sorted(str(m.get("name", "")) for m in data.get("models", []) if m.get("name"))


def _model_present(model: str, models: Sequence[str]) -> bool:
    if not model:
        return False
    return model in models or f"{model}:latest" in models


def get_status(settings: Settings) -> Status:
    """Modo pedido y modo efectivo. La sonda dura menos de 1 s y no se hace en ``off``."""
    status = Status(settings.mode, MODE_OFF, settings.url, False, settings.tool_model, False)
    if settings.mode == MODE_OFF:
        status.reason = "Modo off."
        return status
    try:
        status.models = list_models(settings)
        status.reachable = True
    except LocalModelError as exc:
        status.reason = str(exc)
        return status
    status.tool_model_present = _model_present(settings.tool_model, status.models)
    if not settings.tool_model:
        status.reason = "Sin modelo de herramienta (local_model.tool)."
    elif not status.tool_model_present:
        status.reason = f"El modelo {settings.tool_model} no está descargado (ollama pull {settings.tool_model})."
    else:
        status.effective = MODE_TOOL
    return status


def chat_raw(settings: Settings, system: str, user: str, json_format: bool, model: str = "") -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": model or settings.tool_model,
        "messages": [{"role": "system", K_CONTENT: system}, {"role": "user", K_CONTENT: user}],
        "stream": False,
        "options": {K_NUM_CTX: settings.num_ctx},
    }
    if json_format:
        payload[K_FORMAT] = FORMAT_JSON
    return _http_json(f"{settings.url}/api/chat", payload, settings.timeout_s)


def chat(settings: Settings, system: str, user: str, json_format: bool) -> str:
    data = chat_raw(settings, system, user, json_format)
    return str(data.get("message", {}).get(K_CONTENT, "")).strip()


def tokens_per_second(data: Mapping[str, Any]) -> float:
    count = data.get("eval_count") or 0
    duration_ns = data.get("eval_duration") or 0
    return round(count / (duration_ns / 1e9), 1) if count and duration_ns else 0.0


# --------------------------------------------------------------------------- tareas

def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def read_paths(paths: Sequence[str], root: Path, max_chars: int) -> Tuple[str, bool]:
    """Lee los ficheros dentro de ``root``. El contenido nunca vuelve al agente, solo al modelo local."""
    parts: List[str] = []
    total = 0
    truncated = False
    for raw in paths:
        path = (root / raw).resolve() if not Path(raw).is_absolute() else Path(raw).resolve()
        if not _within(path, root) or not path.is_file():
            raise LocalModelError(f"Ruta no válida o fuera del proyecto: {raw}")
        text = path.read_text(encoding=ENCODING, errors="replace")
        block = f"--- {path.relative_to(root).as_posix()} ---\n{text}"
        if total + len(block) > max_chars:
            block = block[: max(0, max_chars - total)]
            truncated = True
        parts.append(block)
        total += len(block)
        if truncated:
            break
    return "\n\n".join(parts), truncated


def build_instruction(spec: Mapping[str, Any], params: Mapping[str, Any]) -> str:
    values = {**spec.get(K_DEFAULTS, {}), **{k: v for k, v in params.items() if v not in (None, "")}}
    missing = [p for p in spec.get(K_PARAMS, []) if p not in values]
    if missing:
        raise LocalModelError(f"Faltan parámetros: {', '.join(missing)}")
    rendered = {k: ", ".join(map(str, v)) if isinstance(v, list) else str(v) for k, v in values.items()}
    try:
        return str(spec[K_INSTRUCTION]).format(**rendered)
    except (KeyError, IndexError) as exc:
        raise LocalModelError(f"Instrucción de tarea mal formada: {exc}") from exc


def _source(args: Mapping[str, Any], root: Path, max_chars: int) -> Tuple[str, bool]:
    text = args.get("text")
    paths = args.get("paths")
    if bool(text) == bool(paths):
        raise LocalModelError("Pasa 'text' o 'paths', uno de los dos.")
    if paths:
        return read_paths([str(p) for p in paths], root, max_chars)
    raw = str(text)
    return raw[:max_chars], len(raw) > max_chars


def run_task(settings: Settings, args: Mapping[str, Any], root: Optional[Path] = None) -> Dict[str, Any]:
    """Ejecuta una tarea del catálogo. Siempre devuelve un dict; ``error`` si algo falla."""
    started = time.monotonic()
    result: Dict[str, Any] = {"model": settings.tool_model, K_DURATION: 0, "truncated": False}
    try:
        name = str(args.get("task", ""))
        spec = settings.tasks.get(name)
        if spec is None:
            raise LocalModelError(f"Tarea desconocida '{name}'. Disponibles: {', '.join(sorted(settings.tasks))}")
        if not settings.tool_model:
            raise LocalModelError("Sin modelo de herramienta (local_model.tool).")
        instruction = build_instruction(spec, args.get(K_PARAMS) or {})
        content, truncated = _source(args, (root or Path.cwd()).resolve(), int(spec.get(K_MAX_CHARS, DEFAULT_MAX_CHARS)))
        result["truncated"] = truncated
        result["result"] = chat(settings, instruction, content, spec.get(K_FORMAT) == FORMAT_JSON)
    except LocalModelError as exc:
        result["error"] = str(exc)
    result[K_DURATION] = int((time.monotonic() - started) * 1000)
    log_usage(result, str(args.get("task", "")), root)
    return result


# --------------------------------------------------------------------------- registro de uso (RF-14)

def _git_common_dir(root: Path) -> Optional[Path]:
    for folder in (root, *root.parents):
        git = folder / ".git"
        if git.is_dir():
            return git
        if git.is_file():
            text = git.read_text(encoding=ENCODING, errors="replace").strip()
            if text.startswith("gitdir:"):
                gitdir = (folder / text.split(":", 1)[1].strip()).resolve()
                common = gitdir / "commondir"
                return (gitdir / common.read_text(encoding=ENCODING).strip()).resolve() if common.is_file() else gitdir
    return None


def usage_log_path(root: Optional[Path] = None) -> Optional[Path]:
    common = _git_common_dir((root or Path.cwd()).resolve())
    return common / SERVER_NAME / "usage.jsonl" if common else None


def log_usage(result: Mapping[str, Any], task: str, root: Optional[Path] = None) -> None:
    """Una línea por llamada, sin contenido: tarea, modelo, duración, bytes y si hubo error."""
    path = usage_log_path(root)
    if path is None:
        return
    line = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "task": task,
        "model": result.get("model", ""),
        K_DURATION: result.get(K_DURATION, 0),
        "bytes_out": len(str(result.get("result", ""))),
        "ok": "error" not in result,
    }
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding=ENCODING) as handle:
            handle.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError:
        return


def usage_summary(root: Optional[Path] = None) -> Dict[str, Any]:
    path = usage_log_path(root)
    calls = ok = 0
    ms = 0
    if path and path.is_file():
        for raw in path.read_text(encoding=ENCODING, errors="replace").splitlines():
            try:
                row = json.loads(raw)
            except ValueError:
                continue
            calls += 1
            ok += 1 if row.get("ok") else 0
            ms += int(row.get(K_DURATION, 0))
    return {"calls": calls, "ok": ok, "total_ms": ms, "path": str(path or "")}


def is_private(path: str, settings: Settings, root: Optional[Path] = None) -> bool:
    """True si ``path`` casa con ``local_model.private_globs`` (rutas relativas al proyecto)."""
    if not settings.private_globs:
        return False
    base = (root or Path.cwd()).resolve()
    candidate = Path(path)
    resolved = candidate.resolve() if candidate.is_absolute() else (base / candidate).resolve()
    rel = resolved.relative_to(base).as_posix() if _within(resolved, base) else resolved.as_posix()
    return any(fnmatch.fnmatch(rel, pattern) for pattern in settings.private_globs)


# --------------------------------------------------------------------------- escritura de configuración

def set_mode(mode: str, settings: Settings, start: Optional[Path] = None) -> Path:
    """Guarda ``local_model.mode`` en .governance/aagy.json (idempotente)."""
    if mode not in MODES:
        raise LocalModelError(f"Modo inválido '{mode}'. Usa: {', '.join(MODES)}")
    path = settings.project_file or (_repo_root(start) / aagy_config.PROJECT_FILE)
    data: Dict[str, Any] = {}
    if path.is_file():
        data = json.loads(path.read_text(encoding=ENCODING))
    section = data.setdefault(KEY_ROOT, {})
    if section.get("mode") != mode:
        section["mode"] = mode
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding=ENCODING)
    return path


def _repo_root(start: Optional[Path] = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for folder in (current, *current.parents):
        if (folder / ".git").exists():
            return folder
    return current


def server_entry(python: str = "python") -> Dict[str, Any]:
    return {"command": python, "args": [str(_HERE / "local_model_mcp.py")]}


def register_agy(config_path: Path, python: str = "python") -> bool:
    """Añade aagy-local al mcp_config.json de Antigravity. Devuelve True si cambió algo."""
    data: Dict[str, Any] = {}
    if config_path.is_file():
        data = json.loads(config_path.read_text(encoding=ENCODING) or "{}")
    servers = data.setdefault("mcpServers", {})
    entry = server_entry(python)
    if servers.get(SERVER_NAME) == entry:
        return False
    servers[SERVER_NAME] = entry
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding=ENCODING)
    return True


def default_agy_config() -> Path:
    return Path.home() / ".gemini" / "antigravity" / "mcp_config.json"


# --------------------------------------------------------------------------- setup de la máquina

SETUP_KEYS = ("url", "tool", "only", "fim", K_NUM_CTX)
PULL_TIMEOUT_S = 3600


def write_env_settings(env_path: Path, values: Mapping[str, Any]) -> bool:
    """Funde ``values`` en ``local_model`` de env.json sin tocar el resto. True si cambió algo."""
    data: Dict[str, Any] = {}
    if env_path.is_file():
        data = json.loads(env_path.read_text(encoding=ENCODING) or "{}")
    section = data.setdefault(KEY_ROOT, {})
    wanted = {k: v for k, v in values.items() if v not in (None, "")}
    if all(section.get(k) == v for k, v in wanted.items()):
        return False
    section.update(wanted)
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding=ENCODING)
    return True


def missing_models(settings: Settings, models: Sequence[str]) -> List[str]:
    """Modelos configurados (tool, only, fim) que Ollama no tiene descargados."""
    wanted = [m for m in (settings.tool_model, settings.only_model, settings.fim_model) if m]
    return [m for m in dict.fromkeys(wanted) if not _model_present(m, models)]


def pull_model(settings: Settings, model: str) -> None:
    """``ollama pull`` por la API (sin streaming). Lanza LocalModelError si falla."""
    data = _http_json(f"{settings.url}/api/pull", {"model": model, "stream": False}, PULL_TIMEOUT_S)
    if data.get("status") != "success":
        raise LocalModelError(f"No se pudo descargar {model}: {data.get('error') or data}")


def _setup_env_path(args: argparse.Namespace) -> Path:
    if args.env_dir:
        return Path(args.env_dir).expanduser() / aagy_config.ENV_FILE
    path = aagy_config.env_file()
    if path is None:
        raise LocalModelError(
            f"Falta {aagy_config.ENV_DIR_VAR}: define la carpeta privada de la máquina o pasa --env-dir."
        )
    return path


def _cmd_setup(args: argparse.Namespace, _settings: Settings) -> int:
    env_path = _setup_env_path(args)
    values = {k: getattr(args, k) for k in SETUP_KEYS}
    changed = write_env_settings(env_path, values)
    print(f"[aagy-local] {'actualizado' if changed else 'sin cambios'}: {env_path}")
    if args.env_dir and aagy_config.env_file() != env_path:
        print(f"  Aviso: define {aagy_config.ENV_DIR_VAR}={Path(args.env_dir).expanduser()} para que el plugin lo lea.")
    environ = {**os.environ, aagy_config.ENV_DIR_VAR: str(env_path.parent.parent)}
    settings = load_settings(environ=environ)
    try:
        missing = missing_models(settings, list_models(settings))
    except LocalModelError as exc:
        print(f"  {exc}. Sin Ollama, el modo auto se queda en off.")
        missing = []
    for model in missing:
        if not args.pull:
            print(f"  Falta {model}: ollama pull {model} (o repite con --pull).")
            continue
        print(f"  Descargando {model}...")
        pull_model(settings, model)
    if not args.no_agy:
        config = args.agy_config or default_agy_config()
        reg = register_agy(config, args.python)
        print(f"  Antigravity: {'registrado' if reg else 'ya estaba registrado'} en {config} (reinicia Antigravity).")
    return _cmd_status(argparse.Namespace(json=False), load_settings(environ=environ))


# --------------------------------------------------------------------------- CLI

def _cmd_status(args: argparse.Namespace, settings: Settings) -> int:
    status = get_status(settings)
    if args.json:
        print(json.dumps(asdict(status), ensure_ascii=False, indent=2))
        return 0
    print(f"[aagy-local] modo={status.mode} efectivo={status.effective} url={status.url}")
    print(f"  modelo de herramienta: {status.tool_model or '(sin configurar)'}"
          f" ({'descargado' if status.tool_model_present else 'no disponible'})")
    if status.reason:
        print(f"  {status.reason}")
    return 0


def _cmd_set(args: argparse.Namespace, settings: Settings) -> int:
    path = set_mode(args.command, settings)
    print(f"[aagy-local] local_model.mode={args.command} en {path}")
    if ALIASES["mode"] in os.environ:
        print(f"  Aviso: {ALIASES['mode']}={os.environ[ALIASES['mode']]} manda sobre el fichero en esta sesión.")
    return 0


def _cmd_run(args: argparse.Namespace, settings: Settings) -> int:
    params = dict(p.split("=", 1) for p in args.param or [] if "=" in p)
    payload: Dict[str, Any] = {"task": args.task, K_PARAMS: params}
    if args.path:
        payload["paths"] = args.path
    else:
        payload["text"] = sys.stdin.read()
    result = run_task(settings, payload)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if "error" in result else 0


def _cmd_bench(args: argparse.Namespace, settings: Settings) -> int:
    models = [m for m in (args.models.split(",") if args.models else [settings.tool_model, settings.only_model]) if m]
    if not models:
        print("[aagy-local] Sin modelos que medir (local_model.tool / --models).", file=sys.stderr)
        return 1
    import local_model_ops as ops  # noqa: PLC0415 - evita la importación circular

    root = _repo_root()
    results = [ops.bench_model(settings, model, root) for model in models]
    path = ops.bench_path(settings)
    ops.save_bench(results, path)
    for row in results:
        print(f"[aagy-local] {row['model']}: precisión {row['accuracy']} · {row['tokens_per_s']} tokens/s ({row['samples']} muestras)")
    print(f"  Guardado en {path}")
    return 0


def _cmd_only(args: argparse.Namespace, settings: Settings) -> int:
    import local_model_only as only  # noqa: PLC0415 - solo se carga en este modo

    if args.harness == "agy":
        return only.run_agy(settings)
    extra = [a for a in args.extra if a != "--"]
    return only.run_claude(settings, extra)


def _cmd_usage(_args: argparse.Namespace, _settings: Settings) -> int:
    summary = usage_summary()
    print(f"[aagy-local] {summary['calls']} llamadas ({summary['ok']} sin error), {summary['total_ms']} ms en total. {summary['path']}")
    return 0


def _cmd_register(args: argparse.Namespace, _settings: Settings) -> int:
    path = args.config or default_agy_config()
    changed = register_agy(path, args.python)
    print(f"[aagy-local] {'registrado' if changed else 'ya estaba registrado'} en {path}")
    return 0


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Modelo local con Ollama (aagy-local).")
    sub = parser.add_subparsers(dest="command", required=True)
    p_status = sub.add_parser("status", help="Modo pedido, modo efectivo y modelos.")
    p_status.add_argument("--json", action="store_true")
    for mode in (MODE_AUTO, MODE_OFF, MODE_TOOL):
        sub.add_parser(mode, help=f"Guarda local_model.mode={mode} en .governance/aagy.json.")
    sub.add_parser("on", help="Igual que 'tool'.")
    p_run = sub.add_parser("run", help="Ejecuta una tarea del catálogo (texto por stdin o --path).")
    p_run.add_argument("task")
    p_run.add_argument("--path", action="append")
    p_run.add_argument("--param", action="append", help="clave=valor")
    p_only = sub.add_parser("only", help="Sesión solo local: --harness claude (Claude Code) o agy (SDK de Antigravity).")
    p_only.add_argument("--harness", choices=("claude", "agy"), default="claude")
    p_only.add_argument("extra", nargs=argparse.REMAINDER, help="Argumentos para claude, tras --.")
    p_bench = sub.add_parser("bench", help="Mide precisión y tokens/s de los modelos con ficheros del repo.")
    p_bench.add_argument("--models", default="", help="Lista separada por comas (por defecto, los configurados).")
    sub.add_parser("usage", help="Resumen del registro de uso local (sin contenido).")
    p_reg = sub.add_parser("register-agy", help="Registra aagy-local en el mcp_config.json de Antigravity.")
    p_reg.add_argument("--config", type=Path, default=None)
    p_reg.add_argument("--python", default="python")
    p_setup = sub.add_parser("setup", help="Guarda los modelos en env.json de la máquina, comprueba Ollama y registra Antigravity.")
    p_setup.add_argument("--env-dir", default="", help=f"Carpeta privada de la máquina (por defecto, {aagy_config.ENV_DIR_VAR}).")
    p_setup.add_argument("--url", default="")
    p_setup.add_argument("--tool", default="", help="Modelo para tareas sencillas (local_run).")
    p_setup.add_argument("--only", default="", help="Modelo con llamadas a herramientas para el modo solo local.")
    p_setup.add_argument("--fim", default="", help="Modelo de autocompletado (Tab).")
    p_setup.add_argument("--num-ctx", dest="num_ctx", type=int, default=None)
    p_setup.add_argument("--pull", action="store_true", help="Descarga con Ollama los modelos que falten.")
    p_setup.add_argument("--no-agy", action="store_true", help="No registra el servidor en Antigravity.")
    p_setup.add_argument("--agy-config", type=Path, default=None)
    p_setup.add_argument("--python", default=sys.executable or "python", help="Intérprete para el servidor MCP (por defecto, el actual).")
    args = parser.parse_args(argv)
    if args.command == "on":
        args.command = MODE_TOOL
    return args


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding=ENCODING)
    args = parse_args(argv)
    settings = load_settings()
    handlers = {"status": _cmd_status, "run": _cmd_run, "bench": _cmd_bench, "only": _cmd_only, "usage": _cmd_usage, "register-agy": _cmd_register, "setup": _cmd_setup}
    try:
        return handlers.get(args.command, _cmd_set)(args, settings)
    except (LocalModelError, ValueError, OSError) as exc:
        print(f"[aagy-local] {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
