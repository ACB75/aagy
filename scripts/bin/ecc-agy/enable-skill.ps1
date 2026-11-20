<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/enable-skill.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "enable-skill.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
