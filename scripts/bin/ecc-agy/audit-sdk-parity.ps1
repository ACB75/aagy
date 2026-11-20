<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/audit-sdk-parity.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "audit-sdk-parity.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
