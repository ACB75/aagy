# Manual de Arquitectura de Scripts, Poda de Reglas y Optimización de Tokens

> **Referencia de Gobernanza**: Guía Oficial de Arquitectura del Repositorio `aagy`  
> **ID**: `MANUAL-SCRIPTS-TOKEN-OPT-01` | **Fecha**: `2026-11-20`  
> **Estado**: `VIGENTE`

---

## 1. Visión General y Objetivos de Diseño

El sistema de agentes y herramientas Anything Antigravity (`aagy`) requiere operar bajo límites estrictos de consumo de tokens, separación de responsabilidades y modularidad limpia. Este manual documenta la reorganización modular de scripts, la poda estricta de `rules/` y la eliminación de duplicidad entre el espacio de trabajo local y el plugin global.

---

## 2. Estructura de `scripts/` y lanzador único

Toda la lógica vive en `scripts/py/` (Python 3 stdlib). PowerShell y Bash solo tienen un
lanzador, más los pocos scripts que hacen trabajo propio del shell:

```text
scripts/
├── py/        # motores (workspace_audit.py, complete_task_pr.py, backlog.py, ...) y tests/
├── ps1/       # aagy.ps1 (lanzador), aagy-sync.ps1, git-flow-helper.ps1, install-git-hooks.ps1, lint-markdown.ps1
└── sh/        # aagy.sh (lanzador), aagy-sync.sh, git-flow-helper.sh, install-git-hooks.sh, lint-markdown.sh
```

`aagy <comando> [args]` ejecuta `scripts/py/<comando>.py` (guiones a guion bajo) con los
mismos argumentos, que son los flags de Python:

```bash
bash scripts/sh/aagy.sh help                              # lista los comandos
bash scripts/sh/aagy.sh complete-task-pr --review-only
pwsh -NoProfile -File scripts/ps1/aagy.ps1 workspace-audit --clean
```

Los antiguos envoltorios (`complete-task-pr.ps1`, `audit-workspace.ps1`, `safety-check.ps1`...)
se retiraron. Equivalencias con otro nombre: `audit-workspace` → `workspace-audit`,
`auto-evolve` → `self-improve`, `manage-instincts` → `instinct-manager`, `safety-check` →
`hook-safety`, `enable-skill` / `disable-skill` → `skill-promotion --promote` / `--demote`,
`hook-stop-capture` → `self-improve --capture-stop`.

---

## 3. Poda de `rules/` y Carga Bajo Demanda (*Lazy-Loading*)

### Política de Reglas Nucleares

El directorio `rules/` solo debe contener reglas transversales invariantes de aplicación global en cada turno de conversación:

1. `rules/AGENTS.md`: constitución y estándares universales de ingeniería (Google 5-Pillars, SRE, TBD,
   SonarQube Rating A) y ciclo de vida de la PR (sin auto-merge: la fusiona una persona).

### Migración de Reglas de Stack a Skills

Las guías de desarrollo por lenguaje (Angular, Go, Java, Python, TypeScript, Web) se han trasladado al almacén de habilidades lazy-loaded:

- `skills/typescript-patterns/SKILL.md`: Tipos, interfaces, estrechamiento de `unknown` y prohibición de `any`.
- `skills/angular-developer/`: Componentes standalone, Signals, OnPush y control flow.
- `skills/golang-patterns/`: Concurrencia, interfaces y gestión de errores idiomáticos.
- `skills/java-coding-standards/`: Registros, inmutabilidad y Spring Boot.
- `skills/python-patterns/`: PEP 8, anotaciones de tipo y dataclasses congeladas.
- `skills/frontend-patterns/`: Composición, rendimiento y accesibilidad web.

---

## 4. Deduplicación de `AGENTS.md`

Para evitar que Antigravity cargue dos veces el contenido completo de `AGENTS.md` (una como regla global del plugin `~/.gemini/config/plugins/aagy` y otra como regla local del repositorio), el archivo en la raíz del repositorio actúa como un puntero de referencia:

- Conserva el marcador `<!-- GEMINI CONTEXT CACHING: STATIC PREFIX INVARIANT -->`.
- Define las cabeceras canónicas `## 1. Core Engineering Invariants` y `## 2. Dynamic Task Lifecycle`.
- Reduce el consumo de tokens en turnos de desarrollo dentro de `aagy` en más de 5.500 tokens.

---

## Topes de tokens comprobados en CI (#107)

| Tope | Valor | Dónde se comprueba |
| :--- | :--- | :--- |
| Índice de reglas que inyecta `SessionStart` (aagy-ecc) | ≤ 2 KB | `test_token_caps.py` |
| `description` de skills, agentes y comandos (los dos plugins) | ≤ 200 caracteres | `optimize_catalog_tokens.py --check` y `workspace_audit.py` |
| Mensaje de un hook (`hook_safety.py`) | una línea, ≤ 160 caracteres | `test_token_caps.py`; el detalle con `--verbose` o `AAGY_HOOK_VERBOSE=1` |

- La plantilla `CLAUDE.md` del consumidor (`aagy-ecc/project-template/`) solo importa el `AGENTS.md`
  propio del proyecto: las reglas globales llegan una vez, por `SessionStart`.
- Perfil por defecto `minimal` (`generic`): `install.ps1` / `install.sh` instalan solo el núcleo. Los
  perfiles de stack se instalan bajo demanda (`aagy-sync <perfil>`; en Claude Code, `aagy-ecc-<perfil>`).
