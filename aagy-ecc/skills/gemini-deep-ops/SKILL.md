---
name: gemini-deep-ops
description: "Multimodal diagnostics, context caching, and large log analysis with Gemini. Zero overhead in resting state. Use for 5W postmortems."
---

# Gemini Deep Ops & Multimodal Diagnostics (Zero-Overhead)

> **Invariante de Presupuesto Antigravity**: Esta skill opera bajo demanda en Tier 2 (0 tokens en reposo en el catálogo global).

---

## Cuándo Utilizar Esta Skill

- Diagnosticar volcados de logs masivos ($> 10.000$ líneas) o volcados de memoria (OOMKilled, heap dumps) que sobrecargarían el contexto del chat.
- Producir secciones analíticas asistidas para autopsias SRE y Post-Mortems 5W en ramas `fix/*`.
- Aprovechar *Context Caching* de Gemini para análisis recurrentes de grandes bases de código.
- **Límites Negativos**: NO utilizar para tareas rutinarias de desarrollo, edición de código ni para ejecutar consultas web estándar (usa `search_web` nativo).

---

## Flujo de Trabajo Operativo

### 1. Diagnóstico de Volcados de Logs

Ejecuta el CLI determinista de apoyo sobre el archivo de log sospechoso:

```powershell
pwsh -File scripts/ps1/gemini-deep-ops.ps1 analyze-log --file path/to/crash.log
```

En Linux/WSL:

```bash
scripts/sh/gemini-deep-ops.sh analyze-log --file path/to/crash.log
```

### 2. Generación de Sección Post-Mortem 5W

Para integrar el análisis en una autopsia formal SRE:

```powershell
pwsh -File scripts/ps1/gemini-deep-ops.ps1 postmortem --issue fix/cluster/oom-timeout --file path/to/crash.log
```

El bloque generado se incorpora directamente en el artefacto `doc/post-mortem/PM_<branch>_<timestamp>.md`.

---

## Habilitación Opcional del Plugin MCP

Si requieres interacción interactiva directa con las herramientas completas de `RLabs-Inc/gemini-mcp` durante una sesión:

```powershell
# 1. Habilitar temporalmente:
pwsh -File scripts/ps1/toggle-gemini-mcp.ps1 -Enable

# 2. Tras finalizar la sesión, restaurar el arnés a 0 tokens en reposo:
pwsh -File scripts/ps1/toggle-gemini-mcp.ps1 -Disable
```
