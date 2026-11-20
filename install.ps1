<#
.SYNOPSIS
    Instalador Multi-Distribución del Ecosistema Anything Antigravity (aagy / aagy-ecc).
.DESCRIPTION
    Permite desplegar de forma interactiva o parametrizada cualquiera de las distribuciones:
      - agy      : Distribución nativa para Google Antigravity & Gemini (~/.gemini/config/plugins/aagy).
      - claude   : Distribución hermana aagy-ecc para Claude Code (.claude/, CLAUDE.md, hooks).
      - aagy-ecc : Alias explícito de 'claude'.
      - homelab  : Alias de compatibilidad hacia 'agy'.
.PARAMETER Target
    agy | claude | aagy-ecc | homelab
.PARAMETER Profile
    minimal (por defecto: Nivel 1 Global con ~22 skills nucleares universales) |
    full    (despliegue del catálogo completo optimizado a <=140c)
.PARAMETER Destination
    Directorio de destino (por defecto ~/.gemini/config/plugins/aagy o proyecto actual).
.EXAMPLE
    pwsh -File install.ps1 -Target agy -Profile minimal
    pwsh -File install.ps1 -Target aagy-ecc -Destination C:\Workspace\my-app
#>
param(
    [ValidateSet("claude", "aagy-ecc", "agy", "homelab")]
    [string]$Target = "agy",

    [ValidateSet("minimal", "full")]
    [string]$Profile = "minimal",

    [string]$Destination
)

$ErrorActionPreference = "Stop"
$ScriptRoot = $PSScriptRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "         ANYTHING ANTIGRAVITY (AAGY / AAGY-ECC) INSTALLER        " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Distribución seleccionada: $Target | Perfil: $Profile" -ForegroundColor Yellow

if ($Target -eq "homelab") {
    Write-Host "[i] Nota: 'homelab' ha sido unificado en la distribución 'aagy'." -ForegroundColor Yellow
    $Target = "agy"
}
if ($Target -eq "aagy-ecc") {
    $Target = "claude"
}

switch ($Target) {
    "claude" {
        $sourceDir = Join-Path $ScriptRoot "aagy-ecc"
        if (-not $Destination) {
            $Destination = (Get-Location).Path
        }
        Write-Host "[+] Desplegando aagy-ecc (Claude Code) en: $Destination" -ForegroundColor Green
        if (-not (Test-Path $Destination)) {
            New-Item -ItemType Directory -Force -Path $Destination | Out-Null
        }
        Copy-Item -Path (Join-Path $sourceDir "CLAUDE.md") -Destination $Destination -Force
        Copy-Item -Path (Join-Path $sourceDir ".claude") -Destination (Join-Path $Destination ".claude") -Recurse -Force
        Write-Host "[✓] Distribución aagy-ecc instalada con éxito." -ForegroundColor Green
    }
    "agy" {
        if (-not $Destination) {
            $Destination = Join-Path $env:USERPROFILE ".gemini\config\plugins\aagy"
        }
        Write-Host "[+] Desplegando plugin Anything Antigravity (aagy) en: $Destination" -ForegroundColor Green

        $syncScript = Join-Path $ScriptRoot "scripts\pwsh\aagy-sync.ps1"
        $phase = if ($Profile -eq "full") { "all" } else { "generic" }
        pwsh -NoProfile -File $syncScript -Phase $phase -Clean
        Write-Host "[✓] Plugin aagy instalado en Antigravity bajo perfil '$Profile'." -ForegroundColor Green
    }
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Operación completada exitosamente." -ForegroundColor Cyan
