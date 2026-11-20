<#
.SYNOPSIS
    Gestor de instintos y aprendizajes del proyecto (.agents/instincts/).
.DESCRIPTION
    Guarda, lista y exporta instintos sin inflar AGENTS.md.
.PARAMETER Subcommand
    Comando a ejecutar: save, list o export.
.EXAMPLE
    pwsh -File scripts/bin/ecc-agy/manage-instincts.ps1 list
    pwsh -File scripts/bin/ecc-agy/manage-instincts.ps1 save --id postgres-lock --trigger postgres --learning "Usar CREATE INDEX CONCURRENTLY"
    pwsh -File scripts/bin/ecc-agy/manage-instincts.ps1 export
#>
param(
    [Parameter(Position=0)]
    [string]$Subcommand = "list",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\py\instinct_manager.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "[ERROR] No se encuentra $PyScript"
    exit 1
}

$Arguments = @($PyScript, $Subcommand) + $RemainingArgs
python @Arguments
exit $LASTEXITCODE
