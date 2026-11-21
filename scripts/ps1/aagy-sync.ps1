#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Gestor modular de sincronización de Anything Antigravity (aagy) (Two-Tier Architecture / ADR-0001).
.DESCRIPTION
    Sincroniza módulos, skills o agentes desde la raíz del repositorio
    hacia el plugin global ~/.gemini/config/plugins/aagy (Nivel 1: Transversal)
    o hacia un proyecto específico (.agents/) (Nivel 2: Específico de Dominio).
.PARAMETER Phase
    Fase preconfigurada según la arquitectura en dos niveles:
      - generic    (Nivel 1 Global: 12 core skills y 12 agentes universales de ingeniería)
      - network-infra (Perfil de stack: Docker, K8s, Homelab, Redes, Seguridad)
      - java-spring   (Perfil de stack: Java 25 / Spring Boot 4, Postgres)
      - angular       (Perfil de stack: Angular 21 / TypeScript, E2E)
      - go            (Perfil de stack: Go, Docker, K8s, Latencia, Postgres)
      - python        (Perfil de stack: Python CLI, Testing, Benchmarking)
      - all        (Catálogo completo optimizado)
      - status     (Muestra el estado actual del plugin o proyecto destino)
.PARAMETER Repo
    Ruta a un repositorio consumidor. Instala en <Repo>\.agents\ los perfiles declarados por el propio repo
    en <Repo>\.governance\aagy-profiles.json (delegando en scripts/py/repo_profiles.py). Sin -Repo se
    actualiza el plugin global aagy. El plugin nunca conoce nombres de proyectos consumidores.
.PARAMETER Clean
    Si se especifica, limpia previamente las carpetas skills/ y agents/ del destino antes de sincronizar.
.EXAMPLE
    pwsh -File scripts/ps1/aagy-sync.ps1 -Phase generic -Clean
.EXAMPLE
    pwsh -File scripts/ps1/aagy-sync.ps1 -Repo C:\Ruta\A\MiRepo
#>
param(
    [ValidateSet("generic", "network-infra", "java-spring", "angular", "go", "python", "all", "status")]
    [string]$Phase = "status",
    [string]$Repo = "",
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..\..")).Path
$GlobalPluginDir = Join-Path $HOME ".gemini\config\plugins\aagy"

$SkillsSource = Join-Path $RepoRoot "skills"
$AgentsSource = Join-Path $RepoRoot "agents"

$PhaseConfig = @{
    "generic" = @{
        Skills = @(
            "tdd-workflow", "search-first", "verification-loop",
            "security-review", "git-workflow", "conventional-commit-review",
            "docs-governance", "sonarqube-quality-gate", "todo-lifecycle",
            "safety-guard", "engineering-lifecycle", "shared-backlog",
            "agent-self-evaluation", "aagy-doctor"
        )
        Agents = @(
            "planner.md", "architect.md", "tdd-guide.md", "code-reviewer.md",
            "security-reviewer.md", "build-error-resolver.md", "silent-failure-hunter.md",
            "refactor-cleaner.md", "doc-updater.md", "todo-archiver.md",
            "sync-aligner.md", "lifecycle-coordinator.md"
        )
    }
    "network-infra" = @{
        Skills = @(
            "docker-patterns", "deployment-patterns", "kubernetes-patterns",
            "homelab-network-readiness", "homelab-network-setup", "homelab-pihole-dns",
            "homelab-vlan-segmentation", "homelab-wireguard-vpn", "network-config-validation",
            "network-interface-health", "security-scan", "safety-guard", "sre-reliability"
        )
        Agents = @(
            "homelab-architect.md", "network-architect.md", "network-config-reviewer.md",
            "network-troubleshooter.md"
        )
    }
    "java-spring" = @{
        Skills = @(
            "springboot-patterns", "springboot-security", "springboot-tdd",
            "springboot-verification", "java-coding-standards", "postgres-patterns",
            "database-migrations", "api-design", "sonarqube-quality-gate", "sync-microservice-sdk"
        )
        Agents = @(
            "java-reviewer.md", "java-build-resolver.md", "database-reviewer.md"
        )
    }
    "angular" = @{
        Skills = @(
            "angular-developer", "e2e-testing", "sonarqube-quality-gate", "sync-microservice-sdk"
        )
        Agents = @(
            "typescript-reviewer.md", "e2e-runner.md"
        )
    }
    "go" = @{
        Skills = @(
            "golang-patterns", "golang-testing", "docker-patterns",
            "kubernetes-patterns", "postgres-patterns", "latency-critical-systems",
            "data-throughput-accelerator", "benchmark-optimization-loop",
            "sonarqube-quality-gate", "sync-microservice-sdk", "sre-reliability"
        )
        Agents = @(
            "go-reviewer.md", "go-build-resolver.md", "performance-optimizer.md",
            "database-reviewer.md"
        )
    }
    "python" = @{
        Skills = @(
            "python-patterns", "python-testing", "benchmark-optimization-loop",
            "sonarqube-quality-gate"
        )
        Agents = @(
            "python-reviewer.md", "performance-optimizer.md"
        )
    }
}


function Write-InstallManifest {
    # Deja .aagy-install.json en el plugin global para /aagy-doctor. Nunca aborta la sincronización.
    param([string]$InstalledPhase)
    $manifestScript = Join-Path $RepoRoot "scripts\py\install_manifest.py"
    if (-not (Test-Path $manifestScript)) { return }
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
    if (-not $py) {
        Write-Host "[!] Python no disponible: se omite el manifiesto de instalación." -ForegroundColor Yellow
        return
    }
    & $py.Source $manifestScript write --dest $GlobalPluginDir --harness agy --profile $InstalledPhase --repo-root $RepoRoot
}

if ($Repo) {
    $repoProfiles = Join-Path $RepoRoot "scripts\py\repo_profiles.py"
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }
    if (-not $py) { throw "Python es necesario para -Repo." }
    $action = if ($Phase -eq "status") { "status" } else { "install" }
    & $py.Source $repoProfiles $action --repo $Repo
    exit $LASTEXITCODE
}

