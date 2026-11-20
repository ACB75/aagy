<#
.SYNOPSIS
    Desactiva y retira una skill temporalmente promovida del plugin activo de Antigravity.
.DESCRIPTION
    Elimina la copia en ~/.gemini/config/plugins/ecc-agy/skills/<name> y remueve
    la entrada de .active_promotions.json.
.PARAMETER Name
    Nombre de la skill promovida a retirar.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Name
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\py\skill_promotion.py"

python $PyScript --demote $Name
exit $LASTEXITCODE
