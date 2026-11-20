<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/auto-evolve.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "auto-evolve.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
