# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | ECC ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Analiza las dependencias entre tareas y resuélvelas en el orden secuencial óptimo (gobernanza/harness → tokens/contexto → guardrails de calidad → automatización de git/PRs).
> 2. **Flujo Git Automatizado:** Genera ramas atómicas por tarea, resuelve conflictos de forma contextual, ejecuta tests unitarios/e2e y realiza `auto-merge` continuo en la rama principal hasta agotar el presupuesto de tokens asignado.
> 3. **Tarea Final Obligatoria (Higiene y Meta-Herramientas):** Al completar el backlog funcional, ejecuta una fase final de limpieza: purgar dependencias huérfanas, eliminar código muerto, actualizar documentación técnica y desplegar el motor de autodescubrimiento para sintetizar `skills`, `rules`, `agents` y `git hooks` optimizados para los flujos repetitivos del repositorio.

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

### Tarea 3.4: CLI de Promoción On-Demand de Skills Tier-2 $\leftrightarrow$ Tier-1 (`enable-skill.ps1` / `disable-skill.ps1`)

- [ ] **Implementar utilidades CLI para activar y desactivar dinámicamente skills especializadas de Tier 2 en el plugin activo**
  - **01 - ROLE:** Modular Plugin Architect & CLI Ergonomics Engineer.
  - **02 - CONTEXT:** `[Sector: AI Agent Plugin Management]` `[Data Type: PowerShell & Bash scripts, directory synchronization]` `[Objective: Proporcionar un comando rápido y seguro que permita al desarrollador promover temporalmente una skill de Tier 2 (ej. chrome-devtools, generative_ui, a11y-debugging) a la carpeta activa del plugin (~/.gemini/config/plugins/ecc-agy/skills/) para una tarea concreta, y retirarla al finalizar]` `[Restrictions: No comprometer archivos temporales en el repositorio Git; validar límites <= 140c de frontmatter en la skill promovida]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Contamos con 170 skills en el repositorio pero solo 22 en el plugin activo para mantener el presupuesto siempre activo en ~945 tokens.
    - Cuando surge una tarea puntual que requiere una skill especializada (ej. depuración de memoria o UI generativa), el desarrollador debe copiar la carpeta manualmente o recargar el plugin completo.
  - **04 - PHASE 2 (STRATEGY):**
    - `enable-skill.ps1 -Name <skill>` valida que la skill exista en `skills/`, comprueba su frontmatter y la copia a la carpeta de plugin activo, registrándola en `.active_promotions.json`.
    - `disable-skill.ps1 -Name <skill>` elimina la copia del plugin activo y restaura el estado limpio.
  - **05 - PHASE 3 (EXECUTION):**
    1. Implementar `scripts/bin/ecc-agy/enable-skill.ps1` y `.sh`.
    2. Implementar `scripts/bin/ecc-agy/disable-skill.ps1` y `.sh`.
    3. Añadir validación estricta de frontmatter y comprobación de presupuesto con `workspace_audit.py`.
    4. Crear batería de tests unitarios en `test_skill_promotion.py`.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Evitar que la promoción de una skill sobrescriba accidentalmente una skill core de Tier 1 o que quede huérfana tras un crash de la sesión.
  - **07 - PHASE 5 (FORMAT):**
    - Scripts documentados, con validación de parámetros y mensajes estructurados.
  - **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.100 tokens).
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

### Tarea 3.5: Reubicación y Estandarización de Plantillas Documentales (`TEMPLATE_ADR.md` y `TEMPLATE_POSTMORTEM.md`)

- [ ] **Mover `doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` a `doc/adr/TEMPLATE_ADR.md` y renombrar `doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md` a `doc/post-mortem/TEMPLATE_POSTMORTEM.md`**
  - **01 - ROLE:** Documentation Governance Architect & Repository Hygiene Specialist.
  - **02 - CONTEXT:** `[Sector: Documentation Spine & Governance]` `[Data Type: Markdown templates, .governance/docs-map.json, scripts/skills references]` `[Objective: Mover doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md a doc/adr/TEMPLATE_ADR.md y renombrar doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md a doc/post-mortem/TEMPLATE_POSTMORTEM.md manteniendo cero enlaces rotos]` `[Restrictions: Actualizar todas las referencias en scripts, skills, reglas, INDEX.md y docs-map.json; verificar con audit-workspace.ps1 y lint-markdown.ps1]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Actualmente las plantillas de ADR/Requisitos y Post-Mortem tienen nombres y ubicaciones inconsistentes (`doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md` suelto en `doc/` y `TEMPLATE_POSTMORTEM_5W.md` en `doc/post-mortem/`).
    - Mover o renombrar archivos sin actualizar referencias rompe `.governance/docs-map.json`, scripts de automatización y enlaces Markdown.
  - **04 - PHASE 2 (STRATEGY):**
    - Localizar todas las referencias con búsqueda global (`Select-String` / `git grep`) antes de mover/renombrar usando `git mv`.
    - Actualizar referencias en scripts, skills, `doc/INDEX.md` y `.governance/docs-map.json`.
  - **05 - PHASE 3 (EXECUTION):**
    1. Ejecutar `git mv doc/TEMPLATE_REQUISITOS_ARQUITECTURA.md doc/adr/TEMPLATE_ADR.md` y `git mv doc/post-mortem/TEMPLATE_POSTMORTEM_5W.md doc/post-mortem/TEMPLATE_POSTMORTEM.md`.
    2. Actualizar todas las referencias detectadas en `scripts/`, `skills/`, `doc/` y `.governance/docs-map.json`.
    3. Validar con `lint-markdown.ps1`, `audit-workspace.ps1` y `pytest` (exit code `0`).
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Verificar que ningún test unitario ni skill (`architecture-decision-records`, `todo-lifecycle`, `lifecycle-coordinator`) apunte a los nombres anteriores.
  - **07 - PHASE 5 (FORMAT):**
    - Rutas renombradas con `git mv`, cero enlaces rotos y auditoría completa en verde.
  - **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~800 tokens).
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

