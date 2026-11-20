<#
.SYNOPSIS
    Alterna de forma segura el plugin opcional gemini-mcp (zero-overhead).
.DESCRIPTION
    Habilita, deshabilita o consulta el estado de gemini-mcp en mcp_config.json.
.PARAMETER Enable
    Habilita temporalmente gemini-mcp.
.PARAMETER Disable
    Deshabilita gemini-mcp para restablecer el presupuesto de 0 tokens en reposo.
.PARAMETER Status
    Muestra el estado actual.
.EXAMPLE
    pwsh -File scripts/bin/ecc-agy/toggle-gemini-mcp.ps1 -Status
    pwsh -File scripts/bin/ecc-agy/toggle-gemini-mcp.ps1 -Enable
    pwsh -File scripts/bin/ecc-agy/toggle-gemini-mcp.ps1 -Disable
#>
param(
    [switch]$Enable,
    [switch]$Disable,
    [switch]$Status,
    [string]$Config = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\py\toggle_gemini_mcp.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "[ERROR] No se encuentra $PyScript"
    exit 1
}

$Arguments = @($PyScript)
if ($Enable) { $Arguments += "--enable" }
if ($Disable) { $Arguments += "--disable" }
if ($Status) { $Arguments += "--status" }
if ($Config) { $Arguments += @("--config", $Config) }

python @Arguments
exit $LASTEXITCODE
