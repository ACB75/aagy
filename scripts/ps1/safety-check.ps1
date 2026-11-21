<#
.SYNOPSIS
    Hook de seguridad determinista ejecutado antes de run_command (PreToolUse).
.DESCRIPTION
    Intercepta comandos de riesgo catastrófico (rm -rf /, DROP DATABASE, mkfs)
    y los comandos git que crean o publican ramas fuera de la convención
    <tipo>/<proyecto>/<nombre> (scripts/py/validate_branch.py --git-command),
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

    # Guardarraíl de ramas: mismo validador que el hook de aagy-ecc (fail-open si no hay Python)
    if ($CommandLine -match '(^|[\s;&|])git(\.exe)?\s') {
        $validator = Join-Path (Split-Path $PSScriptRoot -Parent) "py/validate_branch.py"
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) { $python = Get-Command python3 -ErrorAction SilentlyContinue }
        if ($python -and (Test-Path $validator)) {
            try {
                $branchReason = & $python.Source $validator --git-command $CommandLine 2>$null
                if ($LASTEXITCODE -eq 1 -and $branchReason) {
                    @{
                        decision = "deny"
                        reason   = (($branchReason | Out-String).Trim())
                    } | ConvertTo-Json -Compress
                    exit 0
                }
            } catch {
                # fail-open
            }
        }
    }
}

@{ decision = "allow" } | ConvertTo-Json -Compress
exit 0
