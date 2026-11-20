---
title: "**Adoptar hooks deterministas, escaneo de seguridad del harness e instintos por proyecto desde `affaan-m/ECC`**"
status: COMPLETED
completed_at: "2026-11-20 20:13:08"
---

# TODO: **Adoptar hooks deterministas, escaneo de seguridad del harness e instintos por proyecto desde `affaan-m/ECC`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 20:13:08

### Detalle Original

- **01 - ROLE:** AI Security & Agent Reliability Engineer (experto en *AgentShield*, hooks deterministas de ciclo de vida y sistemas de aprendizaje continuo por proyecto).
- **02 - CONTEXT:** `[Sector: Agent Security & Continuous Learning]` `[Data Type: Antigravity hooks.json, Python/PowerShell Security Scanner, .agents/instincts/]` `[Objective: Trasladar controles clave de AGENTS.md a hooks.json deterministas (0 tokens), incorporar auditoría AgentShield sobre configuraciones del harness y adaptar continuous-learning-v2 a .agents/ en home-lab]` `[Restrictions: hooks.json debe ubicarse en la raíz del plugin nativo; mantener presupuesto de Tier 1 intacto]`.
- **03 - PHASE 1 (ANALYSIS):**
  - Hoy el cumplimiento de `lint-markdown.ps1` o bloqueos de `safety-guard` depende de la atención del modelo sobre `AGENTS.md`.
  - `ecc` contiene `skills/continuous-learning-v2/` orientado a rutas `~/.claude/`, y falta un escáner tipo *AgentShield* que audite `mcp_config.json`, `hooks.json` y `skills/` contra secretos o *prompt injection*.
- **04 - PHASE 2 (STRATEGY):**
  - *Enfoque A*: Añadir solo `hooks.json` mínimo en `ecc-agy` para validaciones post-edición y pre-comando.
  - *Enfoque B*: Integrar módulo *AgentShield* en `workspace_audit.py` para auditar permisos, secretos y scripts de hooks/MCPs.
  - *Enfoque C (Integral)*: Implementar `hooks.json` en la raíz del plugin + módulo AgentShield en `workspace_audit.py` + adaptador de instintos hacia `.agents/instincts/` en `home-lab`.
- **05 - PHASE 3 (EXECUTION):**
    1. Diseñar y validar `hooks.json` en la raíz del plugin `ecc-agy` (sin exceder latencia ni romper flujos Windows `pwsh`).
    2. Añadir chequeos *AgentShield* (secretos en `mcp_config.json`, comandos inseguros en `hooks.json`, patrones sospechosos en `skills/`) dentro de `workspace_audit.py` + tests.
    3. Adaptar la captura de instintos de `continuous-learning-v2` para persistir aprendizajes específicos del clúster en `home-lab/.agents/instincts/` sin inflar `AGENTS.md`.
    4. Ejecutar suite completa de auditoría, `pytest` y `lint-markdown.ps1`.
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Evitar hooks bloqueantes lentos que degraden cada edición de archivo; limitar los hooks síncronos a operaciones sub-segundo o rutas específicas.
- **07 - PHASE 5 (FORMAT):**
  - `hooks.json` válido, extensión auditada de `workspace_audit.py` con tests en verde y documentación en `doc/`.
- **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens) para el modelo de amenazas de hooks y AgentShield; **Carbon ($C_6$)** para la implementación de código.
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 3. Entregables y Notas de Cierre

Hooks nativos hooks.json, suite AgentShield y gestor de instintos por proyecto completados

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `feat/ecc/hooks-agentshield-instincts`
- **Commit SHA**: `0506591`
- **Fecha**: `2026-11-20 20:13:08`
- **Gobernanza**: Quality Gate A / markdownlint OK
