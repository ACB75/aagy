#!/usr/bin/env python3
"""
scripts/py/session_token_monitor.py - Monitor de Telemetría de Presupuesto en Sesión

Analiza el archivo transcript.jsonl de la conversación activa de Antigravity,
calcula el recuento estimado de tokens consumidos y alerta cuando supera
el umbral de presupuesto (por defecto 45.000 tokens), recomendando /compact.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
import logging
import math
import os
from pathlib import Path
import sys
from typing import Optional, Sequence

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger: logging.Logger = logging.getLogger("session-token-monitor")

CHARS_PER_TOKEN: float = 3.8
DEFAULT_THRESHOLD: int = 45_000
KEY_TRANSCRIPT_PATH = "transcript_path"
KEY_ESTIMATED_TOKENS = "estimated_tokens"


@dataclass(frozen=True)
class SessionTokenReport:
    transcript_path: str
    steps: int
    total_chars: int
    estimated_tokens: int
    threshold: int
    compact_recommended: bool


def find_transcripts(home: Optional[Path] = None) -> list[Path]:
    """Todos los transcript.jsonl de Antigravity brain, del más reciente al más antiguo."""
    brain_base = (home or Path.home()) / ".gemini" / "antigravity" / "brain"
    if not brain_base.is_dir():
        return []
    candidates = [t for t in brain_base.glob("*/.system_generated/logs/transcript.jsonl") if t.is_file()]
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates


def _find_latest_transcript() -> Optional[Path]:
    """Localiza el transcript.jsonl más reciente en la estructura de Antigravity brain."""
    candidates = find_transcripts()
    return candidates[0] if candidates else None


def _extract_step_chars(data: dict) -> int:
    """Calcula los caracteres representativos de un paso en el transcript."""
    chars = 0
    content = data.get("content")
    if isinstance(content, str):
        chars += len(content)

    thinking = data.get("thinking")
    if isinstance(thinking, str):
        chars += len(thinking)

    tool_calls = data.get("tool_calls")
    if tool_calls:
        try:
            chars += len(json.dumps(tool_calls))
        except (TypeError, ValueError) as err:
            logger.debug("Error serializando tool_calls: %s", err)

    return chars


def analyze_transcript(
    transcript_path: Optional[Path] = None,
    threshold: int = DEFAULT_THRESHOLD,
) -> SessionTokenReport:
    """
    Analiza un archivo transcript.jsonl y genera un reporte de telemetría de tokens.
    """
    target = transcript_path or _find_latest_transcript()
    if target is None or not target.is_file():
        return SessionTokenReport(
            transcript_path=str(target) if target else "unknown",
            steps=0,
            total_chars=0,
            estimated_tokens=0,
            threshold=threshold,
            compact_recommended=False,
        )

    total_chars = 0
    step_count = 0

    try:
        with target.open("r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line_str = line.strip()
                if not line_str:
                    continue
                step_count += 1
                try:
                    data = json.loads(line_str)
                    if isinstance(data, dict):
                        total_chars += _extract_step_chars(data)
                except json.JSONDecodeError:
                    total_chars += len(line_str)
    except OSError as err:
        logger.debug("Error leyendo transcript %s: %s", target, err)

    estimated_tokens = math.ceil(total_chars / CHARS_PER_TOKEN)
    compact_recommended = estimated_tokens > threshold

    return SessionTokenReport(
        transcript_path=str(target),
        steps=step_count,
        total_chars=total_chars,
        estimated_tokens=estimated_tokens,
        threshold=threshold,
        compact_recommended=compact_recommended,
    )


def _output_report(report: SessionTokenReport, json_output: bool, alert_only: bool) -> int:
    if json_output:
        print(json.dumps(asdict(report), indent=2))
        return 0

    if alert_only:
        if report.compact_recommended:
            logger.warning(
                "[ALERTA SRE] Sesion cargada: ~%d tokens superan el umbral de %d. Se recomienda /compact.",
                report.estimated_tokens,
                report.threshold,
            )
            return 1
        return 0

    logger.info("=======================================================")
    logger.info("       TELEMETRIA DE PRESUPUESTO DE TOKENS EN SESION   ")
    logger.info("=======================================================")
    logger.info("Transcript:          %s", report.transcript_path)
    logger.info("Pasos registrados:   %d", report.steps)
    logger.info("Caracteres totales:  %d", report.total_chars)
    logger.info("Tokens estimados:    ~%d", report.estimated_tokens)
    logger.info("Umbral maximo:       %d tokens", report.threshold)
    logger.info("-------------------------------------------------------")
    if report.compact_recommended:
        logger.warning("[!] ALERTA: Consumo elevado de contexto en conversacion.")
        logger.warning("    Se recomienda ejecutar el comando /compact para")
        logger.warning("    reducir el coste por turno y preservar atencion.")
        return 1

    logger.info("[OK] Presupuesto de sesion saludable. No se requiere compactacion.")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Monitor de telemetría de tokens en sesión activa de Antigravity."
    )
    parser.add_argument(
        "--transcript",
        "-t",
        type=Path,
        help="Ruta específica a transcript.jsonl (por defecto auto-detectado).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Umbral de tokens para recomendar compactación (def: {DEFAULT_THRESHOLD}).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emitir reporte en formato JSON estructurado.",
    )
    parser.add_argument(
        "--alert-only",
        action="store_true",
        help="Silencioso si está dentro del umbral; emite advertencia y código 1 si excede.",
    )

    args = parser.parse_args(argv)
    report = analyze_transcript(transcript_path=args.transcript, threshold=args.threshold)
    return _output_report(report, json_output=args.json, alert_only=args.alert_only)


if __name__ == "__main__":
    sys.exit(main())
