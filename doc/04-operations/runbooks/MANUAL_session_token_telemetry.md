# Manual de Operación: Telemetría de Tokens en Sesión y Política de Compactación

> **Referencia de Gobernanza**: Optimización de Contexto y Gestión del Ciclo de Vida de Agentes  
> **Ámbito**: Ecosistema Antigravity (`AGY`), Harness `aagy` y Monorepo `app`  
> **Fecha de Publicación**: `2026-11-20`  

---

## 1. Fundamentos y Necesidad de Telemetría

Durante sesiones prolongadas de desarrollo, ejecución de pruebas y análisis de código, el archivo de registro estructurado de la conversación (`transcript.jsonl`) acumula difs, salidas de terminal, llamadas a herramientas y razonamiento interno (*thinking*).

### 1.1. Degradación Atencional y Coste por Turno

- **Crecimiento Lineal del Coste**: En cada turno sucesivo, todo el historial de la conversación previa debe ser re-evaluado, incrementando el coste de inferencia.
- **Degradación Atencional (*Needle-in-a-Haystack*)**: A partir de los 45.000 tokens en sesión, la capacidad del modelo para recordar restricciones operacionales o detalles específicos introducidos al inicio de la sesión experimenta una degradación progresiva.
- **Solución Canónica**: Ejecución oportuna del comando de compactación `/compact`, que resume la trayectoria conservando el estado crítico.

---

## 2. Herramienta `session-token-monitor`

El monitor analiza el archivo `transcript.jsonl` de la sesión en $< 150\text{ ms}$, estimando el recuento total de tokens computados mediante el ratio estándar del arnés ($3.8\text{ caracteres/token}$).

### 2.1. Opciones de Invocación

En Windows 11 (`pwsh`):

```powershell
# Diagnóstico completo interactivo
pwsh -File scripts/ps1/aagy.ps1 session-token-monitor

# Salida en JSON para automatizaciones
pwsh -File scripts/ps1/aagy.ps1 session-token-monitor --json

# Modo alerta (silencioso salvo si excede 45k tokens)
pwsh -File scripts/ps1/aagy.ps1 session-token-monitor --alert-only
```

En Linux o WSL (`bash` / `sh`):

```sh
./scripts/sh/aagy.sh session-token-monitor --alert-only
```

---

## 3. Integración en el Pipeline de Finalización de PR (`aagy complete-task-pr`)

Al concluir con éxito una tarea e integrar su PR en `main`, `aagy complete-task-pr` ejecuta automáticamente:

```powershell
pwsh -File scripts/ps1/aagy.ps1 session-token-monitor --threshold 45000 --alert-only
```

Si el transcript supera los 45.000 tokens acumulados, el arnés emite una advertencia destacada recomendando al desarrollador o agente ejecutar `/compact` antes de comenzar la siguiente tarea del backlog.

---

## 4. Página viva de telemetría y memoria (`live_status.py`)

El módulo [`scripts/py/live_status.py`](../../../scripts/py/live_status.py) (espejado en `aagy-ecc/scripts/py/`) consolida en una vista viva el estado del repositorio, el catálogo real (`aagy` ↔ `aagy-ecc`), la telemetría de sesiones de **Antigravity** (`session_token_monitor` / `aagy_ui`) y **Claude Code** (`aagy_statusline`), y la trazabilidad arquitectónica desde Two-Tier ([ADR-0001](../../02-adr/ADR_aagy_0001_two_tier_global_plugin_and_project_scaffolding.md) → [ADR-0004](../../02-adr/ADR_aagy_0004_stack_profiles_declared_by_consumer_repo.md)):

- **Hooks `SessionStart` y `Stop`** (`live_status.py --hook`): actualizan `.agents/LIVE_TELEMETRY.md` (gitignored) dentro del worktree del agente (`<repo>-aagy` o `<repo>-aagy-ecc`) en `< 150 ms` gracias a la caché incremental `.agents/telemetry-cache.json` por hash SHA-256 + `mtime/size`. Así el estado vivo nunca ensucia git ni bloquea `agent_worktree.py recycle` ni `backlog.py handoff`.
- **Sincronización de `doc/STATUS.md`**: `python scripts/py/live_status.py sync` actualiza la versión, el catálogo, la trazabilidad y la instantánea de telemetría en [`doc/STATUS.md`](../../STATUS.md); `live_status.py check` verifica coherencia de catálogo y marcadores sin fallar por variación entre turnos.
- **Privacidad y `consumer_refs`**: todas las etiquetas de workspace y textos renderizados se sanitizan contra `consumer_refs` de `.governance/aagy.json` para no filtrar rutas locales ni nombres de repositorios consumidores.
- **Disciplina de sesión por tarea (`1 tarea TODO / issue = 1 sesión nueva en su <repo>`)**: cada tarea de `TODO.md` o issue se abre en una sesión nueva dentro de su repositorio propietario (`rules/AGENTS.md`, `shared-backlog`, `todo-lifecycle`), evitando sesiones largas con contextos mezclados y manteniendo la telemetría atribuible 1:1.

---

## 5. Métricas de Rendimiento y Rendimiento SRE

- **Tiempo de Parseo**: $< 120\text{ ms}$ para transcripts de más de 2.000 pasos.
- **Tolerancia a Concurrencia**: Manejo de lecturas en caliente con reintentos defensivos ante bloqueos transitorios de I/O.
- **Aislamiento**: Implementado íntegramente con Python stdlib sin dependencias externas pesadas.