---

## 4. Prioridad 4: Optimizaciones Específicas de Home-Lab (Microservicios, SDK y Resiliencia LTS)

### Tarea 4.1: Linter Automático de Paridad de Contratos `home-lab-sdk` (`audit-sdk-parity.py` / `.ps1`)

- [ ] **Desarrollar linter de paridad estática de contratos entre microservicios (`services/`, `cluster/`) y `home-lab-sdk`**
  - **01 - ROLE:** Distributed Systems Contract Architect & Polyglot SDK Engineer.
  - **02 - CONTEXT:** `[Sector: Microservices Contract Parity & Type Safety]` `[Data Type: Go structs/routes (Gin/chi/mux), TypeScript interfaces, Python models]` `[Objective: Implementar un validador estático automatizado que inspeccione las rutas y modelos expuestos por los microservicios y certifique que el SDK cliente polyglot (Go/TS/Python) contiene los métodos y tipos correspondientes, bloqueando PRs con divergencia]` `[Restrictions: Sin dependencias pesadas de terceros; análisis determinista con Python stdlib (ast, regex)]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - La regla "Mandatory Microservice & SDK Contract Parity" es un pilar crítico para evitar errores 404/400 en tiempo de ejecución entre microservicios.
    - Actualmente la sincronización depende de la disciplina del desarrollador. Si se añade un endpoint en Go sin actualizar el cliente en TypeScript de `home-lab-sdk`, la compilación local no siempre falla hasta las pruebas E2E.
  - **04 - PHASE 2 (STRATEGY):**
    - Parser estático en Python que extraiga endpoints declarados en controladores Go (`r.GET(...)`, `r.POST(...)`) y los contraste contra los métodos cliente en `home-lab-sdk/`.
    - Reporte de diferencias: endpoints sin cliente, modelos con campos desalineados.
  - **05 - PHASE 3 (EXECUTION):**
    1. Desarrollar `scripts/ecc-agy/audit_sdk_parity.py` y wrapper `scripts/bin/ecc-agy/audit-sdk-parity.ps1`.
    2. Integrar el chequeo como paso de validación en la Fase 4 del lifecycle (`04_PROPUESTA_COMMITS_PR.md` y `complete-task-pr.ps1`).
    3. Crear suite de tests `scripts/ecc-agy/tests/test_audit_sdk_parity.py` simulando contratos sincronizados y desincronizados.
    4. Ejecutar verificación y documentar en `doc/manual/`.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Excluir del escaneo rutas internas no públicas como `/metrics`, `/health`, `/livez`, `/readyz` y endpoints de depuración.
  - **07 - PHASE 5 (FORMAT):**
    - Script Python tipado con salida JSON/tabular y código de salida `0` (aprobado) o `1` (divergencia).
  - **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~8.000 tokens) para el diseño del AST y análisis de contratos; **Carbon ($C_6$)** para la implementación del parser y tests.
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

### Tarea 4.2: Analizador Estático de Bloqueos DDL y Concurrencia en PostgreSQL LTS (`audit-pg-locks.py` / `.ps1`)

- [ ] **Construir analizador estático de migraciones SQL para prevención de bloqueos `ACCESS EXCLUSIVE` en PostgreSQL LTS**
  - **01 - ROLE:** Principal Database Reliability Engineer (DBRE) & PostgreSQL Internalist.
  - **02 - CONTEXT:** `[Sector: Multi-Tenant Database Infrastructure]` `[Data Type: SQL migration files (*.sql), PostgreSQL DDL syntax]` `[Objective: Desarrollar un analizador estático que escanee scripts de migración SQL buscando operaciones que tomen bloqueos ACCESS EXCLUSIVE prolongados o causen reescrituras de tabla, bloqueando despliegues que pongan en riesgo la disponibilidad de la base de datos central multitenant]` `[Restrictions: Python stdlib, tiempo de ejecución < 500ms, aplicable en Fase 1 y Fase 4 del lifecycle]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Home-Lab consolida todos los microservicios en una instancia única y endurecida de PostgreSQL LTS.
    - Ciertas operaciones DDL (ej. `ALTER TABLE t ADD COLUMN c int NOT NULL DEFAULT now()`, `CREATE INDEX` sin `CONCURRENTLY`, cambios de tipo de columna incompatibles) adquieren bloqueos `ACCESS EXCLUSIVE` que congelan todas las lecturas y escrituras, provocando agotamiento del pool de conexiones en los microservicios.
  - **04 - PHASE 2 (STRATEGY):**
    - Clasificar las sentencias DDL en 3 categorías de riesgo:
      - *Verde*: Operaciones concurrentes o metadata-only (ej. añadir columna nullable, `CREATE INDEX CONCURRENTLY`).
      - *Amarillo*: Bloqueos compartidos breves.
      - *Rojo*: `ACCESS EXCLUSIVE` o reescritura de tabla completa.
    - Para sentencias en *Rojo*, sugerir la alternativa segura sin bloqueo (estrategia dual-write o adición en 3 pasos).
  - **05 - PHASE 3 (EXECUTION):**
    1. Programar `scripts/ecc-agy/audit_pg_locks.py` y `audit-pg-locks.ps1`.
    2. Crear reglas de detección léxica para sentencias DDL bloqueantes de PostgreSQL.
    3. Añadir suite de tests `test_audit_pg_locks.py` con fixtures de migraciones seguras y peligrosas.
    4. Integrar en `complete-task-pr.ps1` cuando se detecten archivos `.sql` modificados.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Distinguir entre versiones de PostgreSQL: en PG 11+ añadir columna con default constante no reescribe la tabla, pero expresiones volátiles (ej. `random()`, funciones PL/pgSQL) sí lo hacen.
  - **07 - PHASE 5 (FORMAT):**
    - Script CLI con reporte estructurado de riesgos y remediaciones sugeridas.
  - **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~10.000 tokens) para el modelado de concurrencia y catálogo de bloqueos; **Carbon ($C_6$)** para el parser.
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