if ($Phase -eq "status") {
    $targetInfo = $GlobalPluginDir
    Write-Host "=== Estado de Anything Antigravity (aagy) ($targetInfo) ===" -ForegroundColor Cyan
    if (Test-Path "$targetInfo\skills") {
        $skills = @(Get-ChildItem "$targetInfo\skills" -Directory | Select-Object -ExpandProperty Name)
        Write-Host "Skills activas ($($skills.Count)): $($skills -join ', ')" -ForegroundColor Green
    } else {
        Write-Host "Skills activas (0)" -ForegroundColor Gray
    }
    if (Test-Path "$targetInfo\agents") {
        $agents = @(Get-ChildItem "$targetInfo\agents" -File -Filter "*.md" | Select-Object -ExpandProperty Name)
        Write-Host "Agentes activos ($($agents.Count)): $($agents -join ', ')" -ForegroundColor Yellow
    } else {
        Write-Host "Agentes activos (0)" -ForegroundColor Gray
    }
    exit 0
}

$destRoot = $GlobalPluginDir
if ($Clean) {
    Write-Host "[+] Limpiando directorio destino: $destRoot" -ForegroundColor Cyan
    if (Test-Path "$destRoot\skills") { Remove-Item -Path "$destRoot\skills" -Recurse -Force }
    if (Test-Path "$destRoot\agents") { Remove-Item -Path "$destRoot\agents" -Recurse -Force }
    if (Test-Path "$destRoot\rules") { Remove-Item -Path "$destRoot\rules" -Recurse -Force }
}
New-Item -ItemType Directory -Force -Path "$destRoot\skills" | Out-Null
New-Item -ItemType Directory -Force -Path "$destRoot\agents" | Out-Null

New-Item -ItemType Directory -Force -Path "$GlobalPluginDir\rules" | Out-Null
$rulesSrc = Join-Path $RepoRoot "rules"
if (Test-Path $rulesSrc) {
    Copy-Item -Path (Join-Path $rulesSrc "*.md") -Destination "$GlobalPluginDir\rules\" -Force
    Write-Host "[+] Reglas globales sincronizadas -> $GlobalPluginDir\rules\" -ForegroundColor Cyan
}
$pluginJsonSrc = Join-Path $RepoRoot "plugin.json"
if (Test-Path $pluginJsonSrc) {
    Copy-Item -Path $pluginJsonSrc -Destination "$GlobalPluginDir\plugin.json" -Force
}
$hooksJsonSrc = Join-Path $RepoRoot "hooks.json"
if (Test-Path $hooksJsonSrc) {
    Copy-Item -Path $hooksJsonSrc -Destination "$GlobalPluginDir\hooks.json" -Force
}

