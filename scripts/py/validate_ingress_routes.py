#!/usr/bin/env python3
"""Validador estatico de congruencia entre Ingress Traefik, Split-DNS (CoreDNS) y catalogo /portal."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("validate_ingress_routes")

# Constantes de estado y claves para prevenir duplicacion de literales (SonarQube S1192)
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_SKIPPED = "SKIPPED"

KEY_INGRESS_STATUS = "ingress_status"
KEY_TRAEFIK_HOSTS = "traefik_hosts"
KEY_DNS_HOSTS = "dns_hosts"
KEY_PORTAL_HOSTS = "portal_hosts"
KEY_MISSING_IN_DNS = "missing_in_dns"
KEY_MISSING_IN_PORTAL = "missing_in_portal"
KEY_DNS_FIX_SUGGESTIONS = "dns_fix_suggestions"
KEY_PORTAL_FIX_SUGGESTIONS = "portal_fix_suggestions"
KEY_SUMMARY = "summary"

ZONE_HOME_LAB = "home.lab"

# Regex para extraccion de reglas Host(`...`) en etiquetas Traefik
_TRAEFIK_HOST_RULE_RE = re.compile(
    r"traefik\.http\.routers\.[a-zA-Z0-9_\-]+\.rule\s*=\s*Host\(`([^`]+)`\)",
    re.IGNORECASE,
)
_TRAEFIK_HOST_ALT_RE = re.compile(
    r"Host\([\"']?([a-zA-Z0-9_\-\.]+\.home\.lab)[\"']?\)",
    re.IGNORECASE,
)

# Regex para dominios locales en Corefile / archivos de zona
_HOMELAB_DOMAIN_RE = re.compile(r"\b([a-zA-Z0-9_\-]+\.home\.lab)\b", re.IGNORECASE)

# Regex para URLs en catalogo Go del portal
_PORTAL_URL_RE = re.compile(r"https?://([a-zA-Z0-9_\-]+\.home\.lab)", re.IGNORECASE)


def _extract_hosts_from_block(block: str, hosts: set[str]) -> None:
    """Extrae hosts de un bloque individual de servicio en compose."""
    if re.search(r"traefik\.enable\s*=\s*[\"']?false[\"']?", block, re.IGNORECASE):
        return

    for match in _TRAEFIK_HOST_RULE_RE.finditer(block):
        for raw_host in match.group(1).split(","):
            cleaned = raw_host.strip(" `\"'").lower()
            if cleaned:
                hosts.add(cleaned)

    for match in _TRAEFIK_HOST_ALT_RE.finditer(block):
        cleaned = match.group(1).strip().lower()
        if cleaned:
            hosts.add(cleaned)


def extract_traefik_hosts(content: str) -> set[str]:
    """Extrae todos los hostnames expuestos por Traefik en un docker-compose.yml."""
    hosts: set[str] = set()
    services = re.split(r"\n\s{2}[a-zA-Z0-9_\-]+:\s*\n", content)
    for block in services:
        _extract_hosts_from_block(block, hosts)
    return hosts


def extract_coredns_hosts(content: str) -> set[str]:
    """Extrae todos los hostnames registrados en un archivo Corefile o de zona DNS."""
    hosts: set[str] = set()
    for match in _HOMELAB_DOMAIN_RE.finditer(content):
        cleaned = match.group(1).strip().lower()
        if cleaned != ZONE_HOME_LAB:
            hosts.add(cleaned)
    return hosts


def extract_portal_hosts(content: str) -> set[str]:
    """Extrae los hostnames catalogados en cluster/cmd/server/main.go o configs del portal."""
    hosts: set[str] = set()
    for match in _PORTAL_URL_RE.finditer(content):
        cleaned = match.group(1).strip().lower()
        if cleaned != ZONE_HOME_LAB:
            hosts.add(cleaned)

    for match in _HOMELAB_DOMAIN_RE.finditer(content):
        cleaned = match.group(1).strip().lower()
        if cleaned != ZONE_HOME_LAB:
            hosts.add(cleaned)

    return hosts


def find_compose_files(root: Path) -> list[Path]:
    """Localiza archivos docker-compose*.yml o compose*.yml en la raiz o subcarpetas."""
    found: list[Path] = []
    for pattern in ["docker-compose*.yml", "docker-compose*.yaml", "compose*.yml", "compose*.yaml"]:
        found.extend(root.rglob(pattern))
    return sorted(list(set(found)))


def find_corefiles(root: Path) -> list[Path]:
    """Localiza archivos Corefile o zonas DNS en la raiz o subcarpetas."""
    found: list[Path] = []
    for pattern in ["Corefile*", "*.zone", "hosts*"]:
        found.extend(root.rglob(pattern))
    return sorted(list(set(found)))


def find_portal_sources(root: Path) -> list[Path]:
    """Localiza archivos fuente Go o JSON del portal de servicios."""
    server_dir = root / "cluster" / "cmd" / "server"
    if server_dir.exists():
        return list(server_dir.glob("*.go"))
    portal_candidates = list(root.rglob("portal*.json"))
    return portal_candidates


def validate_ingress_congruence(
    root_dir: Path | None = None,
    generate_fix: bool = False,
) -> dict[str, Any]:
    """Comprueba la congruencia trilateral entre Ingress Traefik, CoreDNS y /portal."""
    base_root = root_dir or Path.cwd()

    compose_files = find_compose_files(base_root)
    corefiles = find_corefiles(base_root)
    portal_files = find_portal_sources(base_root)

    # Si no se detectan archivos de infraestructura, omitir elegantemente
    if not compose_files and not corefiles and not portal_files:
        return {
            KEY_INGRESS_STATUS: STATUS_SKIPPED,
            KEY_TRAEFIK_HOSTS: [],
            KEY_DNS_HOSTS: [],
            KEY_PORTAL_HOSTS: [],
            KEY_MISSING_IN_DNS: [],
            KEY_MISSING_IN_PORTAL: [],
            KEY_SUMMARY: "No se detectaron archivos docker-compose ni CoreDNS; validacion omitida.",
        }

    traefik_hosts: set[str] = set()
    for cf in compose_files:
        try:
            content = cf.read_text(encoding="utf-8", errors="ignore")
            traefik_hosts.update(extract_traefik_hosts(content))
        except OSError as err:
            logger.debug("Error leyendo archivo compose %s: %s", cf, err)

    dns_hosts: set[str] = set()
    for df in corefiles:
        try:
            content = df.read_text(encoding="utf-8", errors="ignore")
            dns_hosts.update(extract_coredns_hosts(content))
        except OSError as err:
            logger.debug("Error leyendo archivo DNS %s: %s", df, err)

    portal_hosts: set[str] = set()
    for pf in portal_files:
        try:
            content = pf.read_text(encoding="utf-8", errors="ignore")
            portal_hosts.update(extract_portal_hosts(content))
        except OSError as err:
            logger.debug("Error leyendo archivo portal %s: %s", pf, err)

    missing_in_dns = sorted(traefik_hosts - dns_hosts)
    missing_in_portal = sorted(traefik_hosts - portal_hosts)

    is_passing = (len(missing_in_dns) == 0) and (len(missing_in_portal) == 0)
    status = STATUS_PASS if is_passing else STATUS_FAIL

    result: dict[str, Any] = {
        KEY_INGRESS_STATUS: status,
        KEY_TRAEFIK_HOSTS: sorted(list(traefik_hosts)),
        KEY_DNS_HOSTS: sorted(list(dns_hosts)),
        KEY_PORTAL_HOSTS: sorted(list(portal_hosts)),
        KEY_MISSING_IN_DNS: missing_in_dns,
        KEY_MISSING_IN_PORTAL: missing_in_portal,
        KEY_SUMMARY: f"Congruencia aprobada: {len(traefik_hosts)} hosts Traefik alineados con DNS y Portal."
        if is_passing
        else f"Discrepancias detectadas: {len(missing_in_dns)} faltantes en DNS, {len(missing_in_portal)} faltantes en Portal.",
    }

    if generate_fix:
        result[KEY_DNS_FIX_SUGGESTIONS] = [f"192.168.1.100 {h}" for h in missing_in_dns]
        result[KEY_PORTAL_FIX_SUGGESTIONS] = [
            f'{{Name: "{h.split(".")[0].title()}", URL: "https://{h}"}},' for h in missing_in_portal
        ]

    return result


def _print_fix_suggestions(result: dict[str, Any]) -> None:
    """Imprime sugerencias de configuracion faltante generadas con --fix."""
    dns_sugg = result.get(KEY_DNS_FIX_SUGGESTIONS)
    if dns_sugg:
        print("\nSugerencias para Corefile / Zona DNS:")
        for s in dns_sugg:
            print(f"  {s}")

    portal_sugg = result.get(KEY_PORTAL_FIX_SUGGESTIONS)
    if portal_sugg:
        print("\nSugerencias para Catalogo Go en /portal:")
        for s in portal_sugg:
            print(f"  {s}")


def _print_text_report(result: dict[str, Any], show_fix: bool) -> None:
    """Imprime el reporte en formato tabular legible para terminal."""
    status = result[KEY_INGRESS_STATUS]
    traefik = result[KEY_TRAEFIK_HOSTS]
    missing_dns = result[KEY_MISSING_IN_DNS]
    missing_portal = result[KEY_MISSING_IN_PORTAL]

    print(f"Estado de Congruencia Ingress: [{status}]")
    print(f"Hosts Traefik Detectados:      {len(traefik)}")
    print(f"Faltantes en Split-DNS:        {len(missing_dns)}")
    print(f"Faltantes en Catalogo Portal:  {len(missing_portal)}")

    if missing_dns:
        print("\nHosts Traefik sin registro en CoreDNS:")
        for h in missing_dns:
            print(f"  - {h}")

    if missing_portal:
        print("\nHosts Traefik no catalogados en /portal:")
        for h in missing_portal:
            print(f"  - {h}")

    if show_fix:
        _print_fix_suggestions(result)

    print(f"\nResumen: {result[KEY_SUMMARY]}")


def main() -> int:
    """Punto de entrada principal CLI."""
    parser = argparse.ArgumentParser(
        description="Validador de congruencia entre Ingress Traefik, Split-DNS (CoreDNS) y catalogo /portal."
    )
    parser.add_argument("--root", type=Path, default=None, help="Raiz del repositorio a validar.")
    parser.add_argument("--fix", action="store_true", help="Generar sugerencias de configuracion faltante.")
    parser.add_argument("--no-strict", action="store_true", help="No retornar error 1 ante discrepancias.")
    parser.add_argument("--json", action="store_true", help="Salida estructurada en JSON.")
    args = parser.parse_args()

    result = validate_ingress_congruence(root_dir=args.root, generate_fix=args.fix)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        _print_text_report(result, args.fix)

    if result[KEY_INGRESS_STATUS] == STATUS_FAIL and not args.no_strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
