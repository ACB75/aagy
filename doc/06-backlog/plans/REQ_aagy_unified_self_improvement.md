# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/aagy/unified-self-improvement` (`Tarea 0.3`)  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Autonomous Agent Reliability & Self-Improvement Systems Architect`  
> **Estado**: `APROBADO`

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**: El repositorio contiene piezas desconectadas para autodescubrimiento y aprendizaje continuo (`scripts/bin/ecc-agy/auto-evolve.ps1/.sh` acoplado a `home-lab`, `scripts/ecc-agy/instinct_manager.py`, y skills heredadas `continuous-learning`, `continuous-learning-v2`, `agent-self-evaluation`, `eval-harness`, `prompt-optimizer`) que no comparten un ciclo unificado ni están conectadas a los hooks de Antigravity (`hooks.json` `Stop`) ni al hard gate de presupuesto de tokens.
- **Objetivo Principal**: Unificar y optimizar todas las capacidades de autodescubrimiento y automejora en un motor único agnóstico para `aagy` (con paridad en `ecc` y ejecución manual CLI), operando con captura híbrida (`Stop` hook `0` tokens + CLI bajo demanda), almacenamiento a doble nivel (proyecto + `PLUGIN_DATA`) y promoción controlada por confirmación explícita, *smoke-test* y *budget gate*.
- **Alcance (`In-Scope`)**:
  - Unificación de `auto-evolve`, `instinct_manager` y evaluación/aprendizaje continuo en un único motor modular bajo `scripts/{py,sh,pwsh}/` (con sus `/tests`).
  - Eliminación o consolidación de skills redundantes (`continuous-learning`, `continuous-learning-v2`, `eval-harness`, etc.) en una sola capacidad coherente dentro del catálogo de `aagy`.
  - Captura híbrida: hook `Stop` en `hooks.json` (pasivo, sub-segundo, `0` tokens de contexto) + comandos manuales equivalentes.
  - Persistencia a doble nivel: instintos de proyecto en `<repo>/.agents/instincts/` e instintos globales reutilizables en `PLUGIN_DATA` de `aagy`.
  - Flujo de promoción seguro: generación de candidato/borrador $\rightarrow$ validación de presupuesto de tokens + *smoke-test* $\rightarrow$ confirmación explícita del usuario antes de escribir en `skills/`, `rules/` o `scripts/`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Escritura autónoma no supervisada en `AGENTS.md`, `rules/` o `skills/` Tier-1 sin confirmación del usuario.
  - Dependencias externas de ML/NLP pesadas (mantener Python stdlib / PowerShell / Bash).

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Captura Híbrida Zero-Overhead)**: El hook `Stop` en `hooks.json` captura métricas de sesión/errores/comandos repetidos de forma pasiva y sub-segundo (`0` tokens en prompt), complementado con ejecución manual (`--discover`, `--review`, `--promote`) desde terminal.
- **`RF-02` (Persistencia a Doble Nivel)**:
  - Nivel Proyecto: `<repo>/.agents/instincts/` (patrones específicos del repositorio, ej. `home-lab`).
  - Nivel Global Plugin: `$PLUGIN_DATA/instincts/` (patrones transversales reutilizables en `aagy` / `ecc`).
- **`RF-03` (Detección y Consolidación de Patrones)**: El motor unificado analiza instintos, fallos recurrentes y tareas repetitivas ($\ge 2$ ocurrencias) deduplicando candidatos similares antes de proponer artefactos nuevos.
- **`RF-04` (Promoción Controlada con Confirmación y Gates)**: Ningún candidato se promueve automáticamente a `skills/`, `rules/` o `scripts/`; se genera un borrador/propuesta que debe superar:
  1. Hard gate de presupuesto (`rules` $\le 24\text{ KB}$ / $\le 20.000$ tokens, `MAX_SKILL_DESC = 140`, `MAX_AGENT_DESC = 120`, preferencia por Tier 2 o `hooks.json` `0` tokens).
  2. *Smoke-test* automático (exit code `0`).
  3. Confirmación explícita del usuario.
- **`RF-05` (Desacoplamiento Agnóstico)**: Eliminar referencias hardcodeadas a `home-lab` en `auto-evolve`; el motor debe operar sobre cualquier repositorio objetivo (`--repo-root`).

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [x] **`CA-01`**: Dado un cierre de sesión con hook `Stop`, cuando se detecte un patrón repetitivo o aprendizaje válido, entonces se registrará en `.agents/instincts/` (o `PLUGIN_DATA`) en $< 1\text{ s}$ sin modificar `AGENTS.md` ni consumir tokens del prompt.
- [x] **`CA-02`**: Dado un candidato listo para promoción, cuando supere el umbral y se ejecute el comando de revisión/promoción, entonces el sistema validará el presupuesto de tokens y ejecutará un *smoke-test* antes de solicitar confirmación al usuario.
- [x] **`CA-03`**: Dado el rechazo o falta de confirmación del usuario, el artefacto no se escribirá en `skills/`, `rules/` ni `scripts/`.
- [x] **`CA-04`**: Cobertura de tests unitarios $\ge 80\%$ sobre el motor unificado (`pytest` exit code `0`).

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | No modifica contratos de microservicios ni DTOs. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Persistencia local en JSON/Markdown. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin cambios en Traefik/CoreDNS. |
| **Resolución Split-DNS** | `NO` | - | Sin impacto. |
| **Restricciones de Hardware** | `NO` | - | Ejecución sub-segundo en Python stdlib; `0` overhead en prompt. |
| **Instintos en `home-lab/.agents/instincts/`** | `SÍ` | `Bajo` | Mantiene compatibilidad con `.agents/instincts/` en `home-lab` separando lo global en `PLUGIN_DATA`. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (Retrocompatible con .agents/instincts/) | [ ] SÍ`
- **Estrategia Aditiva**: Los instintos ya capturados en `.agents/instincts/` siguen siendo leídos por el motor unificado; las skills legacy duplicadas se consolidan con redirección/limpieza documentada en `Tarea 0.1`.

---

## 5. Compuertas SRE de Rendimiento y Persistencia Segura

- **Latencia del Hook `Stop`**: $\le 500\text{ ms}$ (timeout máximo en `hooks.json`: `5s`).
- **Aislamiento de Fallos**: Si el hook `Stop` falla o no tiene permisos de escritura, registra advertencia no bloqueante y devuelve `{}` para no interrumpir al usuario.

---

## 6. Threat Modeling y Bastionado de Seguridad

| Vector de Ataque / Amenaza | Riesgo (`Bajo/Medio/Alto/N/A`) | Mitigación y Bastionado Aplicado |
| :--- | :---: | :--- |
| **Envenenamiento de instintos (*Prompt Injection*)** | `Alto` | Sanitización AgentShield sobre candidatos antes de promover; prohibida auto-escritura en `AGENTS.md`/`rules/` sin confirmación humana. |
| **Desbordamiento de presupuesto de tokens** | `Medio` | Hard gate obligatorio de `workspace_audit.py` antes de aceptar cualquier skill/rule promovida. |
| **Exposición de secretos en instintos** | `Medio` | Filtrado de patrones de credenciales/tokens (`API_KEY`, `Bearer`, `password`) antes de persistir en `.agents/instincts/` o `PLUGIN_DATA`. |
