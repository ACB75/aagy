<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/hook-stop-capture.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "hook-stop-capture.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
