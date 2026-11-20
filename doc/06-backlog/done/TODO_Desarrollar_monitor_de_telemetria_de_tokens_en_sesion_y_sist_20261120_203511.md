---
title: "**Desarrollar monitor de telemetría de tokens en sesión y sistema proactivo de alerta/ejecución de compactación**"
status: COMPLETED
completed_at: "2026-11-20 20:35:11"
---

# TODO: **Desarrollar monitor de telemetría de tokens en sesión y sistema proactivo de alerta/ejecución de compactación**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 20:35:11

### Detalle Original

- **01 - ROLE:** Context Lifecycle Engineer & SRE Token Optimization Specialist.
- **02 - CONTEXT:** `[Sector: AI Agent Lifecycle & Token Throttling]` `[Data Type: Python stdlib / PowerShell, Transcript JSONL reader]` `[Objective: Implementar una utilidad de diagnóstico y alerta que analice el transcript de la sesión activa, calcule el volumen acumulado de tokens y alerte cuando la sesión supere los 45.000 tokens recomendando o disparando /compact]` `[Restrictions: No interferir con la ejecución normal de comandos; tiempo de cómputo < 150ms]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Conforme la conversación avanza acumulando logs y difs de código, el coste por turno crece linealmente y la precisión de atención del modelo puede experimentar degradación en los detalles iniciales.
  - Se requiere un indicador objetivo en el entorno que informe cuándo es el momento óptimo para compactar.
- **04 - PHASE 2 (STRATEGY):**
  - Crear `scripts/bin/aagy/session-token-monitor.ps1` y script de soporte `scripts/aagy/session_token_monitor.py` que lea `transcript.jsonl` y determine el recuento estimado de tokens.
  - Integrar la recomendación proactiva en el resumen de `complete-task-pr.ps1`.
- **05 - PHASE 3 (EXECUTION):**
    1. Programar `session_token_monitor.py` para parsear los pasos de la sesión y sumar tokens de entrada/salida.
    2. Exponer banderas `--threshold <n>` y `--alert-only`.
    3. Incorporar el chequeo al final de `complete-task-pr.ps1`: si tokens > 45k, emitir recomendación explícita de `/compact`.
    4. Añadir tests unitarios en `test_session_token_monitor.py`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Manejar de forma robusta la ausencia o bloqueo de lectura en caliente del archivo `transcript.jsonl`.
- **07 - PHASE 5 (FORMAT):**
  - Script CLI en Python/PowerShell con reporte conciso y tests unitarios al 100%.
- **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.000 tokens).
- **COMPACT TRIGGER:** Inmediato tras la ejecución si la sesión supera 45.000 tokens.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Monitor session_token_monitor.py, wrappers .ps1/.sh, integracion en complete-task-pr.ps1 y manual MANUAL_session_token_telemetry.md

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/aagy/session-budget-telemetry`
- **Commit SHA**: `f9ef3a4`
- **Fecha**: `2026-11-20 20:35:11`
- **Gobernanza**: Quality Gate A / markdownlint OK
