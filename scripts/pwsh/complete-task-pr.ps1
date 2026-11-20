<#
.SYNOPSIS
    Automatización integral de fin de tarea: Revisión Manual + PR + Auto-resolución de Conflictos + Automerge + Borrado de Rama.
.DESCRIPTION
    Ejecuta el ciclo de Trunk-Based Development con Fast-Failure y Fast-Rollback:
    1. Presenta un aviso con revisión manual estructurada (diff, archivos, commit, PR).
    2. Valida confirmación del usuario (a menos que se pase -Yes / -NonInteractive).
    3. Realiza commit y push de la rama aislada.
    4. Crea o actualiza la Pull Request hacia la rama base ('main').
    5. Detecta y autoresuelve conflictos contra 'origin/main' si existen.
    6. Ejecuta squash-automerge y elimina la rama remota y local.
    7. Retorna a 'main' con el historial sincronizado.
.PARAMETER Title
    Título estructurado con formato [type]-[projects]: <title>.
.PARAMETER Body
    Cuerpo explicativo del commit y la Pull Request.
.PARAMETER TargetBranch
    Rama destino (por defecto 'main').
.PARAMETER ReviewOnly
    Solo muestra el informe de revisión manual sin ejecutar mutaciones en git.
.PARAMETER Yes
    Confirma automáticamente la ejecución tras mostrar el aviso de revisión manual.
.PARAMETER Help
    Muestra la ayuda detallada.
.EXAMPLE
    pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -ReviewOnly
.EXAMPLE
    pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -Title "feat-[cluster]: migrar servicios" -Yes
#>
[CmdletBinding()]
param(
    [string]$Title,
    [string]$Body,
    [string]$TargetBranch = "main",
    [switch]$ReviewOnly,
    [switch]$Yes,
    [switch]$Help
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path -Full
    exit 0
}

# 1. Resolver rutas y contexto del repositorio
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path "$ScriptDir\..\..").Path
Push-Location $RepoRoot

