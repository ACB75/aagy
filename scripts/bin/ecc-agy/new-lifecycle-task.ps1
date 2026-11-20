<#
.SYNOPSIS
    Instancia los artefactos de las 4 fases del Engineering Lifecycle para una tarea.
.DESCRIPTION
    Genera REQ_<slug>.md, PLAN_<slug>.md, DOCS_<slug>.md y REVIEW_<slug>.md a partir
    de las plantillas de doc/templates/ hacia doc/plan/.
.PARAMETER TaskId
    Identificador o rama de la tarea (ej. 'feat/kakebo/export-csv').
.PARAMETER OutputDir
    Directorio de salida (por defecto 'doc/plan').
.PARAMETER Force
    Sobrescribe archivos si ya existen.
.PARAMETER DryRun
    Simula la creación sin escribir archivos.
.EXAMPLE
    pwsh -File scripts/bin/ecc-agy/new-lifecycle-task.ps1 -TaskId "feat/kakebo/export-csv"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$TaskId,

    [string]$OutputDir = "doc/plan",

    [switch]$Force,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\ecc-agy\new_lifecycle_task.py"

if (-not (Test-Path $PyScript)) {
    throw "Script python no encontrado: $PyScript"
}

$cmdArgs = @(
    $PyScript,
    "--task-id", $TaskId,
    "--repo-root", $RepoRoot,
    "--output-dir", $OutputDir
)

if ($Force) { $cmdArgs += "--force" }
if ($DryRun) { $cmdArgs += "--dry-run" }

python @cmdArgs
exit $LASTEXITCODE
