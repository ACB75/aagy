<#
.SYNOPSIS
    Hook de seguridad determinista ejecutado antes de run_command (PreToolUse).
.DESCRIPTION
    Intercepta comandos de riesgo catastrófico (rm -rf /, DROP DATABASE, mkfs).
#>
param(
    [string]$CommandLine = ""
)

$ErrorActionPreference = "Stop"

if ($CommandLine) {
    $Dangerous = @(
        "rm\s+-rf\s+/[^a-zA-Z0-9_]?",
        "mkfs(\.[a-zA-Z0-9]+)?\s+",
        "DROP\s+DATABASE",
        ">\s*/dev/sd[a-z]",
        "dd\s+if=.*of=/dev/sd"
    )
    foreach ($pattern in $Dangerous) {
        if ($CommandLine -match $pattern) {
            Write-Error "[SAFETY-GUARD] Comando bloqueado por regla de seguridad: $CommandLine"
            exit 1
        }
    }
}
exit 0
