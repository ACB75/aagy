# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `refactor/aagy/token-opt-and-scripts-reorg` (`Tarea 0.1`)  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Principal Agentic Runtime & Token Budget Optimizer`  
> **Estado**: `APROBADO`

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**:
  1. El plugin y el repositorio duplican innecesariamente `AGENTS.md` (21.4 KB, ~5.600 tokens cargados doblemente cuando se opera en el espacio de trabajo de la herramienta).
  2. La carpeta `rules/` contiene 37 guías de lenguaje/stack (`rules/angular/`, `rules/golang/`, `rules/java/`, `rules/python/`, `rules/typescript/`, `rules/web/`, `rules/common/`) que deberían ser skills cargadas bajo demanda (*lazy-loaded*) en lugar de reglas agregadas estáticas.
  3. Existen artefactos huérfanos/redundantes como el directorio raíz legacy `commands/` (97 archivos ya migrados y respaldados en el subplugin `ecc/commands/` para Claude Code).
  4. Los scripts de automatización se encontraban dispersos entre `scripts/ecc-agy/` y `scripts/bin/ecc-agy/`, requiriendo una reestructuración canónica por entorno de ejecución (`scripts/py/` con `/tests`, `scripts/pwsh/` con `/tests`, `scripts/sh/` con `/tests`).
- **Objetivo Principal**:
  1. Eliminar la duplicación entre `rules/AGENTS.md` y `<repo>/AGENTS.md`, manteniendo `rules/AGENTS.md` como la fuente canónica de verdad del plugin y un puntero conciso en el root.
  2. Dejar en `rules/` estrictamente `AGENTS.md` + `pr-automerge-lifecycle.md`, migrando las 37 guías a skills lazy-loaded (unificando stack TypeScript y complementando Frontend).
  3. Purgar comandos y artefactos muertos del root de `aagy`, manteniendo paridad e integridad en `ecc/commands/`.
  4. Reorganizar `scripts/` en `scripts/py/`, `scripts/pwsh/` y `scripts/sh/`, cada una con su suite de pruebas dedicada en `tests/`, garantizando retrocompatibilidad transparente (cero enlaces o invocaciones rotas).
- **Alcance (`In-Scope`)**:
  - Deduplicación de `AGENTS.md` y sincronización con el plugin instalado `~/.gemini/config/plugins/aagy`.
  - Reubicación/migración de reglas de stack a skills lazy-loaded (`skills/typescript-patterns/`, etc.).
  - Purgado de `commands/` huérfano en la raíz de `aagy`.
  - Reestructuración de `scripts/` en `py/`, `pwsh/`, `sh/` y creación de suites de tests en cada carpeta.
  - Actualización de invocaciones canónicas en `hooks.json`, skills, `complete-task-pr.ps1`, `complete-task-pr.sh` y wrappers de retrocompatibilidad.
  - Ejecución de suites completas con código de salida `0` y cobertura $\ge 80\%$.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Modificación de la estructura de `/doc` v2 (pertenece a la `Tarea 0.2`).
  - Cambios en el motor de autodescubrimiento / instintos (pertenece a la `Tarea 0.3`).

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Deduplicación de `AGENTS.md`)**: El archivo `rules/AGENTS.md` se consolida como la regla maestra del plugin; el `AGENTS.md` de la raíz del repositorio se simplifica a un puntero estático con marcadores invariantes de context-caching, reduciendo el consumo de tokens en turnos de trabajo dentro de `aagy`.
- **`RF-02` (Poda y Migración de `rules/` a Skills Lazy-Loaded)**: La carpeta `rules/` contendrá exclusivamente `rules/AGENTS.md` y `rules/pr-automerge-lifecycle.md`. Las 37 reglas de lenguaje/stack se unifican en skills existentes y nuevas (`skills/typescript-patterns/SKILL.md`).
- **`RF-03` (Purga de Artefactos Muertos en la Raíz)**: La carpeta obsoleta `commands/` (97 archivos) se retira de la raíz de `aagy`, confirmando que el subplugin `ecc/commands/` mantiene la colección completa para Claude Code.
- **`RF-04` (Reestructuración de Scripts por Runtime)**:
  - `scripts/py/`: Scripts Python operativos (`workspace_audit.py`, `sonar_audit.py`, etc.) y subdirectorio `scripts/py/tests/`.
  - `scripts/pwsh/`: Scripts PowerShell 7 (`complete-task-pr.ps1`, `audit-workspace.ps1`, etc.) y subdirectorio `scripts/pwsh/tests/`.
  - `scripts/sh/`: Scripts POSIX Bash (`complete-task-pr.sh`, `audit-workspace.sh`, etc.) y subdirectorio `scripts/sh/tests/`.
