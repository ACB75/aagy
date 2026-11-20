<#
.SYNOPSIS
    Hook determinista ejecutado tras write_file y edit_file (PostToolUse).
.DESCRIPTION
    Ejecuta lint-markdown.ps1 automáticamente sobre archivos Markdown modificados.
#>
param(
    [string]$Path = ""
)

$ErrorActionPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..\..").Path

if ($Path -and $Path.EndsWith(".md", [System.StringComparison]::OrdinalIgnoreCase) -and (Test-Path $Path)) {
    $Linter = Join-Path $RepoRoot "scripts\bin\ecc-agy\lint-markdown.ps1"
    if (Test-Path $Linter) {
        pwsh -File $Linter -Target $Path -Fix | Out-Null
    }
}
exit 0