### Tarea 4.3: Validador de Rutas Traefik, Split-DNS (CoreDNS) y Catálogo `/portal`

- [ ] **Desarrollar validador de congruencia de Ingress único, Split-DNS y catálogo de servicios `/portal`**
  - **01 - ROLE:** Edge Ingress & Network Infrastructure Architect.
  - **02 - CONTEXT:** `[Sector: Home-Lab Networking & Service Mesh]` `[Data Type: docker-compose.yml (traefik labels), Corefile / zone files, Go source (main.go)]` `[Objective: Implementar un script de validación que certifique que cualquier servicio HTTP definido en docker-compose tenga configuradas sus etiquetas Traefik (router, service, middleware TLS), su registro DNS coincidente en CoreDNS y su entrada en el catálogo /portal]` `[Restrictions: Python stdlib / PowerShell, sin requerir daemon Docker corriendo en modo estático]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - El Pilar 2 de Google Engineering ("Single Ingress & Unified TLS") y la regla 7 de `GEMINI.md` requieren que los microservicios no expongan puertos crudos y que el catálogo `/portal` se mantenga sincronizado.
    - La configuración manual de etiquetas Traefik y registros DNS puede sufrir desalineaciones sutiles (ej. un subdominio mal escrito en un router).
  - **04 - PHASE 2 (STRATEGY):**
    - Parser estático que cruce:
      1. Servicios en `docker-compose*.yml` con etiquetas `traefik.http.routers.*.rule=Host(...)`.
      2. Registros en los archivos de zona de CoreDNS.
      3. Entradas del mapa `/portal` en `cluster/cmd/server/main.go`.
  - **05 - PHASE 3 (EXECUTION):**
    1. Desarrollar `scripts/ecc-agy/validate_ingress_routes.py` y `validate-ingress-routes.ps1`.
    2. Añadir opción `-Audit` y `-Fix` para sugerir las líneas faltantes en `/portal` o DNS.
    3. Crear tests unitarios en `test_validate_ingress_routes.py`.
    4. Documentar en `doc/manual/`.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Soportar servicios internos deliberadamente aislados (ej. PostgreSQL, Redis, exportadores de métricas) que no deben tener entrada Ingress.
  - **07 - PHASE 5 (FORMAT):**
    - Script CLI con validación determinista y reporte estructurado de congruencia.
  - **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.200 tokens).
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

### Tarea 4.4: Automatización de Pipeline de Despliegue Docker Compose por Tag en `git-flow-helper.ps1`

- [ ] **Extender `git-flow-helper.ps1` para despliegue automatizado por etiquetas de promoción (`vX.Y.Z-sandbox` y `vX.Y.Z`)**
  - **01 - ROLE:** Release Automation & Multi-Tier Deployment Engineer.
  - **02 - CONTEXT:** `[Sector: Continuous Delivery & Infrastructure Automation]` `[Data Type: PowerShell git-flow-helper.ps1, SSH / Docker Compose commands]` `[Objective: Integrar en la acción 'promote' de git-flow-helper.ps1 la capacidad opcional (-Deploy) de conectarse al host de Home-Lab mediante SSH o localmente, ejecutar el pull de imágenes o checkout del tag, levantar los contenedores y verificar los healthchecks automáticos con rollback en < 2 minutos si fallan]` `[Restrictions: No interrumpir servicios no afectados; rollback garantizado ante cualquier código de salida no-cero]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Actualmente `git-flow-helper.ps1 -Action promote` crea el tag semántico anotado y lo sube a GitHub, pero el despliegue físico en el servidor de destino requiere pasos manuales por SSH.
    - Se busca cerrar el ciclo Trunk-Based para que la promoción ejecute el despliegue y valide las sondas de salud de forma unificada.
  - **04 - PHASE 2 (STRATEGY):**
    - Añadir parámetro `-Deploy` y `-Environment [sandbox|live]`.
    - Secuencia de despliegue: Backup de estado -> Pull/Recreate contenedores -> Liveness probes (3 intentos x 5s) -> Si OK: Confirmar tag; Si FAIL: Ejecutar rollback automático al tag anterior.
  - **05 - PHASE 3 (EXECUTION):**
    1. Actualizar `scripts/bin/ecc-agy/git-flow-helper.ps1` con la lógica de despliegue y sondas de salud.
    2. Añadir modo `-DryRun` para simular la secuencia sin impactar contenedores reales.
    3. Incorporar tests en `test_git_flow_helper.py` o suite de integración.
    4. Actualizar ADR-0006 con el flujo automatizado de promoción y despliegue.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Evitar fallos de red durante el despliegue; asegurar que los secretos (`.env`) nunca se expongan en logs del pipeline.
  - **07 - PHASE 5 (FORMAT):**
    - Script PowerShell endurecido con manejo de errores estricto (`Set-StrictMode`, `$ErrorActionPreference = 'Stop'`).
  - **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens) para el protocolo de resiliencia y rollback; **Carbon ($C_6$)** para la implementación en PowerShell.
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

