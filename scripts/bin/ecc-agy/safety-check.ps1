<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/safety-check.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "safety-check.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
