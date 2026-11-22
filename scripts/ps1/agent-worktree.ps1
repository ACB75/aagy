<#
.SYNOPSIS
    Un git worktree fijo por agente: <repo>-aagy (Antigravity) y <repo>-aagy-ecc (Claude Code).
.DESCRIPTION
    Delega en scripts/py/agent_worktree.py y opera sobre el repositorio de la carpeta actual.
    Pasa stdin al script (lo usa el hook PreToolUse 'guard').
.EXAMPLE
    pwsh -File scripts/ps1/agent-worktree.ps1 init
    pwsh -File scripts/ps1/agent-worktree.ps1 status
    pwsh -File scripts/ps1/agent-worktree.ps1 recycle --agent agy
#>
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PyScript = Join-Path $ScriptDir "..\py\agent_worktree.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "[ERROR] No se encuentra el script en $PyScript"
    exit 1
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
if (-not $python) {
    if ($args -contains "guard") { @{ decision = "allow" } | ConvertTo-Json -Compress; exit 0 }
    Write-Error "[ERROR] No se encuentra Python."
    exit 1
}

if ([Console]::IsInputRedirected) {
    $stdinText = [Console]::In.ReadToEnd()
    $stdinText | & $python.Source $PyScript @args
} else {
    & $python.Source $PyScript @args
}
exit $LASTEXITCODE
