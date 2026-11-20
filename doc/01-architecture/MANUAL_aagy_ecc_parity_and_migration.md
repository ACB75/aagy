# Manual de Arquitectura y Paridad Multi-Harness: Anything Antigravity (`aagy`) y Claude Code (`aagy-ecc`)

> **Referencia Canónica**: `doc/01-architecture/MANUAL_aagy_ecc_parity_and_migration.md`  
> **Ámbito**: Orquestación y Gobernanza Dual `aagy` (Google Antigravity & Gemini) $\leftrightarrow$ `aagy-ecc` (Anthropic Claude Code)  

---

## 1. Visión General y Propósito

El ecosistema **Anything Antigravity (`aagy`)** implementa una arquitectura desacoplada y simétrica para soportar dos harnesses de inteligencia artificial líderes en la industria:

1. **`aagy` (Raíz del Repositorio)**:
   - Diseñado específicamente para **Google Antigravity** y **Gemini CLI**.
   - Integra catálogo de habilidades en dos niveles (Two-Tier Architecture), agentes canónicos (`argon`, `hydrogen`, `carbon`, `neon`), compuertas de calidad SonarQube Rating A y telemetría de tokens.
2. **`aagy-ecc` (`aagy-ecc/`)**:
   - Subplugin dedicado para **Anthropic Claude Code**.
   - Provee artefactos nativos como `CLAUDE.md`, `.claude/commands/`, hooks bash/python de ciclo de vida y configuración de plugins Claude.

```mermaid
flowchart LR
    subgraph Repo["Repositorio Unificado /aagy"]
        AAGY["aagy<br/>(Google Antigravity & Gemini)"]
        AAGY["aagy-ecc/<br/>(Anthropic Claude Code)"]
    end

    subgraph Harnesses["Harnesses de Ejecución"]
        AGY_Harness["Google Antigravity IDE / CLI<br/>(~/.gemini/config/plugins/aagy)"]
        Claude_Harness["Claude Code CLI<br/>(claude plugin install ./aagy-ecc)"]
    end

    subgraph Parity["Compuerta de Paridad"]
        Linter["audit_plugin_parity.py<br/>(Verificación Continua)"]
    end

    AAGY --> AGY_Harness
    AAGY --> Claude_Harness
    AAGY -.-> Linter
    AAGY -.-> Linter

    classDef core fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef aagy fill:#fff3e0,stroke:#f57c00,stroke-width:2px;
    classDef harness fill:#e8f5e9,stroke:#388e3c,stroke-width:1px;
    classDef tool fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px;

    class AAGY core;
    class AAGY aagy;
    class AGY_Harness,Claude_Harness harness;
    class Linter tool;
```

---

## 2. Invocación de la Auditoría de Paridad

Para verificar que no exista deriva ni discrepancias entre ambos plugins:

```powershell
# En Windows 11 con PowerShell 7
pwsh -File scripts/ps1/audit-plugin-parity.ps1

# Solo verificación (retorna código 0 o 1)
pwsh -File scripts/ps1/audit-plugin-parity.ps1 -CheckOnly

# Salida estructurada JSON para pipelines CI/CD
pwsh -File scripts/ps1/audit-plugin-parity.ps1 -Json
```

En entornos Linux / WSL (POSIX LF):

```bash
bash scripts/sh/audit-plugin-parity.sh --check-only
```

---

## 3. Instalación y Despliegue

```powershell
# Instalar / sincronizar plugin para Google Antigravity (aagy)
pwsh -File install.ps1 -Target agy -Profile minimal

# Sincronizar el espejo e instalar aagy-ecc como plugin de Claude Code
pwsh -File install.ps1 -Target aagy-ecc

# Además, copiar la plantilla CLAUDE.md + .claude/ en un proyecto
pwsh -File install.ps1 -Target aagy-ecc -Destination C:\Ruta\A\Proyecto
```

### 3.1. Qué verifica la auditoría de paridad

[`audit_plugin_parity.py`](../../scripts/py/audit_plugin_parity.py) falla (`exit 1`) si:

- `aagy-ecc/skills/`, `aagy-ecc/agents/`, `aagy-ecc/rules/AGENTS.md` o `aagy-ecc/scripts/py/` difieren de la raíz (comparación por contenido vía [`sync_aagy_ecc.py`](../../scripts/py/sync_aagy_ecc.py)).
- Algún script referenciado con `${CLAUDE_PLUGIN_ROOT}` en `aagy-ecc/hooks/hooks.json` no existe dentro del plugin.
- El nombre o la versión de `aagy-ecc/.claude-plugin/plugin.json` no coinciden con `aagy-ecc` y con la versión de `plugin.json` raíz, o `marketplace.json` no publica `aagy-ecc`.

Tras editar skills, agentes, reglas o motores Python en la raíz:

```powershell
pwsh -File scripts/ps1/sync-aagy-ecc.ps1
```
