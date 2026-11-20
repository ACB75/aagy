#!/usr/bin/env python3
"""Linter de paridad estatica de contratos entre microservicios y home-lab-sdk."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("audit_sdk_parity")

# Constantes de estado y claves para prevenir duplicacion de literales (SonarQube S1192)
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_SKIPPED = "SKIPPED"
KEY_PARITY_STATUS = "parity_status"
KEY_TOTAL_ENDPOINTS = "total_endpoints"
KEY_COVERED_ENDPOINTS = "covered_endpoints"
KEY_MISSING_ENDPOINTS = "missing_endpoints"
KEY_DETAILS = "details"

# Patrones de exclusion para rutas internas de infraestructura y diagnostico
EXCLUDED_ROUTE_PATTERNS = [
    re.compile(r"^/(metrics|health|healthz|livez|readyz|ping|status)$", re.IGNORECASE),
    re.compile(r"^/debug(/.*)?$", re.IGNORECASE),
    re.compile(r"^/(favicon\.ico|openapi\.json|docs|redoc|swagger(/.*)?)$", re.IGNORECASE),
]

# Regex para extraccion de rutas en Go (Gin, Chi, gorilla/mux, http)
_GO_GIN_CHI_RE = re.compile(
    r"\b(?:r|router|g|group|mux|v1|api)\.(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD|Get|Post|Put|Delete|Patch|Options|Head)\s*\(\s*[\"']([^\"']+)[\"']",
    re.MULTILINE,
)
_GO_HANDLE_RE = re.compile(
    r"\b(?:HandleFunc|Handle)\s*\(\s*[\"']([^\"']+)[\"']",
    re.MULTILINE,
)

# Regex para extraccion de rutas en Python (FastAPI / Flask)
_PY_ROUTE_RE = re.compile(
    r"@(?:app|router|bp|blueprint)\.(get|post|put|delete|patch)\s*\(\s*[\"']([^\"']+)[\"']",
    re.MULTILINE | re.IGNORECASE,
)

# Regex para extraccion de rutas en Java (Spring Boot)
_JAVA_MAPPING_CLASS_RE = re.compile(
    r"@RequestMapping\s*\(\s*(?:(?:value|path)\s*=\s*)?[\"']([^\"']+)[\"']",
    re.MULTILINE,
)
_JAVA_MAPPING_METHOD_RE = re.compile(
    r"@(Get|Post|Put|Delete|Patch)Mapping(?:\s*\(\s*(?:(?:value|path)\s*=\s*)?[\"']?([^\"'\)]*)[\"']?\s*\))?",
    re.MULTILINE,
)

# Regex para buscar cadenas de endpoint o path en archivos cliente SDK
_SDK_PATH_STRING_RE = re.compile(r"[\"'](/[a-zA-Z0-9_\-\.\/\{\}:]+)[\"']")


@dataclass(frozen=True)
class Endpoint:
    """Representacion inmutable de un endpoint expuesto por un microservicio."""

    method: str
    path: str
    source_file: str


def is_excluded_path(path: str) -> bool:
    """Determina si una ruta es interna de diagnostico y debe excluirse de la auditoria."""
    cleaned = path.strip()
    return any(pattern.match(cleaned) for pattern in EXCLUDED_ROUTE_PATTERNS)


def normalize_route_path(path: str) -> str:
    """Normaliza rutas reemplazando parametros tipo :id por {param}."""
    normalized = re.sub(r":([a-zA-Z0-9_]+)", r"{\1}", path.strip())
    if len(normalized) > 1 and normalized.endswith("/"):
        normalized = normalized[:-1]
    return normalized


def extract_endpoints_from_go(content: str, file_path: str) -> list[Endpoint]:
    """Extrae endpoints REST definidos en controladores Go."""
    endpoints: list[Endpoint] = []
    for match in _GO_GIN_CHI_RE.finditer(content):
        method = match.group(1).upper()
        raw_path = match.group(2)
        if not is_excluded_path(raw_path):
            endpoints.append(Endpoint(method=method, path=normalize_route_path(raw_path), source_file=file_path))
    for match in _GO_HANDLE_RE.finditer(content):
        raw_path = match.group(1)
        if not is_excluded_path(raw_path):
            endpoints.append(Endpoint(method="ANY", path=normalize_route_path(raw_path), source_file=file_path))
    return endpoints


def extract_endpoints_from_python(content: str, file_path: str) -> list[Endpoint]:
    """Extrae endpoints definidos en controladores FastAPI / Flask."""
    endpoints: list[Endpoint] = []
    for match in _PY_ROUTE_RE.finditer(content):
        method = match.group(1).upper()
        raw_path = match.group(2)
        if not is_excluded_path(raw_path):
            endpoints.append(Endpoint(method=method, path=normalize_route_path(raw_path), source_file=file_path))
    return endpoints


def extract_endpoints_from_java(content: str, file_path: str) -> list[Endpoint]:
    """Extrae endpoints definidos en controladores Spring Boot."""
    endpoints: list[Endpoint] = []
    base_prefix = ""
    class_match = _JAVA_MAPPING_CLASS_RE.search(content)
    if class_match:
        base_prefix = normalize_route_path(class_match.group(1))

    for match in _JAVA_MAPPING_METHOD_RE.finditer(content):
        method = match.group(1).upper()
        sub_path = match.group(2) or ""
        normalized_sub = normalize_route_path(sub_path)
        full_path = f"{base_prefix}/{normalized_sub.lstrip('/')}".rstrip("/")
        if not full_path.startswith("/"):
            full_path = "/" + full_path
        if not is_excluded_path(full_path):
            endpoints.append(Endpoint(method=method, path=full_path, source_file=file_path))
    return endpoints


def extract_endpoints_from_file(file_path: Path) -> list[Endpoint]:
    """Lee y extrae endpoints segun la extension del archivo de controlador."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except OSError as err:
        logger.debug("No se pudo leer archivo %s: %s", file_path, err)
        return []

    ext = file_path.suffix.lower()
    rel_path = str(file_path)
    if ext == ".go":
        return extract_endpoints_from_go(content, rel_path)
    if ext == ".py":
        return extract_endpoints_from_python(content, rel_path)
    if ext == ".java":
        return extract_endpoints_from_java(content, rel_path)
    return []


