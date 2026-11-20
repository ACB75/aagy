# Plantilla de Plugin Opcional: Gemini MCP (Zero-Overhead)

> **Gobernanza de Presupuesto Antigravity**: Este plugin integra el servidor `RLabs-Inc/gemini-mcp` con compuerta dura en reposo (`"disabled": true`).

---

## 1. Propósito y Arquitectura

El servidor MCP `gemini-mcp` expone más de 30 herramientas de Gemini (Context Caching, Deep Research, análisis multimodal de PDFs/vídeos/logs y salida estructurada).
Para evitar sobrecargar el prompt conversacional diario con más de 4.500 tokens en reposo, este plugin permanece **desactivado por defecto** y solo debe habilitarse para tareas específicas de alta intensidad analítica.

---

## 2. Gestión de Credenciales y Secretos

El servidor requiere la variable de entorno `GEMINI_API_KEY`:

```powershell
# En Windows PowerShell:
$env:GEMINI_API_KEY = "tu_api_key_de_google_ai_studio"

# En Linux / macOS / WSL:
export GEMINI_API_KEY="tu_api_key_de_google_ai_studio"
```

> [!WARNING]
> Nunca escribas claves reales en `mcp_config.json`. La configuración utiliza siempre la referencia segura `${GEMINI_API_KEY}`.

---

## 3. Alternancia Segura

Para alternar el estado del plugin sin editar manualmente JSON:

```powershell
# Activar temporalmente para una sesión interactiva:
pwsh -File scripts/bin/ecc-agy/toggle-gemini-mcp.ps1 -Enable

# Desactivar tras concluir el análisis (retorno a 0 tokens):
pwsh -File scripts/bin/ecc-agy/toggle-gemini-mcp.ps1 -Disable

# Comprobar estado:
pwsh -File scripts/bin/ecc-agy/toggle-gemini-mcp.ps1 -Status
```
