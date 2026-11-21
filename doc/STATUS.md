# Estado de Salud y Métricas Operacionales | AAGY / `aagy` Ecosystem

> **Espina Dorsal de Gobernanza Documental**: [ACB75/aagy](https://github.com/ACB75/aagy) (`aagy` -> `aagy`)  
> **Versión**: `4.2.0` (`/doc` v2) | **Fecha de Auditoría**: 2026-11-20  
> **Estado Operativo Global**: 🟢 **SALUDABLE (VERDE)**

---

## 1. Métricas de Calidad y Quality Gate

| Dimensión | Indicador / Umbral | Estado Actual | Cumplimiento |
| :--- | :--- | :--- | :---: |
| **SonarQube Quality Gate** | Rating A (0 violaciones críticas) | 0 violaciones detectadas | ✅ PASS |
| **Complejidad Cognitiva** | $\le 15$ por función/método (`S3776`) | Máximo $\le 15$ en todo el código | ✅ PASS |
| **Duplicación de Literales** | Cero cadenas $\ge 3$ repetidas (`S1192`) | 0 duplicados detectados | ✅ PASS |
| **Parámetros de Función** | $\le 7$ parámetros (`S107`) | Cumple en todos los módulos | ✅ PASS |
| **Seguridad Estática** | 0 secretos / 0 inyecciones de comandos | 0 vulnerabilidades detectadas | ✅ PASS |
| **Estándar Markdown** | DavidAnson `.markdownlint.json` | 100% compliant (`--check-only`) | ✅ PASS |
| **Tests Multi-Runtime** | Cobertura $\ge 80\%$, exit code 0 | 154+ tests pasando (`py` / `ps1` / `sh`) | ✅ PASS |
| **Integridad `/doc` v2** | Cero enlaces rotos y `docs-map.json` válido | 0 incidencias en `map_docs.py` y `audit-docs.py` | ✅ PASS |
| **Hard Gate Presupuesto** | Reglas $\le 24$ KB, tokens $\le 16$k, eager $\le 3$k | 100% compliant en Root y Plugin | ✅ PASS |

---

## 2. Presupuesto de Tokens y Contexto (Two-Tier Architecture)

- **Tier 1 (Global Plugin `~/.gemini/config/plugins/aagy`)**:
  - **Reglas Globales (`rules/`)**: Archivo canónico único [`rules/AGENTS.md`](../rules/AGENTS.md) compactado a `< 12 KB` (~2.050 tokens frente al límite de 16.000), integrando el ciclo completo de PR y squash-automerge.
  - **`AGENTS.md` en Raíz**: Puntero estático ultra-ligero (~14 líneas) con marcador KV-cache (`<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->`).
- **Tier 2 (Lazy / Por Demanda en Repositorio)**:
  - **Skills de Stack**: Cargadas bajo demanda (`0` tokens en reposo) manteniendo descripciones $\le 140$ caracteres.
  - **Subagentes**: Frontmatter `description` $\le 120$ caracteres con principio de mínimo privilegio.

---

## 3. Estado de Automatización y Gobernanza del Harness

- **Arquitectura Documental `/doc` v2 y Fallback Clásico**: Resuelta por [`scripts/py/docs_map.py`](../scripts/py/docs_map.py) leyendo [`.governance/docs-map.json`](../.governance/docs-map.json) (`schema_version: 2`) con fallback automático para `home-lab` y bloqueo estricto contra *path traversal*. Estándar en [`DOC_STANDARDS.md`](00-governance/DOC_STANDARDS.md).
- **Flujo Flexible `[IDEAS -> REQ -> PLAN -> TODO]` y Paridad Manual 1-a-1**: Soportado por [`new_lifecycle_task.py`](../scripts/py/new_lifecycle_task.py) (`--phase ALL|IDEAS|REQ|PLAN|TODO|DOCS|REVIEW`), [`MANUAL_WORKFLOW.md`](00-governance/MANUAL_WORKFLOW.md) y wrappers espejo en `scripts/ps1/`, `scripts/sh/` y proxies en `scripts/ps1/`.
- **Workflow de Ingeniería 4 Fases**: Estandarizado en [`doc/00-governance/templates/README.md`](00-governance/templates/README.md).
- **Hard Gate de Presupuesto en Harness**: Implementado en [`scripts/py/workspace_audit.py`](../scripts/py/workspace_audit.py), integrando validación de `.governance/docs-map.json`.
- **Integración Zero-Overhead Gemini MCP & Deep Ops**: Plantilla con `"disabled": true` y CLI [`scripts/py/gemini_deep_ops.py`](../scripts/py/gemini_deep_ops.py) / [`scripts/py/toggle_gemini_mcp.py`](../scripts/py/toggle_gemini_mcp.py).
- **Hooks Nativos, AgentShield, Instintos a Doble Nivel y Automejora Unificada**: Manifiesto [`hooks.json`](../hooks.json) (con hook pasivo `Stop` `< 500 ms` y `0` tokens), motor [`scripts/py/self_improve.py`](../scripts/py/self_improve.py), auditoría [`scripts/py/security_audit.py`](../scripts/py/security_audit.py), instintos proyecto + `PLUGIN_DATA` en [`scripts/py/instinct_manager.py`](../scripts/py/instinct_manager.py) y manual [`MANUAL_unified_self_improvement.md`](04-operations/runbooks/MANUAL_unified_self_improvement.md).
- **Validadores de Gobernanza Git y Home-Lab**:
  - Ramas canónicas: [`scripts/py/validate_branch.py`](../scripts/py/validate_branch.py)
  - Autopsias 5W: [`scripts/py/generate_postmortem.py`](../scripts/py/generate_postmortem.py)
  - Paridad SDK: [`scripts/py/audit_sdk_parity.py`](../scripts/py/audit_sdk_parity.py)
  - Bloqueos DDL PG LTS: [`scripts/py/audit_pg_locks.py`](../scripts/py/audit_pg_locks.py)
  - Ingress / Split-DNS: [`scripts/py/validate_ingress_routes.py`](../scripts/py/validate_ingress_routes.py)
  - Paridad Multi-Harness `aagy` $\leftrightarrow$ `aagy-ecc`: [`scripts/py/audit_plugin_parity.py`](../scripts/py/audit_plugin_parity.py)
- **Ciclo Completo de PR y Automerge**: Orquestado en [`scripts/ps1/complete-task-pr.ps1`](../scripts/ps1/complete-task-pr.ps1) y [`scripts/sh/complete-task-pr.sh`](../scripts/sh/complete-task-pr.sh) con resolución dinámica de `TODO.md`/`done/`, suites `pytest` multi-runtime y compuerta documental `map_docs.py --check-docs-map`.
- **Backlog Activo**: En [`doc/06-backlog/TODO.md`](06-backlog/TODO.md) (`0` tareas pendientes; `Tarea 0.1`, `Tarea 0.2`, `Tarea 0.3`, `Tarea 0.4` y `Tarea 5.1` completadas y archivadas en `doc/06-backlog/done/`).