def extract_endpoints_from_services(services_dir: Path) -> list[Endpoint]:
    """Escanea recursivamente los controladores de microservicios y devuelve endpoints unicos."""
    if not services_dir.exists():
        return []

    endpoints_dict: dict[tuple[str, str], Endpoint] = {}
    valid_extensions = {".go", ".py", ".java"}

    for path in services_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in valid_extensions:
            # Excluir suites de tests internas de servicios
            if "test" in path.name.lower() or "_test.go" in path.name:
                continue
            for ep in extract_endpoints_from_file(path):
                key = (ep.method, ep.path)
                if key not in endpoints_dict:
                    endpoints_dict[key] = ep

    return list(endpoints_dict.values())


def extract_sdk_patterns(sdk_dir: Path) -> set[str]:
    """Extrae las rutas, literales y patrones declarados en las bibliotecas cliente de home-lab-sdk."""
    patterns: set[str] = set()
    if not sdk_dir.exists():
        return patterns

    valid_sdk_extensions = {".ts", ".go", ".py", ".java", ".js"}
    for path in sdk_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in valid_sdk_extensions:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
                for match in _SDK_PATH_STRING_RE.finditer(text):
                    normalized = normalize_route_path(match.group(1))
                    patterns.add(normalized)
            except OSError as err:
                logger.debug("Error leyendo archivo SDK %s: %s", path, err)

    return patterns


def is_endpoint_covered(endpoint: Endpoint, sdk_patterns: set[str]) -> bool:
    """Comprueba si un endpoint de microservicio esta cubierto por algun patron del SDK."""
    if endpoint.path in sdk_patterns:
        return True

    # Comprobacion de coincidencia difusa para rutas parametrizadas ej. /api/v1/users/{id}
    clean_ep = re.sub(r"\{[a-zA-Z0-9_]+\}", "", endpoint.path).rstrip("/")
    for pat in sdk_patterns:
        clean_pat = re.sub(r"\{[a-zA-Z0-9_]+\}", "", pat).rstrip("/")
        if clean_ep and clean_ep == clean_pat:
            return True
    return False


