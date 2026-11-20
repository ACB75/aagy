<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/git-flow-helper.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "git-flow-helper.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
