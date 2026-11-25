# Manual: UI de Claude Code y Antigravity (`MANUAL_ui.md`)

> **Motor**: [`aagy_ui.py`](../../../scripts/py/aagy_ui.py), [`aagy_statusline.py`](../../../scripts/py/aagy_statusline.py), [`aagy_notify.py`](../../../scripts/py/aagy_notify.py)
> **Claude Code**: `/aagy-ui` | **Antigravity**: skill `aagy-ui` | **Issues**: #116, #123, #124

---

## 1. Qué hace

| Pieza | Claude Code | Antigravity |
| :--- | :--- | :--- |
| Comando | `/aagy-ui` (mismos subcomandos) | Skill `aagy-ui` (mismos subcomandos) |
| Configuración | `ui.*` / `AAGY_UI_*` | Igual |
| Status line | Línea fija con modelo, rama, contexto, coste, modo local, épica y tarea, `ccusage` opcional | CLI: la misma línea con `statusline on --harness agy` (sección 2.1). **Asimetría** en el editor: no tiene status line; `/aagy-ui` da el estado en una línea |
| Avisos de escritorio | Al pedir permiso o quedar a la espera (`Notification`) y al terminar un turno largo (`Stop`) | Con la status line del CLI: aviso de confirmación pendiente y `Stop` con `ui.notify_min_s`. **Asimetría** en el editor o sin ella: solo `Stop`, siempre (sección 4.1) |
| `ccusage` / `usage` | Opcional (`ccusage`, con coste en $) | **Asimetría**: `ccusage` solo lee transcripts de Claude Code. `/aagy-ui usage [daily\|monthly\|session]` da tokens estimados con `session_token_monitor.py`, sin coste en $ |
| Extensiones recomendadas | `aagy_ui.py vscode --apply` | Igual (Open VSX) |

Todo corre fuera del contexto del modelo: no gasta tokens. Sin git, sin backlog o sin
escritorio, el segmento o el aviso se omite y el hook sale con 0.

## 2. Status line de Claude Code

```bash
python scripts/py/aagy_ui.py statusline on                 # ~/.claude/settings.json
python scripts/py/aagy_ui.py statusline on --scope project # .claude/settings.json del repo
python scripts/py/aagy_ui.py statusline off
```

Ejemplo:

```text
Opus | feat/aagy/ui-statusline-notify | ctx 120k/200k 60% | $0.42 | local:auto | #116 ui-statusline | hoy $3.10
```

- **Contexto**: verde, amarillo desde `ui.context_warn_pct` (60) y rojo con la pista `/compact` desde
  `ui.context_crit_pct` (80). Es el mismo criterio que la skill `context-budget`, visible siempre.
- **Coste**: el que calcula Claude Code para la sesión (con suscripción es orientativo).
- **local**: modo pedido del modelo local (`auto/off/tool/only`, ver [MANUAL_local_model.md](MANUAL_local_model.md)); no sondea Ollama.
- **Épica y tarea**: la que el agente tiene reclamada con `backlog.py claim` ([MANUAL_shared_backlog.md](MANUAL_shared_backlog.md)).
- El comando solo toca la `statusLine` de aagy. Si ya tienes otra, pide `--force`.
- Al actualizar el plugin cambia su carpeta; el hook `SessionStart` (`aagy_ui.py repair`) corrige la ruta.

### 2.1. Status line del CLI de Antigravity

El CLI de Antigravity tiene `statusLine` en `~/.gemini/antigravity-cli/settings.json`, con el mismo
formato que Claude Code: ejecuta el comando (con `sh -c`, o `cmd /c` en Windows) en cada cambio de estado del
agente, como mucho cada 300 ms, y le pasa la sesión en JSON por `stdin`. Si tarda más de 5 s lo corta.

```bash
python scripts/py/aagy_ui.py statusline on --harness agy    # o off
```

- El comando usa la ruta absoluta del Python que lo instala, sin sintaxis de shell, para que valga con `sh` y con `cmd`.
- Coste: `cost.total_usd` del CLI. Contexto: el de `context_window` si lo trae; si no, la estimación de
  `session_token_monitor.py` sobre `transcript_path`.