---

## 5. Prioridad 5: Cierre Maestro — Rebranding y Migración de `/ecc` a `/aagy` (`Anything Antigravity`)

### Tarea 5.1: Migración de `/ecc` a `/aagy` (*Anything Antigravity*) y Sincronización del Plugin `ecc`

- [ ] **Ejecutar el cierre maestro del backlog: migrar `/ecc` a `/aagy` (*Anything Antigravity*) conservando el historial Git, aplicando *full rename* a `aagy` y sincronizando el plugin `ecc` para Claude Code en `aagy/ecc/`**
  - **01 - ROLE:** Principal Release & Repository Migration Architect (experto en rebranding estructural de monorepos, migración segura de git remotes/workspaces y publicación de plugins multiagente).
  - **02 - CONTEXT:** `[Sector: Repository Lifecycle & Brand Migration]` `[Data Type: Git repo /ecc -> /aagy (preservando historial), plugin aagy + plugin Claude Code aagy/ecc/ sincronizado]` `[Objective: Migrar el repositorio actual /ecc a /aagy ("Anything Antigravity") conservando el historial Git, renombrando el remoto en GitHub (gh repo rename aagy), aplicando full rename a aagy (incluido ~/.gemini/config/plugins/aagy) y manteniendo dentro de aagy/ecc/ el plugin para Claude Code llamado ecc siempre sincronizado con aagy para paridad multiagente]` `[Restrictions: Ejecutar EXCLUSIVAMENTE como última tarea del TODO.md tras completar y verificar todas las prioridades anteriores; conservar el historial Git completo; NO regenerar ni purgar la documentación en esta tarea (se ajustará a posteriori); prohibido ejecutar rm/delete destructivo sin verificación previa en /aagy y confirmación explícita del usuario; mantener 0 enlaces rotos y 100% cumplimiento de budget hard gate + paridad aagy<->ecc]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - El directorio/nombre raíz `/ecc` ya no refleja la identidad nativa de *Anything Antigravity* (`/aagy`), y es necesario unificar el ecosistema manteniendo el plugin de Claude Code (`ecc`) sincronizado dentro de `aagy/ecc/`.
    - La documentación se actualizará a posteriori, por lo que esta tarea se centra exclusivamente en la migración limpia de repositorio, remoto, plugin instalado y paridad `aagy` $\leftrightarrow$ `ecc` sin duplicar trabajo documental.
  - **04 - PHASE 2 (STRATEGY):**
    - *Enfoque A (In-Place Rename)*: Renombrar carpeta y editar archivos en sitio, arriesgando romper rutas activas antes de validar.
    - *Enfoque B (History-Preserving Cutover & Dual-Plugin Parity - Recomendado)*:
      1. Verificar que todas las tareas previas (`2.3` a `4.4`) estén archivadas en `TODO_DONE/` y en verde (`audit-workspace.ps1` + `pytest`).
      2. Migrar `c:\Workspace\projects\ecc` hacia `c:\Workspace\projects\aagy` (*Anything Antigravity*) **conservando el historial Git completo** y renombrar el remoto (`gh repo rename aagy`), aplicando *full rename* a `aagy` (`plugin.json`, `package.json`, rutas y `~/.gemini/config/plugins/aagy`).
      3. Estructurar y sincronizar dentro de `aagy/ecc/` el plugin para Claude Code llamado **`ecc`** (con chequeo de paridad automatizado `aagy` $\leftrightarrow$ `ecc` para operar de forma idéntica en multiagentes).
      4. Validar integridad completa en `/aagy` (`pytest`, `audit-workspace.ps1`, `lint-markdown.ps1`, smoke-test de ambos plugins) y, solo tras confirmación explícita del usuario, eliminar el antiguo directorio `/ecc`.
  - **05 - PHASE 3 (EXECUTION):**
    1. Gate previo: confirmar backlog previo (`2.3`–`4.4`) completado al 100%.
    2. Crear `/aagy` preservando el historial Git (`git log` íntegro), renombrar remoto en GitHub (`gh repo rename aagy`) y ejecutar *full rename* de identidad a `aagy` / *Anything Antigravity*.
    3. Consolidar dentro de `aagy/ecc/` el plugin de Claude Code **`ecc`** y su mecanismo/script de sincronización y paridad continua con `aagy`.
    4. Validar `pytest`, `audit-workspace.ps1` y `lint-markdown.ps1` con código de salida `0`.
    5. Actualizar el plugin instalado a `~/.gemini/config/plugins/aagy`, obtener confirmación final del usuario y retirar `/ecc`.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Riesgo crítico de pérdida irreversible si se borra `/ecc` antes de validar el 100% de tests, git remote y enlaces en `home-lab` o `~/.gemini/`. Mitigación: cutover en dos pasos con verificación integral en `/aagy` y confirmación explícita antes de borrar `/ecc`.
  - **07 - PHASE 5 (FORMAT):**
    - Repositorio `/aagy` operativo con historial íntegro, remoto renombrado, `aagy/ecc/` sincronizado, tests y `audit-workspace.ps1` en verde (exit `0`).
  - **MODELO & AGENTE ASIGNADO:** **Argon ($Ar_{18}$) / Gemini 3.8 Pro Thinking** (~6.000 tokens) para la auditoría de cutover y paridad; **Carbon ($C_6$)** para *full rename* y validación.
  - **COMPACT TRIGGER:** Al completar el cutover final en `/aagy`.

---

## 6. Gobernanza de Modelos, Tokens y Política de Auto-Compact

### 6.1. Matriz de Asignación de Modelos por Tarea (Token Optimization)

| Tarea | Agente Elemental | Modelo Gemini 3.8 | Presupuesto Tokens / Turno | Justificación de Eficiencia |
| :--- | :--- | :--- | :--- | :--- |
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
