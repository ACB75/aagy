<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/security-audit.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "security-audit.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
