<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/manage-instincts.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "manage-instincts.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
