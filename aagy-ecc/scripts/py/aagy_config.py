#!/usr/bin/env python3
"""
Configuración externa de aagy en tres capas (aagy_config.py).

El plugin no guarda datos de ningún proyecto, usuario ni máquina. Todo lo que
depende de ellos se lee de fuera, por este orden (gana la primera que tenga la
clave):

1. Variables ``AAGY_<CLAVE>`` (``hosts.live.ip`` -> ``AAGY_HOSTS_LIVE_IP``).
2. Capa de proyecto: ``.governance/aagy.json`` en el repo consumidor (se busca
   desde el directorio actual hacia arriba). Lo propio del proyecto: lista de
   proyectos de commit, SDK compartido, puertas de calidad, sufijo de ingress.
3. Capa de entorno: ``<AAGY_ENV_DIR>/aagy/env.json``, en un repo privado de la
   máquina fuera de cualquier proyecto. Hosts, IPs, dominios, rutas y modelos
   locales. Sin secretos: los tokens se quedan en variables de entorno y el
   fichero solo guarda el nombre de la variable.
4. El valor por defecto que pase quien llama (neutro; si falta un dato, el
   script se salta el paso y avisa en vez de inventarlo).

Uso desde otros scripts::

    import aagy_config
    suffix = aagy_config.get("ingress.domain_suffix")

Uso desde PowerShell o bash::

    python aagy_config.py get hosts.live.ip
    python aagy_config.py show
    python aagy_config.py check

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
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

ENCODING = "utf-8"
ENV_DIR_VAR = "AAGY_ENV_DIR"
ENV_PREFIX = "AAGY_"
PROJECT_FILE = Path(".governance") / "aagy.json"
ENV_FILE = Path("aagy") / "env.json"

LAYER_VAR = "variable"
LAYER_PROJECT = "proyecto"
LAYER_ENV = "entorno"
LAYER_DEFAULT = "defecto"

STATUS_PASS = "PASS"
STATUS_WARN = "WARN"
STATUS_SKIP = "SKIP"

EXIT_OK = 0
EXIT_MISSING = 1
EXIT_INVALID = 2

# Claves de primer nivel que entiende cada capa. Una clave desconocida no rompe
# nada, pero el doctor avisa (suele ser una errata).
PROJECT_KEYS = frozenset({"projects", "sdk", "quality_gates", "ingress", "ci", "local_model", "budget", "consumer_refs"})
ENV_KEYS = frozenset({"hosts", "domains", "paths", "local_model", "secrets_env", "budget", "consumer_refs"})

# Un valor con pinta de secreto no debe estar en el fichero de entorno.
_SECRET_NAME_RE = re.compile(r"(token|secret|password|passwd|api[_-]?key|private[_-]?key)", re.IGNORECASE)
_KEY_RE = re.compile(r"^[a-z0-9_]+(\.[a-z0-9_]+)*$")


class ConfigError(ValueError):
    """Fichero de configuración ilegible o con forma inválida."""


@dataclass(frozen=True)
class Layer:
    """Una capa cargada: de dónde viene y qué contiene."""
    name: str
    path: Optional[Path]
    data: Mapping[str, Any]
    error: str = ""


@dataclass
class Config:
    """Las capas resueltas, en orden de prioridad."""
    environ: Mapping[str, str]
    project: Layer
    env: Layer
    warnings: List[str] = field(default_factory=list)

    def lookup(self, key: str) -> Tuple[Any, str]:
        """Devuelve (valor, capa) o (None, "") si ninguna capa tiene la clave."""
        if not _KEY_RE.match(key):
            raise ConfigError(f"Clave inválida '{key}': usa minúsculas, dígitos, '_' y '.'.")
        raw = self.environ.get(env_var_name(key))
        if raw is not None and raw.strip():
            return _parse_scalar(raw.strip()), LAYER_VAR
        for layer in (self.project, self.env):
            found, value = _dig(layer.data, key)
            if found:
                return value, layer.name
        return None, ""

    def get(self, key: str, default: Any = None) -> Any:
        value, layer = self.lookup(key)
        return default if not layer else value


def env_var_name(key: str) -> str:
    """``hosts.live.ip`` -> ``AAGY_HOSTS_LIVE_IP``."""
    return ENV_PREFIX + key.replace(".", "_").upper()


def _parse_scalar(raw: str) -> Any:
    """Las variables llegan como texto; acepta JSON (listas, números, booleanos) y si no, texto."""
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def _dig(data: Mapping[str, Any], key: str) -> Tuple[bool, Any]:
    node: Any = data
    for part in key.split("."):
        if not isinstance(node, Mapping) or part not in node:
            return False, None
        node = node[part]
    return True, node


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding=ENCODING))
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"No se puede leer {path}: {exc}") from exc
    except ValueError as exc:
        raise ConfigError(f"{path} no es JSON válido: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"{path} debe ser un objeto JSON.")
    return data


def _load_layer(name: str, path: Optional[Path]) -> Layer:
    if path is None or not path.is_file():
        return Layer(name, path, {})
    try:
        return Layer(name, path, _read_json(path))
    except ConfigError as exc:
        return Layer(name, path, {}, str(exc))


def find_project_file(start: Optional[Path] = None) -> Optional[Path]:
    """Busca .governance/aagy.json desde ``start`` hacia arriba; se para en la raíz del repo git."""
    current = (start or Path.cwd()).resolve()
    for folder in (current, *current.parents):
        candidate = folder / PROJECT_FILE
        if candidate.is_file():
            return candidate
        if (folder / ".git").exists():
            return None
    return None


def env_file(environ: Optional[Mapping[str, str]] = None) -> Optional[Path]:
    """Ruta de env.json según AAGY_ENV_DIR, o None si la variable no está."""
    env = os.environ if environ is None else environ
    raw = env.get(ENV_DIR_VAR, "").strip()
    if not raw:
        return None
    return Path(raw).expanduser() / ENV_FILE


def load(start: Optional[Path] = None, environ: Optional[Mapping[str, str]] = None) -> Config:
    """Carga las tres capas. Nunca lanza por un fichero roto: lo deja en ``Layer.error``."""
    env = dict(os.environ if environ is None else environ)
    project = _load_layer(LAYER_PROJECT, find_project_file(start))
    environment = _load_layer(LAYER_ENV, env_file(env))
    return Config(env, project, environment)


def get(key: str, default: Any = None, start: Optional[Path] = None, environ: Optional[Mapping[str, str]] = None) -> Any:
    """Atajo: valor de ``key`` en la primera capa que lo tenga, o ``default``."""
    return load(start, environ).get(key, default)


def paid_allowed(start: Optional[Path] = None, environ: Optional[Mapping[str, str]] = None) -> bool:
    """Presupuesto 0 $ por defecto: solo con ``budget`` (``AAGY_BUDGET``) mayor que 0 se activa algo de pago."""
    raw = get("budget", 0, start, environ)
    try:
        return float(raw) > 0
    except (TypeError, ValueError):
        return False


_COST_RE = re.compile(r"^\s*cost:\s*['\"]?(free|paid)['\"]?\s*$", re.MULTILINE)


def skill_cost(skill_md: Path) -> str:
    """``free``, ``paid`` o ``""`` según el frontmatter ``cost:`` (en la raíz o en ``metadata``)."""
    try:
        text = skill_md.read_text(encoding=ENCODING, errors="replace")
    except OSError:
        return ""
    head = text.split("---", 2)[1] if text.startswith("---") and text.count("---") >= 2 else ""
    match = _COST_RE.search(head)
    return match.group(1) if match else ""


def paid_skills(skills_dir: Path) -> List[str]:
    return sorted(p.parent.name for p in skills_dir.glob("*/SKILL.md") if skill_cost(p) == "paid")


def _unknown_keys(layer: Layer, known: frozenset) -> List[str]:
    return sorted(k for k in layer.data if k not in known)


def secret_like_values(data: Mapping[str, Any], prefix: str = "") -> List[str]:
    """Claves con nombre de secreto y un valor no vacío (``secrets_env`` guarda nombres de variable, se permite)."""
    found: List[str] = []
    for key, value in data.items():
        path = f"{prefix}{key}"
        if path == "secrets_env":
            continue
        if isinstance(value, Mapping):
            found.extend(secret_like_values(value, f"{path}."))
        elif _SECRET_NAME_RE.search(key) and value not in (None, "", [], {}):
            found.append(path)
    return found


def _layer_problems(layer: Layer, known: frozenset) -> List[str]:
    if layer.error:
        return [layer.error]
    unknown = _unknown_keys(layer, known)
    return [f"Claves desconocidas en {layer.path}: {', '.join(unknown)}"] if unknown else []


def _env_problems(cfg: Config) -> List[str]:
    env_dir = cfg.environ.get(ENV_DIR_VAR, "").strip()
    if not env_dir:
        return []
    root = Path(env_dir).expanduser()
    if not root.is_dir():
        return [f"{ENV_DIR_VAR} apunta a {root}, que no existe."]
    if cfg.env.path is None or not cfg.env.path.is_file():
        return [f"Falta {cfg.env.path} (capa de entorno)."]
    problems = _layer_problems(cfg.env, ENV_KEYS)
    secrets = secret_like_values(cfg.env.data)
    if secrets:
        problems.append(f"Posibles secretos en {cfg.env.path}: {', '.join(secrets)}. Guarda solo el nombre de la variable en secrets_env.")
    workflows = root / ".github" / "workflows"
    if workflows.is_dir() and any(workflows.iterdir()):
        problems.append(f"{workflows} tiene workflows de GitHub Actions; en un repo privado gastan minutos de pago.")
    return problems


def _actions_problems(cfg: Config) -> List[str]:
    """Workflows de Actions activos en un repo que declara ``ci.private``: gastan minutos de pago."""
    if cfg.project.path is None or not cfg.get("ci.private", False):
        return []
    workflows = cfg.project.path.parent.parent / ".github" / "workflows"
    if workflows.is_dir() and any(workflows.glob("*.y*ml")):
        return [f"{workflows} tiene workflows y el repo es privado (ci.private): gastan minutos de pago. Usa ci_local.py actions off."]
    return []


def doctor_findings(start: Optional[Path] = None, environ: Optional[Mapping[str, str]] = None) -> Tuple[str, str, List[str]]:
    """Resultado del check de configuración externa para los dos doctors: (estado, mensaje, evidencias)."""
    cfg = load(start, environ)
    problems = _layer_problems(cfg.project, PROJECT_KEYS) + _env_problems(cfg) + _actions_problems(cfg)
    evidence = [
        f"Proyecto: {cfg.project.path or 'sin ' + PROJECT_FILE.as_posix()}",
        f"Entorno: {cfg.env.path or 'sin ' + ENV_DIR_VAR}",
    ]
    if problems:
        return STATUS_WARN, problems[0], problems[1:6] + evidence
    if cfg.project.path is None and cfg.env.path is None:
        return STATUS_SKIP, f"Sin configuración externa ({PROJECT_FILE.as_posix()} ni {ENV_DIR_VAR}); los pasos que la necesitan se omiten.", evidence
    if cfg.env.path is None:
        return STATUS_PASS, f"Capa de proyecto válida; sin {ENV_DIR_VAR}, los pasos de entorno se omiten.", evidence
    return STATUS_PASS, "Capas de configuración válidas.", evidence


def _print_json(value: Any) -> None:
    if isinstance(value, str):
        print(value)
    else:
        print(json.dumps(value, ensure_ascii=False, indent=2))


def _cmd_get(args: argparse.Namespace, cfg: Config) -> int:
    value, layer = cfg.lookup(args.key)
    if not layer:
        if args.default is not None:
            print(args.default)
            return EXIT_OK
        print(f"[aagy-config] '{args.key}' no está en ninguna capa ({env_var_name(args.key)}, {PROJECT_FILE.as_posix()}, {ENV_DIR_VAR}).", file=sys.stderr)
        return EXIT_MISSING
    _print_json(value)
    return EXIT_OK


def _cmd_show(_args: argparse.Namespace, cfg: Config) -> int:
    overrides = sorted(k for k in cfg.environ if k.startswith(ENV_PREFIX) and k != ENV_DIR_VAR)
    _print_json({
        LAYER_VAR: overrides,
        LAYER_PROJECT: {"path": str(cfg.project.path or ""), "error": cfg.project.error, "data": cfg.project.data},
        LAYER_ENV: {"path": str(cfg.env.path or ""), "error": cfg.env.error, "data": cfg.env.data},
    })
    return EXIT_OK


def _cmd_check(args: argparse.Namespace, _cfg: Config) -> int:
    status, message, evidence = doctor_findings(args.start)
    print(f"[{status}] {message}")
    for line in evidence:
        print(f"  - {line}")
    return EXIT_INVALID if status == STATUS_WARN else EXIT_OK


def _cmd_paid_allowed(args: argparse.Namespace, _cfg: Config) -> int:
    allowed = paid_allowed(args.start)
    print("yes" if allowed else "no")
    return EXIT_OK if allowed else EXIT_MISSING


def _cmd_paid_skills(args: argparse.Namespace, _cfg: Config) -> int:
    for name in paid_skills(args.skills_dir):
        print(name)
    return EXIT_OK


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configuración externa de aagy (proyecto, entorno, variables AAGY_*).")
    parser.add_argument("--start", type=Path, default=None, help="Directorio desde el que buscar .governance/aagy.json.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_get = sub.add_parser("get", help="Imprime el valor de una clave (p. ej. hosts.live.ip).")
    p_get.add_argument("key")
    p_get.add_argument("--default", default=None, help="Valor si ninguna capa tiene la clave.")
    sub.add_parser("show", help="Muestra las capas cargadas.")
    sub.add_parser("check", help="Valida las capas (lo mismo que el check del doctor).")
    sub.add_parser("paid-allowed", help="yes/no: ¿se puede activar algo de pago? (budget o AAGY_BUDGET > 0).")
    p_paid = sub.add_parser("paid-skills", help="Skills con cost: paid en una carpeta de skills.")
    p_paid.add_argument("skills_dir", type=Path)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding=ENCODING)
    args = parse_args(argv)
    try:
        cfg = load(args.start)
        handler = {"get": _cmd_get, "show": _cmd_show, "check": _cmd_check,
                   "paid-allowed": _cmd_paid_allowed, "paid-skills": _cmd_paid_skills}[args.command]
        return handler(args, cfg)
    except ConfigError as exc:
        print(f"[aagy-config] {exc}", file=sys.stderr)
        return EXIT_INVALID


if __name__ == "__main__":
    sys.exit(main())
