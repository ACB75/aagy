<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/audit-workspace.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "audit-workspace.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
