<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/lint-markdown.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "lint-markdown.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
