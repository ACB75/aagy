<#
.SYNOPSIS
    Diagnostica la instalación de aagy-ecc en Claude Code (/aagy-ecc-doctor).
.DESCRIPTION
    Wrapper de aagy-ecc/scripts/py/aagy_ecc_doctor.py: catálogo común DOC-01..DOC-14,
    el mismo que usa /aagy-doctor en Antigravity. Solo lectura salvo -Fix.
.PARAMETER Json
    Emitir salida en formato JSON estructurado.
.PARAMETER Fix
    Proponer arreglos seguros y aplicarlos tras confirmarlos.
.PARAMETER Yes
    Con -Fix, aplicar sin preguntar.
.PARAMETER Strict
    Un WARN cuenta como fallo (exit 1).
.PARAMETER Only
    IDs a ejecutar, separados por comas (DOC-05,DOC-09).
.EXAMPLE
    pwsh -NoProfile -File scripts/ps1/aagy-ecc-doctor.ps1
    pwsh -NoProfile -File scripts/ps1/aagy-ecc-doctor.ps1 -Fix
#>
[CmdletBinding()]
param(
    [switch]$Json,
    [switch]$Fix,
    [switch]$Yes,
    [switch]$Strict,
    [string]$Only = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $ProjectRoot "aagy-ecc\scripts\py\aagy_ecc_doctor.py"

$ArgsList = @("--repo-root", $ProjectRoot)
if ($Json) { $ArgsList += "--json" }
if ($Fix) { $ArgsList += "--fix" }
if ($Yes) { $ArgsList += "--yes" }
if ($Strict) { $ArgsList += "--strict" }
if ($Only) { $ArgsList += @("--only", $Only) }

python $PyScript @ArgsList
exit $LASTEXITCODE
