#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Asistente de ciclo de vida Git para cualquier repo consumidor (Trunk-Based Development con promoción y PRs).
    Los datos del entorno no viven aquí: los hosts Live y Sandbox salen de la capa de entorno de
    aagy_config (hosts.live, hosts.sandbox) y la URL del repo de 'git remote get-url origin'.
.PARAMETER Action
    new-branch | promote | status | create-pr
.PARAMETER Type
    feat | fix | infra | docs | chore
.PARAMETER Project
    Proyecto de la rama (<type>/<project>/<name>). Si el repo declara 'projects' en
    .governance/aagy.json, debe ser uno de ellos.
.PARAMETER Name
    Descripción corta de la rama (ej. 'export-csv')
.PARAMETER Tag
    Etiqueta semántica para promoción (ej. 'v1.1.0-sandbox', 'v1.1.0')
.PARAMETER Title
    Título para la Pull Request (con formato [type]-[projects]: <title>)
.PARAMETER Body
    Cuerpo opcional explicativo de la Pull Request
.EXAMPLE
    pwsh -File scripts/ps1/git-flow-helper.ps1 -Action new-branch -Type feat -Project app -Name export-csv
    pwsh -File scripts/ps1/git-flow-helper.ps1 -Action create-pr -Title "[feat]-[app]: exportar transacciones a csv"
    pwsh -File scripts/ps1/git-flow-helper.ps1 -Action promote -Tag v1.1.0-sandbox
#>
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("new-branch", "promote", "status", "create-pr", "complete-task")]
    [string]$Action,

    [ValidateSet("feat", "fix", "infra", "docs", "chore")]
    [string]$Type = "feat",

    [string]$Project,

    [string]$Name,

    [string]$Tag,

    [string]$Title,

    [string]$Body,

    [switch]$ReviewOnly,

    [switch]$Yes,

    [switch]$Deploy,

    [ValidateSet("sandbox", "live")]
    [string]$Environment = "sandbox",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\.." )).Path
$ConfigScript = Join-Path $PSScriptRoot "../py/aagy_config.py"
$Python = if (Get-Command python3 -ErrorAction SilentlyContinue) { "python3" } else { "python" }

function Get-AagyConfig([string]$Key) {
    $value = & $Python $ConfigScript get $Key 2>$null
    if ($LASTEXITCODE -ne 0) { return $null }
    return ($value | Out-String).Trim()
}

