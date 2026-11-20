# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `chore/aagy/clean-docs-and-repo-migration` (`Tarea 5.1`)  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Principal Release & Repository Migration Architect`  
> **Estado**: `APROBADO`

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**: El repositorio actual `c:\Workspace\projects\ecc` arrastra documentación histórica fragmentada (múltiples planes, estados intermedios, referencias mixtas a `ecc` y `ecc-claude`) y mantiene el nombre de directorio/repositorio `/ecc`, el cual ya no representa la identidad nativa de **Anything Antigravity (`/aagy`)**.
- **Objetivo Principal**: Ejecutar como **última tarea atómica del `TODO.md`** (tras completar las Prioridades 2, 3 y 4) la purga y regeneración limpia de toda la documentación junto con la creación del repositorio limpio `/aagy` (*Anything Antigravity*) y la retirada segura de `/ecc`.
- **Alcance (`In-Scope`)**:
  - Gate previo de completitud del backlog (`Tareas 2.3` a `4.4` completadas y verificadas).
  - Migración del repositorio hacia `c:\Workspace\projects\aagy` (*Anything Antigravity*) **conservando el historial Git completo** y aplicando *full rename* a `aagy` (`plugin.json`, `package.json`, `AGENTS.md`, scripts, tests e identificador `~/.gemini/config/plugins/aagy`).
  - Mantenimiento y sincronización continua del **plugin de Claude Code llamado `ecc`** dentro de `/aagy`, garantizando paridad funcional y de capacidades multiagente entre `aagy` (Antigravity) y `ecc` (Claude Code).
  - Eliminación de toda la documentación heredada y generación desde cero de la espina documental limpia en `aagy/doc/` (`INDEX.md`, `STATUS.md`, `LOG.md`, `TODO.md`, `adr/`, `manual/`, `diagrams/`, `.governance/docs-map.json`) y `aagy/README.md`.
  - Validación integral (`pytest`, `audit-workspace.ps1`, `lint-markdown.ps1`, presupuesto de tokens `rules` y `customizations`, paridad `aagy` $\leftrightarrow$ `ecc`) y retirada controlada de `/ecc` tras confirmación explícita del usuario.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Ejecutar la migración antes de completar las `Tareas 2.3` a `4.4`.
  - Modificar la lógica funcional de los microservicios de `home-lab` (salvo actualizar rutas o referencias al plugin si fuera necesario).
  - Borrar `/ecc` sin verificación previa al 100% en `/aagy` ni sin confirmación explícita del usuario.

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Orden de Ejecución Estricto)**: `Tarea 5.1` actúa como cierre maestro del backlog; no debe ejecutarse hasta que todas las tareas previas (`2.3`, `3.1`–`3.4`, `4.1`–`4.4`) estén archivadas en `TODO_DONE/` y fusionadas en `main`.
- **`RF-02` (Regeneración Documental Limpia)**: Toda la documentación previa obsoleta, borradores de planes históricos (`doc/plan/`), historiales redundantes y referencias desactualizadas deben ser descartados en la rama de cierre, generando una documentación nueva, minimalista, veraz y 100% sincronizada con el código real de `/aagy` y su plugin hermano `ecc`.
- **`RF-03` (Full Rename `/ecc` $\rightarrow$ `/aagy` Conservando Historial Git y Remoto)**: El repositorio `c:\Workspace\projects\aagy` (*Anything Antigravity*) debe **conservar el historial Git completo** (`git log` íntegro), renombrar el remoto en GitHub (`gh repo rename aagy`) para preservar issues/PRs, y aplicar *full rename* a `aagy` (`plugin.json`, `package.json`, `AGENTS.md`, scripts, tests e identificador de plugin `~/.gemini/config/plugins/aagy`).
- **`RF-04` (Invariante de Presupuesto y Calidad)**: El repositorio `/aagy` debe superar con código de salida `0` el hard gate de presupuesto (`rules` $\le 24\text{ KB}$/archivo y $\le 20.000$ tokens agregados, `MAX_SKILL_DESC = 140`, `MAX_AGENT_DESC = 120`, MCPs pesados desactivados por defecto), `pytest`, `audit-workspace.ps1` y `lint-markdown.ps1`.
- **`RF-05` (Cutover en Dos Fases y Retirada Segura de `/ecc`)**: Primero se construye y valida completamente `/aagy`; únicamente tras confirmar que todas las pruebas, enlaces y los plugins (`aagy` + `ecc`) operan correctamente y contar con aprobación explícita del usuario, se elimina `/ecc`.
- **`RF-06` (Plugin `ecc` para Claude Code en `aagy/ecc/` Sincronizado)**: Dentro de `/aagy` existirá la subcarpeta dedicada **`aagy/ecc/`** para el plugin de Claude Code, sincronizada automáticamente desde los artefactos core de `aagy` (reglas, skills, agentes, hooks y verificación automatizada de paridad multiagente) para garantizar un comportamiento equivalente en ambos entornos.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [ ] **`CA-01`**: Dado el backlog `TODO.md` con las tareas `2.3`–`4.4` completadas, cuando se construya `c:\Workspace\projects\aagy`, entonces se conservará el historial Git íntegro y no existirá ningún archivo de documentación heredado ni enlaces rotos.
- [ ] **`CA-02`**: Dado el nuevo árbol `aagy/doc/`, cuando se ejecuten `lint-markdown.ps1` y `audit-workspace.ps1`, entonces ambos finalizarán con código de salida `0`, cero enlaces rotos en `.governance/docs-map.json` y cumplimiento estricto de presupuestos de tokens.
- [ ] **`CA-03`**: Dado el conjunto de suites en `aagy/scripts/ecc-agy/tests/` (o su ruta renombrada `aagy`), cuando se ejecute `pytest`, entonces el 100% de los tests pasarán con cobertura $\ge 80\%$ y código de salida `0`.
- [ ] **`CA-04`**: Dado el *full rename* a `aagy`, cuando se instale en `~/.gemini/config/plugins/aagy`, entonces Antigravity cargará las skills, agentes y hooks sin errores de manifiesto ni desbordamiento de presupuesto.
- [ ] **`CA-05`**: Antes de ejecutar cualquier borrado sobre `c:\Workspace\projects\ecc`, el sistema presentará el reporte de verificación completo de `/aagy` y esperará confirmación explícita del usuario.
- [ ] **`CA-06`**: Dado el plugin **`ecc`** para Claude Code dentro de `/aagy`, cuando se ejecute la validación de sincronización/paridad `aagy` $\leftrightarrow$ `ecc`, entonces ambos plugins compartirán capacidades equivalentes sin deriva de contratos ni skills huérfanas.

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | No modifica contratos de microservicios ni DTOs de `home-lab-sdk`. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin cambios en bases de datos ni DDL. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin cambios en Traefik, Apache ni rutas HTTP. |
| **Resolución Split-DNS** | `NO` | - | Sin cambios en CoreDNS ni hostnames `.home.lab`. |
| **Restricciones de Hardware** | `NO` | - | Mantiene footprint ligero y `rules`/`customizations` dentro del presupuesto de tokens. |
| **Variables `.env` / Rutas Plugin** | `SÍ` | `Medio` | Scripts o enlaces en `~/.gemini/config/plugins/` y `home-lab` que apunten a `/ecc` deben actualizarse a `/aagy`. Mitigación: búsqueda global previa (`rg`) y smoke-test del plugin. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

