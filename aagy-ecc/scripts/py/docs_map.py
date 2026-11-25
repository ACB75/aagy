#!/usr/bin/env python3
"""
Resolvedor centralizado de rutas documentales vía `.governance/docs-map.json` (docs_map.py).

Soporta:
  - Esquema v2 (`/doc` numerado `00-governance`..`06-backlog` y subclave `paths`).
  - Esquema v1 parcial (claves de nivel superior en `docs-map.json`).
  - Fallback transparente a rutas clásicas heredadas (esquema v1: `doc/TODO.md`, `doc/TODO_DONE/`, etc.).
  - Validación estricta contra path traversal y rutas absolutas externas.

Cumple con SonarQube Quality Gate A (S3776 <= 15, S1192 sin duplicados, S107 <= 7).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path, PureWindowsPath
import re
import sys
from typing import Any, Dict, List, Optional, Sequence

DOCS_MAP_REL = ".governance/docs-map.json"
KEY_PATHS = "paths"
KEY_SCHEMA_VERSION = "schema_version"
DRIVE_PREFIX_REGEX = re.compile(r"^[A-Za-z]:")

ROLE_CONSTITUTION = "constitution"
ROLE_MAP = "map"
ROLE_CONTEXT = "context"
ROLE_STATUS = "status"
ROLE_HISTORY = "history"
ROLE_ADR_DIR = "adr_dir"
ROLE_ADR_INDEX = "adr_index"

LEGACY_DEFAULTS: Dict[str, str] = {
    ROLE_CONSTITUTION: "AGENTS.md",
    "doc_root": "doc",
    ROLE_MAP: "doc/INDEX.md",
    ROLE_CONTEXT: "doc/CONTEXT.md",
    ROLE_STATUS: "doc/STATUS.md",
    ROLE_HISTORY: "doc/LOG.md",
    "governance": "doc",
    "references": "doc",
    "templates": "doc/templates",
    ROLE_ADR_DIR: "doc/adr",
    ROLE_ADR_INDEX: "doc/adr/README.md",
    "adr_template": "doc/adr/TEMPLATE_ADR.md",
    "architecture": "doc/manual",
    "domain_and_flows": "doc/diagrams",
    "operations": "doc/manual",
    "postmortems": "doc/post-mortem",
    "postmortem_template": "doc/post-mortem/TEMPLATE_POSTMORTEM.md",
    "backlog": "doc",
    "ideas": "doc/IDEAS.md",
    "todo": "doc/TODO.md",
    "todo_done": "doc/TODO_DONE",
    "plans": "doc/plan",
    "quick": "doc/plan",
}

V2_DEFAULTS: Dict[str, str] = {
    ROLE_CONSTITUTION: "AGENTS.md",
    "doc_root": "doc",
    ROLE_MAP: "doc/INDEX.md",
    ROLE_CONTEXT: "doc/CONTEXT.md",
    ROLE_STATUS: "doc/STATUS.md",
    ROLE_HISTORY: "doc/LOG.md",
    "governance": "doc/00-governance",
    "references": "doc/00-governance/references",
    "templates": "doc/00-governance/templates",
    ROLE_ADR_DIR: "doc/02-adr",
    ROLE_ADR_INDEX: "doc/02-adr/README.md",
    "adr_template": "doc/00-governance/templates/TEMPLATE_ADR.md",
    "architecture": "doc/01-architecture",
    "domain_and_flows": "doc/03-domain-and-flows",
    "operations": "doc/04-operations",
    "postmortems": "doc/05-post-mortems",
    "postmortem_template": "doc/00-governance/templates/TEMPLATE_POSTMORTEM.md",
    "backlog": "doc/06-backlog",
    "ideas": "doc/06-backlog/IDEAS.md",
    "todo": "doc/06-backlog/TODO.md",
    "todo_done": "doc/06-backlog/done",
    "plans": "doc/06-backlog/plans",
    "quick": "doc/06-backlog/quick",
}

V1_TOP_LEVEL_KEYS: frozenset[str] = frozenset({
    ROLE_CONSTITUTION,
    ROLE_MAP,
    ROLE_CONTEXT,
    ROLE_STATUS,
    ROLE_HISTORY,
    ROLE_ADR_DIR,
    ROLE_ADR_INDEX,
})


def validate_repo_relative_path(repo_root: Path, rel_path: str) -> Path:
    """Valida que una ruta sea relativa al repositorio y resuelva estrictamente dentro de `repo_root`."""
    if not isinstance(rel_path, str):
        raise ValueError(f"La ruta debe ser una cadena de texto válida: {rel_path!r}")

    cleaned = rel_path.strip()
    if not cleaned or "\x00" in cleaned:
        raise ValueError(f"Ruta vacía o con byte nulo no permitida: {rel_path!r}")

    if (
        cleaned.startswith(("/", "\\"))
        or bool(DRIVE_PREFIX_REGEX.match(cleaned))
        or Path(cleaned).is_absolute()
        or PureWindowsPath(cleaned).is_absolute()
    ):
        raise ValueError(f"Se prohíbe ruta absoluta en docs-map.json: {rel_path!r}")

    root_resolved = repo_root.resolve()
    candidate = (root_resolved / cleaned).resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(
            f"Path traversal detectado: '{rel_path}' escapa fuera de '{root_resolved}'"
        ) from exc

    return candidate


@dataclass(frozen=True)
class DocsMap:
    """Representa el mapa de documentación resuelto para un repositorio."""

    repo_root: Path
    schema_version: int
    paths: Dict[str, str]

    def resolve(self, key: str) -> Path:
        """Retorna la ruta absoluta validada dentro del repositorio para la clave `key`."""
        if key not in self.paths:
            raise KeyError(f"Clave documental desconocida en docs-map: '{key}'")
        return validate_repo_relative_path(self.repo_root, self.paths[key])

    def relative(self, key: str) -> str:
        """Retorna la ruta relativa POSIX para la clave `key`."""
        if key not in self.paths:
            raise KeyError(f"Clave documental desconocida en docs-map: '{key}'")
        return self.paths[key].replace("\\", "/")

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el mapa resuelto en formato diccionario."""
        return {
            "repo_root": str(self.repo_root),
            KEY_SCHEMA_VERSION: self.schema_version,
            KEY_PATHS: dict(self.paths),
        }