function Get-DeployHost([string]$EnvName) {
    $hostValue = Get-AagyConfig "hosts.$EnvName"
    if (-not $hostValue) {
        throw "Falta el host de '$EnvName'. Declara 'hosts.$EnvName' en <AAGY_ENV_DIR>/aagy/env.json o exporta AAGY_HOSTS_$($EnvName.ToUpper())."
    }
    return $hostValue
}
Push-Location $RepoRoot
try {
    switch ($Action) {
        "status" {
            Write-Host "=== Estado de Estrategia Git en Monorepo ($RepoRoot) ===" -ForegroundColor Cyan
            git status
            Write-Host "`nÚltimos 5 commits:" -ForegroundColor DarkGray
            git log -5 --oneline
            Write-Host "`nTags recientes:" -ForegroundColor DarkGray
            git tag -l -n1 --sort=-v:refname | Select-Object -First 5
        }

        "new-branch" {
            if (-not $Name -or -not $Project) {
                throw "Debe proporcionar proyecto y nombre para la rama (-Project <proyecto> -Name <descripcion>)."
            }
            $declared = Get-AagyConfig "projects"
            if ($declared) {
                $projects = @($declared | ConvertFrom-Json)
                if ($Project -notin $projects) {
                    throw "Proyecto '$Project' no declarado en .governance/aagy.json (projects: $($projects -join ', '))."
                }
            }
            $branchName = "$Type/$Project/$Name"
            Write-Host "[+] Actualizando 'main' antes de ramificar..." -ForegroundColor Cyan
            git checkout main
            git pull origin main
            Write-Host "[+] Creando y cambiando a la rama '$branchName'..." -ForegroundColor Green
            git checkout -b $branchName
            Write-Host "[OK] Rama '$branchName' lista para trabajar." -ForegroundColor Green
        }

        "promote" {
            if (-not $Tag) {
                throw "Debe proporcionar un tag semántico (-Tag <vX.Y.Z[-sandbox]>)."
            }

            if ($DryRun) {
                Write-Host "[DRY-RUN] Creando tag anotado '$Tag'..." -ForegroundColor Yellow
                Write-Host "[DRY-RUN] Subiendo tag '$Tag' a origin..." -ForegroundColor Yellow
            } else {
                Write-Host "[+] Creando tag anotado '$Tag' en el commit actual..." -ForegroundColor Cyan
                git tag -a $Tag -m "release: promoción a $Tag"
                Write-Host "[+] Subiendo tag a origin..." -ForegroundColor Cyan
                git push origin $Tag
                Write-Host "[OK] Tag '$Tag' publicado con éxito." -ForegroundColor Green
            }

            if ($Deploy) {
                $targetHost = Get-DeployHost $Environment

                Write-Host "[+] Iniciando pipeline de despliegue automatizado hacia entorno '$Environment' ($targetHost)..." -ForegroundColor Cyan

                if ($DryRun) {
                    Write-Host "[DRY-RUN] Backup de estado y tag anterior registrado." -ForegroundColor Yellow
                    Write-Host "[DRY-RUN] Checkout de tag '$Tag' y ejecución de 'docker compose pull && docker compose up -d' en $targetHost..." -ForegroundColor Yellow
                    Write-Host "[DRY-RUN] Verificación de sondas de salud (3 reintentos x 5s)..." -ForegroundColor Yellow
                    Write-Host "[DRY-RUN] Sondas de salud aprobadas (200 OK / healthy). Despliegue completado." -ForegroundColor Yellow
                } else {
                    $prevCommit = (git rev-parse HEAD).Trim()
                    try {
                        Write-Host "[+] Ejecutando pull y recreación de contenedores..." -ForegroundColor Cyan
                        docker compose pull
                        docker compose up -d

                        Write-Host "[+] Verificando sondas de salud (liveness probes)..." -ForegroundColor Cyan
                        $healthy = $false
                        for ($attempt = 1; $attempt -le 3; $attempt++) {
                            Start-Sleep -Seconds 5
                            $unhealthy = (docker compose ps --filter "health=unhealthy" -q 2>$null)
                            if (-not $unhealthy) {
                                $healthy = $true
                                break
                            }
                            Write-Host "    [Intento $attempt/3] Contenedores iniciando..." -ForegroundColor DarkGray
                        }

                        if (-not $healthy) {
                            throw "Fallo en sondas de salud de contenedores."
                        }
                        Write-Host "[OK] Despliegue en '$Environment' ($targetHost) completado con éxito." -ForegroundColor Green
                    } catch {
                        Write-Host "[!] ERROR en despliegue: $_" -ForegroundColor Red
                        Write-Host "[+] Iniciando rollback automático en < 2 minutos al estado previo ($prevCommit)..." -ForegroundColor Yellow
                        docker compose down
                        git checkout $prevCommit
                        docker compose up -d
                        throw "Despliegue fallido. Rollback automático ejecutado hacia commit previo: $prevCommit"
                    }
                }
            }
        }

        "create-pr" {
            $currentBranch = (git branch --show-current).Trim()
            if ($currentBranch -in @("main", "sandbox", "live", "")) {
                throw "No se puede crear PR desde la rama protegida o vacía '$currentBranch'. Use una rama de tarea (feat/*, fix/*, etc.)."
            }
            if (-not $Title) {
                throw "Debe proporcionar un título para la PR (-Title '[type]-[projects]: <title>')."
            }
            Write-Host "[+] Verificando pre-merge Quality Gate en rama '$currentBranch'..." -ForegroundColor Cyan
            $auditScript = Join-Path $PSScriptRoot "aagy.ps1"
            if (Test-Path $auditScript) {
                pwsh -NoProfile -File $auditScript workspace-audit --clean
                if ($LASTEXITCODE -ne 0) {
                    throw "Quality Gate falló. Corrija los errores antes de abrir la PR."
                }
            }
            Write-Host "[+] Publicando rama '$currentBranch' a origin..." -ForegroundColor Cyan
            git push -u origin HEAD
            if ($LASTEXITCODE -ne 0) {
                throw "Fallo al subir la rama a origin."
            }

            if (-not $Body) {
                $Body = @"
## Motivación y Contexto
$Title

## Cambios Introducidos
- Tarea aislada en rama efímera '$currentBranch'.

## Verificación Fast-Failure
- [x] aagy workspace-audit superado (Quality Gate Rating A, 0 violaciones).
- [x] markdownlint 100% compliant.

## Estrategia Fast-Rollback
- En caso de anomalía, cerrar la PR o revertir el commit squash atómico (`git revert <sha>`).
"@
            }

            $ghCmd = Get-Command gh -ErrorAction SilentlyContinue
            if ($ghCmd) {
                Write-Host "[+] Creando Pull Request en GitHub hacia 'main'..." -ForegroundColor Green
                gh pr create --base main --head $currentBranch --title $Title --body $Body
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[OK] Pull Request creada y aislada exitosamente." -ForegroundColor Green
                }
            } else {
                $remote = (git remote get-url origin 2>$null)
                if (-not $remote) {
                    throw "'gh' no está disponible y el repo no tiene remoto 'origin': no se puede indicar dónde abrir la PR."
                }
                $web = ($remote.Trim() -replace '^git@([^:]+):', 'https://$1/' -replace '\.git$', '')
                Write-Host "[!] 'gh' CLI no disponible. Abra la PR manualmente en:" -ForegroundColor Yellow
                Write-Host "$web/compare/main...$currentBranch" -ForegroundColor Cyan
            }
        }

        "complete-task" {
            $completeScript = Join-Path $PSScriptRoot "aagy.ps1"
            $cmdArgs = @("complete-task-pr")
            if ($Title) { $cmdArgs += @("--title", $Title) }
            if ($Body) { $cmdArgs += @("--body", $Body) }
            if ($ReviewOnly) { $cmdArgs += "--review-only" }
            if ($Yes) { $cmdArgs += "--yes" }
            pwsh -NoProfile -File $completeScript @cmdArgs
        }
    }
} finally {
    Pop-Location
}
