<#
.SYNOPSIS
    Instala o desinstala los Git hooks nativos (pre-commit, commit-msg, pre-push) en .git/hooks/.
.DESCRIPTION
    Copia scripts/py/hooks/* a .git/hooks/, asegurando validación determinista
    de mensajes de commit y archivos Markdown staged en cada confirmación.
.PARAMETER Uninstall
    Elimina los hooks instalados por aagy en .git/hooks/.
.PARAMETER Force
    Sobrescribe hooks existentes sin confirmación interactiva.
#>
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
$GitHooksDir = Join-Path $RepoRoot ".git\hooks"
$SourceHooksDir = Join-Path $RepoRoot "scripts\py\hooks"

if (-not (Test-Path $GitHooksDir)) {
    Write-Error "[ERROR] Directorio .git/hooks no encontrado en $RepoRoot. ¿Es este un repositorio Git?"
    exit 1
}

$HookNames = @("pre-commit", "commit-msg", "pre-push")

if ($Uninstall) {
    Write-Host "[+] Desinstalando Git hooks de aagy en $GitHooksDir..."
    foreach ($name in $HookNames) {
        $target = Join-Path $GitHooksDir $name
        if (Test-Path $target) {
            Remove-Item $target -Force
            Write-Host "  [-] Eliminado: $name"
        }
    }
    Write-Host "[OK] Git hooks desinstalados con éxito."
    exit 0
}

Write-Host "[+] Instalando Git hooks nativos de aagy en $GitHooksDir..."

foreach ($name in $HookNames) {
    $src = Join-Path $SourceHooksDir $name
    $dst = Join-Path $GitHooksDir $name

    if (-not (Test-Path $src)) {
        Write-Warning "Hook origen no encontrado: $src"
        continue
    }

    if ((Test-Path $dst) -and -not $Force) {
        $backup = "$dst.bak"
        Copy-Item $dst $backup -Force
        Write-Host "  [i] Backup creado: $name -> $name.bak"
    }

    Copy-Item $src $dst -Force
    Write-Host "  [+] Instalado hook: $name"
}

Write-Host "[OK] Git hooks (pre-commit, commit-msg, pre-push) instalados con éxito."
exit 0
