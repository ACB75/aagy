<#
.SYNOPSIS
    Promueve una skill especializada de Tier 2 al plugin activo de Antigravity (Tier 1).
.DESCRIPTION
    Copia skills/<name> a ~/.gemini/config/plugins/aagy/skills/<name>, valida frontmatter
    y registra la promoción en .active_promotions.json.
.PARAMETER Name
    Nombre de la skill a activar/promover (ej. chrome-devtools, generative_ui).
.PARAMETER List
    Lista todas las skills temporalmente promovidas.
#>
[CmdletBinding()]
param(
    [string]$Name = "",
    [switch]$List
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $RepoRoot "scripts\py\skill_promotion.py"

if ($List -or -not $Name) {
    python $PyScript --list
    exit $LASTEXITCODE
}

python $PyScript --promote $Name
exit $LASTEXITCODE
