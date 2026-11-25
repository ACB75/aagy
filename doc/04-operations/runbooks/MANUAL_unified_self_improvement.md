# Runbook Operativo: Motor Unificado de Autodescubrimiento y Automejora (`self_improve.py`)

> **Alcance**: `aagy` (*Anything Antigravity*) y paridad `aagy` (*Claude Code*)  
> **Requisitos Cubiertos**: [`REQ_aagy_unified_self_improvement.md`](../../06-backlog/plans/REQ_aagy_unified_self_improvement.md) (`RF-01`..`RF-05`, `CA-01`..`CA-04`)  
> **Módulos Canónicos**: [`scripts/py/self_improve.py`](../../../scripts/py/self_improve.py), [`scripts/py/instinct_manager.py`](../../../scripts/py/instinct_manager.py), [`hooks.json`](../../../hooks.json), [`skills/agent-self-evaluation/SKILL.md`](../../../skills/agent-self-evaluation/SKILL.md)

---

## 1. Arquitectura y Flujo de Fin a Fin

El sistema unifica `auto-evolve`, `instinct_manager` y `agent-self-evaluation` en un único motor determinista en Python stdlib con wrappers multiplataforma (`pwsh` y `bash`):

1. **Captura Híbrida Zero-Overhead (`RF-01`)**:
   - **Pasiva (`hooks.json` `Stop`)**: Ejecuta `python scripts/py/self_improve.py --capture-stop` al cierre de sesión en $< 500\text{ ms}$ (timeout `5s`), consume `0` tokens en el prompt y devuelve `{}` incluso ante errores o entradas vacías.
   - **Manual CLI**: Invocable desde terminal mediante `aagy self-improve` / `aagy self-improve` / `self_improve.py`.
2. **Persistencia a Doble Nivel (`RF-02`)**:
   - **Nivel Proyecto (`project`)**: `<repo>/.agents/instincts/` (archivos `<id>.md` y `observations.jsonl`). Mantiene retrocompatibilidad 100% con `app`.
   - **Nivel Global Plugin (`global`)**: `$PLUGIN_DATA/instincts/` (resuelto por `--plugin-data`, `AGY_PLUGIN_DATA`, `CLAUDE_PLUGIN_DATA` o `~/.gemini/config/plugins/aagy/.data/instincts/`).
3. **Sanitización AgentShield y Redacción de Secretos (`RF-03`)**:
   - Filtra tokens `Bearer`, `API_KEY`, `password`, claves GitHub (`ghp_`), AWS (`AKIA`) y Google (`AIza`) reemplazándolas por `[REDACTED]` antes de escribir en disco.
   - Bloquea vectores de *prompt injection* (`ignore previous instructions`, `bypass access control`, `exfiltrate`, `rm -rf /`) rechazando la observación o promoción.
4. **Promoción Controlada por 4 Compuertas (`RF-04`)**:
   - **Gate 1 (AgentShield)**: 0 patrones de inyección o comandos peligrosos.
   - **Gate 2 (Hard Gate de Presupuesto)**: Valida con [`workspace_audit.py`](../../../scripts/py/workspace_audit.py) (`MAX_SKILL_DESC = 140`, `MAX_AGENT_DESC = 120`, `MAX_RULE_FILE_BYTES = 24000`, `MAX_RULES_TOTAL_TOKENS = 16000`), priorizando artefactos Tier-2 (`skill`, `script`, `hook`) sobre `rule`.
   - **Gate 3 (Smoke-Test en Directorio Efímero)**: Compila y audita el borrador en un `TemporaryDirectory` antes de tocar el árbol real.
   - **Gate 4 (Confirmación Humana Explícita)**: Sin `--confirm` (`-Confirm`), solo genera el borrador en `.agents/instincts/proposals/` (`STATUS: PENDING_CONFIRMATION`) y jamás escribe en `skills/`, `rules/` ni `scripts/`.

---

## 2. Paridad 1-a-1 de Comandos en Terminal

### 2.1. Descubrimiento y Deduplicación de Candidatos (`--discover`)

```powershell
# Windows 11 (PowerShell 7)
pwsh -NoProfile -File scripts/ps1/aagy.ps1 self-improve --discover --repo-root . --scope all

# Salida JSON estructurada
pwsh -NoProfile -File scripts/ps1/aagy.ps1 self-improve --discover --json
```

```bash
# Linux / WSL / macOS (Bash)
bash scripts/sh/aagy.sh self-improve --discover --repo-root . --scope all
```

### 2.2. Revisión de Compuertas y Promoción Segura (`--review` / `--promote`)

```powershell
# Revisar candidato (ejecuta AgentShield + Budget Gate + Smoke-Test sin promover)
pwsh -NoProfile -File scripts/ps1/aagy.ps1 self-improve --review "pg-lock-safety" --tier skill

# Promover candidato tras confirmación explícita del usuario
pwsh -NoProfile -File scripts/ps1/aagy.ps1 self-improve --promote "pg-lock-safety" --tier skill --confirm
```

### 2.3. Gestión Directa de Instintos (`manage-instincts`) y Autoevaluación 5 Ejes (`--evaluate`)

```powershell
# Guardar, listar y exportar instintos (project | global | all)
pwsh -NoProfile -File scripts/ps1/aagy.ps1 instinct-manager save --id pg-ddl --trigger "PostgreSQL DDL" --learning "Usar CREATE INDEX CONCURRENTLY" --scope project
pwsh -NoProfile -File scripts/ps1/aagy.ps1 instinct-manager list --scope all
pwsh -NoProfile -File scripts/ps1/aagy.ps1 instinct-manager export --scope all

# Evaluar salida del agente en los 5 ejes (Accuracy, Completeness, Clarity, Actionability, Conciseness)
python scripts/py/self_improve.py --evaluate "All 154 tests passed (exit code 0)." --task "Run verification suite" --json
```
