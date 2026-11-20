<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/sync-ideas-todo.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "sync-ideas-todo.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
