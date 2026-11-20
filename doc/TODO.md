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

### Tarea 2.2: Integración Zero-Overhead de `gemini-mcp` (`disabled: true`) y Skill `gemini-deep-ops`

- [ ] **Configurar perfil opcional `gemini-mcp` desactivado por defecto y skill bajo demanda para `ecc-agy` y `home-lab`**
  - **01 - ROLE:** Gemini Platform Architect & Developer Experience Engineer (experto en MCP, SDK oficial `google-genai` y flujos multimodales de bajo consumo de contexto).
  - **02 - CONTEXT:** `[Sector: Multimodal AI Tooling & Home-Lab Diagnostics]` `[Data Type: Plugin AGY (plugin.json, mcp_config.json), Skill Tier 2 (SKILL.md), Wrapper CLI Python/PowerShell]` `[Objective: Aprovechar las capacidades diferenciales de RLabs-Inc/gemini-mcp (Context Caching, Deep Research, análisis de PDFs/vídeos/logs, Structured JSON Output) en ecc-agy y home-lab con 0 tokens en reposo]` `[Restrictions: Jamás habilitar las 30+ tools MCP por defecto; cero secretos hardcoded (GEMINI_API_KEY vía entorno); sin dependencias de terceros no oficiales en scripts propios]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Antigravity ya ejecuta Gemini de forma nativa y dispone de `search_web`, `image-generator` y `gemini-api-docs`, por lo que activar `gemini-mcp` completo siempre duplica herramientas e infla el presupuesto.
    - Las capacidades realmente diferenciales para `ecc-agy` y `home-lab` son el análisis masivo de logs/PDFs/capturas para Post-Mortems 5W (`fix/*`), *Context Caching* y salida JSON estructurada.
  - **04 - PHASE 2 (STRATEGY):**
    - *Enfoque A (Plugin aislado `disabled: true`)*: Empaquetar `gemini-mcp` en un plugin independiente con `"disabled": true` en `plugin.json` para activación manual puntual.
    - *Enfoque B (Skill Tier 2 + CLI/SDK)*: Crear la skill `skills/gemini-deep-ops/SKILL.md` (`<= 140` chars, 0 tokens en Tier 1) que delega en un script ligero usando `google-genai` o el CLI `gcli`.
    - *Enfoque C (Combinado recomendado)*: Proveer la plantilla del plugin aislado (`disabled: true`) para sesiones interactivas puntuales y la skill `gemini-deep-ops` (sin MCP en prompt) para flujos reproducibles en `ecc` y `home-lab`.
  - **05 - PHASE 3 (EXECUTION):**
    1. Crear plantilla/instalador del plugin opcional `gemini-mcp` con `"disabled": true` y lectura de `GEMINI_API_KEY` por entorno.
    2. Crear `skills/gemini-deep-ops/SKILL.md` (`<= 140` chars en `description`) en Tier 2 y script de apoyo en `scripts/bin/ecc-agy/`.
    3. Documentar el flujo de diagnóstico multimodal para `doc/postmortem/` en `home-lab`.
    4. Validar con `workspace_audit.py` (confirmando 0 incremento en Tier 1 y 0 exceso de budget) y smoke-test del script.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Verificar que el plugin opcional no se active accidentalmente tras `ecc-agy-sync` y que nunca se filtre `GEMINI_API_KEY` en logs o commits.
  - **07 - PHASE 5 (FORMAT):**
    - Artefactos del plugin (`plugin.json`, `mcp_config.json`), `SKILL.md` validado por `markdownlint`, y smoke-test con exit code `0`.
  - **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.000 tokens). Creación de plantillas y CLI deterministicos.
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

### Tarea 2.3: Hooks Nativos (`hooks.json`), Auditoría AgentShield e Instintos AGY (`home-lab`)

- [ ] **Adoptar hooks deterministas, escaneo de seguridad del harness e instintos por proyecto desde `affaan-m/ECC`**
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

---

## 3. Prioridad 3: Optimizaciones Genéricas del Plugin (`ecc-agy`)

### Tarea 3.1: Alineación de Prompt Caching de Gemini 3.8 y Reordenamiento Estático de System Prompts

- [ ] **Reestructurar `AGENTS.md` y reglas globales para maximizar el hit-ratio del Gemini Context Caching**
  - **01 - ROLE:** Gemini LLM Systems Performance & Context Caching Architect.
  - **02 - CONTEXT:** `[Sector: LLM Runtime Optimization]` `[Data Type: Markdown rules (AGENTS.md, rules/AGENTS.md, .gemini/GEMINI.md)]` `[Objective: Reestructurar el contenido de AGENTS.md y reglas asociadas de manera que el prefijo del prompt permanezca 100% idéntico entre turnos y sesiones, permitiendo al compilador de contexto de Gemini 3.8 reutilizar los KV-caches y reducir la latencia TTFT en un 60%]` `[Restrictions: Preservar intactas todas las reglas de gobernanza, SRE y Trunk-Based]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Gemini 3.8 implementa *context caching* por coincidencia exacta de prefijo. Cualquier sección volátil colocada al inicio del prompt invalida toda la memoria de claves/valores posterior.
    - Las secciones dinámicas deben quedar delimitadas estrictamente al final del contexto del sistema.
  - **04 - PHASE 2 (STRATEGY):**
    - *Enfoque A*: Mantener un único archivo grande y reordenar manualmente sus secciones.
    - *Enfoque B (Recomendado)*: Dividir la estructura conceptual de reglas en dos bloques: Bloque Estático Invariable (Google 5-Pillar, SRE, Trunk-Based, Stack Standards) y Bloque Contextual / Per-Project Rules.
  - **05 - PHASE 3 (EXECUTION):**
    1. Auditar y reordenar `AGENTS.md` y `rules/AGENTS.md` asegurando que el bloque estático de alta densidad ocupe el prefijo continuo.
    2. Documentar la directiva de estabilidad de prefijos para desarrolladores en `doc/manual/`.
    3. Añadir test en `test_workspace_audit.py` que verifique la invariancia de prefijo de las reglas core.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Confirmar que el reordenamiento no altere la precedencia de evaluación de directivas en Antigravity ni confunda a los subagentes.
  - **07 - PHASE 5 (FORMAT):**
    - Reglas formateadas, markdownlint validado y exit code `0` en tests.
  - **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.000 tokens). Tarea de reordenamiento y formato.
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

### Tarea 3.2: Git Pre-Commit Hook Nativo y Scripts de Instalación (`install-git-hooks.ps1` / `.sh`)

- [ ] **Construir instalador e infraestructura de pre-commit hooks nativos para validación determinista de commits y markdown**
  - **01 - ROLE:** Git Operations Engineer & Developer Tooling Specialist.
  - **02 - CONTEXT:** `[Sector: Developer Infrastructure & Tooling]` `[Data Type: Git hooks (POSIX sh & pwsh), PowerShell y Bash]` `[Objective: Crear una utilidad de instalación de git hooks que intercepte 'git commit' localmente y ejecute format_commit.py --strict sobre el mensaje propuesto y lint-markdown.ps1 sobre los archivos staged, previniendo commits no conformes antes de subir a origin]` `[Restrictions: Tiempo de ejecución < 800ms; soporte nativo dual Windows 11 (pwsh) y Linux/WSL (bash)]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Actualmente la validación de formato depende de que el desarrollador invoque `format-commit.ps1` o de que la PR corra `audit-workspace.ps1`.
    - Si un desarrollador humano o agente emite un commit manual fuera del arnés, puede eludir la regla y romper la uniformidad del monorepo.
  - **04 - PHASE 2 (STRATEGY):**
    - Hook `commit-msg` para validar el título `[type]-[projects]: <title>` y el cuerpo explicativo.
    - Hook `pre-commit` para validar con markdownlint solo los archivos `.md` en el área de preparación (*staged*).
    - Scripts idempotentes de instalación en `scripts/bin/ecc-agy/install-git-hooks.ps1` y `.sh`.
  - **05 - PHASE 3 (EXECUTION):**
    1. Implementar scripts de hooks en `scripts/ecc-agy/hooks/` (POSIX sh para compatibilidad Git universal).
    2. Crear instalador `install-git-hooks.ps1` y `install-git-hooks.sh` que vincule o copie a `.git/hooks/`.
    3. Añadir soporte para bypass controlado en emergencias (`git commit --no-verify`).
    4. Crear test unitario en `test_scripts_bin.py` verificando la instalación y el comportamiento del hook.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Evitar que el hook tarde más de 1 segundo en validar, asegurando que solo revise los archivos staged (`git diff --cached --name-only`).
  - **07 - PHASE 5 (FORMAT):**
    - Scripts idempotentes, código limpio sin dependencias externas y tests pasando con exit code `0`.
  - **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.200 tokens).
  - **COMPACT TRIGGER:** Tras squash-automerge de PR en `main`.

### Tarea 3.3: Telemetría Proactiva de Presupuesto en Sesión y Política de Auto-Compact / Compact Estratégico

- [ ] **Desarrollar monitor de telemetría de tokens en sesión y sistema proactivo de alerta/ejecución de compactación**
  - **01 - ROLE:** Context Lifecycle Engineer & SRE Token Optimization Specialist.
  - **02 - CONTEXT:** `[Sector: AI Agent Lifecycle & Token Throttling]` `[Data Type: Python stdlib / PowerShell, Transcript JSONL reader]` `[Objective: Implementar una utilidad de diagnóstico y alerta que analice el transcript de la sesión activa, calcule el volumen acumulado de tokens y alerte cuando la sesión supere los 45.000 tokens recomendando o disparando /compact]` `[Restrictions: No interferir con la ejecución normal de comandos; tiempo de cómputo < 150ms]`.
  - **03 - PHASE 1 (ANALYSIS):**
    - Conforme la conversación avanza acumulando logs y difs de código, el coste por turno crece linealmente y la precisión de atención del modelo puede experimentar degradación en los detalles iniciales.
    - Se requiere un indicador objetivo en el entorno que informe cuándo es el momento óptimo para compactar.
  - **04 - PHASE 2 (STRATEGY):**
    - Crear `scripts/bin/ecc-agy/session-token-monitor.ps1` y script de soporte `scripts/ecc-agy/session_token_monitor.py` que lea `transcript.jsonl` y determine el recuento estimado de tokens.
    - Integrar la recomendación proactiva en el resumen de `complete-task-pr.ps1`.
  - **05 - PHASE 3 (EXECUTION):**
    1. Programar `session_token_monitor.py` para parsear los pasos de la sesión y sumar tokens de entrada/salida.
    2. Exponer banderas `--threshold <n>` y `--alert-only`.
    3. Incorporar el chequeo al final de `complete-task-pr.ps1`: si tokens > 45k, emitir recomendación explícita de `/compact`.
    4. Añadir tests unitarios en `test_session_token_monitor.py`.
  - **06 - PHASE 4 (CRITIC):**
    - *Auditoría*: Manejar de forma robusta la ausencia o bloqueo de lectura en caliente del archivo `transcript.jsonl`.
  - **07 - PHASE 5 (FORMAT):**
    - Script CLI en Python/PowerShell con reporte conciso y tests unitarios al 100%.
  - **MODELO & AGENTE ASIGNADO:** **Carbon ($C_6$) / Gemini 3.8 Flash** (~1.000 tokens).
  - **COMPACT TRIGGER:** Inmediato tras la ejecución si la sesión supera 45.000 tokens.

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

## 5. Gobernanza de Modelos, Tokens y Política de Auto-Compact

### 5.1. Matriz de Asignación de Modelos por Tarea (Token Optimization)

| Tarea | Agente Elemental | Modelo Gemini 3.8 | Presupuesto Tokens / Turno | Justificación de Eficiencia |
| :--- | :--- | :--- | :--- | :--- |
| **2.1 Hard Gate Presupuesto** | **Carbon ($C_6$)** | `flash` | ~1.200 tokens | Código Python stdlib directo sin necesidad de razonamiento extendido. |
| **2.2 Integración gemini-mcp** | **Carbon ($C_6$)** | `flash` | ~1.000 tokens | Generación de manifiestos JSON estáticos y scripts de soporte. |
| **2.3 Hooks & AgentShield** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (diseño) + `flash` (código) | ~6.000 tokens | Modelado de amenazas de seguridad requiere Pro Thinking; código en Flash. |
| **3.1 Prompt Caching Alignment** | **Carbon ($C_6$)** | `flash` | ~1.000 tokens | Reordenamiento estructural de Markdown con formato determinista. |
| **3.2 Git Pre-Commit Hooks** | **Carbon ($C_6$)** | `flash` | ~1.200 tokens | Scripts de automatización en PowerShell y Bash POSIX. |
| **3.3 Telemetría Tokens Sesión**| **Carbon ($C_6$)** | `flash` | ~1.000 tokens | Análisis de archivos JSONL y métricas numéricas. |
| **3.4 CLI Promoción Skills** | **Carbon ($C_6$)** | `flash` | ~1.100 tokens | Operaciones de archivos y validación de frontmatter. |
| **4.1 Linter Paridad SDK** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (análisis) + `flash` (código) | ~8.000 tokens | Análisis de contratos políglotas (Go/TS/Python) requiere Pro Thinking. |
| **4.2 Analizador Bloqueos PG** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (semántica) + `flash` (parser) | ~10.000 tokens| El análisis de transacciones, deadlocks y bloqueos LTS requiere Pro Thinking. |
| **4.3 Validador Ingress / Portal**| **Carbon ($C_6$)** | `flash` | ~1.200 tokens | Cruce de configuraciones estáticas YAML, Go y CoreDNS. |
| **4.4 Despliegue Tagged CD** | **Argon ($Ar_{18}$)** $\rightarrow$ **Carbon ($C_6$)** | `pro` (rollback) + `flash` (script) | ~6.000 tokens | Garantía de rollback $< 2$ min y probes de resiliencia SRE. |

---

### 5.2. Política de Compactación & Disparadores de Auto-Compact

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
