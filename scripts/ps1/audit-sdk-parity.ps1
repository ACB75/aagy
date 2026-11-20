<#
.SYNOPSIS
    Linter estático de paridad de contratos entre microservicios y home-lab-sdk.
.DESCRIPTION
    Inspecciona rutas y modelos en services/ o cluster/ y certifica que home-lab-sdk
    posee los clientes correspondientes, previniendo contract drift.
.PARAMETER Root
    Ruta raíz opcional del repositorio o monorepo a auditar.
.PARAMETER ServicesDir
    Ruta opcional al directorio de microservicios.
.PARAMETER SdkDir
    Ruta opcional al directorio de home-lab-sdk.
.PARAMETER NoStrict
    No retornar código de error 1 ante divergencias.
.PARAMETER Json
    Emitir salida en formato JSON estructurado.
#>
[CmdletBinding()]
param(
    [string]$Root = "",
    [string]$ServicesDir = "",
    [string]$SdkDir = "",
    [switch]$NoStrict,
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\py\audit_sdk_parity.py"

$ArgsList = @()
if ($Root) {
    $ArgsList += @("--root", $Root)
}
if ($ServicesDir) {
    $ArgsList += @("--services-dir", $ServicesDir)
}
if ($SdkDir) {
    $ArgsList += @("--sdk-dir", $SdkDir)
}
if ($NoStrict) {
    $ArgsList += "--no-strict"
}
if ($Json) {
    $ArgsList += "--json"
}

python $PyScript @ArgsList
exit $LASTEXITCODE
