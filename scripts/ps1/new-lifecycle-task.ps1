<#
.SYNOPSIS
    Instancia los artefactos del Engineering Lifecycle desde cualquier punto de entrada (IDEAS, REQ, PLAN, TODO, ALL).
.DESCRIPTION
    Genera artefactos del flujo flexible [IDEAS -> REQUISITOS -> PLAN -> TODO] resolviendo rutas
    dinámicamente vía .governance/docs-map.json (con fallback clásico).
.PARAMETER TaskId
    Identificador o rama de la tarea (ej. 'feat/kakebo/export-csv').
.PARAMETER Phase
    Punto de entrada del ciclo de vida: ALL (defecto), IDEAS, REQ, PLAN, TODO, DOCS, REVIEW.
.PARAMETER OutputDir
    Directorio de salida opcional (si se omite, lee .governance/docs-map.json).
.PARAMETER Force
    Sobrescribe archivos si ya existen.
.PARAMETER DryRun
    Simula la creación sin escribir archivos.
.EXAMPLE
    pwsh -File scripts/ps1/new-lifecycle-task.ps1 -TaskId "feat/kakebo/export-csv" -Phase PLAN
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$TaskId,

    [ValidateSet("ALL", "IDEAS", "REQ", "PLAN", "TODO", "DOCS", "REVIEW")]
    [string]$Phase = "ALL",

    [string]$OutputDir = "",

    [switch]$Force,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\py\new_lifecycle_task.py"

if (-not (Test-Path $PyScript)) {
    throw "Script python no encontrado: $PyScript"
}

$cmdArgs = @(
    $PyScript,
    "--task-id", $TaskId,
    "--repo-root", $RepoRoot,
    "--phase", $Phase
)

if (-not [string]::IsNullOrWhiteSpace($OutputDir)) {
    $cmdArgs += @("--output-dir", $OutputDir)
}
if ($Force) { $cmdArgs += "--force" }
if ($DryRun) { $cmdArgs += "--dry-run" }

python @cmdArgs
exit $LASTEXITCODE
