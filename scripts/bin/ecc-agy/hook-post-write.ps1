<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/hook-post-write.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "hook-post-write.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
