<#
.SYNOPSIS
    Linter Markdown (PostToolUse): envoltorio fino de scripts/py/hook_post_write.py --format agy.
#>
param([string]$Path = "")

$engine = Join-Path $PSScriptRoot "..\py\hook_post_write.py"
$python = if (Get-Command python -ErrorAction SilentlyContinue) { "python" } else { "python3" }
$payload = if ($Path) { @{ toolCall = @{ args = @{ Path = $Path } } } | ConvertTo-Json -Compress -Depth 4 }
           elseif ([Console]::IsInputRedirected) { [Console]::In.ReadToEnd() } else { "{}" }
$payload | & $python $engine --format agy
exit 0
