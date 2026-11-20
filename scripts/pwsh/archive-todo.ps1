<#
.SYNOPSIS
    Archiva tareas completadas (- [x]) desde TODO.md hacia el directorio done configurado en docs-map.json.
.DESCRIPTION
    Script rutinario para Windows 11 (pwsh) que delega en scripts/py/archive_todo.py.
    Resuelve dinámicamente TODO.md y done/ vía .governance/docs-map.json (con fallback clásico).
.PARAMETER TodoPath
    Ruta opcional al archivo TODO principal (si se omite, lee .governance/docs-map.json).
.PARAMETER DoneDir
    Directorio destino opcional de archivo (si se omite, lee .governance/docs-map.json).
.PARAMETER Complete
    Título o substring de la tarea específica a archivar.
.PARAMETER AllCompleted
    Archiva todas las tareas marcadas como completadas (- [x]).
.PARAMETER Notes
    Notas adicionales de entregables o verificación a registrar.
.PARAMETER DryRun
    Muestra qué tareas se archivarían sin alterar el disco.
.EXAMPLE
    pwsh -File scripts/pwsh/archive-todo.ps1 -AllCompleted
#>
param(
    [string]$TodoPath = "",
    [string]$DoneDir = "",
    [string]$Complete,
    [switch]$AllCompleted,
    [string]$Notes,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = (Resolve-Path "$ScriptDir\..\..").Path
$PyScript = Join-Path $WorkspaceRoot "scripts\py\archive_todo.py"
$DocsMapScript = Join-Path $WorkspaceRoot "scripts\py\docs_map.py"

if (-not (Test-Path $PyScript)) {
    Write-Error "[ERROR] No se encuentra el script en $PyScript"
    exit 1
}

function Resolve-ConfiguredPath([string]$ExplicitPath, [string]$DocsKey, [string]$FallbackRel) {
    if (-not [string]::IsNullOrWhiteSpace($ExplicitPath)) {
        if ([System.IO.Path]::IsPathRooted($ExplicitPath)) {
            return $ExplicitPath
        }
        return Join-Path $WorkspaceRoot $ExplicitPath
    }
    if (Test-Path $DocsMapScript) {
        $resolved = (python $DocsMapScript --repo-root $WorkspaceRoot --key $DocsKey 2>$null)
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
            return $resolved.Trim()
        }
    }
    return Join-Path $WorkspaceRoot $FallbackRel
}

$ResolvedTodo = Resolve-ConfiguredPath $TodoPath "todo" "doc/TODO.md"
$ResolvedDone = Resolve-ConfiguredPath $DoneDir "todo_done" "doc/TODO_DONE"

$ArgsList = @($PyScript, "--repo-root", $WorkspaceRoot, "--todo", $ResolvedTodo, "--done-dir", $ResolvedDone)

if ($Complete) {
    $ArgsList += @("--complete", $Complete)
}
if ($AllCompleted) {
    $ArgsList += "--all-completed"
}
if ($Notes) {
    $ArgsList += @("--notes", $Notes)
}
if ($DryRun) {
    $ArgsList += "--dry-run"
}

python @ArgsList
$pyExit = $LASTEXITCODE

if ($pyExit -eq 0 -and -not $DryRun) {
    $lintScript = Join-Path $ScriptDir "lint-markdown.ps1"
    if (Test-Path $lintScript) {
        if (Test-Path $ResolvedDone) {
            pwsh -NoProfile -File $lintScript -Target $ResolvedDone -Fix >$null 2>&1
        }
        if (Test-Path $ResolvedTodo) {
            pwsh -NoProfile -File $lintScript -Target $ResolvedTodo -Fix >$null 2>&1
        }
    }
}

exit $pyExit
