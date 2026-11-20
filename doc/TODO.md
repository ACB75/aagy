# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | ECC ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Analiza las dependencias entre tareas y resuélvelas en el orden secuencial óptimo (gobernanza/harness → tokens/contexto → guardrails de calidad → automatización de git/PRs).
> 2. **Flujo Git Automatizado:** Genera ramas atómicas por tarea, resuelve conflictos de forma contextual, ejecuta tests unitarios/e2e y realiza `auto-merge` continuo en la rama principal hasta agotar el presupuesto de tokens asignado.
> 3. **Tarea Final Obligatoria (Higiene y Meta-Herramientas):** Al completar el backlog funcional, ejecuta una fase final de limpieza: purgar dependencias huérfanas, eliminar código muerto, actualizar documentación técnica y desplegar el motor de autodescubrimiento para sintetizar `skills`, `rules`, `agents` y `git hooks` optimizados para los flujos repetitivos del repositorio.

---

## 0. Máxima Prioridad: Optimización de Tokens, Purga General, Unificación y Estructura `/doc` v2

### Tarea 0.1: Optimización Máxima de Tokens, Purga de Artefactos Muertos, Unificación y Reestructuración `scripts/`

### Tarea 0.2: Purga y Regeneración Limpia de `/doc` v2, Parametrización `docs-map.json` y Paridad 1-a-1 Manual

- [ ] **Purgar `/doc` y regenerarlo desde cero con estructura v2 (`00-governance`..`06-backlog`, `<folder>/dgrms/`), parametrizar scripts y garantizar paridad manual $\leftrightarrow$ plugin**
  - **01 - ROLE:** Documentation Governance & Developer Experience Architect.
  - **02 - CONTEXT:** `[Sector: Documentation Architecture & CLI Workflow Parity]` `[Data Type: /doc v2, .governance/docs-map.json, scripts/{py,sh,pwsh}, diagramas .puml/.bpmn/.mmd]` `[Objective: Purgar doc/plan/ y documentación obsoleta que no siga convención; regenerar /doc v2 (raíz solo INDEX.md, CONTEXT.md, STATUS.md, LOG.md; 00-governance a 06-backlog; dgrms/ en todas las carpetas con diagramas; the-security-guide.md conservado y STACK_MODERNO_GOOGLE.md renombrado a google-modern-stack.md); parametrizar rutas vía .governance/docs-map.json con fallback retrocompatible para home-lab; habilitar flujo flexible [IDEAS -> REQUISITOS -> PLAN -> TODO] y paridad 1-a-1 manual]` `[Restrictions: Zero-Breaking con home-lab mediante fallback; validar rutas contra path traversal; ver REQ_doc_structure_v2_and_manual_parity.md]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Ver requisitos aprobados en [REQ_doc_structure_v2_and_manual_parity.md](file:///c:/Workspace/projects/ecc/doc/plan/REQ_doc_structure_v2_and_manual_parity.md).
  - **04 - PHASE 2 (STRATEGY):**
    - Implementar resolvedor `.governance/docs-map.json` con fallback $\rightarrow$ migrar/regenerar `/doc` v2 $\rightarrow$ documentar `DOC_STANDARDS.md` y `MANUAL_WORKFLOW.md`.
  - **05 - PHASE 3 (EXECUTION):**
    1. Implementar resolvedor de rutas + tests unitarios.
    2. Purgar `doc/` heredado y regenerar árbol `/doc` v2 rescatando ADRs (`02-adr/`), `the-security-guide.md`, `google-modern-stack.md` y plantillas renombradas (`TEMPLATE_ADR.md`, `TEMPLATE_POSTMORTEM.md`).
    3. Actualizar scripts para flujo flexible y paridad CLI manual, verificando `pytest` y `lint-markdown.ps1` (exit `0`).
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Confirmar que `home-lab` sigue operando sin errores gracias al *fallback* y que `complete-task-pr.ps1` mantiene el gate de `pytest` verde.
  - **07 - PHASE 5 (FORMAT):**
    - Árbol `/doc` v2 limpio, cero enlaces rotos y tests en verde.
  - **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens); **Carbon ($C_6$)** para scripts y tests.
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

### Tarea 0.3: Optimización y Unificación del Sistema de Autodescubrimiento y Automejora

- [ ] **Unificar y optimizar `auto-evolve`, `instinct_manager`, `agent-self-evaluation` y skills de aprendizaje continuo en un motor único para `aagy`**
  - **01 - ROLE:** Autonomous Agent Reliability & Self-Improvement Systems Architect.
  - **02 - CONTEXT:** `[Sector: Agent Self-Discovery & Continuous Learning]` `[Data Type: auto-evolve, instinct_manager.py, hooks.json, skills de evaluación/aprendizaje]` `[Objective: Unificar las piezas sueltas de autodescubrimiento y automejora en un flujo determinista y acotado en presupuesto para aagy]` `[Restrictions: Toma de requisitos dedicada previa a la implementación; cero inflación de AGENTS.md/rules/; promoción segura con smoke-test y gate de presupuesto]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Existen piezas desconectadas (`auto-evolve.ps1` orientado a `home-lab`, `instinct_manager.py`, skills legacy `continuous-learning-v2` / `eval-harness` / `agent-self-evaluation`).
    - Ver requisitos aprobados en [REQ_aagy_unified_self_improvement.md](file:///c:/Workspace/projects/ecc/doc/plan/REQ_aagy_unified_self_improvement.md).
  - **04 - PHASE 2 (STRATEGY):**
    - Definir requisitos formales primero y consolidar un único motor agnóstico conectado al ciclo de vida y presupuesto.
  - **05 - PHASE 3 (EXECUTION):**
    1. Completar toma de requisitos (`REQ_`).
    2. Unificar módulos y eliminar redundancias.
    3. Validar con `pytest` y `audit-workspace.ps1` (exit `0`).
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Evitar auto-generación de reglas/skills que desborden el presupuesto de tokens.
  - **07 - PHASE 5 (FORMAT):**
    - Motor unificado, documentado y cubierto por tests.
  - **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens); **Carbon ($C_6$)** para implementación.
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

