#!/usr/bin/env python3
"""Analizador estatico de bloqueos DDL y concurrencia para PostgreSQL LTS en Home-Lab."""

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
logger = logging.getLogger("audit_pg_locks")

# Constantes de severidad y estado para prevenir duplicacion de literales (SonarQube S1192)
RISK_HIGH = "HIGH"
RISK_MEDIUM = "MEDIUM"
RISK_LOW = "LOW"
STATUS_PASS = "PASS"
STATUS_FAIL = "FAIL"
STATUS_SKIPPED = "SKIPPED"
LOCK_ACCESS_EXCLUSIVE = "ACCESS EXCLUSIVE"
LOCK_SHARE = "SHARE"

KEY_LOCK_STATUS = "lock_status"
KEY_TOTAL_STATEMENTS = "total_statements"
KEY_FINDINGS = "findings"
KEY_SUMMARY = "summary"

# Recomendaciones estandarizadas reutilizables
REC_CREATE_INDEX_CONCURRENTLY = (
    "Usar 'CREATE INDEX CONCURRENTLY' fuera de transacciones para evitar bloquear escrituras."
)
REC_DROP_INDEX_CONCURRENTLY = (
    "Usar 'DROP INDEX CONCURRENTLY' para evitar bloqueos exclusivos sobre consultas concurrentes."
)
REC_ADD_CONSTRAINT_NOT_VALID = (
    "Añadir constraint con 'NOT VALID' (bloqueo instantaneo) y validar despues con 'VALIDATE CONSTRAINT'."
)
REC_DROP_COLUMN_DEPRECATE = (
    "Deprecar columna en codigo de aplicacion antes de eliminarla; 'DROP COLUMN' adquiere ACCESS EXCLUSIVE."
)
REC_ALTER_COLUMN_TYPE_REWRITE = (
    "El cambio de tipo causa reescritura de tabla completa. Crear columna nueva, poblar y migrar."
)
REC_DROP_TABLE_EXCLUSIVE = (
    "'DROP TABLE' adquiere ACCESS EXCLUSIVE. Verificar archivado previo o renombrado temporal."
)
REC_TRUNCATE_EXCLUSIVE = (
    "'TRUNCATE' adquiere ACCESS EXCLUSIVE. Evaluar eliminacion por lotes si la tabla tiene trafico continuo."
)
REC_ADD_COLUMN_VOLATILE_DEFAULT = (
    "Añadir columna con valor default volatil reescribe la tabla. Añadir nullable y poblar en lotes."
)
REC_VACUUM_FULL_EXCLUSIVE = (
    "'VACUUM FULL' bloquea la tabla por completo. Usar 'pg_repack' o VACUUM estandar con autovacuum afinado."
)


@dataclass(frozen=True)
class DDLFinding:
    """Representacion inmutable de un hallazgo de bloqueo DDL en un archivo SQL."""

    file_path: str
    line_number: int
    risk_level: str
    lock_mode: str
    statement_snippet: str
    recommendation: str


