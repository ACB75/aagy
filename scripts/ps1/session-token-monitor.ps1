<#
.SYNOPSIS
    Monitor de telemetría de presupuesto de tokens en sesión activa de Antigravity.
.DESCRIPTION
    Inspecciona transcript.jsonl y alerta si la sesión supera el umbral de tokens
    recomendando la ejecución de /compact.
.PARAMETER Threshold
    Umbral máximo de tokens antes de alertar (def: 45000).
.PARAMETER Json
    Emitir salida en formato JSON estructurado.
.PARAMETER AlertOnly
    Modo silencioso salvo si se excede el umbral.
.PARAMETER Transcript
    Ruta opcional al archivo transcript.jsonl.
#>
[CmdletBinding()]
param(
    [int]$Threshold = 45000,
    [switch]$Json,
    [switch]$AlertOnly,
    [string]$Transcript = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\py\session_token_monitor.py"

$ArgsList = @()
if ($Transcript) {
    $ArgsList += @("--transcript", $Transcript)
}
if ($Threshold) {
    $ArgsList += @("--threshold", $Threshold)
}
if ($Json) {
    $ArgsList += "--json"
}
if ($AlertOnly) {
    $ArgsList += "--alert-only"
}

python $PyScript @ArgsList
exit $LASTEXITCODE
