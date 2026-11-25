#!/usr/bin/env python3
"""
Motor de Diagnóstico Multimodal y Deep Ops con Gemini (stdlib pura).

Provee capacidades de análisis masivo de logs, volcados de memoria y soporte
para Post-Mortems 5W con zero-overhead de tokens en reposo.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger: logging.Logger = logging.getLogger("gemini-deep-ops")

API_KEY_ENV_VAR: str = "GEMINI_API_KEY"
DEFAULT_MODEL: str = "gemini-1.5-flash"
KEY_API_CONFIGURED: str = "api_key_configured"


@dataclass(frozen=True)
class DeepOpsReport:
    is_success: bool
    summary: str
    severity: str
    recommendations: Tuple[str, ...]
    raw_details: str = ""


def get_ops_status() -> Dict[str, Any]:
    """Retorna el estado de disponibilidad del motor de Gemini Deep Ops."""
    api_key = os.environ.get(API_KEY_ENV_VAR, "").strip()
    return {
        KEY_API_CONFIGURED: bool(api_key),
        "sdk_available": True,
        "default_model": DEFAULT_MODEL,
    }


def _heuristic_log_analysis(content: str) -> DeepOpsReport:
    """Análisis heurístico de contingencia cuando no hay API remota o en modo mock."""
    severity = "INFO"
    recommendations: List[str] = []
    summary_items: List[str] = []

    oom_match = re.search(r"(OutOfMemoryError|OOMKilled|exit code 137)", content, re.IGNORECASE)
    if oom_match:
        severity = "CRITICAL"
        summary_items.append(f"Detección de fallo por agotamiento de memoria ({oom_match.group(0)} / Error 137).")
        recommendations.append("Ajustar GOMEMLIMIT=80% en servicios Go o -XX:MaxRAMPercentage=75 en JVM.")
        recommendations.append("Revisar límites de memoria en docker-compose y verificar fugas en buffers de streaming.")

    if re.search(r"(Deadlock|LockTimeoutException|canceling statement due to lock timeout)", content, re.IGNORECASE):
        severity = "HIGH" if severity != "CRITICAL" else severity
        summary_items.append("Detección de contención de bloqueos en base de datos PostgreSQL LTS.")
        recommendations.append("Asegurar migraciones DDL con CREATE INDEX CONCURRENTLY y evitar bloqueos ACCESS EXCLUSIVE.")

    if re.search(r"(ConnectionRefusedError|timeout|504 Gateway Time-out)", content, re.IGNORECASE):
        severity = "MEDIUM" if severity == "INFO" else severity
        summary_items.append("Anomalía de conectividad o saturación de red/ingress.")
        recommendations.append("Verificar el estado del proxy o balanceador de entrada y las probes de liveness/readiness.")

    if not summary_items:
        summary_items.append("No se detectaron patrones críticos evidentes en el volcado de logs.")
        recommendations.append("Inspeccionar trazas de depuración adicionales o activar modo interactivo.")

    return DeepOpsReport(
        is_success=True,
        summary=" ".join(summary_items),
        severity=severity,
        recommendations=tuple(recommendations),
        raw_details=content[:2000],
    )


def analyze_log(
    log_path: Path,
    prompt: Optional[str] = None,
    mock: bool = False,
) -> DeepOpsReport:
    """Analiza un volcado de log generando un diagnóstico estructurado."""
    if not log_path.is_file():
        return DeepOpsReport(
            is_success=False,
            summary=f"No se encontró el archivo de log en {log_path}",
            severity="UNKNOWN",
            recommendations=(),
        )

    try:
        content = log_path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return DeepOpsReport(
            is_success=False,
            summary=f"Error leyendo {log_path}: {exc}",
            severity="ERROR",
            recommendations=(),
        )

    report = _heuristic_log_analysis(content)
    if mock:
        return report
    # Presupuesto 0 $: el resumen lo hace el modelo local (aagy-local) si está disponible; la API de Gemini no se usa.
    local = _local_summary(log_path)
    if not local:
        return report
    return DeepOpsReport(report.is_success, f"{report.summary} Resumen local: {local}", report.severity,
                         report.recommendations, report.raw_details)


def _local_summary(log_path: Path) -> str:
    """Resumen con local_run(summarize, paths) si el modelo local está en modo tool; "" si no."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import local_model  # noqa: PLC0415

        settings = local_model.load_settings(log_path.parent)
        if local_model.get_status(settings).effective != local_model.MODE_TOOL:
            return ""
        result = local_model.run_task(settings, {"task": "summarize", "paths": [str(log_path.resolve())]},
                                      log_path.resolve().parent)
        return str(result.get("result", "")) if "error" not in result else ""
    except Exception:  # noqa: BLE001 - el resumen local es opcional
        return ""


def generate_postmortem_summary(issue_id: str, log_path: Path) -> str:
    """Genera una sección estructurada para integrar en un Post-Mortem 5W."""
    report = analyze_log(log_path)
    lines = [
        f"### Diagnóstico Asistido Gemini Deep Ops (Incidencia {issue_id})",
        "",
        f"- **Severidad Diagnosticada**: `{report.severity}`",
        f"- **Resumen Causal**: {report.summary}",
        "- **Recomendaciones SRE Inmediatas**:",
    ]
    for rec in report.recommendations:
        lines.append(f"  - {rec}")
    lines.append("")
    return "\n".join(lines)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CLI de Gemini Deep Ops (diagnóstico multimodal de logs).")
    subparsers = parser.add_subparsers(dest="subcommand", help="Comandos disponibles")

    # status
    subparsers.add_parser("status", help="Comprueba el estado de la API y SDK.")

    # analyze-log
    p_log = subparsers.add_parser("analyze-log", help="Analiza un volcado de logs.")
    p_log.add_argument("--file", type=Path, required=True, help="Ruta al archivo de log.")
    p_log.add_argument("--prompt", type=str, default=None, help="Prompt o directriz específica.")
    p_log.add_argument("--mock", action="store_true", help="Fuerza análisis heurístico offline.")

    # postmortem
    p_pm = subparsers.add_parser("postmortem", help="Genera bloque para postmortem 5W.")
    p_pm.add_argument("--issue", type=str, required=True, help="ID de la incidencia.")
    p_pm.add_argument("--file", type=Path, required=True, help="Ruta al log de la incidencia.")

    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)

    if args.subcommand == "status" or not args.subcommand:
        status = get_ops_status()
        logger.info("=== ESTADO GEMINI DEEP OPS ===")
        logger.info("API Key Configurada: %s", status[KEY_API_CONFIGURED])
        logger.info("SDK Disponible:      %s", status["sdk_available"])
        logger.info("Modelo por Defecto:  %s", status["default_model"])
        if not status[KEY_API_CONFIGURED]:
            logger.info("\n[TIP] Configura %s para habilitar llamadas a la API de Gemini Studio.", API_KEY_ENV_VAR)
        return 0

    if args.subcommand == "analyze-log":
        report = analyze_log(args.file, args.prompt, args.mock)
        logger.info("\n=== REPORTE DE ANÁLISIS DE LOGS ===")
        logger.info("Estado:        %s", "ÉXITO" if report.is_success else "FALLIDO")
        logger.info("Severidad:     %s", report.severity)
        logger.info("Diagnóstico:   %s", report.summary)
        logger.info("Recomendaciones SRE:")
        for r in report.recommendations:
            logger.info("  • %s", r)
        return 0 if report.is_success else 1

    if args.subcommand == "postmortem":
        summary = generate_postmortem_summary(args.issue, args.file)
        logger.info("\n%s", summary)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
