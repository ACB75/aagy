# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | ECC ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Analiza las dependencias entre tareas y resuélvelas en el orden secuencial óptimo (gobernanza/harness → tokens/contexto → guardrails de calidad → automatización de git/PRs).
> 2. **Flujo Git Automatizado:** Genera ramas atómicas por tarea, resuelve conflictos de forma contextual, ejecuta tests unitarios/e2e y realiza `auto-merge` continuo en la rama principal hasta agotar el presupuesto de tokens asignado.
> 3. **Tarea Final Obligatoria (Higiene y Meta-Herramientas):** Al completar el backlog funcional, ejecuta una fase final de limpieza: purgar dependencias huérfanas, eliminar código muerto, actualizar documentación técnica y desplegar el motor de autodescubrimiento para sintetizar `skills`, `rules`, `agents` y `git hooks` optimizados para los flujos repetitivos del repositorio.

---

## 0. Máxima Prioridad: Optimización de Tokens, Purga General, Unificación y Estructura `/doc` v2

### Tarea 0.2: Purga y Regeneración Limpia de `/doc` v2, Parametrización `docs-map.json` y Paridad 1-a-1 Manual

### Tarea 0.3: Optimización y Unificación del Sistema de Autodescubrimiento y Automejora

- [ ] **Unificar y optimizar `auto-evolve`, `instinct_manager`, `agent-self-evaluation` y skills de aprendizaje continuo en un motor único para `aagy`**
  - **01 - ROLE:** Autonomous Agent Reliability & Self-Improvement Systems Architect.
  - **02 - CONTEXT:** `[Sector: Agent Self-Discovery & Continuous Learning]` `[Data Type: auto-evolve, instinct_manager.py, hooks.json, skills de evaluación/aprendizaje]` `[Objective: Unificar las piezas sueltas de autodescubrimiento y automejora en un flujo determinista y acotado en presupuesto para aagy]` `[Restrictions: Toma de requisitos dedicada previa a la implementación; cero inflación de AGENTS.md/rules/; promoción segura con smoke-test y gate de presupuesto]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Existen piezas desconectadas (`auto-evolve.ps1` orientado a `home-lab`, `instinct_manager.py`, skills legacy `continuous-learning-v2` / `eval-harness` / `agent-self-evaluation`).
    - Ver requisitos aprobados en [`REQ_aagy_unified_self_improvement.md`](plans/REQ_aagy_unified_self_improvement.md).
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

### Tarea 0.4: Limpieza de `scripts/*.js` / `lib/`, `AGENTS.md` Raíz, Scripts Raíz y Paridad `aagy-ecc`

- [ ] **Consolidar `scripts/` (eliminando `bin/` y `ecc-agy/`), purgar `.js`/`lib/` muertos, deduplicar `AGENTS.md` raíz, ordenar scripts raíz y actualizar `aagy-ecc` al mismo nivel que `aagy`**
  - **01 - ROLE:** Principal Repository Hygiene & Multi-Agent Packaging Engineer.
  - **02 - CONTEXT:** `[Sector: Repo Hygiene & Dual-Plugin Parity]` `[Data Type: manifests/, schemas/, templates/, scripts/*.js, scripts/lib/, rules/AGENTS.md, pr-automerge-lifecycle.md, ~/.gemini/config/plugins/ecc-agy, ecc.json, VERSION, package-lock.json, .vscode/, .gemini/GEMINI.md, root AGENTS.md, install.ps1/.sh, ecc-agy-sync.ps1/.sh, aagy-ecc/]` `[Objective: (1) Eliminar scripts/bin/ y scripts/ecc-agy/ si queda algún remanente frente a scripts/{py,pwsh,sh}/tests/; (2) Purgar manifests/, schemas/, templates/ (raíz), ecc.json, VERSION, package-lock.json, .vscode/ecc-aecb.code-workspace y scripts/*.js + scripts/lib/ del instalador Node.js antiguo (unificando instalación de aagy y aagy-ecc vía install.ps1/.sh), además de revisar/podar .gemini/GEMINI.md y actualizar package.json (workspaces: aagy-ecc); (3) Compactar rules/AGENTS.md de 21.4 KB a < 12 KB delegando tutoriales/detalles a skills lazy-loaded, fusionar pr-automerge-lifecycle.md en AGENTS.md y retirar la copia duplicada ~/.gemini/config/plugins/ecc-agy dejando solo aagy; (4) Dejar root AGENTS.md ultra-corto (~10-15 líneas), mantener install.ps1/.sh en raíz y mover ecc-agy-sync a scripts/{pwsh,sh}/]` `[Restrictions: Zero-Breaking en hooks.json y flujo de instalación; pytest y tests pwsh/sh en verde]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - `scripts/*.js` (`10`) y `scripts/lib/` (`53`) contienen código heredado de Cursor/Codex/OpenCode sin uso en `aagy`.
    - `AGENTS.md` en raíz duplica `rules/AGENTS.md` y `ecc-agy-sync` en raíz duplica lógica que pertenece a `scripts/{pwsh,sh}/`.
  - **04 - PHASE 2 (STRATEGY):**
    - Purga selectiva + actualización de `aagy-ecc` (paridad total con `aagy`) + adelgazamiento de raíz.
  - **05 - PHASE 3 (EXECUTION):**
    1. Purgar remanentes de `bin/`, `ecc-agy/` y módulos `.js`/`lib/` de Cursor/Codex/OpenCode; conservar/mover a `scripts/js/tests/` (o `aagy-ecc/`) lo activo de Claude Code.
    2. Actualizar y renombrar `ecc` $\rightarrow$ `aagy-ecc` funcionando igual que `aagy`.
    3. Reducir `AGENTS.md` raíz a ~10-15 líneas locales; mantener `install.ps1/.sh` en raíz y mover `ecc-agy-sync` a `scripts/{pwsh,sh}/`.
    4. Verificar `pytest`, `audit-workspace.ps1` y `lint-markdown.ps1` (exit `0`).
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Confirmar que `install.ps1` / `.sh` instala tanto `aagy` como `aagy-ecc` sin rutas rotas.
  - **07 - PHASE 5 (FORMAT):**
    - Raíz limpia, `scripts/{py,pwsh,sh,js}/tests/` ordenado y `aagy-ecc` operativo.
  - **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.500 tokens).
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

---

## 5. Prioridad 5: Cierre Maestro — Rebranding y Migración de `/ecc` a `/aagy` (`Anything Antigravity`)

### Tarea 5.1: Migración de `/ecc` a `/aagy` (*Anything Antigravity*) y Sincronización del Plugin `aagy-ecc`

---

## 6. Gobernanza de Modelos, Tokens y Política de Auto-Compact

### 6.1. Matriz de Asignación de Modelos por Tarea (Token Optimization)

| Tarea | Agente Elemental | Modelo Gemini 3.8 | Presupuesto Tokens / Turno | Justificación de Eficiencia |
| :--- | :--- | :--- | :--- | :--- |
| **0.2 `/doc` v2 & Paridad Manual**| **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (diseño) + `flash` (scripts) | ~6.000 tokens | Resolvedor `docs-map.json` con fallback, purga `/doc` y paridad CLI. |
| **0.3 Autodescubrimiento Unificado**| **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (diseño) + `flash` (código) | ~6.000 tokens | Unificación de `auto-evolve`, instintos y autoevaluación bajo budget gate. |
| **0.4 Limpieza JS/Raíz & `aagy-ecc`**| **Carbon ($C_6$)** | `flash` | ~1.500 tokens | Purga `.js`/`lib/` muertos, `AGENTS.md` raíz mínimo y paridad `aagy-ecc`. |
| **5.1 Migración Repo `/aagy` + `aagy-ecc`**| **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (cutover) + `flash` (rename) | ~6.000 tokens | Migración con historial Git, *full rename* y paridad `aagy` $\leftrightarrow$ `aagy-ecc`. |

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