- **`RF-05` (Wrappers de Retrocompatibilidad)**: Se mantienen wrappers de redirección en `scripts/bin/ecc-agy/` y `scripts/ecc-agy/` para garantizar que herramientas o hooks externos existentes no fallen.
- **`RF-06` (Actualización de Hooks y Canónicos)**: Se actualizan `hooks.json`, `install.ps1`, `ecc-agy-sync.ps1`, `ecc-agy-sync.sh` y skills para apuntar a las nuevas rutas canónicas.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [ ] **`CA-01`**: Dado el directorio `rules/`, cuando se audite su contenido, entonces únicamente contendrá `AGENTS.md` y `pr-automerge-lifecycle.md`, con tamaño total inferior al presupuesto de 16.000 tokens.
- [ ] **`CA-02`**: Dado el archivo `AGENTS.md` en la raíz de `aagy`, cuando se lea en el inicio de turno, entonces ocupará $< 1.000$ caracteres conservando los marcadores de context caching y redirigiendo a `rules/AGENTS.md`.
- [ ] **`CA-03`**: Dado el árbol de `scripts/`, cuando se verifiquen `scripts/py/tests/`, `scripts/pwsh/tests/` y `scripts/sh/tests/`, entonces cada runtime contará con su subdirectorio de pruebas pasando al 100%.
- [ ] **`CA-04`**: Dado el archivo `hooks.json`, cuando Antigravity intercepte llamadas a herramientas, entonces los comandos invocarán scripts existentes en `scripts/pwsh/` sin generar errores de ruta.
- [ ] **`CA-05`**: Cuando se ejecute `workspace_audit.py` y `sonar_audit.py`, entonces ambos reportarán `0` violaciones de higiene, `0` violaciones de presupuesto y SonarQube Rating A.
- [ ] **`CA-06`**: Cuando se ejecute `pytest`, entonces todas las suites pasarán con código de salida `0` y cobertura $\ge 80\%$.

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Componente | Impacto | Medida de Mitigación / Retrocompatibilidad |
| :--- | :--- | :--- |
| **Harness Antigravity (`aagy`)** | Reducción de ~5.500 tokens por turno al evitar cargar `AGENTS.md` por duplicado. | Puntero invariante de caché estática en root `AGENTS.md`. |
| **Plugin Rules Budget** | Reducción de 39 archivos en `rules/` a 2 archivos. | Migración a `skills/` lazy-loaded de bajo coste. |
| **Rutas de Scripts (`scripts/bin/ecc-agy`)** | Reorganización en `scripts/{py,pwsh,sh}`. | Creación de wrappers proxy en rutas históricas para evitar rupturas. |
| **Calidad y SonarQube** | Mantenimiento de Rating A y cobertura de pruebas. | Suites en `scripts/py/tests/`, `scripts/pwsh/tests/` y `scripts/sh/tests/`. |

---

## 4. Plan de Rollback Inmediato (< 2 Minutos)

- **Comando Git**: `git checkout main && git branch -D refactor/aagy/token-opt-and-scripts-reorg`.
- **Restauración de Plugin**: En caso de anomalía, ejecutar `pwsh -File install.ps1 -Target agy -Profile minimal` para restablecer el plugin global.
