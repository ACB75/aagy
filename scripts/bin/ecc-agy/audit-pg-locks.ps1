<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/audit-pg-locks.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "audit-pg-locks.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