> **Invariante Canónico**: Queda terminantemente prohibido introducir cambios destructivos sin ruta de verificación y respaldo previa.

- **¿Introduce Breaking Changes?**: `[ ] NO (100% Retrocompatible) | [x] SÍ (Excepción Aprobada por Rebranding Explícito del Usuario)`
- **Justificación**: El usuario solicitó explícitamente eliminar la documentación histórica acumulada y reemplazar el repositorio `/ecc` por `/aagy` (*Anything Antigravity*) como tarea final de cierre.
- **Estrategia de Transición Segura**:
  - Construcción paralela no destructiva en `c:\Workspace\projects\aagy`.
  - Verificación completa (`pytest`, `audit-workspace.ps1`, `lint-markdown.ps1`, validación del plugin) antes de tocar `/ecc`.
  - Confirmación explícita del usuario previa a la eliminación física de `/ecc` y actualización de cualquier referencia en `~/.gemini/config/plugins/`.

---

## 5. Compuertas SRE de Rendimiento y Persistencia Segura

### 5.1. Rendimiento y Throttling de Recursos

- **Presupuesto de Contexto Antigravity**:
  - Archivos en `rules/`: $\le 24.000$ bytes por archivo y $\le 20.000$ tokens agregados (`defaultRulesBudget`).
  - `SKILL.md` description $\le 140$ caracteres; `agent` description $\le 120$ caracteres; MCPs pesados con `"disabled": true` por defecto.
- **Tiempo de Ejecución de Auditoría**: `audit-workspace.ps1` y `lint-markdown.ps1` deben completar en $< 10\text{ s}$ sobre el árbol limpio.

### 5.2. Persistencia Segura

- **No aplicable a PostgreSQL LTS**, pero se aplica **Seguridad de Cutover en Filesystem/Git**: prohibido ejecutar borrado irreversible de `/ecc` sin verificación de integridad en `/aagy` y respaldo/confirmación del usuario.

---

## 6. Threat Modeling y Bastionado de Seguridad

| Vector de Ataque / Amenaza | Riesgo (`Bajo/Medio/Alto/N/A`) | Mitigación y Bastionado Aplicado |
| :--- | :---: | :--- |
| **Pérdida irreversible de código/scripts** | `Alto` | Cutover en dos fases: construir y validar `/aagy` al 100% antes de solicitar confirmación para borrar `/ecc`. |
| **Referencias huérfanas o rutas rotas** | `Medio` | Búsqueda exhaustiva (`rg -n "ecc"`) tras la copia y validación de enlaces en `audit-workspace.ps1`. |
| **Desbordamiento de presupuesto de contexto** | `Medio` | Ejecución obligatoria del Hard Gate de `workspace_audit.py` sobre `/aagy` antes del cierre. |
| **Exposición de secretos / credenciales** | `Bajo` | No copiar archivos `.env`, tokens locales ni cachés temporales al nuevo repositorio `/aagy`. |
| **Inyección / comandos inseguros en hooks** | `Bajo` | Validación previa de `hooks.json` y scripts con AgentShield y `safety-guard`. |