---

## 1. Prioridad 1: Harness Universal de Gobernanza (`aagy` / `ecc`) & Automatización Git

*(Completadas y Archivadas en `doc/TODO_DONE/`)*:

- Tarea 1.1: Desacoplamiento Agnóstico de `ecc` a `aagy` y Saneamiento de Submódulos -> `TODO_DONE/`
- Tarea 1.2: Pipeline Automatizado de Ingesta `IDEAS.md` -> `TODO.md` & CLI de Mapeo Documental -> `TODO_DONE/`
- Tarea 1.3: Estandarización de Política de Ramas de Incidencias en el Harness (`fix/<id>`) -> `TODO_DONE/`
- Tarea 1.4: Generador Automatizado de Post-Mortem 5W (`PM_<branch>_<timestamp>.md`) -> `TODO_DONE/`
- Tarea 1.5: Finalización Automatizada de Tarea en Curso y Orquestación PR (`complete-task-pr`) -> `TODO_DONE/`

---

## 2. Prioridad 2: Integraciones `affaan-m/ECC` & `RLabs-Inc/gemini-mcp` (Zero-Budget-Overflow)

*(Completadas y Archivadas en `doc/TODO_DONE/`)*:

- Tarea 2.1: Hard Gate de Presupuesto de Rules, Customizations y MCPs en `workspace_audit.py` -> `TODO_DONE/`
- Tarea 2.2: Integración Zero-Overhead de `gemini-mcp` (`disabled: true`) y Skill `gemini-deep-ops` -> `TODO_DONE/`
- Tarea 2.3: Hooks Nativos (`hooks.json`), Auditoría AgentShield e Instintos AGY -> `TODO_DONE/`

