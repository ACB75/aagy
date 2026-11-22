# Manual: Backlog Compartido entre Claude Code y Antigravity (`MANUAL_shared_backlog.md`)

> **Decisión**: [ADR-0005](../../02-adr/ADR_aagy_0005_shared_backlog_multi_harness.md) | **Motor**: [`backlog.py`](../../../scripts/py/backlog.py)
> **Claude Code**: `/aagy-todo`, `/epic-decompose`, `/epic-claim`, `/epic-sync`, `/epic-close` | **Antigravity**: skill `shared-backlog`

---

## 1. Qué se comparte

| Qué | Dónde |
| :--- | :--- |
| Tareas y épicas | `TODO.md` (ruta de `.governance/docs-map.json`) |
| Dueño, estado, rama, último commit, nota | `.git/aagy-backlog/state.json` (común a todos los worktrees, fuera de git) |
| Notas de relevo | `doc/06-backlog/quick/HANDOFF_<id>.md` |
| Tareas terminadas | `doc/06-backlog/done/` (vía `archive_todo.py`) |

Estados: `todo`, `in_progress`, `review`, `handoff`, `blocked`, `done`. Un claim en
`in_progress`/`review` sin actualizar durante 4 h queda libre (`AAGY_BACKLOG_TTL_HOURS`).

---

## 2. Órdenes

Ejecuta desde la carpeta del repo en el que trabajas. Indica el agente con `--agent claude|agy|human` o `AAGY_AGENT`.

```powershell
pwsh -NoProfile -File scripts/ps1/backlog.ps1 init                              # repo nuevo del home-lab
pwsh -NoProfile -File scripts/ps1/backlog.ps1 list                              # en curso, relevos y pendientes
pwsh -NoProfile -File scripts/ps1/backlog.ps1 next --agent agy --claim          # siguiente libre (relevos primero)
pwsh -NoProfile -File scripts/ps1/backlog.ps1 claim mi-tarea --agent claude --worktree
pwsh -NoProfile -File scripts/ps1/backlog.ps1 checkpoint --agent claude --note "tests en verde, falta doc"
pwsh -NoProfile -File scripts/ps1/backlog.ps1 handoff --agent claude --note "falta X; siguiente: pytest -k y"
pwsh -NoProfile -File scripts/ps1/backlog.ps1 done mi-tarea --agent agy --note "verificado con pytest"
pwsh -NoProfile -File scripts/ps1/backlog.ps1 release mi-tarea --agent human --force   # liberar a mano
```

```bash
bash scripts/sh/backlog.sh list --brief
python3 scripts/py/backlog.py --json list --all
```

### Épicas

```bash
python3 scripts/py/backlog.py epic add "Backup nocturno" --objective "Copias diarias verificadas"
python3 scripts/py/backlog.py add "Script de backup" --epic backup-nocturno --detail "**01 - ROLE:** SRE ..."
python3 scripts/py/backlog.py next --agent agy --epic backup-nocturno --claim
python3 scripts/py/backlog.py epic sync backup-nocturno
python3 scripts/py/backlog.py epic close backup-nocturno --agent claude
```

---

## 3. Flujos

### 3.1. Relevo por tokens (uno detrás de otro)

1. Claude trabaja con `claim` y hace `checkpoint --note` tras cada paso.
2. Al quedarse sin presupuesto: commit de lo que compile y `handoff --note "hecho / pendiente / siguiente comando"`. Si la sesión se cierra, el hook `SessionEnd` hace el relevo con la última nota; si se corta sin aviso, queda el checkpoint del último turno y, a las 4 h, la tarea se libera.
3. Agy abre la misma carpeta, ejecuta `list --brief` (los relevos salen primero), lee `quick/HANDOFF_<id>.md`, hace `claim` y sigue en la rama indicada.

### 3.2. Trabajo simultáneo (tareas distintas)

Si el repo usa worktrees fijos por agente ([`MANUAL_agent_worktrees.md`](MANUAL_agent_worktrees.md)), cada agente reclama en su worktree (`<repo>-aagy` / `<repo>-aagy-ecc`) sin `--worktree`: la rama se crea allí y `handoff` la suelta para el otro agente. Lo que sigue es para tareas extra en paralelo:

1. Cada agente reclama su tarea con `--worktree`: se crea `<repo>.wt/<id>` en la rama `feat/<proyecto>/<id>` (o `--branch fix/...`).
2. Abre esa carpeta en el agente correspondiente. El estado es común, así que `claim` impide que los dos cojan la misma tarea.
3. `done` marca `[x]`, archiva y borra el worktree si no tiene cambios sin commit.

---

## 4. Hooks

| Harness | Evento | Acción |
| :--- | :--- | :--- |
| Claude Code | `SessionStart` | Añade el resumen `list --brief` al contexto |
| Claude Code | `Stop`, `PreCompact` | `checkpoint --auto` (rama, commit, ficheros sin commit) |
| Claude Code | `SessionEnd` | `handoff --auto` de las tareas en curso |
| Antigravity | `Stop` | `checkpoint --auto` (dentro del repo aagy) |

`--auto` nunca falla ni escribe nada si el repo no tiene backlog o el agente no tiene tareas en curso.

---

## 5. Problemas frecuentes

- **"La tarea la tiene claude/agy"**: no la toques; usa `next`. Master puede liberarla con `release --agent human --force`.
- **"El backlog está bloqueado"**: otro proceso está escribiendo; el lock se rompe solo a los 60 s.
- **Estado perdido**: borrar `.git/aagy-backlog/` deja todas las tareas en `todo`; `TODO.md` no cambia.
