# Anything Antigravity for Everything Claude Code (`aagy-ecc`)

> **Distribución hermana de Anything Antigravity (`aagy`) para Everything Claude Code**
> Parte del ecosistema maestro [`aagy`](../README.md).

---

## 1. Visión General

`aagy-ecc` es el plugin de Claude Code equivalente al plugin raíz `aagy` de
Google Antigravity. Claude Code solo carga archivos que viven dentro de la
carpeta del plugin, por eso `aagy-ecc/` lleva su propia copia de las skills,
subagentes, reglas y motores Python, generada desde la raíz por
[`sync_aagy_ecc.py`](../scripts/py/sync_aagy_ecc.py) y vigilada por
[`audit_plugin_parity.py`](../scripts/py/audit_plugin_parity.py).

| Capacidad | `aagy` (Antigravity) | `aagy-ecc` (Claude Code) |
| :--- | :--- | :--- |
| Skills | `skills/` (169) | `skills/` (perfil `generic`) + paquetes opcionales en `packs/` |
| Subagentes | `agents/` | `agents/` (perfil `generic`) + paquetes opcionales en `packs/` |
| Reglas Tier 1 | `rules/AGENTS.md` siempre cargado | índice de `rules/AGENTS.md` (espejo) inyectado por el hook `SessionStart`, con la ruta del texto completo |
| Safety gate | `PreToolUse` `run_command` → `safety-check.ps1` | `PreToolUse` `Bash\|PowerShell` → `scripts/hooks/safety_check.py` |
| Linter Markdown | `PostToolUse` `write_file`/`edit_file` → `hook-post-write.ps1` | `PostToolUse` `Write\|Edit\|MultiEdit` → `scripts/hooks/post_write_lint.py` |
| Self-improve | `Stop` → `self_improve.py --capture-stop` | `Stop` → `scripts/py/self_improve.py --capture-stop` (espejo) |
| Comandos slash | — | `commands/` (propios de Claude Code) |

---

## 2. Estructura

- **`.claude-plugin/`**: manifiesto [`plugin.json`](.claude-plugin/plugin.json) y marketplace local [`marketplace.json`](.claude-plugin/marketplace.json).
- **`packs/<perfil>/`**: paquetes opcionales generados (plugins `aagy-ecc-<perfil>`), uno por perfil de stack de `scripts/sh/aagy-sync.sh` más `extras` con lo que no está en ningún perfil. Sus `commands/` sí se editan aquí.
- **`skills/`, `agents/`, `rules/AGENTS.md`, `scripts/py/`**: espejos generados (el núcleo lleva el perfil `generic`). **No se editan aquí**; se editan en la raíz y se ejecuta `scripts/ps1/sync-aagy-ecc.ps1` (o `scripts/sh/sync-aagy-ecc.sh`).
- **`hooks/hooks.json`** y **`scripts/hooks/`**: hooks propios de Claude Code (ver [`hooks/README.md`](hooks/README.md)).
- **`commands/`**: comandos slash (`/plan`, `/code-review`, `/tdd`, `/evolve`, `/promote`, `/aagy-ecc-doctor`, `/aagy-todo`, `/epic-*`, `/aagy-worktree`...). `/aagy-todo` y `/epic-*` comparten el backlog con Antigravity; ver [`MANUAL_shared_backlog.md`](../doc/04-operations/runbooks/MANUAL_shared_backlog.md). `/aagy-worktree` gestiona el worktree fijo de Claude (`<repo>-aagy-ecc`); ver [`MANUAL_agent_worktrees.md`](../doc/04-operations/runbooks/MANUAL_agent_worktrees.md).
- **`scripts/py/aagy_ecc_doctor.py`**: motor de `/aagy-ecc-doctor` (fuente propia, no espejo). Ver [`MANUAL_aagy_doctor.md`](../doc/04-operations/runbooks/MANUAL_aagy_doctor.md).
- **`project-template/`**: [`CLAUDE.md`](project-template/CLAUDE.md) y `.claude/rules/` opcionales para copiar en un proyecto.

---

## 3. Instalación

Requisitos: Claude Code CLI y Python 3 en el `PATH` (los hooks usan `python` o `python3`).

```powershell
# Windows 11 (PowerShell 7+): sincroniza el espejo e instala el plugin
pwsh -NoProfile -File ../install.ps1 -Target aagy-ecc

# Además, copiar la plantilla CLAUDE.md + .claude/ en un proyecto
pwsh -NoProfile -File ../install.ps1 -Target aagy-ecc -Destination C:\Ruta\A\Tu\Proyecto
```

```bash
# Linux / WSL / macOS
../install.sh aagy-ecc                       # sincroniza e instala
../install.sh aagy-ecc /ruta/a/tu/proyecto   # y copia la plantilla de proyecto
```

Instalación manual equivalente:

```bash
python scripts/py/sync_aagy_ecc.py           # desde la raíz del repositorio
claude plugin marketplace add ./aagy-ecc
claude plugin install aagy-ecc@aagy-ecc
```

### 3.1. Paquetes opcionales

Cada skill, subagente y comando añade su descripción al contexto de **todas** las sesiones, así que el núcleo solo trae el perfil `generic` y el resto se habilita por paquetes, igual que los perfiles de stack de Antigravity (ADR-0004):

| Paquete | Contenido |
| :--- | :--- |
| `aagy-ecc-go`, `aagy-ecc-python`, `aagy-ecc-java-spring`, `aagy-ecc-angular`, `aagy-ecc-network-infra` | Skills, subagentes y comandos del perfil de stack |
| `aagy-ecc-extras` | Todo lo que no está en ningún perfil (orquestación `orch-*`, PRP, ML, ops...) |

```bash
claude plugin install aagy-ecc-go@aagy-ecc --scope user
```

Un repositorio consumidor puede declarar los que necesita en su `.claude/settings.json` (`enabledPlugins`), sin que el plugin sepa nada de él.

Instalar `aagy-ecc` no afecta al plugin `aagy` de Antigravity: cada uno vive en su propio harness.

---

## 4. Verificación

```powershell
pwsh -NoProfile -File ../scripts/ps1/sync-aagy-ecc.ps1 -Check   # espejo sin deriva
pwsh -NoProfile -File ../scripts/ps1/audit-plugin-parity.ps1    # paridad aagy <-> aagy-ecc
claude plugin validate ./aagy-ecc                                # manifiesto, skills y hooks
pwsh -NoProfile -File ../scripts/ps1/aagy-ecc-doctor.ps1         # diagnóstico de la instalación (DOC-01..14)
```
