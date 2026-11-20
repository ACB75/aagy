<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/complete-task-pr.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "complete-task-pr.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