def _read_docs_map_json(config_path: Path) -> Dict[str, Any]:
    try:
        raw_text = config_path.read_text(encoding="utf-8")
        data = json.loads(raw_text)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"Error leyendo '{config_path}': {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"'{config_path}' debe contener un objeto JSON.")
    return data


def _determine_schema_version(data: Dict[str, Any]) -> int:
    raw_version = data.get(KEY_SCHEMA_VERSION, 1)
    if not isinstance(raw_version, int) or raw_version not in (1, 2):
        raise ValueError(f"'{KEY_SCHEMA_VERSION}' inválido en docs-map.json: {raw_version!r}")
    return raw_version


def _overlay_mapping_entries(
    merged: Dict[str, str],
    entries: Dict[str, Any],
    allowed_keys: Optional[frozenset[str]] = None,
) -> None:
    for key, val in entries.items():
        if allowed_keys is not None and key not in allowed_keys:
            continue
        if not isinstance(val, str):
            raise ValueError(f"Valor inválido para '{key}' en docs-map.json: debe ser texto.")
        merged[key] = val.strip().replace("\\", "/")


def load_docs_map(repo_root: Path) -> DocsMap:
    """Carga `.governance/docs-map.json` o aplica fallback clásico si no existe."""
    resolved_root = repo_root.resolve()
    config_path = validate_repo_relative_path(resolved_root, DOCS_MAP_REL)

    if not config_path.exists():
        return DocsMap(repo_root=resolved_root, schema_version=1, paths=dict(LEGACY_DEFAULTS))

    data = _read_docs_map_json(config_path)
    schema_version = _determine_schema_version(data)
    base_defaults = V2_DEFAULTS if schema_version == 2 else LEGACY_DEFAULTS
    merged: Dict[str, str] = dict(base_defaults)

    _overlay_mapping_entries(merged, data, allowed_keys=V1_TOP_LEVEL_KEYS)

    sub_paths = data.get(KEY_PATHS)
    if sub_paths is not None:
        if not isinstance(sub_paths, dict):
            raise ValueError(f"La sección '{KEY_PATHS}' en docs-map.json debe ser un objeto JSON.")
        _overlay_mapping_entries(merged, sub_paths)

    for rel_val in merged.values():
        validate_repo_relative_path(resolved_root, rel_val)

    return DocsMap(repo_root=resolved_root, schema_version=schema_version, paths=merged)


