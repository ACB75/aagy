# Anything Antigravity for Claude Code (`aagy-ecc`)

> **Distribución Hermana de Anything Antigravity (`aagy`) para Anthropic Claude Code**  
> Parte del ecosistema maestro [`aagy`](../README.md).

---

## 1. Visión General

`aagy-ecc` provee los artefactos, reglas, comandos slash y hooks para **Anthropic Claude Code**, manteniendo paridad estructural y funcional con el plugin raíz **Anything Antigravity (`aagy`)** verificada automáticamente mediante [`scripts/py/audit_plugin_parity.py`](../scripts/py/audit_plugin_parity.py).

---

## 2. Artefactos Incluidos

- **[`CLAUDE.md`](CLAUDE.md)**: Instrucciones maestras de contexto, defensa de prompts, invariantes de ingeniería (Google 5-Pillars, SRE, SonarQube Quality Gate A) y ciclo de vida de 4 fases.
- **`.claude/`**: Configuración nativa con comandos slash (`commands/`), reglas (`rules/`), flujos (`workflows/`) y controles empresariales (`enterprise/`).
- **[`.claude-plugin/plugin.json`](.claude-plugin/plugin.json)**: Manifiesto oficial del plugin `aagy-ecc` (`v4.0.0`).
- **`hooks/`**: Hooks deterministas de ciclo de vida y persistencia.
- **`commands/`**: Catálogo de comandos slash operativos (`/tdd`, `/plan`, `/e2e`, `/code-review`, `/evolve`, `/promote`, `/instinct-status`).
- **`scaffolds/`**: Plantillas de inicio rápido para proyectos.

---

## 3. Instalación y Uso

### Opción A: Instalador Maestro Multiplataforma

```powershell
# Windows 11 (PowerShell 7+)
pwsh -NoProfile -File ../install.ps1 -Target aagy-ecc -Destination C:\Ruta\A\Tu\Proyecto
```

```bash
# Linux / WSL / macOS
../install.sh aagy-ecc /ruta/a/tu/proyecto
```

### Opción B: Instalación como Plugin en Claude Code CLI

```bash
claude plugin install ./aagy-ecc
```