---

## 3. Prioridad 3: Optimizaciones Genéricas del Plugin (`ecc-agy`)

*(Completadas y Archivadas en `doc/TODO_DONE/`)*:

- Tarea 3.1: Alineación de Prompt Caching de Gemini 3.8 y Reordenamiento Estático de System Prompts -> `TODO_DONE/`
- Tarea 3.2: Git Pre-Commit Hook Nativo y Scripts de Instalación (`install-git-hooks.ps1` / `.sh`) -> `TODO_DONE/`
- Tarea 3.3: Telemetría Proactiva de Presupuesto en Sesión y Política de Auto-Compact / Compact Estratégico -> `TODO_DONE/`
- Tarea 3.4: CLI de Promoción On-Demand de Skills Tier-2 $\leftrightarrow$ Tier-1 (`enable-skill.ps1` / `disable-skill.ps1`) -> `TODO_DONE/`
- Tarea 3.5: Reubicación y Estandarización de Plantillas Documentales (`TEMPLATE_ADR.md` y `TEMPLATE_POSTMORTEM.md`) -> `TODO_DONE/`

---

## 4. Prioridad 4: Optimizaciones Específicas de Home-Lab (Microservicios, SDK y Resiliencia LTS)

*(Completadas y Archivadas en `doc/TODO_DONE/`)*:

- Tarea 4.1: Linter Automático de Paridad de Contratos `home-lab-sdk` (`audit-sdk-parity.py` / `.ps1`) -> `TODO_DONE/`
- Tarea 4.2: Analizador Estático de Bloqueos DDL y Concurrencia en PostgreSQL LTS (`audit-pg-locks.py` / `.ps1`) -> `TODO_DONE/`
- Tarea 4.3: Validador de Rutas Traefik, Split-DNS (CoreDNS) y Catálogo `/portal` -> `TODO_DONE/`
- Tarea 4.4: Automatización de Pipeline de Despliegue Docker Compose por Tag en `git-flow-helper.ps1` -> `TODO_DONE/`

---

## 5. Prioridad 5: Cierre Maestro — Rebranding y Migración de `/ecc` a `/aagy` (`Anything Antigravity`)

### Tarea 5.1: Migración de `/ecc` a `/aagy` (*Anything Antigravity*) y Sincronización del Plugin `ecc`

---

## 6. Gobernanza de Modelos, Tokens y Política de Auto-Compact

### 6.1. Matriz de Asignación de Modelos por Tarea (Token Optimization)

