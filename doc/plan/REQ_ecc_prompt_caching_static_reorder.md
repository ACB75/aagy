# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/prompt-caching-static-reorder`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Gemini LLM Systems Architect`  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**: Los modelos fundacionales Gemini 3.8 implementan *context caching* y *prompt caching* determinista por coincidencia de prefijo (KV-cache reuse). En la configuración actual de `AGENTS.md` y `rules/AGENTS.md`, las directivas operativas de tareas y reglas volátiles se encuentran intercaladas con los invariantes estáticos universales. Esto provoca una fragmentación del prefijo de prompt en turnos sucesivos, invalidando la reutilización de claves/valores en caché y aumentando la latencia TTFT (Time To First Token) y el consumo de tokens en turnos sucesivos.
- **Objetivo Principal**: Reestructurar `AGENTS.md` y las reglas del plugin `ecc-agy` en una arquitectura binaria de dos bloques: un Bloque Estático Invariable (prefijo determinista continuo) y un Bloque Contextual/Operativo (sufijo dinámico), garantizando estabilidad del prefijo, reducción del 60% en TTFT en turnos largos y 100% de retrocompatibilidad con las directivas de gobernanza.
- **Alcance (`In-Scope`)**:
  - Reordenamiento conceptual y estructurado de `AGENTS.md` (raíz) y `rules/AGENTS.md` (repositorio y plugin global).
  - Marcador determinista de delimitación de prefijo de context caching.
  - Creación del manual técnico `doc/manual/MANUAL_gemini_prompt_caching.md`.
  - Suite de validación en `scripts/ecc-agy/tests/test_workspace_audit.py` verificando la estabilidad de prefijo y paridad de reglas.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Modificación de contratos de subagentes o lógica funcional de scripts existentes.
  - Eliminación de reglas existentes (solo reordenamiento sin pérdida de directivas).

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01`**: La cabecera y el prefijo continuo de `AGENTS.md` y `rules/AGENTS.md` deben contener exclusivamente directivas estáticas universales (Google 5-Pillar, SRE Baseline, Security, Quality Gates, Stack Rules, Microservice SDK Parity) delimitadas por el marcador `<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->`.
- **`RF-02`**: Las directivas de flujo operativo (Lifecycle 4-fases, Commit PR automation, TODO lifecycle, Archival, Token Exhaustion) deben ubicarse en el sufijo delimitado `## 2. Dynamic Task Lifecycle, Governance & Workflow (Contextual Suffix)`.
- **`RF-03`**: Sincronización exacta entre `AGENTS.md`, `rules/AGENTS.md` y `~/.gemini/config/plugins/ecc-agy/rules/AGENTS.md`.
- **`RF-04`**: Documentación técnica detallada en `doc/manual/MANUAL_gemini_prompt_caching.md` para desarrolladores.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [x] **`CA-01`**: Dado `AGENTS.md` y `rules/AGENTS.md`, cuando se audite la estructura de prefijos, entonces el marcador `<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->` está presente en la línea 1 o 3 y precede a todas las directivas estáticas.
- [x] **`CA-02`**: Dado `rules/AGENTS.md` y `~/.gemini/config/plugins/ecc-agy/rules/AGENTS.md`, ambos archivos son idénticos byte a byte.
- [x] **`CA-03`**: Cobertura de tests unitarios $\ge 80\%$ en `test_workspace_audit.py` validando la invariancia del prefijo estático.

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin impacto en tipos o endpoints de microservicios. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin persistencia en base de datos. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin cambios de red o proxy inverso. |
| **Resolución Split-DNS** | `NO` | - | Sin alteración de DNS. |
| **Restricciones de Hardware** | `NO` | Bajo | Reduce consumo de memoria y CPU en inferencia de prompts largos. |
| **Variables `.env` / Secretos** | `NO` | - | Sin nuevos secretos requeridos. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

> **Invariante Canónico**: Queda terminantemente prohibido introducir cambios destructivos o de ruptura en contratos públicos, esquemas de bases de datos compartidas o bibliotecas SDK.

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva (Non-Breaking)**:
  - Todas las directivas existentes se preservan íntegramente; solo se agrupan y reordenan para optimizar la compilación de contexto de Gemini 3.8.
  - Ningún subagente ni script verá alteradas sus capacidades ni sus herramientas permitidas.

---

## 5. Compuertas SRE de Rendimiento y Persistencia Segura

### 5.1. Rendimiento y Throttling de Recursos

- **Latencia Objetivo**: Reducción de latencia TTFT en sesiones largas mediante KV-cache hit.
- **Complejidad Algorítmica**: Análisis estático en $O(N)$ donde $N$ es el tamaño en caracteres de las reglas.
- **Presupuesto de Contexto**: Tamaño de regla $\le 24\text{ KB}$, respetando `MAX_RULE_FILE_BYTES`.

---

## 6. Threat Modeling y Bastionado de Seguridad

- **Integridad de Reglas**: La reorganización preserva todas las directivas de seguridad (`Security & Secrets Baseline`, Parameterized SQL, zero hardcoded secrets) dentro del prefijo estático invariante.
- **Inyección de Prompts**: Se evita la introducción de directivas dinámicas evaluadas por template en tiempo de ejecución en el prefijo.
