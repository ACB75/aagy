<#
.SYNOPSIS
    Hook determinista ejecutado tras write_file y edit_file (PostToolUse).
.DESCRIPTION
    Ejecuta lint-markdown.ps1 automáticamente sobre archivos Markdown modificados
    siguiendo el contrato JSON stdin/stdout de Antigravity PostToolUse.
#>
param(
    [string]$Path = ""
)

$ErrorActionPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PayloadCwd = ""

if (-not $Path -and [Console]::IsInputRedirected) {
    $rawInput = [Console]::In.ReadToEnd()
    if ($rawInput -and $rawInput.Trim()) {
        try {
            $payload = $rawInput | ConvertFrom-Json
            if ($payload.toolCall -and $payload.toolCall.args -and $payload.toolCall.args.Path) {
                $Path = [string]$payload.toolCall.args.Path
            }
            if ($payload.cwd) {
                $PayloadCwd = [string]$payload.cwd
            }
        } catch {
            # Ignorar payload no JSON
        }
    }
}

if ($Path -and $Path.EndsWith(".md", [System.StringComparison]::OrdinalIgnoreCase) -and (Test-Path $Path)) {
    $Linter = Join-Path $RepoRoot "scripts\pwsh\lint-markdown.ps1"
    if (-not (Test-Path $Linter) -and $PayloadCwd) {
        $Linter = Join-Path $PayloadCwd "scripts\pwsh\lint-markdown.ps1"
    }
    if (Test-Path $Linter) {
        pwsh -NoProfile -File $Linter -Target $Path -Fix | Out-Null
    }
}

Write-Output "{}"
exit 0
