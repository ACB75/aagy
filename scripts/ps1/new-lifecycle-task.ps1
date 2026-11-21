<#
.SYNOPSIS
    Instancia los artefactos del Engineering Lifecycle desde cualquier punto de entrada (IDEAS, REQ, PLAN, TODO, ALL).
.DESCRIPTION
    Genera artefactos del flujo flexible [IDEAS -> REQUISITOS -> PLAN -> TODO] resolviendo rutas
    dinámicamente vía .governance/docs-map.json (con fallback clásico) o vinculando una GitHub Issue (-Issue <N>).
.PARAMETER TaskId
    Identificador o rama de la tarea (ej. 'feat/kakebo/export-csv'). Opcional si se indica -Issue.
.PARAMETER Issue
    Número de GitHub Issue (ej. 60): lee título/labels con gh issue view, auto-asigna @me,
    crea rama <type>/<project>/gh-<N>-<slug> validada por validate_branch.py y registra .governance/active-issue.json.
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
.EXAMPLE
    pwsh -File scripts/ps1/new-lifecycle-task.ps1 -Issue 60 -Phase REQ
#>
[CmdletBinding()]
param(
    [string]$TaskId = "",

    [int]$Issue = 0,

    [int]$ParentIssue = 0,

    [switch]$AttachIssue,

    [ValidateSet("ALL", "IDEAS", "REQ", "PLAN", "TODO", "DOCS", "REVIEW")]
    [string]$Phase = "ALL",

    [string]$OutputDir = "",

    [switch]$Force,

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ([string]::IsNullOrWhiteSpace($TaskId) -and $Issue -le 0 -and $ParentIssue -le 0) {
    throw "Debe especificar -TaskId, -Issue <N> o -ParentIssue <N>."
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\py\new_lifecycle_task.py"

if (-not (Test-Path $PyScript)) {
    throw "Script python no encontrado: $PyScript"
}

$cmdArgs = @(
    $PyScript,
    "--repo-root", $RepoRoot,
    "--phase", $Phase
)

if (-not [string]::IsNullOrWhiteSpace($TaskId)) {
    $cmdArgs += @("--task-id", $TaskId)
}
if ($Issue -gt 0) {
    $cmdArgs += @("--issue", "$Issue")
}
if ($ParentIssue -gt 0) {
    $cmdArgs += @("--parent-issue", "$ParentIssue")
}
if ($AttachIssue) {
    $cmdArgs += "--attach-issue"
}
if (-not [string]::IsNullOrWhiteSpace($OutputDir)) {
    $cmdArgs += @("--output-dir", $OutputDir)
}
if ($Force) { $cmdArgs += "--force" }
if ($DryRun) { $cmdArgs += "--dry-run" }

python @cmdArgs
exit $LASTEXITCODE