# Reglas de deteccion lexica ordenadas por prioridad
DDL_RULES: list[tuple[re.Pattern[str], str, str, str]] = [
    # 1. VACUUM FULL
    (
        re.compile(r"\bVACUUM\s+FULL\b", re.IGNORECASE),
        RISK_HIGH,
        LOCK_ACCESS_EXCLUSIVE,
        REC_VACUUM_FULL_EXCLUSIVE,
    ),
    # 2. TRUNCATE
    (
        re.compile(r"\bTRUNCATE\s+(?:TABLE\s+)?([a-zA-Z0-9_\.]+)", re.IGNORECASE),
        RISK_HIGH,
        LOCK_ACCESS_EXCLUSIVE,
        REC_TRUNCATE_EXCLUSIVE,
    ),
    # 3. DROP TABLE
    (
        re.compile(r"\bDROP\s+TABLE\s+(?:IF\s+EXISTS\s+)?([a-zA-Z0-9_\.]+)", re.IGNORECASE),
        RISK_HIGH,
        LOCK_ACCESS_EXCLUSIVE,
        REC_DROP_TABLE_EXCLUSIVE,
    ),
    # 4. DROP COLUMN
    (
        re.compile(r"\bALTER\s+TABLE\s+.*?\bDROP\s+COLUMN\b", re.IGNORECASE | re.DOTALL),
        RISK_HIGH,
        LOCK_ACCESS_EXCLUSIVE,
        REC_DROP_COLUMN_DEPRECATE,
    ),
    # 5. ALTER COLUMN TYPE
    (
        re.compile(r"\bALTER\s+TABLE\s+.*?\bALTER\s+COLUMN\s+.*?\bTYPE\b", re.IGNORECASE | re.DOTALL),
        RISK_HIGH,
        LOCK_ACCESS_EXCLUSIVE,
        REC_ALTER_COLUMN_TYPE_REWRITE,
    ),
    # 6. ADD CONSTRAINT sin NOT VALID
    (
        re.compile(
            r"\bALTER\s+TABLE\s+.*?\bADD\s+CONSTRAINT\s+.*?\b(?:FOREIGN\s+KEY|CHECK)\b(?!.*?\bNOT\s+VALID\b)",
            re.IGNORECASE | re.DOTALL,
        ),
        RISK_HIGH,
        LOCK_ACCESS_EXCLUSIVE,
        REC_ADD_CONSTRAINT_NOT_VALID,
    ),
    # 7. ADD COLUMN con DEFAULT volatil (now, random, gen_random_uuid)
    (
        re.compile(
            r"\bALTER\s+TABLE\s+.*?\bADD\s+COLUMN\s+.*?\bDEFAULT\s+(?:now\(\)|random\(\)|uuid_generate\w*\(|gen_random_uuid\(\))",
            re.IGNORECASE | re.DOTALL,
        ),
        RISK_HIGH,
        LOCK_ACCESS_EXCLUSIVE,
        REC_ADD_COLUMN_VOLATILE_DEFAULT,
    ),
    # 8. CREATE INDEX sin CONCURRENTLY
    (
        re.compile(r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+(?!CONCURRENTLY\b)", re.IGNORECASE),
        RISK_MEDIUM,
        LOCK_SHARE,
        REC_CREATE_INDEX_CONCURRENTLY,
    ),
    # 9. DROP INDEX sin CONCURRENTLY
    (
        re.compile(r"\bDROP\s+INDEX\s+(?!CONCURRENTLY\b)", re.IGNORECASE),
        RISK_MEDIUM,
        LOCK_ACCESS_EXCLUSIVE,
        REC_DROP_INDEX_CONCURRENTLY,
    ),
]


def split_sql_statements(content: str) -> list[tuple[int, str]]:
    """Divide el contenido SQL en sentencias individuales manteniendo la linea de inicio."""
    statements: list[tuple[int, str]] = []
    lines = content.splitlines()
    current_stmt: list[str] = []
    start_line = 1

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        # Ignorar comentarios puros
        if stripped.startswith("--") or stripped.startswith("/*"):
            continue
        if not current_stmt:
            start_line = idx
        current_stmt.append(line)

        if ";" in line:
            full_stmt = "\n".join(current_stmt).strip()
            if full_stmt:
                statements.append((start_line, full_stmt))
            current_stmt = []

    if current_stmt:
        full_stmt = "\n".join(current_stmt).strip()
        if full_stmt:
            statements.append((start_line, full_stmt))

    return statements


def evaluate_statement(statement: str, line_no: int, file_path: str) -> DDLFinding | None:
    """Evalua una sentencia SQL frente a las reglas de bloqueos DDL."""
    clean_stmt = " ".join(statement.split())

    # Si es CREATE INDEX CONCURRENTLY o DROP INDEX CONCURRENTLY, es seguro
    if re.search(r"\bCREATE\s+(?:UNIQUE\s+)?INDEX\s+CONCURRENTLY\b", clean_stmt, re.IGNORECASE):
        return None
    if re.search(r"\bDROP\s+INDEX\s+CONCURRENTLY\b", clean_stmt, re.IGNORECASE):
        return None

    # Si es ADD CONSTRAINT con NOT VALID, es seguro
    if re.search(r"\bADD\s+CONSTRAINT\b.*?\bNOT\s+VALID\b", clean_stmt, re.IGNORECASE):
        return None

    snippet = clean_stmt[:80] + "..." if len(clean_stmt) > 80 else clean_stmt

    for pattern, risk, lock_mode, rec in DDL_RULES:
        if pattern.search(clean_stmt):
            return DDLFinding(
                file_path=file_path,
                line_number=line_no,
                risk_level=risk,
                lock_mode=lock_mode,
                statement_snippet=snippet,
                recommendation=rec,
            )
    return None


def audit_sql_content(content: str, file_name: str) -> dict[str, Any]:
    """Analiza una cadena de contenido SQL y devuelve los hallazgos de concurrencia."""
    statements = split_sql_statements(content)
    findings: list[dict[str, Any]] = []

    for line_no, stmt in statements:
        finding = evaluate_statement(stmt, line_no, file_name)
        if finding:
            findings.append(asdict(finding))

    status = STATUS_PASS if len(findings) == 0 else STATUS_FAIL
    return {
        KEY_LOCK_STATUS: status,
        KEY_TOTAL_STATEMENTS: len(statements),
        KEY_FINDINGS: findings,
        KEY_SUMMARY: f"Se detectaron {len(findings)} operaciones DDL de riesgo sobre {len(statements)} sentencias."
        if findings
        else f"{len(statements)} sentencias analizadas sin bloqueos exclusivos peligrosos.",
    }


def find_sql_files(target: Path) -> list[Path]:
    """Localiza todos los archivos .sql en un archivo, directorio o arbol."""
    if not target.exists():
        return []
    if target.is_file():
        return [target] if target.suffix.lower() == ".sql" else []

    excluded_dirs = {".git", ".pytest_cache", "node_modules", "skills", ".agents"}
    sql_files: list[Path] = []
    for p in target.rglob("*.sql"):
        try:
            rel_parts = p.relative_to(target).parts[:-1]
            if any(part in excluded_dirs for part in rel_parts):
                continue
            sql_files.append(p)
        except ValueError:
            sql_files.append(p)
    return sorted(sql_files)


def audit_sql_path(target_path: Path, strict: bool = True) -> dict[str, Any]:
    """Ejecuta la auditoria sobre un archivo o directorio SQL."""
    sql_files = find_sql_files(target_path)
    if not sql_files:
        return {
            KEY_LOCK_STATUS: STATUS_SKIPPED,
            KEY_TOTAL_STATEMENTS: 0,
            KEY_FINDINGS: [],
            KEY_SUMMARY: "No se detectaron archivos de migracion SQL; auditoria omitida.",
        }

    all_findings: list[dict[str, Any]] = []
    total_statements = 0

    for sql_file in sql_files:
        try:
            content = sql_file.read_text(encoding="utf-8", errors="ignore")
            file_result = audit_sql_content(content, str(sql_file))
            total_statements += file_result[KEY_TOTAL_STATEMENTS]
            all_findings.extend(file_result[KEY_FINDINGS])
        except OSError as err:
            logger.debug("Error leyendo archivo SQL %s: %s", sql_file, err)

    has_high = any(f["risk_level"] == RISK_HIGH for f in all_findings)
    has_medium = any(f["risk_level"] == RISK_MEDIUM for f in all_findings)

    if has_high or (strict and has_medium):
        status = STATUS_FAIL
    elif has_medium:
        status = "WARN"
    else:
        status = STATUS_PASS

    return {
        KEY_LOCK_STATUS: status,
        KEY_TOTAL_STATEMENTS: total_statements,
        KEY_FINDINGS: all_findings,
        KEY_SUMMARY: f"Auditoria finalizada sobre {len(sql_files)} archivos ({total_statements} sentencias). "
        f"Hallazgos: {len(all_findings)}.",
    }


def main() -> int:
    """Punto de entrada principal CLI."""
    parser = argparse.ArgumentParser(
        description="Analizador estatico de bloqueos DDL para PostgreSQL LTS en Home-Lab."
    )
    parser.add_argument("--file", type=Path, default=None, help="Archivo .sql especifico a auditar.")
    parser.add_argument("--dir", type=Path, default=None, help="Directorio con archivos .sql a auditar.")
    parser.add_argument("--root", type=Path, default=None, help="Raiz del repositorio.")
    parser.add_argument("--no-strict", action="store_true", help="No retornar error 1 ante riesgos MEDIUM.")
    parser.add_argument("--json", action="store_true", help="Salida estructurada en JSON.")
    args = parser.parse_args()

    target = args.file or args.dir or args.root or Path.cwd()
    result = audit_sql_path(target, strict=not args.no_strict)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = result[KEY_LOCK_STATUS]
        total = result[KEY_TOTAL_STATEMENTS]
        findings = result[KEY_FINDINGS]
        print(f"Estado de Auditoria DDL: [{status}]")
        print(f"Total de Sentencias SQL:  {total}")
        print(f"Total de Hallazgos:       {len(findings)}")

        if findings:
            print("\nDetalle de Operaciones de Riesgo:")
            for f in findings:
                print(f"  [{f['risk_level']}] {f['lock_mode']} en {f['file_path']}:{f['line_number']}")
                print(f"    Snippet: {f['statement_snippet']}")
                print(f"    Accion:  {f['recommendation']}\n")
        print(f"Resumen: {result[KEY_SUMMARY]}")

    if result[KEY_LOCK_STATUS] == STATUS_FAIL and not args.no_strict:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
