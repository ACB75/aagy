# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | ECC ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Analiza las dependencias entre tareas y resuélvelas en el orden secuencial óptimo (gobernanza/harness → tokens/contexto → guardrails de calidad → automatización de git/PRs).
> 2. **Flujo Git Automatizado:** Genera ramas atómicas por tarea, resuelve conflictos de forma contextual, ejecuta tests unitarios/e2e y realiza `auto-merge` continuo en la rama principal hasta agotar el presupuesto de tokens asignado.
> 3. **Tarea Final Obligatoria (Higiene y Meta-Herramientas):** Al completar el backlog funcional, ejecuta una fase final de limpieza: purgar dependencias huérfanas, eliminar código muerto, actualizar documentación técnica y desplegar el motor de autodescubrimiento para sintetizar `skills`, `rules`, `agents` y `git hooks` optimizados para los flujos repetitivos del repositorio.

---

## 0. Máxima Prioridad: Optimización de Tokens, Purga General, Unificación y Estructura `/doc` v2

### Tarea 0.3: Optimización y Unificación del Sistema de Autodescubrimiento y Automejora

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

### Tarea 5.1: Migración de `/ecc` a `/aagy` (*Anything Antigravity*), Nuevo `README.md`, Reinstalación del Plugin y Sincronización `aagy-ecc`

- [ ] **Ejecutar el cierre maestro: migrar `/ecc` a `/aagy` (*Anything Antigravity*) conservando historial Git, generar el nuevo `README.md` del repo, sincronizar `aagy/aagy-ecc/` y reinstalar el plugin limpio**
  - **01 - ROLE:** Principal Release & Repository Migration Architect.
  - **02 - CONTEXT:** `[Sector: Repository Lifecycle & Brand Migration]` `[Data Type: Git repo /ecc -> /aagy (historial íntegro), README.md raíz, plugin ~/.gemini/config/plugins/aagy, aagy/aagy-ecc/]` `[Objective: (1) Migrar /ecc a /aagy conservando historial Git y renombrando el remoto (gh repo rename aagy); (2) Mantener aagy/aagy-ecc/ actualizado, operativo y sincronizado con aagy; (3) Generar un nuevo README.md en la raíz de /aagy reflejando la arquitectura final (aagy + aagy-ecc, /doc v2, scripts/{py,pwsh,sh}, instalación manual y paridad CLI); (4) Reinstalar limpiamente el plugin mediante install.ps1/.sh verificando smoke-test y retirando /ecc tras confirmación explícita]` `[Restrictions: Ejecutar como última tarea tras completar 0.2, 0.3 y 0.4; conservar historial Git; 0 referencias rotas; budget hard gate y pytest en verde]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Ver requisitos aprobados en [`REQ_aagy_clean_docs_and_repo_migration.md`](plans/REQ_aagy_clean_docs_and_repo_migration.md).
  - **04 - PHASE 2 (STRATEGY):**
    - Cutover preservando historial $\rightarrow$ sincronización `aagy` $\leftrightarrow$ `aagy-ecc` $\rightarrow$ nuevo `README.md` $\rightarrow$ reinstalación limpia (`install.ps1` / `.sh`) $\rightarrow$ verificación integral y retirada de `/ecc` con confirmación.
  - **05 - PHASE 3 (EXECUTION):**
    1. Confirmar `0.2`, `0.3` y `0.4` completadas y en verde.
    2. Migrar `/ecc` $\rightarrow$ `/aagy` preservando historial Git y renombrar remoto (`gh repo rename aagy`).
    3. Sincronizar `aagy/aagy-ecc/` y generar el nuevo `README.md` de raíz.
    4. Reinstalar el plugin limpio (`./install.ps1`) en `~/.gemini/config/plugins/aagy` (y `aagy-ecc`), validando `pytest`, `audit-workspace.ps1` y `lint-markdown.ps1` (exit `0`).
    5. Solicitar confirmación final al usuario para retirar `/ecc`.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: No eliminar `/ecc` hasta verificar el plugin reinstalado y el 100% de tests en verde en `/aagy`.
  - **07 - PHASE 5 (FORMAT):**
    - `/aagy` operativo, `README.md` nuevo, plugin reinstalado y tests en verde.
  - **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens); **Carbon ($C_6$)** para `README.md`, reinstalación y tests.
  - **COMPACT TRIGGER:** Al completar el cutover final en `/aagy`.

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
