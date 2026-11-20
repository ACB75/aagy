# Fase 3: Documentación y Notas de Release (`Release Notes`)

> **Referencia de Gobernanza**: Fase 3 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/session-budget-telemetry`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / SRE Token Optimization Specialist`  
> **Estado**: `APROBADO`  

---

## 1. Release Notes SemVer (`v2.5.0`)

### 1.1. Resumen Ejecutivo de la Versión

Introducción del subsistema de telemetría proactiva de tokens en sesión (`session-token-monitor`). Permite monitorizar en tiempo real el consumo acumulado de contexto en la conversación activa de Antigravity, alertando automáticamente tras la finalización de una PR si la sesión supera los 45.000 tokens para recomendar una compactación estratégica oportuna (`/compact`).

### 1.2. Cambios Introducidos

- **Herramientas de Telemetría (`feat`)**:
  - `scripts/ecc-agy/session_token_monitor.py`: Analizador de alta velocidad de transcripts JSONL.
  - `scripts/bin/ecc-agy/session-token-monitor.ps1` y `.sh`: Wrappers multiplataforma.
  - Integración en `complete-task-pr.ps1` para aviso de compactación al cierre de tareas.
- **Documentación (`docs`)**:
  - `doc/manual/MANUAL_session_token_telemetry.md`: Guía de monitoreo y ciclo de vida de tokens en sesión.
- **Tests (`test`)**:
  - Suite unitaria `test_session_token_monitor.py`.

---

## 2. Actualización de la Espina Documental

- `STATUS.md`: Añadida telemetría de sesión.
- `LOG.md`: Registro de la tarea `feat/ecc/session-budget-telemetry`.
- `doc/manual/MANUAL_session_token_telemetry.md`: Creado.
