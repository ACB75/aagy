<#
.SYNOPSIS
    Safety gate (PreToolUse): envoltorio fino de scripts/py/hook_safety.py --format agy.
.DESCRIPTION
    El motor único es hook_safety.py (los dos plugins). Lee el payload de Antigravity por stdin,
    o el comando con -CommandLine para probarlo a mano.
#>
param([string]$CommandLine = "")

$engine = Join-Path $PSScriptRoot "..\py\hook_safety.py"
$python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }
$payload = if ($CommandLine) { @{ toolCall = @{ args = @{ CommandLine = $CommandLine } } } | ConvertTo-Json -Compress -Depth 4 }
           elseif ([Console]::IsInputRedirected) { [Console]::In.ReadToEnd() } else { "{}" }
$payload | & $python $engine --format agy
exit 0
