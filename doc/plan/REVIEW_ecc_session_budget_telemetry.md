# Fase 4: Propuesta de Commits, Pre-Flight Review y Apertura de PR

> **Referencia de Gobernanza**: Fase 4 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/session-budget-telemetry`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / SRE Token Optimization Specialist`  
> **Estado**: `APROBADO`  

---

## 1. Verificación de Rama Canónica

- **Rama**: `feat/ecc/session-budget-telemetry`
- **Validación con arnés**: Exit code `0` (`validate_branch.py`).

---

## 2. Propuesta Estructurada de Commit y PR

- **Título**: `[feat]-[ecc,scripts]: telemetria proactiva de tokens en sesion y recomendador de auto-compact`
- **Cuerpo Explicativo**:
  - **Contexto**: A fin de prevenir degradación de atención en turnos largos y evitar el desbordamiento silencioso del presupuesto de tokens por conversación, se añade un monitor de sesión en tiempo real.
  - **Cambios**:
    - `scripts/ecc-agy/session_token_monitor.py` y wrappers `.ps1` / `.sh`.
    - Integración en `complete-task-pr.ps1` alertando cuando la sesión supere 45.000 tokens.
    - Manual operativo `doc/manual/MANUAL_session_token_telemetry.md`.
    - Pruebas unitarias en `test_session_token_monitor.py`.
  - **Verificación**: Tests unitarios passing (100%), markdownlint passing y SonarQube Rating A.
