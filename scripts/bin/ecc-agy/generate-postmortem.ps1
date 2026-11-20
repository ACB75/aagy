<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/generate-postmortem.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "generate-postmortem.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
