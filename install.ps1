<#
.SYNOPSIS
    Instalador Multi-Distribución del Ecosistema ECC (ADR-0001 Two-Tier Architecture).
.DESCRIPTION
    Permite desplegar de forma interactiva o parametrizada cualquiera de las distribuciones:
      - claude  : Boilerplates oficiales para Claude Code (.claude/, CLAUDE.md, hooks).
      - agy     : Distribución unificada para Google Antigravity & Gemini.
      - homelab : Alias de compatibilidad hacia 'agy'.
.PARAMETER Target
    claude | agy | homelab
.PARAMETER Profile
    minimal (por defecto: Nivel 1 Global con ~23 skills nucleares universales, ~800 tokens) |
    full    (despliegue del catálogo completo de 320 skills optimizadas a <=140c)
.PARAMETER Destination
    Directorio de destino (por defecto el entorno configurado de AGY o proyecto actual).
.EXAMPLE
    # Instalación recomendada (Tier 1 Global ADR-0001 - 98% ahorro de tokens):
    pwsh -File install.ps1 -Target agy -Profile minimal
    
    # Instalación de catálogo completo:
    pwsh -File install.ps1 -Target agy -Profile full
#>
param(
    [ValidateSet("claude", "agy", "homelab")]
    [string]$Target = "agy",

    [ValidateSet("minimal", "full")]
    [string]$Profile = "minimal",

    [string]$Destination
)

$ErrorActionPreference = "Stop"
$ScriptRoot = $PSScriptRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "                ECC MASTER MULTI-DISTRIBUTION INSTALLER          " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Distribución seleccionada: $Target | Perfil: $Profile" -ForegroundColor Yellow

if ($Target -eq "homelab") {
    Write-Host "[i] Nota: 'homelab' ha sido unificado en la distribución 'ecc-agy'. Desplegando ecc-agy..." -ForegroundColor Yellow
    $Target = "agy"
}

switch ($Target) {
    "claude" {
        $sourceDir = Join-Path $ScriptRoot "ecc"
        if (-not $Destination) {
            $Destination = Get-Location
        }
        Write-Host "[+] Desplegando boilerplates de Claude Code en: $Destination" -ForegroundColor Green
        Copy-Item -Path (Join-Path $sourceDir "CLAUDE.md") -Destination $Destination -Force
        Copy-Item -Path (Join-Path $sourceDir ".claude") -Destination (Join-Path $Destination ".claude") -Recurse -Force
        Write-Host "[✓] Boilerplates de Claude Code instalados con éxito." -ForegroundColor Green
    }
    "agy" {
        if (-not $Destination) {
            $Destination = Join-Path $env:USERPROFILE ".gemini\config\plugins\aagy"
        }
        Write-Host "[+] Desplegando plugin Antigravity en: $Destination" -ForegroundColor Green

        $syncScript = Join-Path $ScriptRoot "ecc-agy-sync.ps1"
        $phase = if ($Profile -eq "full") { "all" } else { "generic" }
        pwsh -NoProfile -File $syncScript -Phase $phase -Clean
        # Asegurar copia espejo hacia aagy
        if (-not (Test-Path $Destination)) {
            New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        }
        if (Test-Path (Join-Path $env:USERPROFILE ".gemini\config\plugins\ecc-agy")) {
            Copy-Item -Path (Join-Path $env:USERPROFILE ".gemini\config\plugins\ecc-agy\*") -Destination $Destination -Recurse -Force
        }
        Write-Host "[✓] Plugin aagy instalado en Antigravity bajo perfil '$Profile'." -ForegroundColor Green
    }
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Operación completada exitosamente." -ForegroundColor Cyan
