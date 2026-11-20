<#
.SYNOPSIS
    Auditoría, mapeo y validación de enlaces relativos en documentación Markdown y docs-map.json.
.DESCRIPTION
    Script rutinario para Windows 11 (pwsh) que delega en scripts/py/map_docs.py.
    Detecta enlaces rotos en /doc y verifica integridad de .governance/docs-map.json.
.PARAMETER DocRoot
    Directorio o archivo raíz opcional a auditar (si se omite, resuelve desde docs-map.json).
.EXAMPLE
    pwsh -File scripts/bin/ecc-agy/map-docs.ps1
    pwsh -File scripts/bin/ecc-agy/map-docs.ps1 -DocRoot "doc/02-adr"
#>
[CmdletBinding()]
param(
    [string]$DocRoot = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $WorkspaceRoot "scripts\py\map_docs.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "[ERROR] No se encuentra el script en $PyScript"
    exit 1
}

$cmdArgs = @("--repo-root", $WorkspaceRoot, "--check-docs-map")
if (-not [string]::IsNullOrWhiteSpace($DocRoot)) {
    $resolvedRoot = if ([System.IO.Path]::IsPathRooted($DocRoot)) { $DocRoot } else { Join-Path $WorkspaceRoot $DocRoot }
    $cmdArgs += @("--doc-root", $resolvedRoot)
}

python $PyScript @cmdArgs
exit $LASTEXITCODE
