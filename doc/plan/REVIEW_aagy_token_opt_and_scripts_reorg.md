# Fase 4: Propuesta de Commits, Pre-Flight Review & PR

> **Referencia de Gobernanza**: Fase 4 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `refactor/aagy/token-opt-and-scripts-reorg` (`Tarea 0.1`)  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Principal Agentic Runtime & Token Budget Optimizer`  
> **Estado**: `PENDIENTE DE REVISIÓN Y CONFIRMACIÓN`

---

## 1. Aviso de Revisión Manual Obligatoria (Pre-Flight Review)

- **Rama Origen**: `refactor/aagy/token-opt-and-scripts-reorg`
- **Rama Destino**: `main`
- **Título Propuesto**: `[refactor]-[aagy,rules,scripts]: optimizacion de tokens, purga de reglas y reestructuracion scripts`

---

## 2. Cuerpo Explicativo Estructurado del Commit y Pull Request

```text
[refactor]-[aagy,rules,scripts]: optimizacion de tokens, purga de reglas y reestructuracion scripts

- Contexto y Motivación:
  El entorno Antigravity cargaba por duplicado AGENTS.md al operar dentro del repositorio
  del plugin, y mantenía 37 reglas estáticas de stack en rules/, inflando el presupuesto
  de tokens. Adicionalmente, persistían comandos obsoletos en la raíz (97 archivos ya
  migrados al subplugin ecc/commands/ de Claude Code) y scripts sin separación por runtime.

- Modificaciones Principales:
  1. Deduplicación de AGENTS.md: Reducción del archivo raíz a un puntero estático con marcadores
     invariantes de context caching, ahorrando ~5.500 tokens por turno en Antigravity.
  2. Poda de rules/: Reducción a estrictamente 2 reglas (AGENTS.md y pr-automerge-lifecycle.md),
     trasladando las guías de lenguaje a skills lazy-loaded y creando typescript-patterns.
  3. Purga de comandos obsoletos en la raíz (97 archivos eliminados), garantizando la integridad
     del subplugin ecc/commands/ para Claude Code.
  4. Reestructuración de scripts/ en scripts/py/ (+ /tests), scripts/pwsh/ (+ /tests) y
     scripts/sh/ (+ /tests), desplegando proxies de retrocompatibilidad en scripts/bin/ecc-agy/
     y scripts/ecc-agy/ con cero cambios rompientes.
  5. Actualización de hooks.json, install.ps1, ecc-agy-sync.ps1/sh y suites de pruebas unitarias.

- Verificación y Calidad:
  - 120/120 pruebas unitarias superadas exitosamente (pytest scripts/py/tests scripts/pwsh/tests scripts/sh/tests).
  - SonarQube Quality Gate Rating A alcanzado (0 violaciones, Cognitive Complexity <= 15).
  - Presupuesto de tokens respetado: rules/ = 6.164 tokens (límite: 16.000 tokens).
  - 100% de cumplimiento con linter Markdown DavidAnson (.markdownlint.json).
  - Paridad multi-harness verificada (aagy <-> ecc).
```

---

## 3. Resumen de Archivos Afectados

- **Nuevas Skills y Reglas**: `skills/typescript-patterns/SKILL.md`, `rules/pr-automerge-lifecycle.md`.
- **Estructura Modular de Scripts**: `scripts/py/`, `scripts/pwsh/`, `scripts/sh/` y sus subcarpetas `tests/`.
- **Archivos Purgados**: 97 comandos en `commands/` y 37 reglas de stack en `rules/{angular,golang,java,python,typescript,web,common}`.
- **Documentación Técnica**: `doc/manual/MANUAL_scripts_and_token_optimization.md`, `doc/plan/REQ_...`, `PLAN_...`, `DOCS_...`, `REVIEW_...`.
