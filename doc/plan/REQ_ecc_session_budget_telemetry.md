# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/session-budget-telemetry`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / SRE Token Optimization Specialist`  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**: A medida que una conversación con el agente de IA avanza ejecutando tareas, inspeccionando archivos y generando salidas de terminal, el transcript acumulado crece. Conforme supera los 45.000 tokens en la sesión activa, el coste computacional por turno se incrementa y la precisión atencional del modelo en detalles previos puede experimentar degradación (*needle-in-a-haystack decay*).
- **Objetivo Principal**: Desarrollar un monitor CLI determinista y de ultra-baja latencia (`session_token_monitor.py` y wrappers `.ps1` / `.sh`) que inspeccione el transcript activo, estime el volumen de tokens acumulados e informe proactivamente en los resúmenes de PR (`complete-task-pr.ps1`) cuándo es óptimo ejecutar `/compact`.
- **Alcance (`In-Scope`)**:
  - `scripts/ecc-agy/session_token_monitor.py` (motor de análisis de transcript JSONL).
  - `scripts/bin/ecc-agy/session-token-monitor.ps1` y `session-token-monitor.sh`.
  - Integración proactiva al final de `complete-task-pr.ps1`.
  - Manual operativo `doc/manual/MANUAL_session_token_telemetry.md`.
  - Suite unitaria `scripts/ecc-agy/tests/test_session_token_monitor.py`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Compactación destructiva no solicitada por el usuario (la herramienta alerta y recomienda, la decisión pertenece al usuario o slash command).

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Detección y Parseo de Transcript)**: Localizar automáticamente el `transcript.jsonl` más reciente en el directorio de Antigravity brain o aceptar `--transcript <path>`.
- **`RF-02` (Estimación Determinista de Tokens)**: Calcular tokens acumulados sobre `content`, `thinking` y `tool_calls` usando la constante de arnés $3.8\text{ chars/token}$.
- **`RF-03` (Umbrales Configurables y Banderas)**: Soportar `--threshold <n>` (por defecto $45.000$), `--alert-only` y `--json`.
- **`RF-04` (Tolerancia a Fallos y Concurrencia)**: Capturar errores de archivo en caliente (`PermissionError`, `FileNotFoundError`) retornando estado seguro sin abortar scripts llamadores.
- **`RF-05` (Integración en `complete-task-pr.ps1`)**: Emitir un aviso visible si la sesión supera el umbral de 45.000 tokens recomendando `/compact`.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [x] **`CA-01`**: Dado un transcript con 50.000 tokens estimados, cuando se ejecute con `--threshold 45000`, entonces `compact_recommended` es `True` y el reporte incluye alerta destacada.
- [x] **`CA-02`**: Dado un archivo inexistente o vacío, cuando se invoque la utilidad, entonces maneja la situación de forma segura devolviendo 0 tokens sin lanzar excepciones no controladas.
- [x] **`CA-03`**: Tiempo de procesamiento para 1.000 pasos de transcript $< 150\text{ ms}$.

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin impacto en SDKs. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin persistencia en base de datos. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin cambios de red. |
| **Resolución Split-DNS** | `NO` | - | Sin cambios DNS. |
| **Restricciones de Hardware** | `NO` | Bajo | Monitoreo liviano en Python stdlib. |
| **Variables `.env` / Secretos** | `NO` | - | Sin secretos requeridos. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva (Non-Breaking)**:
  - La utilidad se integra de forma informativa; si el script no encuentra un transcript, simplemente se omite el aviso sin interrumpir `complete-task-pr.ps1`.
