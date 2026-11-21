<#
.SYNOPSIS
    Backlog compartido entre Claude Code (aagy-ecc) y Antigravity (aagy).
.DESCRIPTION
    Delega en scripts/py/backlog.py y opera sobre el repositorio de la carpeta actual.
    Todos los argumentos se pasan tal cual (list, next, claim, checkpoint, handoff, done, epic ...).
.EXAMPLE
    pwsh -File scripts/ps1/backlog.ps1 list
    pwsh -File scripts/ps1/backlog.ps1 claim mi-tarea --agent agy --worktree
    pwsh -File scripts/ps1/backlog.ps1 handoff --agent claude --note "falta el test de integración"
#>
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyScript = Join-Path $ScriptDir "..\py\backlog.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "[ERROR] No se encuentra el script en $PyScript"
    exit 1
}

python $PyScript @args
exit $LASTEXITCODE
