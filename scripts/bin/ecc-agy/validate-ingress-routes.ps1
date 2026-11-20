<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/validate-ingress-routes.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "validate-ingress-routes.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
