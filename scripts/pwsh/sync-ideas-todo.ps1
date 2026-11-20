<#
.SYNOPSIS
    Ingesta y sincronización automatizada de IDEAS.md hacia TODO.md.
.DESCRIPTION
    Script rutinario para Windows 11 (pwsh) que delega en scripts/py/sync_ideas_todo.py.
    Resuelve rutas vía .governance/docs-map.json y aplica metodología de 7 fases.
.PARAMETER Check
    Comprueba si existen ideas aprobadas pendientes de sincronizar sin modificar TODO.md.
.PARAMETER DryRun
    Simula la sincronización y muestra los resultados en consola.
.EXAMPLE
    pwsh -File scripts/bin/ecc-agy/sync-ideas-todo.ps1
    pwsh -File scripts/bin/ecc-agy/sync-ideas-todo.ps1 -Check
#>
[CmdletBinding()]
param(
    [switch]$Check,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $WorkspaceRoot "scripts\py\sync_ideas_todo.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "[ERROR] No se encuentra el script en $PyScript"
    exit 1
}

$cmdArgs = @("--repo-root", $WorkspaceRoot)
if ($Check) { $cmdArgs += "--check" }
if ($DryRun) { $cmdArgs += "--dry-run" }

python $PyScript @cmdArgs
exit $LASTEXITCODE
