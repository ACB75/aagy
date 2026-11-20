---
title: "**Consolidar `scripts/` (eliminando `bin/` y `aagy/`), purgar `.js`/`lib/` muertos, deduplicar `AGENTS.md` raíz, ordenar scripts raíz y actualizar `aagy-ecc` al mismo nivel que `aagy`**"
status: COMPLETED
completed_at: "2026-11-20 22:56:37"
---

# TODO: **Consolidar `scripts/` (eliminando `bin/` y `aagy/`), purgar `.js`/`lib/` muertos, deduplicar `AGENTS.md` raíz, ordenar scripts raíz y actualizar `aagy-ecc` al mismo nivel que `aagy`**

## 1. Descripción de la Tarea

- **Estado**: COMPLETED
- **Fecha de Finalización**: 2026-11-20 22:56:37

### Detalle Original

- **01 - ROLE:** Principal Repository Hygiene & Multi-Agent Packaging Engineer.
- **02 - CONTEXT:** `[Sector: Repo Hygiene & Dual-Plugin Parity]` `[Data Type: manifests/, schemas/, templates/, scripts/*.js, scripts/lib/, rules/AGENTS.md, pr-automerge-lifecycle.md, ~/.gemini/config/plugins/aagy, plugin.json, VERSION, package-lock.json, .vscode/, .gemini/GEMINI.md, root AGENTS.md, install.ps1/.sh, aagy-sync.ps1/.sh, aagy-ecc/]` `[Objective: (1) Eliminar scripts/bin/ y scripts/aagy/ si queda algún remanente frente a scripts/{py,pwsh,sh}/tests/; (2) Purgar manifests/, schemas/, templates/ (raíz), plugin.json, VERSION, package-lock.json, .vscode/aagy.code-workspace y scripts/*.js + scripts/lib/ del instalador Node.js antiguo (unificando instalación de aagy y aagy-ecc vía install.ps1/.sh), además de revisar/podar .gemini/GEMINI.md y actualizar package.json (workspaces: aagy-ecc); (3) Compactar rules/AGENTS.md de 21.4 KB a < 12 KB delegando tutoriales/detalles a skills lazy-loaded, fusionar pr-automerge-lifecycle.md en AGENTS.md y retirar la copia duplicada ~/.gemini/config/plugins/aagy dejando solo aagy; (4) Dejar root AGENTS.md ultra-corto (~10-15 líneas), mantener install.ps1/.sh en raíz y mover aagy-sync a scripts/{pwsh,sh}/]` `[Restrictions: Zero-Breaking en hooks.json y flujo de instalación; pytest y tests pwsh/sh en verde]`.
- **03 - PHASE 1 (ANALYSIS):**
  - `scripts/*.js` (`10`) y `scripts/lib/` (`53`) contienen código heredado de Cursor/Codex/OpenCode sin uso en `aagy`.
  - `AGENTS.md` en raíz duplica `rules/AGENTS.md` y `aagy-sync` en raíz duplica lógica que pertenece a `scripts/{pwsh,sh}/`.
- **04 - PHASE 2 (STRATEGY):**
  - Purga selectiva + actualización de `aagy-ecc` (paridad total con `aagy`) + adelgazamiento de raíz.
- **05 - PHASE 3 (EXECUTION):**
    1. Purgar remanentes de `bin/`, `aagy/` y módulos `.js`/`lib/` de Cursor/Codex/OpenCode; conservar/mover a `scripts/js/tests/` (o `aagy-ecc/`) lo activo de Claude Code.
    2. Actualizar y renombrar `aagy` $\rightarrow$ `aagy-ecc` funcionando igual que `aagy`.
    3. Reducir `AGENTS.md` raíz a ~10-15 líneas locales; mantener `install.ps1/.sh` en raíz y mover `aagy-sync` a `scripts/{pwsh,sh}/`.
    4. Verificar `pytest`, `audit-workspace.ps1` y `lint-markdown.ps1` (exit `0`).
- **06 - PHASE 4 (CRITIC):**
  - *Auditoría*: Confirmar que `install.ps1` / `.sh` instala tanto `aagy` como `aagy-ecc` sin rutas rotas.
- **07 - PHASE 5 (FORMAT):**
  - Raíz limpia, `scripts/{py,pwsh,sh,js}/tests/` ordenado y `aagy-ecc` operativo.
- **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.500 tokens).
- **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

## 2. Verificación y Criterios de Aceptación

- [x] Tarea implementada y verificada contra criterios de aceptación.

## 4. Metadatos de Integración y Commit

- **Rama / PR**: `refactor/aagy/root-cleanup-and-aagy-aagy-parity`
- **Commit SHA**: `72adabc`
- **Fecha**: `2026-11-20 22:56:37`
- **Gobernanza**: Quality Gate A / markdownlint OK
