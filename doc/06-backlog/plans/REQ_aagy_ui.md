# Fase 1: Toma de Requisitos — UI de Claude Code y Antigravity (`aagy` / `aagy-ecc`)

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería AAGY
> **ID de Tarea**: `feat/aagy/ui-statusline-notify` | **Issue**: #116
> **Fecha**: `2026-11-25` | **Autor/Rol**: `Claude (toma de requisitos) / Master (aprobación)`
> **Estado**: `APROBADO` (Master aprobó implementarlo todo, aunque no haya paridad completa entre plugins)
> **Ubicación en el repo**: `doc/06-backlog/plans/REQ_aagy_ui.md`

---

## 0. Estado actual (hallazgos en `main` @ `aaf7fe1`)

| Pieza | Dónde | Qué hace hoy | Relevancia |
| :--- | :--- | :--- | :--- |
| Status line | Ninguna | Claude Code muestra su pie por defecto | No se ve rama, épica, modo local ni presupuesto de contexto. |
| Presupuesto de contexto | `session_token_monitor.py`, skill `context-budget` | Estima tokens del transcript de Antigravity y recomienda `/compact` | La status line reutiliza la idea (umbrales), no el script. |
| Modo local | `local_model.py` (`load_settings`) | Resuelve `auto/off/tool/only` sin red | La status line lee el modo pedido sin sondear Ollama. |
| Backlog | `backlog.py`, `.git/aagy-backlog/state.json` | Reclamos por agente | Fuente de la tarea y la épica activas. |
| Avisos | Ninguno | Hay que mirar la terminal | Hooks `Stop` y `Notification`. |
| Extensiones VS Code | Ninguna recomendación | Cada uno instala las suyas | `.vscode/extensions.json` del repo consumidor. |

---

## 1. Contexto, Necesidad y Objetivos

- **Problema**: no se ve de un vistazo en qué modelo, rama, tarea o modo local está la sesión ni cuánto contexto queda, y hay que vigilar la terminal para saber si el agente terminó o pide permiso.
- **Objetivo**: mejorar la UI de los dos harnesses sin dependencias duras, sin coste y con poco gasto de tokens (todo corre fuera del contexto del modelo).
- **Alcance (`In-Scope`)**:
  1. Status line de Claude Code: modelo, rama, contexto (tokens y %), coste de la sesión, modo local, tarea y épica; se enciende y apaga.
  2. Guía de la extensión de Claude Code para VS Code y Antigravity.
  3. `ccusage` opcional para el uso diario de tokens y coste.
  4. Notificaciones de escritorio al terminar un turno largo y al pedir permiso (Windows, macOS, Linux; sin escritorio no hace nada).
  5. Antigravity: extensiones recomendadas (panel de TODO, estado Git) y estado en una línea.
- **Fuera de Alcance (`Out-of-Scope`)**: escribir una extensión propia de VS Code (sería una herramienta *ad hoc*), instalar `ccusage` o extensiones automáticamente, avisos por móvil o correo.

---

## 2. Requisitos Funcionales

| ID | Requisito |
| :--- | :--- |
| RF-01 | `aagy_statusline.py` lee el JSON que Claude Code pasa por `stdin` y escribe una línea con los segmentos de `ui.segments` (por defecto `model,branch,context,cost,local,task,usage`). |
| RF-02 | El segmento de contexto usa `context_window` del JSON y, si falta, el último `usage` del transcript. Cambia a amarillo en `ui.context_warn_pct` (60) y a rojo en `ui.context_crit_pct` (80). |
| RF-03 | `aagy_ui.py statusline on\|off [--scope user\|project\|local]` añade o quita `statusLine` en el `settings.json` de Claude Code. Solo quita o repara la suya; no pisa una ajena sin `--force`. Con `ui.statusline=false` el script no escribe nada. |
| RF-04 | El hook `SessionStart` repara la ruta de la status line cuando el plugin cambia de versión (la caché del plugin cambia de carpeta). |
| RF-05 | `aagy_notify.py` avisa en `Notification` (permiso, espera) y en `Stop` solo si el turno duró más de `ui.notify_min_s` (30 s). `ui.notify`: `auto` (por defecto; apagado en CI, SSH sin escritorio o sesiones remotas), `on`, `off`. |
| RF-06 | Backends: Windows con `powershell.exe` (toast WinRT), macOS con `osascript`, Linux con `notify-send`. Título y texto van como argumentos o variables, nunca dentro del código del script. Sin backend, sale con 0 sin escribir nada. |
| RF-07 | `ui.ccusage=true` añade el segmento `hoy $X` leyendo `ccusage daily --json --offline` desde una caché de 5 min que se refresca en segundo plano. `aagy_ui.py usage [daily\|monthly\|session\|blocks]` llama a `ccusage` si está en el `PATH` y si no, explica cómo instalarlo. Nunca lo descarga. |
| RF-08 | `aagy_ui.py vscode [--apply]` muestra o fusiona las extensiones recomendadas en `.vscode/extensions.json` sin borrar las que ya hay. Si el fichero tiene comentarios (JSONC) no lo toca y muestra el bloque. |
| RF-09 | `aagy_statusline.py --plain --agent agy` da el estado en una línea sin colores para Antigravity (skill `aagy-ui`). |
| RF-10 | Claude Code: comando `/aagy-ui`. Antigravity: skill `aagy-ui`. Mismos scripts. |

## 3. Requisitos No Funcionales

- **Rendimiento**: la status line no hace red y como mucho una llamada a `git`; tarda menos de 300 ms. `ccusage` nunca bloquea la línea.
- **Agnóstico**: sin nombres de usuario, rutas ni modelos en el código; todo con `aagy_config` (`ui.*`, `AAGY_UI_*`).
- **Coste 0 $**: `ccusage` (MIT, gratuito) y las extensiones recomendadas son gratuitas; nada se activa de pago.
- **Degradación**: cualquier fallo (sin git, sin backlog, JSON roto, sin escritorio) omite el segmento o el aviso y sale con 0.
- **Calidad**: stdlib, ficheros `<=400` líneas, tests con `pytest`.

## 4. Paridad y asimetrías

| Pieza | Claude Code | Antigravity |
| :--- | :--- | :--- |
| Status line nativa | Sí (`statusLine`) | No existe: estado con la skill `aagy-ui` (`--plain`) |
| Avisos de escritorio | `Stop` y `Notification` | `Stop` (sin duración del turno, avisa siempre que `ui.notify` lo permita) |
| `ccusage` | Sí (lee los transcripts de Claude Code) | No aplica (no lee Antigravity) |
| Extensiones recomendadas | Sí | Sí (Open VSX) |

## 5. Decisiones

- **D-01**: El plugin no puede fijar `statusLine` por sí mismo; lo escribe `aagy_ui.py` bajo demanda y el hook `SessionStart` repara la ruta.
- **D-02**: La configuración vive en `ui.*` de `aagy_config` (clave `ui` nueva en las capas de proyecto y entorno), igual que `local_model.*`.
- **D-03**: No hay `tasks.json` con rutas absolutas en el repo consumidor (serían datos de máquina); en Antigravity el estado sale por la skill.
