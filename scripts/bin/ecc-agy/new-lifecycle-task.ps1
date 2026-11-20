<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/new-lifecycle-task.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "new-lifecycle-task.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
