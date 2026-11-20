<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/sonar-audit.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "sonar-audit.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