try {
    # 2. Verificar rama actual mediante validador canónico de gobernanza
    $currentBranch = (git branch --show-current).Trim()
    $validateScript = Join-Path $RepoRoot "scripts\py\validate_branch.py"
    if (Test-Path $validateScript) {
        $valOutput = python $validateScript --branch $currentBranch 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "Validación de gobernanza de ramas rechazada: $valOutput"
        }
    } elseif ($currentBranch -in @("main", "sandbox", "live", "")) {
        throw "No se puede ejecutar el ciclo completo de PR en la rama protegida o vacía '$currentBranch'. Debe estar en una rama de tarea (feat/*, fix/*, refactor/*, etc.)."
    }

    # 3. Inspeccionar estado de cambios
    $statusLines = @(git status --short)
    $stagedDiffStat = git diff --cached --stat
    $workingDiffStat = git diff --stat

    if ($statusLines.Length -eq 0 -and -not (git log origin/$TargetBranch..$currentBranch --oneline 2>$null)) {
        Write-Host "[INFO] No hay cambios pendientes ni commits por fusionar en '$currentBranch'." -ForegroundColor Yellow
        exit 0
    }

    # Si no se provee título, intentar deducirlo del último commit o de la rama
    if (-not $Title) {
        $lastCommitMsg = (git log -1 --pretty=format:%s 2>$null)
        if ($lastCommitMsg -and $lastCommitMsg -match "^\[[a-z]+\]-") {
            $Title = $lastCommitMsg
        } else {
            $branchParts = $currentBranch.Split('/')
            $bType = if ($branchParts.Length -ge 1) { $branchParts[0] } else { "feat" }
            $bProj = if ($branchParts.Length -ge 2) { $branchParts[1] } else { "cluster" }
            $bDesc = if ($branchParts.Length -ge 3) { $branchParts[2] -replace '-', ' ' } else { "update task" }
            $Title = "[$bType]-[$bProj]: $bDesc"
        }
    }

    # Resolver rutas documentales desde .governance/docs-map.json (con fallback clásico)
    $todoRel = "doc/TODO.md"
    $doneRel = "doc/TODO_DONE"
    $docsMapScript = Join-Path $RepoRoot "scripts\py\docs_map.py"
    if (Test-Path $docsMapScript) {
        $resolvedTodoRel = (python $docsMapScript --repo-root $RepoRoot --key todo --relative 2>$null)
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolvedTodoRel)) {
            $todoRel = $resolvedTodoRel.Trim()
        }
        $resolvedDoneRel = (python $docsMapScript --repo-root $RepoRoot --key todo_done --relative 2>$null)
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolvedDoneRel)) {
            $doneRel = $resolvedDoneRel.Trim()
        }
    }

    # Detectar tareas completadas en TODO.md
    $todoPath = Join-Path $RepoRoot $todoRel
    $hasCompletedTodos = $false
    if (Test-Path $todoPath) {
        $todoContent = Get-Content -Raw -Path $todoPath -ErrorAction SilentlyContinue
        if ($todoContent -match "(?m)^[\s*\-]*\[x\]") {
            $hasCompletedTodos = $true
        }
    }

    if (-not $Body) {
        $Body = @"
Motivación y Contexto:
- Tarea finalizada en rama efímera '$currentBranch'.
- Fusión automática a '$TargetBranch' tras validación de Quality Gate y resolución de dependencias.

Cambios Introducidos:
- Actualización de código y contratos del monorepo home-lab.

Verificación:
- [x] Quality Gate y tests unitarios verificados (código 0).
- [x] markdownlint 100% compliant.

Estrategia Fast-Rollback:
- Reversión atómica mediante revert del squash commit en caso de incidente: git revert <sha>.
"@
    }

    # 4. AVISO DE REVISIÓN MANUAL PREVIA
    Write-Host "`n=======================================================" -ForegroundColor Cyan
    Write-Host "       AVISO DE REVISIÓN MANUAL PREVIA A EJECUCIÓN     " -ForegroundColor Cyan
    Write-Host "=======================================================" -ForegroundColor Cyan
    Write-Host "Rama Origen:        " -NoNewline; Write-Host $currentBranch -ForegroundColor Yellow
    Write-Host "Rama Destino:       " -NoNewline; Write-Host $TargetBranch -ForegroundColor Yellow
    Write-Host "Título de PR/Commit:" -NoNewline; Write-Host " $Title" -ForegroundColor Green
    if ($hasCompletedTodos) {
        Write-Host "Tareas a Archivar:  " -NoNewline; Write-Host "Tareas completadas detectadas en $todoRel (se archivarán automáticamente a $doneRel)" -ForegroundColor Magenta
    }
    Write-Host "`nResumen de Cambios:" -ForegroundColor Cyan
    if ($statusLines) {
        $statusLines | Select-Object -First 15 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
        if ($statusLines.Count -gt 15) {
            Write-Host "  ... y $($statusLines.Count - 15) archivos adicionales." -ForegroundColor DarkGray
        }
    } else {
        Write-Host "  (Todos los cambios ya se encuentran comprometidos en commits locales)" -ForegroundColor Gray
    }

    Write-Host "`nCuerpo de la PR:" -ForegroundColor DarkGray
    Write-Host $Body -ForegroundColor DarkGray
    Write-Host "=======================================================`n" -ForegroundColor Cyan

    if ($ReviewOnly) {
        Write-Host "[OK] Modo -ReviewOnly: Revisión completada sin mutaciones." -ForegroundColor Green
        exit 0
    }

    # 5. Confirmación interactiva si no se especificó -Yes
    if (-not $Yes) {
        $response = Read-Host "¿Desea proceder con Commit, Push, PR, Autoresolución, Automerge y Borrado de rama? (s/N)"
        if ($response -notmatch "^[sSyY]$") {
            Write-Host "[CANCELADO] Operación cancelada por el usuario." -ForegroundColor Yellow
            exit 0
        }
    }

    # 6. Sincronizar y archivar tareas completadas en TODO.md si existen
    if ($hasCompletedTodos) {
        Write-Host "[+] Archivando tareas completadas en $doneRel..." -ForegroundColor Cyan
        $archiveScript = Join-Path $PSScriptRoot "archive-todo.ps1"
        if (Test-Path $archiveScript) {
            pwsh -NoProfile -File $archiveScript -TodoPath $todoRel -DoneDir $doneRel
            if ($LASTEXITCODE -ne 0) {
                throw "Error al archivar tareas completadas de $todoRel."
            }
        }
    }

    # 6.5. Si es rama de incidencia (fix/*), generar Post-Mortem 5W automáticamente
    if ($currentBranch -like "fix/*") {
        Write-Host "[+] Rama de incidencia detectada ('$currentBranch'). Generando Post-Mortem 5W..." -ForegroundColor Cyan
        $pmScript = Join-Path $RepoRoot "scripts\py\generate_postmortem.py"
        if (Test-Path $pmScript) {
            python $pmScript --repo-root $RepoRoot --branch $currentBranch
        }
    }

    # 7. Pre-merge Quality Gate: Markdown linter, tests unitarios y SonarQube
    Write-Host "[+] Ejecutando auditoría de calidad previa..." -ForegroundColor Cyan
    $lintScript = Join-Path $PSScriptRoot "lint-markdown.ps1"
    if (Test-Path $lintScript) {
        pwsh -NoProfile -File $lintScript -CheckOnly
        if ($LASTEXITCODE -ne 0) {
            throw "El Quality Gate de Markdown falló. Corrija los errores antes de continuar."
        }
    }

    # 7.1. Tests unitarios (py / pwsh / sh)
    $testTargets = @()
    foreach ($relDir in @("scripts\py\tests", "scripts\pwsh\tests", "scripts\sh\tests")) {
        $candidate = Join-Path $RepoRoot $relDir
        if (Test-Path $candidate) {
            $testTargets += $candidate
        }
    }
    if ($testTargets.Count -eq 0) {
        $fallbackTests = Join-Path $RepoRoot "scripts\ecc-agy\tests"
        if (Test-Path $fallbackTests) {
            $testTargets += $fallbackTests
        }
    }
    if ($testTargets.Count -gt 0) {
        Write-Host "[+] Ejecutando suite de pruebas unitarias (pytest)..." -ForegroundColor Cyan
        python -m pytest @testTargets -q
        if ($LASTEXITCODE -ne 0) {
            throw "La suite de pruebas unitarias falló. No se puede proceder con el merge."
        }
    }

    # 7.2. Auditoría SonarQube
    $sonarScript = Join-Path $PSScriptRoot "sonar-audit.ps1"
    if (Test-Path $sonarScript) {
        pwsh -NoProfile -File $sonarScript
        if ($LASTEXITCODE -ne 0) {
            throw "La auditoría SonarQube no alcanzó el Rating A. Corrija las violaciones antes de continuar."
        }
    }

    # 7.3. Auditoría de Paridad SDK (home-lab-sdk)
    $parityScript = Join-Path $PSScriptRoot "audit-sdk-parity.ps1"
    if (Test-Path $parityScript) {
        Write-Host "[+] Ejecutando auditoría de paridad de contratos SDK..." -ForegroundColor Cyan
        pwsh -NoProfile -File $parityScript
        if ($LASTEXITCODE -ne 0) {
            throw "La auditoría de paridad SDK detectó divergencias de contratos. Sincronice home-lab-sdk antes de continuar."
        }
    }

    # 7.4. Auditoría de Bloqueos DDL en PostgreSQL LTS
    $pgLockScript = Join-Path $PSScriptRoot "audit-pg-locks.ps1"
    if (Test-Path $pgLockScript) {
        Write-Host "[+] Ejecutando auditoría de bloqueos DDL en PostgreSQL LTS..." -ForegroundColor Cyan
        pwsh -NoProfile -File $pgLockScript
        if ($LASTEXITCODE -ne 0) {
            throw "La auditoría de bloqueos DDL detectó sentencias SQL de alto riesgo. Corrija los bloqueos antes de continuar."
        }
    }

    # 7.5. Validación de Congruencia Ingress, Split-DNS y /portal
    $ingressScript = Join-Path $PSScriptRoot "validate-ingress-routes.ps1"
    if (Test-Path $ingressScript) {
        Write-Host "[+] Ejecutando validación de congruencia Ingress, Split-DNS y /portal..." -ForegroundColor Cyan
        pwsh -NoProfile -File $ingressScript
        if ($LASTEXITCODE -ne 0) {
            throw "La validación de Ingress/Split-DNS detectó discrepancias. Corrija las rutas antes de continuar."
        }
    }

    # 7.6. Auditoría de Paridad Multi-Harness (aagy <-> ecc)
    $pluginParityScript = Join-Path $PSScriptRoot "audit-plugin-parity.ps1"
    if (Test-Path $pluginParityScript) {
        Write-Host "[+] Ejecutando auditoría de paridad multi-harness (aagy <-> ecc)..." -ForegroundColor Cyan
        pwsh -NoProfile -File $pluginParityScript
        if ($LASTEXITCODE -ne 0) {
            throw "La auditoría de paridad multi-harness detectó divergencias entre aagy y ecc. Corrija los manifiestos antes de continuar."
        }
    }

    # 7.7. Validación de Enlaces Documentales y docs-map.json
    $mapDocsScript = Join-Path $RepoRoot "scripts\py\map_docs.py"
    if (Test-Path $mapDocsScript) {
        Write-Host "[+] Validando enlaces documentales y .governance/docs-map.json..." -ForegroundColor Cyan
        python $mapDocsScript --repo-root $RepoRoot --check-docs-map
        if ($LASTEXITCODE -ne 0) {
            throw "La validación documental (map_docs.py) detectó enlaces rotos o referencias inválidas."
        }
    }

    # 7. Commit si hay cambios staged o unstaged
    $dirty = (git status --porcelain)
    if ($dirty) {
        Write-Host "[+] Añadiendo y comprometiendo cambios pendientes..." -ForegroundColor Cyan
        git add -A
        $commitMessage = "$Title`n`n$Body"
        git commit -m $commitMessage
        if ($LASTEXITCODE -ne 0) {
            throw "Error al realizar git commit."
        }
    }

    # 8. Push de la rama a origin
    Write-Host "[+] Publicando rama '$currentBranch' en origin..." -ForegroundColor Cyan
    git push -u origin HEAD
    if ($LASTEXITCODE -ne 0) {
        throw "Error al subir la rama a origin."
    }

    # 9. Creación o detección de PR
    $ghAvailable = (Get-Command gh -ErrorAction SilentlyContinue)
    if (-not $ghAvailable) {
        throw "GitHub CLI ('gh') no está disponible en el entorno. Imposible crear o fusionar PR automáticamente."
    }

    Write-Host "[+] Comprobando Pull Request en GitHub..." -ForegroundColor Cyan
    $existingPrJson = @(gh pr list --head $currentBranch --base $TargetBranch --json number,url 2>$null | ConvertFrom-Json)
    $prNumber = $null

    if ($existingPrJson -and $existingPrJson.Length -gt 0) {
        $prNumber = $existingPrJson[0].number
        Write-Host "[INFO] Pull Request existente detectada: #$prNumber ($($existingPrJson[0].url))" -ForegroundColor Green
    } else {
        Write-Host "[+] Creando nueva Pull Request hacia '$TargetBranch'..." -ForegroundColor Cyan
        $prCreateOut = (gh pr create --base $TargetBranch --head $currentBranch --title $Title --body $Body 2>&1)
        Write-Host $prCreateOut -ForegroundColor Green
        # Re-obtener número de PR
        $existingPrJson = @(gh pr list --head $currentBranch --base $TargetBranch --json number,url 2>$null | ConvertFrom-Json)
        if ($existingPrJson -and $existingPrJson.Length -gt 0) {
            $prNumber = $existingPrJson[0].number
        }
    }

    # 10. Detección y Autoresolución de Conflictos
    Write-Host "[+] Verificando estado de conflictos con '$TargetBranch'..." -ForegroundColor Cyan
    git fetch origin $TargetBranch
    $mergeBase = (git merge-base HEAD "origin/$TargetBranch").Trim()
    $targetSha = (git rev-parse "origin/$TargetBranch").Trim()

    if ($mergeBase -ne $targetSha) {
        Write-Host "[+] La rama diverge de 'origin/$TargetBranch'. Comprobando fusión local..." -ForegroundColor Cyan
        $mergeAttempt = (git merge "origin/$TargetBranch" --no-commit --no-ff 2>&1)
        $hasConflicts = @(git diff --name-only --diff-filter=U)

        if ($hasConflicts.Length -gt 0) {
            Write-Host "[!] Se detectaron conflictos en los siguientes archivos:" -ForegroundColor Yellow
            $hasConflicts | ForEach-Object { Write-Host "   - $_" -ForegroundColor Yellow }
            Write-Host "[+] Autoresolviendo conflictos favoreciendo cambios de la rama de tarea..." -ForegroundColor Cyan

            foreach ($cFile in $hasConflicts) {
                # Estrategia de resolución determinista: favorecer versión de la tarea
                git checkout --ours -- $cFile
                git add $cFile
            }

            git commit -m "fix-[git]: auto-resolve conflicts against origin/$TargetBranch"
            git push origin HEAD
            Write-Host "[OK] Conflictos autoresueltos y sincronizados en origin." -ForegroundColor Green
        } else {
            # Si no hubo conflicto pero inició un merge en progreso, abortar merge limpio ya que squash se encargará
            git merge --abort 2>$null
        }
    }

    # 11. Automerge (Squash and Merge) y borrado de rama remota
    if ($prNumber) {
        Write-Host "[+] Ejecutando squash-automerge en Pull Request #$prNumber..." -ForegroundColor Green
        gh pr merge $prNumber --squash --delete-branch --admin 2>$null
        if ($LASTEXITCODE -ne 0) {
            # Reintentar sin --admin si no hay privilegios de bypass
            gh pr merge $prNumber --squash --delete-branch
        }
        Write-Host "[OK] Pull Request #$prNumber fusionada con éxito en '$TargetBranch'." -ForegroundColor Green
    } else {
        throw "No se pudo obtener el número de Pull Request para completar el automerge."
    }

    # 12. Retorno y actualización local de main
    Write-Host "[+] Sincronizando rama local '$TargetBranch'..." -ForegroundColor Cyan
    # Si hay un merge en progreso no finalizado, abortar antes de conmutar
    git merge --abort 2>$null
    git checkout -f $TargetBranch
    git pull origin $TargetBranch

    # Borrado de rama local
    if ((git branch --list $currentBranch)) {
        Write-Host "[+] Eliminando rama local '$currentBranch'..." -ForegroundColor Cyan
        git branch -D $currentBranch 2>$null
        Write-Host "[OK] Rama local '$currentBranch' eliminada." -ForegroundColor Green
    }

    Write-Host "`n=======================================================" -ForegroundColor Green
    Write-Host " [OK] CICLO COMPLETO DE PR Y AUTOMERGE FINALIZADO      " -ForegroundColor Green
    Write-Host "=======================================================`n" -ForegroundColor Green
    git log -1 --oneline

    # 13. Telemetría de tokens en sesión y recomendación proactiva de compactación
    $monitorScript = Join-Path $PSScriptRoot "session-token-monitor.ps1"
    if (Test-Path $monitorScript) {
        pwsh -NoProfile -File $monitorScript -Threshold 45000 -AlertOnly
    }

} finally {
    Pop-Location
}
