<#
.SYNOPSIS
    Hook pasivo Stop de captura de aprendizajes y telemetría sub-segundo (< 500 ms).
.DESCRIPTION
    Invoca scripts/py/self_improve.py --capture-stop de forma no bloqueante y devuelve {}.
#>
param(
    [string]$RepoRoot = ""
)

$ErrorActionPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DefaultRoot = (Resolve-Path "$ScriptDir\..\..").Path
$TargetRoot = if ($RepoRoot) { $RepoRoot } else { $DefaultRoot }
$PyScript = Join-Path $DefaultRoot "scripts\py\self_improve.py"

if (Test-Path $PyScript) {
    $out = python $PyScript --capture-stop --repo-root $TargetRoot 2>$null
    if ($LASTEXITCODE -eq 0 -and $out) {
        Write-Output $out
        exit 0
    }
}

Write-Output "{}"
exit 0
