#!/usr/bin/env python3
"""Suite de pruebas unitarias para el analizador de bloqueos DDL en PostgreSQL LTS."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Asegurar import de modulos ecc-agy
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts" / "ecc-agy"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from audit_pg_locks import (
    RISK_HIGH,
    RISK_LOW,
    RISK_MEDIUM,
    STATUS_FAIL,
    STATUS_PASS,
    STATUS_SKIPPED,
    audit_sql_content,
    audit_sql_path,
)


def test_skip_when_no_sql_files(tmp_path: Path) -> None:
    """Verifica omision limpia cuando no existen archivos SQL."""
    result = audit_sql_path(tmp_path)
    assert result["lock_status"] == STATUS_SKIPPED
    assert result["total_statements"] == 0
    assert result["findings"] == []


def test_detect_dangerous_create_index() -> None:
    """Verifica deteccion de CREATE INDEX sin CONCURRENTLY (riesgo MEDIUM)."""
    sql = "CREATE INDEX idx_users_email ON users(email);"
    result = audit_sql_content(sql, "migration.sql")
    assert result["lock_status"] == STATUS_FAIL
    assert len(result["findings"]) == 1
    finding = result["findings"][0]
    assert finding["risk_level"] == RISK_MEDIUM
    assert "CONCURRENTLY" in finding["recommendation"]


def test_detect_safe_create_index_concurrently() -> None:
    """Verifica aprobacion de CREATE INDEX CONCURRENTLY (riesgo LOW / PASS)."""
    sql = "CREATE INDEX CONCURRENTLY idx_users_email ON users(email);"
    result = audit_sql_content(sql, "migration.sql")
    assert result["lock_status"] == STATUS_PASS
    assert len(result["findings"]) == 0


def test_detect_unvalidated_foreign_key() -> None:
    """Verifica deteccion de ADD CONSTRAINT sin NOT VALID (riesgo HIGH)."""
    sql = "ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);"
    result = audit_sql_content(sql, "001_fk.sql")
    assert result["lock_status"] == STATUS_FAIL
    assert len(result["findings"]) == 1
    finding = result["findings"][0]
    assert finding["risk_level"] == RISK_HIGH
    assert "NOT VALID" in finding["recommendation"]


def test_detect_safe_constraint_with_not_valid() -> None:
    """Verifica aprobacion de ADD CONSTRAINT ... NOT VALID y VALIDATE CONSTRAINT."""
    sql = """
    ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID;
    ALTER TABLE orders VALIDATE CONSTRAINT fk_user;
    """
    result = audit_sql_content(sql, "safe_fk.sql")
    assert result["lock_status"] == STATUS_PASS
    assert len(result["findings"]) == 0


def test_detect_table_rewrite_operations() -> None:
    """Verifica deteccion de DROP COLUMN y ALTER COLUMN TYPE (riesgo HIGH)."""
    sql = """
    ALTER TABLE products DROP COLUMN legacy_code;
    ALTER TABLE products ALTER COLUMN price TYPE numeric(12, 4);
    """
    result = audit_sql_content(sql, "rewrite.sql")
    assert result["lock_status"] == STATUS_FAIL
    assert len(result["findings"]) == 2
    for f in result["findings"]:
        assert f["risk_level"] == RISK_HIGH


def test_detect_truncate_and_drop_table() -> None:
    """Verifica deteccion de TRUNCATE y DROP TABLE (riesgo HIGH)."""
    sql = """
    TRUNCATE TABLE temp_logs;
    DROP TABLE old_cache CASCADE;
    """
    result = audit_sql_content(sql, "cleanup.sql")
    assert result["lock_status"] == STATUS_FAIL
    assert len(result["findings"]) == 2
    assert result["findings"][0]["risk_level"] == RISK_HIGH
    assert result["findings"][1]["risk_level"] == RISK_HIGH


def test_cli_execution_with_file(tmp_path: Path) -> None:
    """Verifica ejecucion CLI con archivo seguro y salida JSON."""
    safe_sql = tmp_path / "safe.sql"
    safe_sql.write_text("CREATE INDEX CONCURRENTLY idx_item ON items(name);", encoding="utf-8")

    script_path = _SCRIPTS_DIR / "audit_pg_locks.py"
    proc = subprocess.run(
        [sys.executable, str(script_path), "--file", str(safe_sql), "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0
    data = json.loads(proc.stdout)
    assert data["lock_status"] == STATUS_PASS
