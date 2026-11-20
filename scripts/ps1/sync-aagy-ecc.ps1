<#
.SYNOPSIS
    Sincroniza la distribución hermana aagy-ecc (Claude Code) desde la raíz del repositorio.
.DESCRIPTION
    Copia skills/, agents/, rules/AGENTS.md y los motores Python que usan los hooks
    dentro de aagy-ecc/, porque Claude Code solo carga archivos del propio plugin.
    Wrapper de scripts/py/sync_aagy_ecc.py.
.PARAMETER Check
    Solo verifica la deriva sin escribir (exit 0 / 1).
.PARAMETER Json
    Emitir salida en formato JSON estructurado.
.EXAMPLE
    pwsh -NoProfile -File scripts/ps1/sync-aagy-ecc.ps1
    pwsh -NoProfile -File scripts/ps1/sync-aagy-ecc.ps1 -Check
#>
[CmdletBinding()]
param(
    [switch]$Check,
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $ProjectRoot "scripts\py\sync_aagy_ecc.py"

$ArgsList = @("--repo-root", $ProjectRoot)
if ($Check) { $ArgsList += "--check" }
if ($Json) { $ArgsList += "--json" }

python $PyScript @ArgsList
exit $LASTEXITCODE
