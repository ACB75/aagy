# Anything Antigravity (`aagy`)

> **Ecosistema Maestro Multi-Harness para Google Antigravity, Gemini 3.8 y Anthropic Claude Code (`aagy-ecc`)**  
> Repositorio Canónico: [`ACB75/aagy`](https://github.com/ACB75/aagy) | Versión: `4.1.0`

---

## 1. Visión y Arquitectura

**Anything Antigravity (`aagy`)** es el arnés de ingeniería de software, gobernanza autónoma y optimización de presupuesto de contexto diseñado para **Google Antigravity & Gemini 3.8** con paridad simétrica hacia **Anthropic Claude Code (`aagy-ecc/`)**:

```mermaid
flowchart TD
    subgraph Core["Repositorio Maestro Anything Antigravity (/aagy)"]
        Root["aagy (Raíz: plugin.json, hooks.json, rules/AGENTS.md, skills/, agents/)"]
        Scripts["scripts/{py,ps1,sh}/tests/<br/>(Automatización Multi-Runtime & Paridad Manual 1-a-1)"]
        Docs["doc/ v2 + .governance/docs-map.json<br/>(00-governance .. 06-backlog + fallback home-lab)"]
        SubPlugin["aagy-ecc/<br/>(Distribución Hermana para Claude Code)"]
    end

    subgraph Targets["Entornos de Despliegue"]
        AGY["Google Antigravity & Gemini 3.8<br/>(~/.gemini/config/plugins/aagy)"]
        Claude["Anthropic Claude Code CLI<br/>(CLAUDE.md + .claude/ + .claude-plugin/)"]
        Projects["Proyectos & Monorepos (Home-Lab / Enterprise)<br/>(.agents/instincts/ + Lifecycle 4 Fases)"]
    end

    Root --> AGY
    SubPlugin --> Claude
    Scripts --> Projects
    Docs --> Projects
```

---

## 2. Arquitectura Two-Tier y Distribuciones

| Distribución | Destino | Características Clave | Presupuesto en Reposo |
| :--- | :--- | :--- | :--- |
| **`aagy` (Raíz)** | Google Antigravity & Gemini (`~/.gemini/config/plugins/aagy`) | **Tier 1 Global**: [`rules/AGENTS.md`](rules/AGENTS.md) compactado (`< 12 KB`), 22 skills nucleares transversales, 12 subagentes y [`hooks.json`](hooks.json) deterministas (`PreToolUse`, `PostToolUse`, `Stop`). **Tier 2 Lazy**: 169 skills ($\le 140$ chars) y 49 subagentes ($\le 120$ chars) cargados bajo demanda. | **~3.635 tokens** (bajo el límite duro de 16.000 tokens de reglas y 3.000 tokens eager). |
| **[`aagy-ecc`](aagy-ecc/README.md)** | Anthropic Claude Code (`aagy-ecc/`) | Distribución hermana sincronizada ([`CLAUDE.md`](aagy-ecc/CLAUDE.md), `.claude/`, `.claude-plugin/plugin.json`, `commands/`, `hooks/`) validada continuamente por [`audit_plugin_parity.py`](scripts/py/audit_plugin_parity.py). | Paridad 100% con `aagy`. |

---

## 3. Instalación y Sincronización (`install.ps1` / `install.sh`)

### Windows 11 (PowerShell 7+)

```powershell
# 1. Instalar / actualizar el plugin global aagy en Google Antigravity (Tier 1 recomendado)
pwsh -NoProfile -File install.ps1 -Target agy -Profile minimal

# 2. Instalar el catálogo completo de skills en Antigravity
pwsh -NoProfile -File install.ps1 -Target agy -Profile full

# 3. Desplegar la distribución hermana aagy-ecc (Claude Code) en un proyecto destino
pwsh -NoProfile -File install.ps1 -Target aagy-ecc -Destination C:\Ruta\A\MiProyecto

# 4. Sincronizar perfil de dominio específico (infra, kakebo, cluster, token-hill)
pwsh -NoProfile -File scripts/ps1/aagy-sync.ps1 -Phase kakebo -TargetProject C:\Ruta\A\MiProyecto
```

### Linux / WSL / macOS (POSIX LF `\n`)

```bash
# 1. Instalar plugin global aagy (Tier 1)
./install.sh agy

# 2. Desplegar aagy-ecc (Claude Code) en un proyecto destino
./install.sh aagy-ecc /ruta/a/mi-proyecto
```

---

## 4. Estructura Consolidada de Scripts (`scripts/{py,ps1,sh}/tests/`)

Toda la automatización del ecosistema reside en tres motores multi-runtime con suites `pytest` dedicadas (`154/154` tests) y **paridad manual 1-a-1** (cualquier flujo es ejecutable desde terminal sin depender del plugin):

- **[`scripts/py/`](scripts/py/)**: Motores Python 3 stdlib pura (`docs_map.py`, `new_lifecycle_task.py`, `self_improve.py`, `instinct_manager.py`, `workspace_audit.py`, `sonar_audit.py`, `security_audit.py`, `audit_plugin_parity.py`, `map_docs.py`, `archive_todo.py`, `sync_ideas_todo.py`, `format_commit.py`, `validate_branch.py`, `generate_postmortem.py`) y pruebas en `scripts/py/tests/`.
- **[`scripts/ps1/`](scripts/ps1/)**: Wrappers nativos para Windows PowerShell 7 (`complete-task-pr.ps1`, `new-lifecycle-task.ps1`, `audit-workspace.ps1`, `auto-evolve.ps1`, `aagy-sync.ps1`, `lint-markdown.ps1`, `map-docs.ps1`, etc.) y pruebas en `scripts/ps1/tests/`.
- **[`scripts/sh/`](scripts/sh/)**: Wrappers POSIX con finales de línea `LF (\n)` estrictos para Linux/WSL y pruebas en `scripts/sh/tests/`.

### Comandos Frecuentes de Verificación y Ciclo de Vida

```powershell
# Ejecutar suite completa de tests multi-runtime (Python, PowerShell y Shell)
python -m pytest scripts/py/tests scripts/ps1/tests scripts/sh/tests -q

# Auditoría integral de higiene, presupuesto de tokens, SonarQube Rating A y AgentShield
pwsh -NoProfile -File scripts/ps1/audit-workspace.ps1 -Clean

# Auditoría de paridad multi-harness (aagy <-> aagy-ecc)
pwsh -NoProfile -File scripts/ps1/audit-plugin-parity.ps1

# Validación de enlaces relativos y contrato .governance/docs-map.json
pwsh -NoProfile -File scripts/ps1/map-docs.ps1

# Linter de Markdown (DavidAnson markdownlint)
pwsh -NoProfile -File scripts/ps1/lint-markdown.ps1 -CheckOnly

# Motor unificado de autodescubrimiento, instintos a doble nivel y automejora con budget gate
pwsh -NoProfile -File scripts/ps1/auto-evolve.ps1 -Discover -Scope both
```

---

## 5. Arquitectura Documental `/doc` v2 y Gobernanza

La documentación sigue el estándar **`/doc` v2** gobernado por [`.governance/docs-map.json`](.governance/docs-map.json) (con *fallback* retrocompatible automático para proyectos clásicos como `home-lab`):

- 📑 **[`doc/INDEX.md`](doc/INDEX.md)**: Índice maestro navegable de toda la documentación.
- 🧭 **[`doc/CONTEXT.md`](doc/CONTEXT.md)**: Vocabulario canónico y fronteras del ecosistema `aagy` / `aagy-ecc`.
- 🚦 **[`doc/STATUS.md`](doc/STATUS.md)**: Estado operativo actual, métricas de presupuesto de tokens y SonarQube Quality Gate `A`.
- 📜 **[`doc/LOG.md`](doc/LOG.md)**: Registro histórico *append-only* de hitos y decisiones arquitectónicas.
- 📏 **[`doc/00-governance/DOC_STANDARDS.md`](doc/00-governance/DOC_STANDARDS.md)**: Norma `/doc` v2, convención `<folder>/dgrms/` (`.mmd`, `.puml`, `.bpmn`) y reglas `markdownlint`.
- 🛠️ **[`doc/00-governance/MANUAL_WORKFLOW.md`](doc/00-governance/MANUAL_WORKFLOW.md)**: Guía de paridad manual 1-a-1 CLI $\leftrightarrow$ Plugin y puntos de entrada flexibles (`IDEAS` $\rightarrow$ `REQ` $\rightarrow$ `PLAN` $\rightarrow$ `TODO`).
- 🏗️ **[`doc/01-architecture/`](doc/01-architecture/GUIA_ARQUITECTURA_HARNESS_Y_ENTORNO_AGY.md)**: Arquitectura del harness Antigravity y manual de paridad [`MANUAL_aagy_ecc_parity_and_migration.md`](doc/01-architecture/MANUAL_aagy_ecc_parity_and_migration.md).
- 🏛️ **[`doc/02-adr/README.md`](doc/02-adr/README.md)**: Índice de Architecture Decision Records (`ADR-0001`..`ADR-0003`).
- 🔄 **[`doc/03-domain-and-flows/`](doc/03-domain-and-flows/README.md)**: Flujos de dominio y diagramas PlantUML / BPMN2.
- ⚙️ **[`doc/04-operations/`](doc/04-operations/runbooks/MANUAL_unified_self_improvement.md)**: Runbooks operativos y guías de configuración.
- 🩺 **[`doc/05-post-mortems/`](doc/05-post-mortems/PM_fix_scripts_install_dir_creation_20261120_203232.md)**: Autopsias SRE 5-Whys (*blameless*).
- 📋 **[`doc/06-backlog/TODO.md`](doc/06-backlog/TODO.md)**: Backlog activo, [`IDEAS.md`](doc/06-backlog/IDEAS.md), planes `REQ_*.md` y archivo histórico `doc/06-backlog/done/`.