| Tarea | Agente Elemental | Modelo Gemini 3.8 | Presupuesto Tokens / Turno | Justificación de Eficiencia |
| :--- | :--- | :--- | :--- | :--- |
| **0.1 Tokens, Purga & `scripts/`** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (poda) + `flash` (migración) | ~6.000 tokens | Unificación de duplicados, lazy-loading de rules y reordenación `scripts/`. |
| **0.2 `/doc` v2 & Paridad Manual**| **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (diseño) + `flash` (scripts) | ~6.000 tokens | Resolvedor `docs-map.json` con fallback, purga `/doc` y paridad CLI. |
| **0.3 Autodescubrimiento Unificado**| **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (diseño) + `flash` (código) | ~6.000 tokens | Unificación de `auto-evolve`, instintos y autoevaluación bajo budget gate. |
| **2.1 Hard Gate Presupuesto** | **Carbon ($C_6$)** | `flash` | ~1.200 tokens | Código Python stdlib directo sin necesidad de razonamiento extendido. |
| **2.2 Integración gemini-mcp** | **Carbon ($C_6$)** | `flash` | ~1.000 tokens | Generación de manifiestos JSON estáticos y scripts de soporte. |
| **2.3 Hooks & AgentShield** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (diseño) + `flash` (código) | ~6.000 tokens | Modelado de amenazas de seguridad requiere Pro Thinking; código en Flash. |
| **3.1 Prompt Caching Alignment** | **Carbon ($C_6$)** | `flash` | ~1.000 tokens | Reordenamiento estructural de Markdown con formato determinista. |
| **3.2 Git Pre-Commit Hooks** | **Carbon ($C_6$)** | `flash` | ~1.200 tokens | Scripts de automatización en PowerShell y Bash POSIX. |
| **3.3 Telemetría Tokens Sesión**| **Carbon ($C_6$)** | `flash` | ~1.000 tokens | Análisis de archivos JSONL y métricas numéricas. |
| **3.4 CLI Promoción Skills** | **Carbon ($C_6$)** | `flash` | ~1.100 tokens | Operaciones de archivos y validación de frontmatter. |
| **3.5 Estandarización Plantillas**| **Carbon ($C_6$)** | `flash` | ~800 tokens | `git mv` y actualización determinista de referencias y enlaces. |
| **4.1 Linter Paridad SDK** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (análisis) + `flash` (código) | ~8.000 tokens | Análisis de contratos políglotas (Go/TS/Python) requiere Pro Thinking. |
| **4.2 Analizador Bloqueos PG** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (semántica) + `flash` (parser) | ~10.000 tokens| El análisis de transacciones, deadlocks y bloqueos LTS requiere Pro Thinking. |
| **4.3 Validador Ingress / Portal**| **Carbon ($C_6$)** | `flash` | ~1.200 tokens | Cruce de configuraciones estáticas YAML, Go y CoreDNS. |
| **4.4 Despliegue Tagged CD** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (rollback) + `flash` (script) | ~6.000 tokens | Garantía de rollback $< 2$ min y probes de resiliencia SRE. |
| **5.1 Migración Repo `/aagy` + `ecc`**| **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (cutover) + `flash` (rename) | ~6.000 tokens | Migración con historial Git, *full rename* y paridad `aagy` $\leftrightarrow$ `ecc`. |

---

### 6.2. Política de Compactación & Disparadores de Auto-Compact

Para preservar la atención del modelo y minimizar el consumo de tokens en sesiones largas:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   POLÍTICA DE COMPACTACIÓN DE SESIÓN                   │
├───────────────────────────────────┬────────────────────────────────────┤
│ DISPARADOR POR EVENTO (LIFECYCLE) │ DISPARADOR POR UMBRAL DE TOKENS    │
├───────────────────────────────────┼────────────────────────────────────┤
│ • Al completar la Fase 4 de tarea │ • Sesión acumulada > 45.000 tokens │
│ • Tras 'complete-task-pr.ps1'     │ • Aviso inmediato de telemetría    │
│ • Antes de cambiar de rama / tarea│ • Ejecutar /compact recomendado    │
└───────────────────────────────────┴────────────────────────────────────┘
```

1. **Disparador Basado en Eventos del Ciclo de Vida**:
   - Tras ejecutar exitosamente `complete-task-pr.ps1` y fusionar la rama de tarea en `main`, el contexto de implementación de esa tarea ya no es necesario para la siguiente. Ese es el **punto exacto de compactación** para purgar el historial y comenzar la siguiente tarea con contexto limpio.
2. **Disparador Basado en Umbral Cuantitativo (> 45k tokens)**:
   - Si una tarea compleja requiere múltiples iteraciones de TDD y el transcript acumulado supera los **45.000 tokens**, el agente debe sugerir de inmediato la ejecución del comando `/compact` para consolidar el estado de los archivos modificados y liberar el 70%+ de la ventana de contexto.
3. **Mecanismo de Auto-Compact**:
   - `complete-task-pr.ps1` emitirá en su reporte de cierre el aviso: `[ADVICE] Tarea finalizada. Presupuesto acumulado sugerido para compactación. Ejecute /compact antes de iniciar la siguiente tarea.`