def resolve_directories(
    root_dir: Path | None,
    services_dir_arg: Path | None,
    sdk_dir_arg: Path | None,
) -> tuple[Path | None, Path | None]:
    """Resuelve las rutas de directorios de microservicios y SDK."""
    base_root = root_dir or Path.cwd()
    resolved_services = services_dir_arg or (base_root / "services")
    resolved_sdk = sdk_dir_arg or (base_root / "home-lab-sdk")

    # Si services no existe pero cluster existe, buscar en cluster
    if not resolved_services.exists() and (base_root / "cluster").exists():
        resolved_services = base_root / "cluster"

    return resolved_services, resolved_sdk


def audit_sdk_parity(
    root_dir: Path | None = None,
    services_dir: Path | None = None,
    sdk_dir: Path | None = None,
    strict: bool = True,
) -> dict[str, Any]:
    """Ejecuta la auditoria estatica de paridad entre microservicios y home-lab-sdk."""
    res_services, res_sdk = resolve_directories(root_dir, services_dir, sdk_dir)

    # Si ninguno de los dos directorios existe, omitir con exito para no bloquear repositorios de tooling
    if not (res_services and res_services.exists()) and not (res_sdk and res_sdk.exists()):
        return {
            KEY_PARITY_STATUS: STATUS_SKIPPED,
            KEY_TOTAL_ENDPOINTS: 0,
            KEY_COVERED_ENDPOINTS: 0,
            KEY_MISSING_ENDPOINTS: [],
            KEY_DETAILS: "No se detectaron directorios de microservicios ni home-lab-sdk; auditoria omitida.",
        }

    endpoints = extract_endpoints_from_services(res_services) if res_services and res_services.exists() else []
    sdk_patterns = extract_sdk_patterns(res_sdk) if res_sdk and res_sdk.exists() else set()

    covered: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []

    for ep in endpoints:
        ep_dict = asdict(ep)
        if is_endpoint_covered(ep, sdk_patterns):
            covered.append(ep_dict)
        else:
            missing.append(ep_dict)

    is_passing = len(missing) == 0
    status = STATUS_PASS if is_passing else STATUS_FAIL

    return {
        KEY_PARITY_STATUS: status,
        KEY_TOTAL_ENDPOINTS: len(endpoints),
        KEY_COVERED_ENDPOINTS: len(covered),
        KEY_MISSING_ENDPOINTS: missing,
        KEY_DETAILS: f"{len(covered)}/{len(endpoints)} endpoints cubiertos en SDK."
        if is_passing
        else f"{len(missing)} endpoints carecen de cliente en SDK.",
    }


def main() -> int:
    """Punto de entrada principal CLI."""
    parser = argparse.ArgumentParser(
        description="Audita la paridad estatica entre microservicios y home-lab-sdk."
    )
    parser.add_argument("--root", type=Path, default=None, help="Raiz del repositorio a auditar.")
    parser.add_argument("--services-dir", type=Path, default=None, help="Directorio de microservicios.")
    parser.add_argument("--sdk-dir", type=Path, default=None, help="Directorio de home-lab-sdk.")
    parser.add_argument("--no-strict", action="store_true", help="No retornar error 1 ante divergencias.")
    parser.add_argument("--json", action="store_true", help="Salida estructurada en JSON.")
    args = parser.parse_args()

    result = audit_sdk_parity(
        root_dir=args.root,
        services_dir=args.services_dir,
        sdk_dir=args.sdk_dir,
        strict=not args.no_strict,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = result[KEY_PARITY_STATUS]
        total = result[KEY_TOTAL_ENDPOINTS]
        covered = result[KEY_COVERED_ENDPOINTS]
        print(f"Estado de Paridad SDK: [{status}]")
        print(f"Total de Endpoints Publicos: {total}")
        print(f"Endpoints Cubiertos en SDK:  {covered}")
        if result[KEY_MISSING_ENDPOINTS]:
            print("\nEndpoints Huerfanos (sin cliente en SDK):")
            for ep in result[KEY_MISSING_ENDPOINTS]:
                print(f"  - [{ep['method']}] {ep['path']} (fuente: {ep['source_file']})")
        print(f"\nDetalles: {result[KEY_DETAILS]}")

    if result[KEY_PARITY_STATUS] == STATUS_FAIL and not args.no_strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
