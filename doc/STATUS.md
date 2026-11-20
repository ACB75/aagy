# Estado de Salud y Métricas Operacionales | ECC Ecosystem

> **Espina Dorsal de Gobernanza Documental**: Repositorio [`ACB75/ecc`](https://github.com/ACB75/ecc)  
> **Versión**: `3.3.0` | **Fecha de Auditoría**: 2026-11-20  
> **Estado Operativo Global**: 🟢 **SALUDABLE (VERDE)**  

---

## 1. Métricas de Calidad y Quality Gate

| Dimensión | Indicador / Umbral | Estado Actual | Cumplimiento |
| :--- | :--- | :--- | :---: |
| **SonarQube Quality Gate** | Rating A (0 violaciones críticas) | 0 violaciones detectadas | ✅ PASS |
| **Complejidad Cognitiva** | $\le 15$ por función/método (`S3776`) | Máximo $\le 10$ en todo el código | ✅ PASS |
| **Duplicación de Literales** | Cero cadenas $\ge 3$ repetidas (`S1192`) | 0 duplicados detectados | ✅ PASS |
| **Parámetros de Función** | $\le 7$ parámetros (`S107`) | Cumple en todos los módulos | ✅ PASS |
| **Seguridad Estática** | 0 secretos / 0 inyecciones de comandos | 0 vulnerabilidades detectadas | ✅ PASS |
| **Estándar Markdown** | DavidAnson `.markdownlint.json` | 100% compliant (`--check-only`) | ✅ PASS |
| **Tests Unitarios** | Cobertura $\ge 80\%$, exit code 0 | 79/79 tests superados (1.72s) | ✅ PASS |
| **Hard Gate Presupuesto** | Reglas $\le 24$ KB, tokens $\le 16$k, eager $\le 3$k | 100% compliant en ECC Root y Plugin | ✅ PASS |
| **AgentShield Security** | Escaneo de hooks, MCPs y skills | 100% compliant sin bypass/inyecciones | ✅ PASS |

---

## 2. Presupuesto de Tokens y Contexto (Two-Tier Architecture)

- **Tier 1 (Always-On Global Plugin `~/.gemini/config/plugins/ecc-agy`)**:
  - **Skills Activas**: 22 skills nucleares transversales (incluye `engineering-lifecycle`).
  - **Consumo de Caracteres**: ~2.945 caracteres (~736 tokens).
  - **Optimización Lograda**: Reducción del **98.2%** respecto al estado previo de 40.000 tokens.
- **Tier 2 (Repositorio Base `ACB75/ecc`)**:
  - **Skills Canónicas Disponibles**: 171 skills especializadas (incluye `gemini-deep-ops`, frontmatter $\le 140$ caracteres).
  - **Subagentes Disponibles**: 49 agentes especializados (frontmatter `description` $\le 120$ caracteres).
  - **Reglas Universales**: `rules/AGENTS.md` (20.547 caracteres).
  - **Total Repositorio**: ~12.097 tokens (completamente desacoplado del prompt global).

---

## 3. Estado de Automatización y Gobernanza del Harness

- **Workflow de Ingeniería 4 Fases**: Estandarizado en [`doc/templates/`](templates/README.md) (`1. Requisitos & Impacto` -> `2. Plan de Acción & TDD` -> `3. Documentación & Release Notes` -> `4. Commits & PR`) con enforzamiento de paridad `home-lab-sdk`, PostgreSQL LTS multitenant lock safety, Ingress único y SRE throttling.
- **Hard Gate de Presupuesto en Harness**: Implementado en [`workspace_audit.py`](../scripts/ecc-agy/workspace_audit.py) con límites bloqueantes para bytes de reglas ($\le 24$ KB), tokens agregados ($\le 16.000$), servidores MCP pesados y personalizaciones eager ($\le 3.000$ tokens en plugins).
- **Integración Zero-Overhead Gemini MCP & Deep Ops**: Plantilla opcional en `templates/plugins/gemini-mcp/` con `"disabled": true` y CLI determinista `gemini_deep_ops.py` / `toggle_gemini_mcp.py` para diagnósticos multimodales a 0 tokens en reposo.
- **Hooks Nativos, AgentShield e Instintos**: Manifiesto `hooks.json` nativo (safety guard en `PreToolUse`, auto-lint en `PostToolUse`), módulo AgentShield en `security_audit.py` y motor de instintos `.agents/instincts/` desacoplado de `AGENTS.md`.
- **Alineación de Prompt Caching Gemini 3.8**: Reestructuración binaria de `AGENTS.md` (prefijo estático invariante continuo + sufijo contextual) y marcador canónico `<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->` validado en test de arnés para maximizar hit-ratio de KV-cache y reducir TTFT hasta un 60%.
- **Gobernanza de Ramas**: Enforzada mediante [`validate_branch.py`](../scripts/ecc-agy/validate_branch.py) (patrones `fix/<id>`, `feat/*`, `refactor/*`, `infra/*`, `chore/*`, `docs/*`, `test/*`; bloqueo directo en `main`).
- **Autopsias SRE 5W**: Generación automática obligatoria mediante [`generate_postmortem.py`](../scripts/ecc-agy/generate_postmortem.py) ante cualquier cierre de rama `fix/*`.
- **Ciclo Completo de PR y Automerge**: Implementado de forma idempotente y multiplataforma en [`complete-task-pr.ps1`](../scripts/bin/ecc-agy/complete-task-pr.ps1) y [`complete-task-pr.sh`](../scripts/bin/ecc-agy/complete-task-pr.sh) con Pre-Flight Review, auto-archivo de TODOs, Quality Gates y squash-automerge.
- **Backlog Activo**: 8 tareas pendientes en [`doc/TODO.md`](TODO.md) (Prioridad 2 completada al 100%, archivada en [`doc/TODO_DONE/`](TODO_DONE/)).
