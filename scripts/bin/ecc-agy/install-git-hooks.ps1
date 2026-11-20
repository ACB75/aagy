<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/install-git-hooks.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "install-git-hooks.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