def resolve_doc_path(repo_root: Path, key: str) -> Path:
    """Atajo para resolver la ruta absoluta dentro de `repo_root` para `key`."""
    return load_docs_map(repo_root).resolve(key)


def resolve_doc_rel(repo_root: Path, key: str) -> str:
    """Atajo para obtener la ruta relativa POSIX para `key`."""
    return load_docs_map(repo_root).relative(key)


def validate_docs_map_targets(repo_root: Path) -> List[str]:
    """Verifica integridad y existencia en disco de las rutas declaradas en `.governance/docs-map.json`."""
    resolved_root = repo_root.resolve()
    config_path = resolved_root / DOCS_MAP_REL
    if not config_path.is_file():
        return []

    issues: List[str] = []
    try:
        data = _read_docs_map_json(config_path)
        dmap = load_docs_map(resolved_root)
    except ValueError as exc:
        return [str(exc)]

    explicit_keys = [k for k in V1_TOP_LEVEL_KEYS if k in data]
    if isinstance(data.get(KEY_PATHS), dict):
        explicit_keys.extend(str(k) for k in data[KEY_PATHS].keys())

    for key in sorted(set(explicit_keys)):
        target = dmap.resolve(key)
        if not target.exists():
            issues.append(f"Clave '{key}' apunta a destino inexistente: '{dmap.relative(key)}'")

    return issues


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parsea argumentos CLI."""
    parser = argparse.ArgumentParser(
        description="Resolvedor de rutas documentales desde .governance/docs-map.json con fallback clásico."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Raíz del repositorio.")
    parser.add_argument("--key", type=str, default=None, help="Clave documental a resolver (ej. todo, todo_done).")
    parser.add_argument("--relative", action="store_true", help="Devuelve la ruta relativa en lugar de absoluta.")
    parser.add_argument("--validate", action="store_true", help="Valida que todas las rutas declaradas existan.")
    parser.add_argument("--json", action="store_true", help="Salida estructurada en formato JSON.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Punto de entrada CLI."""
    args = parse_args(argv)
    repo_root = args.repo_root.resolve()

    try:
        dmap = load_docs_map(repo_root)
        if args.validate:
            issues = validate_docs_map_targets(repo_root)
            if args.json:
                print(json.dumps({"valid": len(issues) == 0, "issues": issues, "schema_version": dmap.schema_version}, indent=2))
            elif issues:
                for issue in issues:
                    print(f"[FAIL] {issue}", file=sys.stderr)
            else:
                print(f"[PASS] .governance/docs-map.json (v{dmap.schema_version}) válido.")
            return 1 if issues else 0

        if args.key:
            result_val = dmap.relative(args.key) if args.relative else str(dmap.resolve(args.key))
            print(result_val)
            return 0

        if args.json:
            print(json.dumps(dmap.to_dict(), indent=2))
            return 0

        for k, v in sorted(dmap.paths.items()):
            print(f"{k}: {v}")
        return 0
    except (KeyError, ValueError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
