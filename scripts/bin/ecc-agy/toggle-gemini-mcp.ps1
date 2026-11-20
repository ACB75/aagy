<#
.SYNOPSIS
    Forwarding proxy towards canonical scripts/pwsh/toggle-gemini-mcp.ps1
#>
$CanonicalScript = Join-Path (Resolve-Path "$PSScriptRoot\..\..\pwsh").Path "toggle-gemini-mcp.ps1"
& $CanonicalScript @args
exit $LASTEXITCODE