- El editor de Antigravity no tiene status line: allí el estado sale con `/aagy-ui` (`--plain --agent agy`).
- Fuente: [Status line del CLI](https://antigravity.google/docs/cli/statusline/).

## 3. Configuración (`ui.*`)

Se lee con `aagy_config` (proyecto `.governance/aagy.json`, entorno `<AAGY_ENV_DIR>/aagy/env.json`
o variables `AAGY_UI_*`). Los avisos son una preferencia personal: lo normal es ponerlos en la capa de entorno.

| Clave | Variable | Por defecto |
| :--- | :--- | :--- |
| `ui.statusline` | `AAGY_UI_STATUSLINE` | `true` (con `false` no se pinta nada) |
| `ui.segments` | `AAGY_UI_SEGMENTS` | `["model","branch","context","cost","local","task","usage"]` |
| `ui.context_warn_pct` / `ui.context_crit_pct` | `AAGY_UI_CONTEXT_WARN_PCT` / `..._CRIT_PCT` | `60` / `80` |
| `ui.color` | `AAGY_UI_COLOR` (o `NO_COLOR`) | `true` |
| `ui.notify` | `AAGY_UI_NOTIFY` | `auto` |
| `ui.notify_min_s` | `AAGY_UI_NOTIFY_MIN_S` | `30` |
| `ui.ccusage` | `AAGY_UI_CCUSAGE` | `false` |

## 4. Avisos de escritorio

- `auto`: encendidos salvo en CI, en sesiones remotas de Claude Code (`CLAUDE_CODE_REMOTE`) y por SSH o
  Linux sin escritorio. `on` los fuerza, `off` los apaga.
- Windows 10/11: toast con `powershell.exe` (Windows PowerShell 5.1, viene con el sistema; no hace falta `pwsh`
  ni módulos). macOS: `osascript`. Linux: `notify-send` (paquete `libnotify`).
- El texto del aviso va como dato (variables o argumentos), nunca dentro del código que se ejecuta.

### 4.1. Antigravity: qué da la plataforma

Antigravity documenta estos eventos de hook: `SessionStart`, `PreToolUse`, `PostToolUse`, `PreInvocation`,
`PostInvocation` y `Stop` ([Hooks](https://antigravity.google/docs/hooks/)). El JSON de entrada trae
`conversationId`, `workspacePaths`, `transcriptPath`, `artifactDirectoryPath` y `modelName`. `Stop` añade
`executionNum`, `terminationReason` y `fullyIdle`. No hay evento de permiso ni de mensaje del usuario, y ni los
eventos ni el transcript traen marcas de tiempo.

La status line del CLI sí da el estado: `agent_state` (`idle`, `working`, `tool_use`...) y
`tool_confirmation_pending`. `aagy_notify.agy_observe` lo aprovecha:

- Guarda en `<tmp>/aagy-agy-turn-<conversationId>.json` cuándo el agente sale de `idle`. Esa es la marca de inicio
  del turno, y `Stop` la usa para respetar `ui.notify_min_s`, como en Claude Code.
- Cuando `tool_confirmation_pending` pasa a `true`, avisa «Antigravity espera tu confirmación». Es el equivalente
  de `Notification`.
- Sin la status line del CLI (en el editor, por ejemplo), `Stop` avisa siempre y no hay aviso de confirmación.
  `Notification` sigue en `HOOK_ASYMMETRY_EVENTS` de `audit_plugin_parity.py`, porque no es un evento de hook.
- Probar sin lanzar nada: `echo '{"message":"prueba"}' | python scripts/py/aagy_notify.py --event notification --dry-run`.

## 5. `ccusage` (opcional)

[`ccusage`](https://github.com/ryoppippi/ccusage) lee los transcripts locales de Claude Code y calcula tokens y
coste. Es gratuito (MIT) y aagy no lo instala ni lo descarga.

```bash
npm install -g ccusage                 # una vez, si lo quieres
python scripts/py/aagy_ui.py ccusage on   # segmento "hoy $X" en la status line
python scripts/py/aagy_ui.py usage monthly
```

El segmento lee una caché de 5 minutos (`<tmp>/aagy-ccusage-<fecha>.json`) que se refresca en segundo plano con
`ccusage daily --json --offline`, así que nunca frena la status line.

En Antigravity, `ccusage` no sirve. `usage --harness agy` suma los tokens estimados de cada transcript de
`~/.gemini/antigravity/brain/` con `session_token_monitor.py` (3,8 caracteres por token). No llama a ninguna API y
no da coste en $:

```bash
python scripts/py/aagy_ui.py usage daily --harness agy     # también monthly o session
```

## 6. Extensión de Claude Code en VS Code y Antigravity

1. Instala **Claude Code** (`anthropic.claude-code`) desde el panel de extensiones. Antigravity es un fork de
   VS Code que usa Open VSX; si no aparece allí, abre el terminal integrado, ejecuta `claude` y luego `/ide`:
   la CLI ofrece instalar la extensión en el editor en el que corre.
2. La extensión y la CLI comparten `~/.claude/settings.json`: los hooks, comandos y skills de `aagy-ecc` funcionan
   igual en el panel y en el terminal.
3. La status line es de la CLI: se ve cuando usas `claude` en el terminal integrado. En el panel gráfico de la
   extensión puede no mostrarse; para tenerla siempre, usa el terminal (o la opción de la extensión que abre
   Claude Code en el terminal).
4. Con la CLI en el terminal integrado, `/ide` la conecta al editor: comparte selección, diagnósticos y diffs.

## 7. Extensiones recomendadas (VS Code y Antigravity)

```bash
python scripts/py/aagy_ui.py vscode          # lista
python scripts/py/aagy_ui.py vscode --apply  # las añade a .vscode/extensions.json del repo
```

| Extensión | Para qué |
| :--- | :--- |
| `anthropic.claude-code` | Claude Code en el editor |
| `gruntfuggly.todo-tree` | Panel de TODO/FIXME del código |
| `eamodio.gitlens` | Estado Git, blame y ramas (sin las funciones Pro) |
| `mhutchie.git-graph` | Grafo de ramas y commits |
| `davidanson.vscode-markdownlint` | El mismo markdownlint de los hooks |

`--apply` añade sin quitar nada. Si `extensions.json` tiene comentarios, no lo toca y te deja el bloque para copiar.
El editor ofrece instalarlas al abrir el repo; nada se instala solo.

## 8. Rollback

`python scripts/py/aagy_ui.py statusline off` y `AAGY_UI_NOTIFY=off`. Para quitarlo del todo, `git revert` del
squash y reinstalar el plugin.
