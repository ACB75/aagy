<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/format-commit.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "format-commit.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
