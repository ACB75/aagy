<#
.SYNOPSIS
    Motor Unificado y Agnóstico de Autodescubrimiento y Automejora (aagy / aagy).
.DESCRIPTION
    Delega en scripts/py/self_improve.py para descubrir patrones repetitivos,
    revisar candidatos contra AgentShield y el Hard Gate de presupuesto de tokens,
    ejecutar smoke-tests y promover artefactos tras confirmación explícita.
.PARAMETER RepoRoot
    Ruta al repositorio objetivo (por defecto: raíz del repositorio actual).
.PARAMETER PluginData
    Ruta opcional a PLUGIN_DATA global para instintos transversales.
.PARAMETER Discover
    Ejecuta el autodescubrimiento y deduplicación de patrones candidatos.
.PARAMETER Review
    Revisa un candidato por ID y valida compuertas sin promoverlo.
.PARAMETER Promote
    Promueve un candidato por ID tras validar compuertas (requiere -Confirm para escribir).
.PARAMETER Confirm
    Confirma explícitamente la escritura del artefacto promovido en disco.
.PARAMETER CaptureStop
    Ejecuta la captura pasiva del hook Stop (lee JSON por stdin y devuelve {}).
.PARAMETER Evaluate
    Evalúa una respuesta del agente en los 5 ejes de calidad.
.PARAMETER Task
    Descripción de la tarea para acompañar -Evaluate.
.PARAMETER Scope
    Filtra el ámbito de búsqueda: project, global o all.
.PARAMETER Tier
    Filtra o fuerza el nivel de artefacto (skill, script, hook, rule, agent).
.PARAMETER Limit
    Límite máximo de candidatos a procesar (por defecto: 5).
.PARAMETER MinOccurrences
    Mínimo de ocurrencias para proponer un candidato (por defecto: 2).
.PARAMETER DryRun
    Simula la validación sin escribir el artefacto final.
.PARAMETER Write
    Alias legacy (por seguridad requiere -Confirm para escribir en skills/rules/scripts).
.PARAMETER Json
    Produce salida en formato JSON estructurado.
.PARAMETER Help
    Muestra la ayuda detallada.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = "",
    [string]$PluginData = "",
    [switch]$Discover,
    [string]$Review = "",
    [string]$Promote = "",
    [switch]$Confirm,
    [switch]$CaptureStop,
    [string]$Evaluate = "",
    [string]$Task = "",
    [ValidateSet('project', 'global', 'all')]
    [string]$Scope = 'all',
    [ValidateSet('script', 'skill', 'agent', 'rule', 'hook')]
    [string]$Tier = "",
    [int]$Limit = 5,
    [int]$MinOccurrences = 2,
    [switch]$DryRun,
    [switch]$Write,
    [switch]$Json,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DefaultRoot = (Resolve-Path "$ScriptDir\..\..").Path
$TargetRoot = if ($RepoRoot) { (Resolve-Path $RepoRoot).Path } else { $DefaultRoot }
$CliScript = Join-Path $DefaultRoot "scripts\py\self_improve.py"

if (-not (Test-Path $CliScript)) {
    Write-Error "No se encontró el motor unificado en: $CliScript"
    exit 1
}

$Arguments = @($CliScript, "--repo-root", $TargetRoot, "--scope", $Scope, "--limit", "$Limit", "--min-occurrences", "$MinOccurrences")

if ($PluginData) {
    $Arguments += @("--plugin-data", $PluginData)
}
if ($Discover) {
    $Arguments += "--discover"
}
if ($Review) {
    $Arguments += @("--review", $Review)
}
if ($Promote) {
    $Arguments += @("--promote", $Promote)
}
if ($Confirm) {
    $Arguments += "--confirm"
}
if ($CaptureStop) {
    $Arguments += "--capture-stop"
}
if ($Evaluate) {
    $Arguments += @("--evaluate", $Evaluate)
}
if ($Task) {
    $Arguments += @("--task", $Task)
}
if ($Tier) {
    $Arguments += @("--tier", $Tier)
}
if ($DryRun -or (-not $Confirm -and -not $Write)) {
    $Arguments += "--dry-run"
}
if ($Json) {
    $Arguments += "--json"
}

python @Arguments
exit $LASTEXITCODE
