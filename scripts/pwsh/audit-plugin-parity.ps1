<#
.SYNOPSIS
    Linter estático de paridad multi-harness entre Anything Antigravity (aagy) y Claude Code (ecc).
.DESCRIPTION
    Inspecciona los manifiestos y estructura de plugins en la raíz (Antigravity) y ecc/ (Claude Code)
    certificando que ambos arneses mantienen capacidades simétricas y sin deriva de contratos.
.PARAMETER RepoRoot
    Ruta raíz opcional del repositorio a auditar.
.PARAMETER CheckOnly
    Solo verifica y retorna código de salida 0 o 1 sin reporte verboso.
.PARAMETER Json
    Emitir salida en formato JSON estructurado.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [switch]$CheckOnly,
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $ProjectRoot "scripts\py\audit_plugin_parity.py"

$ArgsList = @()
if ($RepoRoot) {
    $ArgsList += @("--repo-root", $RepoRoot)
} else {
    $ArgsList += @("--repo-root", $ProjectRoot)
}
if ($CheckOnly) {
    $ArgsList += "--check-only"
}
if ($Json) {
    $ArgsList += "--json"
}

python $PyScript @ArgsList
exit $LASTEXITCODE
