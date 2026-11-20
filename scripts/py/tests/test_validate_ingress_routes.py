#!/usr/bin/env python3
"""Suite de pruebas unitarias para el validador de congruencia Ingress, Split-DNS y Portal."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Asegurar import de modulos ecc-agy
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "py"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from validate_ingress_routes import (
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIPPED,
    extract_coredns_hosts,
    extract_portal_hosts,
    extract_traefik_hosts,
    validate_ingress_congruence,
)


def test_skip_when_no_ingress_infrastructure(tmp_path: Path) -> None:
    """Verifica omision limpia cuando no existen archivos de infraestructura."""
    result = validate_ingress_congruence(root_dir=tmp_path)
    assert result["ingress_status"] == STATUS_SKIPPED
    assert result["traefik_hosts"] == []
    assert result["missing_in_dns"] == []
    assert result["missing_in_portal"] == []


def test_congruent_ingress_dns_portal_pass(tmp_path: Path) -> None:
    """Verifica aprobacion cuando hay congruencia trilateral total."""
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """version: '3.8'
services:
  whoiam:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.whoiam.rule=Host(`whoiam.home.lab`)"
  kakebo:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.kakebo.rule=Host(`kakebo.home.lab`)"
  postgres:
    labels:
      - "traefik.enable=false"
""",
        encoding="utf-8",
    )

    corefile = tmp_path / "Corefile"
    corefile.write_text(
        """home.lab:53 {
    hosts {
        192.168.1.100 whoiam.home.lab
        192.168.1.100 kakebo.home.lab
        fallthrough
    }
}
""",
        encoding="utf-8",
    )

    portal_dir = tmp_path / "cluster" / "cmd" / "server"
    portal_dir.mkdir(parents=True)
    portal_go = portal_dir / "main.go"
    portal_go.write_text(
        """package main

var catalog = []Service{
    {Name: "WhoIAm", URL: "https://whoiam.home.lab"},
    {Name: "Kakebo", URL: "https://kakebo.home.lab"},
}
""",
        encoding="utf-8",
    )

    result = validate_ingress_congruence(root_dir=tmp_path)
    assert result["ingress_status"] == STATUS_PASS
    assert set(result["traefik_hosts"]) == {"whoiam.home.lab", "kakebo.home.lab"}
    assert result["missing_in_dns"] == []
    assert result["missing_in_portal"] == []


def test_missing_dns_record_fail(tmp_path: Path) -> None:
    """Verifica deteccion de host Traefik sin registro en CoreDNS."""
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """services:
  citadel:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.citadel.rule=Host(`citadel.home.lab`)"
""",
        encoding="utf-8",
    )

    corefile = tmp_path / "Corefile"
    corefile.write_text("192.168.1.100 other.home.lab", encoding="utf-8")

    result = validate_ingress_congruence(root_dir=tmp_path)
    assert result["ingress_status"] == STATUS_FAIL
    assert "citadel.home.lab" in result["missing_in_dns"]


def test_missing_portal_entry_fail(tmp_path: Path) -> None:
    """Verifica deteccion de host publicado ausente en el catalogo /portal."""
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """services:
  monitor:
    labels:
      - "traefik.http.routers.monitor.rule=Host(`monitor.home.lab`)"
""",
        encoding="utf-8",
    )

    corefile = tmp_path / "Corefile"
    corefile.write_text("192.168.1.100 monitor.home.lab", encoding="utf-8")

    portal_dir = tmp_path / "cluster" / "cmd" / "server"
    portal_dir.mkdir(parents=True)
    portal_go = portal_dir / "main.go"
    portal_go.write_text('var catalog = []string{"https://other.home.lab"}', encoding="utf-8")

    result = validate_ingress_congruence(root_dir=tmp_path)
    assert result["ingress_status"] == STATUS_FAIL
    assert "monitor.home.lab" in result["missing_in_portal"]


def test_fix_suggestions_generated(tmp_path: Path) -> None:
    """Verifica que el modo --fix emita sugerencias estructuradas de configuracion."""
    compose_file = tmp_path / "docker-compose.yml"
    compose_file.write_text(
        """services:
  app:
    labels:
      - "traefik.http.routers.app.rule=Host(`app.home.lab`)"
""",
        encoding="utf-8",
    )

    corefile = tmp_path / "Corefile"
    corefile.write_text("", encoding="utf-8")

    result = validate_ingress_congruence(root_dir=tmp_path, generate_fix=True)
    assert result["ingress_status"] == STATUS_FAIL
    assert "dns_fix_suggestions" in result
    assert any("app.home.lab" in s for s in result["dns_fix_suggestions"])


def test_cli_json_execution(tmp_path: Path) -> None:
    """Verifica invocacion via CLI con salida JSON."""
    script_path = _SCRIPTS_DIR / "validate_ingress_routes.py"
    proc = subprocess.run(
        [sys.executable, str(script_path), "--root", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["ingress_status"] == STATUS_SKIPPED
