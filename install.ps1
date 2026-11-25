<#
.SYNOPSIS
    Instalador Multi-Distribución del Ecosistema Anything Antigravity (aagy / aagy-ecc).
.DESCRIPTION
    Permite desplegar de forma interactiva o parametrizada cualquiera de las distribuciones:
      - agy      : Distribución nativa para Google Antigravity & Gemini (~/.gemini/config/plugins/aagy).
      - claude   : Distribución hermana aagy-ecc para Claude Code: sincroniza el espejo y la instala
                   como plugin (marketplace local). Con -Destination copia además la plantilla
                   de proyecto (CLAUDE.md + .claude/).
      - aagy-ecc : Alias explícito de 'claude'.
.PARAMETER Target
    agy | claude | aagy-ecc
.PARAMETER Profile
    minimal (por defecto: Nivel 1 Global con 16 core skills universales) |
    full    (despliegue del catálogo completo optimizado a <=140c)
.PARAMETER Destination
    agy: directorio de destino (por defecto ~/.gemini/config/plugins/aagy).
    claude / aagy-ecc: proyecto opcional donde copiar la plantilla CLAUDE.md + .claude/.
.PARAMETER NoPlugin
    claude / aagy-ecc: solo sincroniza (y copia la plantilla), sin instalar el plugin en Claude Code.
.EXAMPLE
    pwsh -File install.ps1 -Target agy -Profile minimal
    pwsh -File install.ps1 -Target aagy-ecc
    pwsh -File install.ps1 -Target aagy-ecc -Destination <ruta-del-repo>
#>
param(
    [ValidateSet("claude", "aagy-ecc", "agy")]
    [string]$Target = "agy",

    [ValidateSet("minimal", "full")]
    [string]$Profile = "minimal",

    [string]$Destination,

    [switch]$NoPlugin
)

$ErrorActionPreference = "Stop"
$ScriptRoot = $PSScriptRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "         ANYTHING ANTIGRAVITY (AAGY / AAGY-ECC) INSTALLER        " -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Distribución seleccionada: $Target | Perfil: $Profile" -ForegroundColor Yellow

if ($Target -eq "aagy-ecc") {
    $Target = "claude"
}

switch ($Target) {
    "claude" {
        $sourceDir = Join-Path $ScriptRoot "aagy-ecc"

        # 1. Regenerar el espejo (skills, agentes, reglas y motores Python) dentro de aagy-ecc/
        Write-Host "[+] Sincronizando aagy-ecc desde la raíz del repositorio..." -ForegroundColor Green
        python (Join-Path $ScriptRoot "scripts\py\sync_aagy_ecc.py") --repo-root $ScriptRoot
        if ($LASTEXITCODE -ne 0) { throw "Falló la sincronización de aagy-ecc." }

        # 1b. Manifiesto de instalación para /aagy-ecc-doctor (viaja con el plugin a la caché de Claude Code)
        python (Join-Path $ScriptRoot "scripts\py\install_manifest.py") write --dest $sourceDir --harness claude --profile full --repo-root $ScriptRoot

        # 2. Instalar como plugin de Claude Code (marketplace local + plugin)
        $runtimeAgentsDir = Join-Path $sourceDir ".agents"
        if (Test-Path $runtimeAgentsDir) {
            Remove-Item -Path $runtimeAgentsDir -Recurse -Force -ErrorAction SilentlyContinue
        }
        if ($NoPlugin) {
            Write-Host "[i] -NoPlugin: se omite la instalación del plugin en Claude Code." -ForegroundColor Yellow
        } elseif (Get-Command claude -ErrorAction SilentlyContinue) {
            Write-Host "[+] Registrando marketplace local e instalando aagy-ecc en Claude Code..." -ForegroundColor Green
            claude plugin marketplace add $sourceDir
            claude plugin install aagy-ecc@aagy-ecc
        } else {
            Write-Host "[!] No se encontró el CLI 'claude'. Instala el plugin manualmente con:" -ForegroundColor Yellow
            Write-Host "    claude plugin marketplace add `"$sourceDir`"" -ForegroundColor Yellow
            Write-Host "    claude plugin install aagy-ecc@aagy-ecc" -ForegroundColor Yellow
        }

        # 3. Opcional: plantilla de proyecto (CLAUDE.md + .claude/) en un proyecto destino
        if ($Destination) {
            $templateDir = Join-Path $sourceDir "project-template"
            Write-Host "[+] Copiando plantilla de proyecto (CLAUDE.md + .claude/) a: $Destination" -ForegroundColor Green
            if (-not (Test-Path $Destination)) {
                New-Item -ItemType Directory -Force -Path $Destination | Out-Null
            }
            Copy-Item -Path (Join-Path $templateDir "CLAUDE.md") -Destination $Destination -Force
            Copy-Item -Path (Join-Path $templateDir ".claude") -Destination $Destination -Recurse -Force
        }
        Write-Host "[✓] Distribución aagy-ecc lista." -ForegroundColor Green
    }
    "agy" {
        if (-not $Destination) {
            $Destination = Join-Path $env:USERPROFILE ".gemini\config\plugins\aagy"
        }
        Write-Host "[+] Desplegando plugin Anything Antigravity (aagy) en: $Destination" -ForegroundColor Green

        $syncScript = Join-Path $ScriptRoot "scripts\ps1\aagy-sync.ps1"
        $phase = if ($Profile -eq "full") { "all" } else { "generic" }
        pwsh -NoProfile -File $syncScript -Phase $phase -Clean
        Write-Host "[✓] Plugin aagy instalado en Antigravity bajo perfil '$Profile'." -ForegroundColor Green
    }
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "Operación completada exitosamente." -ForegroundColor Cyan
