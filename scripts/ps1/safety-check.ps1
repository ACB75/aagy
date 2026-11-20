<#
.SYNOPSIS
    Hook de seguridad determinista ejecutado antes de run_command (PreToolUse).
.DESCRIPTION
    Intercepta comandos de riesgo catastrófico (rm -rf /, DROP DATABASE, mkfs)
    siguiendo el contrato JSON stdin/stdout de Antigravity PreToolUse.
#>
param(
    [string]$CommandLine = ""
)

$ErrorActionPreference = "Stop"

if (-not $CommandLine -and [Console]::IsInputRedirected) {
    $rawInput = [Console]::In.ReadToEnd()
    if ($rawInput -and $rawInput.Trim()) {
        try {
            $payload = $rawInput | ConvertFrom-Json
            if ($payload.toolCall -and $payload.toolCall.args -and $payload.toolCall.args.CommandLine) {
                $CommandLine = [string]$payload.toolCall.args.CommandLine
            }
        } catch {
            # Ignorar payload no JSON y permitir por defecto si no hay comando parseable
        }
    }
}

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
            @{
                decision = "deny"
                reason   = "[SAFETY-GUARD] Comando bloqueado por regla de seguridad: $CommandLine"
            } | ConvertTo-Json -Compress
            exit 0
        }
    }
}

@{ decision = "allow" } | ConvertTo-Json -Compress
exit 0