New-Item -ItemType Directory -Force -Path "$GlobalPluginDir\.data\instincts" | Out-Null
New-Item -ItemType Directory -Force -Path "$GlobalPluginDir\scripts\ps1" | Out-Null
New-Item -ItemType Directory -Force -Path "$GlobalPluginDir\scripts\sh" | Out-Null
New-Item -ItemType Directory -Force -Path "$GlobalPluginDir\scripts\py" | Out-Null
foreach ($ps in @("safety-check.ps1", "hook-post-write.ps1", "lint-markdown.ps1", "auto-evolve.ps1", "manage-instincts.ps1", "backlog.ps1", "new-lifecycle-task.ps1", "complete-task-pr.ps1", "archive-todo.ps1", "format-commit.ps1")) {
    $srcPs = Join-Path $RepoRoot "scripts\ps1\$ps"
    if (Test-Path $srcPs) { Copy-Item -Path $srcPs -Destination "$GlobalPluginDir\scripts\ps1\$ps" -Force }
}
foreach ($sh in @("safety-check.sh", "hook-post-write.sh", "lint-markdown.sh", "auto-evolve.sh", "manage-instincts.sh", "backlog.sh", "new-lifecycle-task.sh", "complete-task-pr.sh", "archive-todo.sh", "format-commit.sh")) {
    $srcSh = Join-Path $RepoRoot "scripts\sh\$sh"
    if (Test-Path $srcSh) { Copy-Item -Path $srcSh -Destination "$GlobalPluginDir\scripts\sh\$sh" -Force }
}
foreach ($py in @("self_improve.py", "instinct_manager.py", "security_audit.py", "workspace_audit.py", "docs_map.py", "backlog.py", "archive_todo.py", "new_lifecycle_task.py", "sync_ideas_todo.py", "format_commit.py", "validate_branch.py", "aagy_doctor.py", "doctor_core.py", "install_manifest.py")) {
    $srcPy = Join-Path $RepoRoot "scripts\py\$py"
    if (Test-Path $srcPy) { Copy-Item -Path $srcPy -Destination "$GlobalPluginDir\scripts\py\$py" -Force }
}

if ($Phase -eq "all") {
    Write-Host "[+] Sincronizando catálogo completo optimizado..." -ForegroundColor Cyan
    Copy-Item -Path (Join-Path $SkillsSource "*") -Destination (Join-Path $destRoot "skills") -Recurse -Force
    Copy-Item -Path (Join-Path $AgentsSource "*.md") -Destination (Join-Path $destRoot "agents") -Force
    Write-Host "[OK] Catálogo completo optimizado sincronizado en $destRoot." -ForegroundColor Green
    Write-InstallManifest -InstalledPhase $Phase
    exit 0
}

$cfg = $PhaseConfig[$Phase]
foreach ($s in $cfg.Skills) {
    $src = Join-Path $SkillsSource $s
    $dst = Join-Path "$destRoot\skills" $s
    if (Test-Path $src) {
        if (Test-Path $dst) { Remove-Item -Path $dst -Recurse -Force }
        Copy-Item -Path $src -Destination $dst -Recurse -Force
        Write-Host "[+] Skill instalada ($Phase): $s" -ForegroundColor Green
    }
}

foreach ($a in $cfg.Agents) {
    $src = Join-Path $AgentsSource $a
    $dst = Join-Path "$destRoot\agents" $a
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination $dst -Force
        Write-Host "[+] Agente instalado ($Phase): $a" -ForegroundColor Green
    }
}

Write-Host "[OK] Sincronización finalizada para fase '$Phase' en $destRoot." -ForegroundColor Green
Write-InstallManifest -InstalledPhase $Phase
