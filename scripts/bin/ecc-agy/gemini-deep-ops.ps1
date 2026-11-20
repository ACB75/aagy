<#
.SYNOPSIS
    CLI determinista para diagnóstico multimodal y análisis de logs con Gemini.
.DESCRIPTION
    Invoca scripts/ecc-agy/gemini_deep_ops.py para diagnosticar volcados de logs y generar postmortems 5W.
.PARAMETER Subcommand
    Comando a ejecutar: status, analyze-log o postmortem.
.EXAMPLE
    pwsh -File scripts/bin/ecc-agy/gemini-deep-ops.ps1 status
    pwsh -File scripts/bin/ecc-agy/gemini-deep-ops.ps1 analyze-log --file path/to/error.log
    pwsh -File scripts/bin/ecc-agy/gemini-deep-ops.ps1 postmortem --issue fix/cluster/oom-123 --file path/to/crash.log
#>
param(
    [Parameter(Position=0)]
    [string]$Subcommand = "status",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\ecc-agy\gemini_deep_ops.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "[ERROR] No se encuentra $PyScript"
    exit 1
}

$Arguments = @($PyScript, $Subcommand) + $RemainingArgs
python @Arguments
exit $LASTEXITCODE
