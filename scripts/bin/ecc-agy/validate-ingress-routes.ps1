<#
.SYNOPSIS
    Validador estático de congruencia entre Ingress Traefik, Split-DNS y catálogo /portal.
.DESCRIPTION
    Certifica que cualquier microservicio con etiquetas Traefik tenga su registro
    en CoreDNS y su entrada correspondiente en el catálogo de /portal.
.PARAMETER Root
    Ruta raíz opcional del repositorio a validar.
.PARAMETER Fix
    Generar sugerencias de configuración exacta para DNS y el catálogo Go de /portal.
.PARAMETER NoStrict
    No retornar código de salida 1 ante discrepancias.
.PARAMETER Json
    Emitir salida en formato JSON estructurado.
#>
[CmdletBinding()]
param(
    [string]$Root = "",
    [switch]$Fix,
    [switch]$NoStrict,
    [switch]$Json
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\ecc-agy\validate_ingress_routes.py"

$ArgsList = @()
if ($Root) {
    $ArgsList += @("--root", $Root)
}
if ($Fix) {
    $ArgsList += "--fix"
}
if ($NoStrict) {
    $ArgsList += "--no-strict"
}
if ($Json) {
    $ArgsList += "--json"
}

python $PyScript @ArgsList
exit $LASTEXITCODE
