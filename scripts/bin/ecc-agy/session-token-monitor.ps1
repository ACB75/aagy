<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/session-token-monitor.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "session-token-monitor.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
