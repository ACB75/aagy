<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/archive-todo.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "archive-todo.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
