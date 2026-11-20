<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/gemini-deep-ops.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "gemini-deep-ops.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
