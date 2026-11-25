#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Lanzador único de aagy: `aagy.ps1 <comando> [args]` ejecuta scripts/py/<comando>.py.
.DESCRIPTION
    Los guiones del comando pasan a guion bajo y los argumentos se pasan tal cual
    (flags de Python: --review-only, --json...). `aagy.ps1 help` lista los comandos.
.EXAMPLE
    pwsh -File scripts/ps1/aagy.ps1 complete-task-pr --review-only
#>
$ErrorActionPreference = "Stop"
$PyDir = Join-Path $PSScriptRoot "../py"
$python = Get-Command python3 -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python -ErrorAction SilentlyContinue }
if (-not $python) { [Console]::Error.WriteLine("[aagy] Falta Python 3 en el PATH."); exit 127 }

$cmd = if ($args.Count -gt 0) { [string]$args[0] } else { "help" }
$rest = @($args | Select-Object -Skip 1)
if ($cmd -in @("help", "-h", "--help")) {
    Write-Host "Uso: aagy <comando> [args]   (ej. aagy complete-task-pr --review-only)"
    Write-Host "Comandos:"
    Get-ChildItem -Path $PyDir -Filter "*.py" | Where-Object { Select-String -Path $_.FullName -Pattern "__main__" -Quiet } |
        ForEach-Object { Write-Host ("  " + ($_.BaseName -replace "_", "-")) }
    exit 0
}
$name = ($cmd -replace "-", "_") + ".py"
$script = Join-Path $PyDir $name
# Los motores propios de aagy-ecc (aagy-ecc-doctor) viven en su carpeta.
if (-not (Test-Path $script)) { $script = Join-Path $PSScriptRoot "../../aagy-ecc/scripts/py/$name" }
if (-not (Test-Path $script)) { [Console]::Error.WriteLine("[aagy] Comando desconocido: '$cmd'. Ejecuta 'aagy help'."); exit 2 }
& $python.Source $script @rest
exit $LASTEXITCODE
