<#
.SYNOPSIS
    Diagnostica la instalación de aagy en Antigravity / Gemini (/aagy-doctor).
.DESCRIPTION
    Wrapper de scripts/py/aagy_doctor.py: catálogo común DOC-01..DOC-14,
    el mismo que usa /aagy-ecc-doctor en Claude Code. Solo lectura salvo -Fix.
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
    pwsh -NoProfile -File scripts/ps1/aagy-doctor.ps1
    pwsh -NoProfile -File scripts/ps1/aagy-doctor.ps1 -Fix
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
$PyScript = Join-Path $ProjectRoot "scripts\py\aagy_doctor.py"

$ArgsList = @("--repo-root", $ProjectRoot)
if ($Json) { $ArgsList += "--json" }
if ($Fix) { $ArgsList += "--fix" }
if ($Yes) { $ArgsList += "--yes" }
if ($Strict) { $ArgsList += "--strict" }
if ($Only) { $ArgsList += @("--only", $Only) }

python $PyScript @ArgsList
exit $LASTEXITCODE
