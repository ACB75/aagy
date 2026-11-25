<#
.SYNOPSIS
    Fase 4: envoltorio fino de scripts/py/complete_task_pr.py (motor único de aagy y aagy-ecc).
.DESCRIPTION
    Revisión previa, gate de calidad (ci_local.py y los checks del repo), commit, push y PR.
    Sin auto-merge: solo fusiona con -Merge, cuando una persona lo pide.
.PARAMETER ReviewOnly
    Muestra la revisión previa sin cambiar nada.
.PARAMETER Yes
    No pide confirmación.
.PARAMETER Merge
    Fusiona la PR con squash y recicla el worktree (solo si una persona lo pide).
.EXAMPLE
    pwsh -File scripts/ps1/complete-task-pr.ps1 -ReviewOnly
    pwsh -File scripts/ps1/complete-task-pr.ps1 -Title "[feat]-[aagy]: <título>" -Issue 61 -Yes
#>
param(
    [string]$Title,
    [string]$Body,
    [string]$TargetBranch = "main",
    [int]$Issue = 0,
    [switch]$ReviewOnly,
    [switch]$Yes,
    [switch]$Merge,
    [switch]$SkipGate,
    [switch]$Help
)

$engine = Join-Path $PSScriptRoot "..\py\complete_task_pr.py"
$python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }
$pyArgs = @($engine, "--target", $TargetBranch)
if ($Help) { $pyArgs += "--help" }
if ($Title) { $pyArgs += @("--title", $Title) }
if ($Body) { $pyArgs += @("--body", $Body) }
if ($Issue -gt 0) { $pyArgs += @("--issue", "$Issue") }
if ($ReviewOnly) { $pyArgs += "--review-only" }
if ($Yes) { $pyArgs += "--yes" }
if ($Merge) { $pyArgs += "--merge" }
if ($SkipGate) { $pyArgs += "--skip-gate" }

& $python @pyArgs
exit $LASTEXITCODE
