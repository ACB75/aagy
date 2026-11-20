#!/usr/bin/env python3
"""Suite de pruebas unitarias para el linter de paridad estatica de contratos SDK."""

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

from audit_sdk_parity import (
    Endpoint,
    audit_sdk_parity,
    extract_endpoints_from_services,
    extract_sdk_patterns,
    is_excluded_path,
)


def test_is_excluded_path() -> None:
    """Verifica el filtrado de rutas internas de infraestructura."""
    assert is_excluded_path("/metrics") is True
    assert is_excluded_path("/health") is True
    assert is_excluded_path("/healthz") is True
    assert is_excluded_path("/livez") is True
    assert is_excluded_path("/readyz") is True
    assert is_excluded_path("/ping") is True
    assert is_excluded_path("/debug/pprof") is True
    assert is_excluded_path("/favicon.ico") is True

    # Rutas publicas de negocio NO deben ser excluidas
    assert is_excluded_path("/api/v1/auth/login") is False
    assert is_excluded_path("/api/v1/users") is False
    assert is_excluded_path("/health/report") is False


def test_skip_when_no_services_or_sdk_dir(tmp_path: Path) -> None:
    """Verifica omision limpia cuando no existen directorios de microservicios ni SDK."""
    result = audit_sdk_parity(root_dir=tmp_path)
    assert result["parity_status"] == "SKIPPED"
    assert result["total_endpoints"] == 0
    assert result["missing_endpoints"] == []


def test_parity_pass_when_all_endpoints_covered(tmp_path: Path) -> None:
    """Verifica aprobacion de paridad cuando todos los endpoints tienen cliente SDK."""
    services_dir = tmp_path / "services" / "whoiam"
    services_dir.mkdir(parents=True)
    go_controller = services_dir / "routes.go"
    go_controller.write_text(
        """package main

func registerRoutes(r *gin.Engine) {
    r.GET("/api/v1/auth/login", loginHandler)
    r.POST("/api/v1/users", createUserHandler)
    r.GET("/metrics", prometheusHandler)
}
""",
        encoding="utf-8",
    )

    sdk_dir = tmp_path / "home-lab-sdk" / "frontend"
    sdk_dir.mkdir(parents=True)
    ts_client = sdk_dir / "whoiam-client.ts"
    ts_client.write_text(
        """export class WhoIamClient {
    login() { return this.http.get('/api/v1/auth/login'); }
    createUser(u: User) { return this.http.post('/api/v1/users', u); }
}
""",
        encoding="utf-8",
    )

    result = audit_sdk_parity(root_dir=tmp_path)
    assert result["parity_status"] == "PASS"
    assert result["total_endpoints"] == 2  # /metrics fue excluido
    assert len(result["missing_endpoints"]) == 0


def test_parity_fail_when_endpoint_missing_in_sdk(tmp_path: Path) -> None:
    """Verifica deteccion de divergencia cuando un endpoint no esta cubierto en SDK."""
    services_dir = tmp_path / "services" / "kakebo"
    services_dir.mkdir(parents=True)
    go_controller = services_dir / "router.go"
    go_controller.write_text(
        """package main

func routes(r *chi.Mux) {
    r.Get("/api/v1/transactions", listTransactions)
    r.Post("/api/v1/transactions/export", exportCsv)
}
""",
        encoding="utf-8",
    )

    sdk_dir = tmp_path / "home-lab-sdk" / "frontend"
    sdk_dir.mkdir(parents=True)
    ts_client = sdk_dir / "kakebo-client.ts"
    ts_client.write_text(
        """export class KakeboClient {
    getTransactions() { return this.http.get('/api/v1/transactions'); }
}
""",
        encoding="utf-8",
    )

    result = audit_sdk_parity(root_dir=tmp_path)
    assert result["parity_status"] == "FAIL"
    assert result["total_endpoints"] == 2
    assert len(result["missing_endpoints"]) == 1
    assert result["missing_endpoints"][0]["path"] == "/api/v1/transactions/export"


def test_python_and_java_controller_extraction(tmp_path: Path) -> None:
    """Verifica extraccion de controladores en Python (FastAPI) y Java (Spring Boot)."""
    services_dir = tmp_path / "services" / "mixed"
    services_dir.mkdir(parents=True)

    py_ctrl = services_dir / "app.py"
    py_ctrl.write_text(
        """from fastapi import FastAPI
app = FastAPI()

@app.get("/api/v1/items")
async def get_items(): return []

@router.delete("/api/v1/items/{item_id}")
async def delete_item(item_id: str): pass
""",
        encoding="utf-8",
    )

    java_ctrl = services_dir / "OrderController.java"
    java_ctrl.write_text(
        """package com.homelab.orders;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {
    @GetMapping
    public List<Order> list() { return List.of(); }

    @PostMapping("/{orderId}/pay")
    public void pay(@PathVariable String orderId) {}
}
""",
        encoding="utf-8",
    )

    endpoints = extract_endpoints_from_services(services_dir)
    paths = {ep.path for ep in endpoints}
    assert "/api/v1/items" in paths
    assert "/api/v1/items/{item_id}" in paths
    assert "/api/v1/orders" in paths
    assert "/api/v1/orders/{orderId}/pay" in paths


def test_cli_json_execution(tmp_path: Path) -> None:
    """Verifica invocacion via CLI con salida estructurada JSON."""
    script_path = _SCRIPTS_DIR / "audit_sdk_parity.py"
    proc = subprocess.run(
        [sys.executable, str(script_path), "--root", str(tmp_path), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["parity_status"] == "SKIPPED"
    assert "total_endpoints" in data
