<#
.SYNOPSIS
    Analizador estático de bloqueos DDL para PostgreSQL LTS en Home-Lab.
.DESCRIPTION
    Escanea archivos de migración SQL buscando operaciones que tomen bloqueos
    ACCESS EXCLUSIVE prolongados o causen reescrituras de tabla completas.
.PARAMETER File
    Ruta a un archivo .sql específico a auditar.
.PARAMETER Dir
    Ruta a un directorio que contenga archivos .sql.
.PARAMETER Root
    Ruta raíz del repositorio a escanear.
.PARAMETER NoStrict
    No retornar código de salida 1 ante riesgos MEDIUM.
.PARAMETER Json
    Emitir salida en formato JSON estructurado.
#>
[CmdletBinding()]
param(
    [string]$File = "",
    [string]$Dir = "",
    [string]$Root = "",
    [switch]$NoStrict,
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\py\audit_pg_locks.py"

$ArgsList = @()
if ($File) {
    $ArgsList += @("--file", $File)
}
if ($Dir) {
    $ArgsList += @("--dir", $Dir)
}
if ($Root) {
    $ArgsList += @("--root", $Root)
}
if ($NoStrict) {
    $ArgsList += "--no-strict"
}
if ($Json) {
    $ArgsList += "--json"
}

python $PyScript @ArgsList
exit $LASTEXITCODE
