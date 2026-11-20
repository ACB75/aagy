<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/audit-plugin-parity.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "audit-plugin-parity.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
