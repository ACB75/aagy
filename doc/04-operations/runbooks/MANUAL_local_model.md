# Manual: Modelo Local con Ollama (`MANUAL_local_model.md`)

> **Requisitos**: [REQ_aagy_local_model.md](../../06-backlog/plans/REQ_aagy_local_model.md) | **Motor**: [`local_model.py`](../../../scripts/py/local_model.py)
> **Claude Code**: `/aagy-local` | **Antigravity**: skill `aagy-local` | **Doctor**: DOC-16

---

## 1. Qué hace

El harness puede delegar tareas sencillas (clasificar, resumir, extraer, traducir,
completar) en un modelo local de Ollama y, si se pide, trabajar solo con modelos
locales. Sin Ollama todo sigue igual: el modo `auto` se queda en `off`.

| Modo | Qué pasa |
| :--- | :--- |
| `auto` (por defecto) | Si Ollama responde y tiene el modelo de herramienta, el servidor MCP `aagy-local` expone `local_status` y `local_run`. Si no, no expone nada. |
| `off` | El servidor no expone herramientas. |
| `tool` | Como `auto`, pero forzado: DOC-16 falla si Ollama no responde. |
| `only` | Sesión sin modelo en la nube (sección 4). |

## 2. Configuración

El plugin no trae nombres de modelo. Se leen con `aagy_config` (DOC-17):

```json
{
  "local_model": {
    "url": "http://localhost:11434",
    "tool": "<modelo de herramienta>",
    "only": "<modelo con llamadas a herramientas>",
    "fim": "<modelo de autocompletado>",
    "num_ctx": 8192
  }
}
```

- Modelos y URL: en `<AAGY_ENV_DIR>/aagy/env.json` (la máquina).
- Lo del proyecto (`private_globs`, `tasks`, `mode`): en `.governance/aagy.json`.
- Atajos que mandan sobre los ficheros: `AAGY_LOCAL_MODEL`, `AAGY_OLLAMA_URL`,
  `AAGY_LOCAL_MODEL_NAME`, `AAGY_LOCAL_AGENT_MODEL`, `AAGY_LOCAL_FIM_MODEL`,
  `AAGY_LOCAL_NUM_CTX`, `AAGY_LOCAL_TIMEOUT_S`.

Tareas propias: `local_model.tasks` añade una tarea (`instruction`, `params`,
`format` `text` o `json`, `max_chars`) o quita una con `null`.

## 3. Uso diario

```text
python scripts/py/local_model.py status        # modo pedido y efectivo
python scripts/py/local_model.py on|off|auto   # guarda local_model.mode
python scripts/py/local_model.py bench         # precisión y tokens/s
python scripts/py/local_model.py usage         # llamadas registradas, sin contenido
python scripts/py/local_model.py register-agy  # registra el servidor en Antigravity
```

En Claude Code, `aagy-ecc` registra el servidor en su `.mcp.json`. Los ficheros de
`local_model.private_globs` pasan por la guarda `local_private_guard.py`: Claude Code
pregunta antes de leerlos y Antigravity los deniega y propone `local_run` con `paths`
(su contrato de hooks no admite preguntar).

## 4. Modo solo local

```text
python scripts/py/local_model.py only --harness claude [-- <argumentos de claude>]
python scripts/py/local_model.py only --harness agy
```

- **Claude Code**: fija `ANTHROPIC_BASE_URL` (la URL de Ollama), `ANTHROPIC_AUTH_TOKEN=ollama`,
  `ANTHROPIC_API_KEY=""` y `AAGY_LOCAL_MODEL=only` solo para ese proceso y lanza
  `claude --model <local_model.only>`. El SessionStart lo anuncia e inyecta reglas reducidas.
  Ollama recomienda 64k de contexto (`OLLAMA_CONTEXT_LENGTH`); por debajo de 32k avisa.
- **Antigravity**: el editor no admite Ollama como modelo principal, así que usa el
  SDK (`pip install google-antigravity`) con `LocalOpenAIAgentConfig` contra
  `<url>/v1`, en un bucle de terminal. Sin el SDK, lo dice y no hace nada más.

## 5. Autocompletado (Tab) en VS Code y Antigravity

1. Instala la extensión Continue en el editor.
2. `ollama pull <modelo-fim>` (el de `local_model.fim`).
3. Copia [`continue-config.yaml`](../../../skills/aagy-local/templates/continue-config.yaml)
   a `~/.continue/config.yaml` y cambia `<modelo-fim>`. Los dos editores comparten ese fichero.
4. Desactiva en Continue el chat y el agente: solo se usa el rol `autocomplete`.
   El chat sigue en Claude Code o Antigravity con sus suscripciones.

DOC-16 avisa si `local_model.fim` está configurado y el modelo no está descargado.
