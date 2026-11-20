<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/map-docs.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "map-docs.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
