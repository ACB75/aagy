<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/disable-skill.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "disable-skill.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
