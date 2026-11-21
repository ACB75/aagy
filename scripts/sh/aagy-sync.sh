#!/usr/bin/env bash
# ==============================================================================
# aagy-sync.sh - Sincronizador de Anything Antigravity (aagy) para Linux (ADR-0001, perfiles de stack)
# ==============================================================================
set -euo pipefail

PHASE="${1:-status}"
if [ "$PHASE" = "--repo" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  py="$(command -v python3 || command -v python)"
  exec "$py" "$SCRIPT_DIR/../py/repo_profiles.py" install --repo "${2:?Falta la ruta del repositorio}"
fi
TARGET_DIR="${2:-$HOME/.gemini/config/plugins/aagy}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

mkdir -p "$TARGET_DIR/skills" "$TARGET_DIR/agents" "$TARGET_DIR/rules"

write_install_manifest() {
  # Deja .aagy-install.json en el destino para /aagy-doctor. Nunca aborta la sincronización.
  py="$(command -v python3 || command -v python || true)"
  if [ -n "$py" ] && [ -f "$REPO_ROOT/scripts/py/install_manifest.py" ]; then
    "$py" "$REPO_ROOT/scripts/py/install_manifest.py" write --dest "$TARGET_DIR" --harness agy --profile "$1" --repo-root "$REPO_ROOT" || true
  else
    echo "[!] Python no disponible: se omite el manifiesto de instalación."
  fi
}

case "$PHASE" in
  status)
    echo "=== Anything Antigravity (aagy) Status ($TARGET_DIR) ==="
    echo "Skills ($(find "$TARGET_DIR/skills" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | wc -l)):"
    ls -1 "$TARGET_DIR/skills" 2>/dev/null || true
    echo "Agents ($(find "$TARGET_DIR/agents" -maxdepth 1 -name '*.md' 2>/dev/null | wc -l)):"
    ls -1 "$TARGET_DIR/agents" 2>/dev/null || true
    exit 0
    ;;
  generic)
    SKILLS=(tdd-workflow search-first verification-loop security-review coding-standards git-workflow conventional-commit-review architecture-decision-records error-handling docs-governance workspace-health-audit config-gc sonarqube-quality-gate sync-microservice-sdk todo-lifecycle sre-reliability agent-sort agent-self-evaluation strategic-compact context-budget safety-guard engineering-lifecycle shared-backlog aagy-doctor)
    AGENTS=(planner.md architect.md tdd-guide.md code-reviewer.md security-reviewer.md build-error-resolver.md silent-failure-hunter.md refactor-cleaner.md doc-updater.md todo-archiver.md sync-aligner.md lifecycle-coordinator.md)
    ;;
  network-infra)
    SKILLS=(docker-patterns deployment-patterns kubernetes-patterns homelab-network-readiness homelab-network-setup homelab-pihole-dns homelab-vlan-segmentation homelab-wireguard-vpn network-config-validation network-interface-health security-scan safety-guard)
    AGENTS=(homelab-architect.md network-architect.md network-config-reviewer.md network-troubleshooter.md)
    ;;
  java-spring)
    SKILLS=(springboot-patterns springboot-security springboot-tdd springboot-verification java-coding-standards postgres-patterns database-migrations api-design sonarqube-quality-gate)
    AGENTS=(java-reviewer.md java-build-resolver.md database-reviewer.md)
    ;;
  angular)
    SKILLS=(angular-developer e2e-testing sonarqube-quality-gate)
    AGENTS=(typescript-reviewer.md e2e-runner.md)
    ;;
  go)
    SKILLS=(golang-patterns golang-testing docker-patterns kubernetes-patterns postgres-patterns latency-critical-systems data-throughput-accelerator benchmark-optimization-loop sonarqube-quality-gate)
    AGENTS=(go-reviewer.md go-build-resolver.md performance-optimizer.md database-reviewer.md)
    ;;
  python)
    SKILLS=(python-patterns python-testing benchmark-optimization-loop sonarqube-quality-gate)
    AGENTS=(python-reviewer.md performance-optimizer.md)
    ;;
  all)
    echo "[+] Sincronizando catálogo completo optimizado..."
    cp -R "$REPO_ROOT/skills/"* "$TARGET_DIR/skills/"
    cp "$REPO_ROOT/agents/"*.md "$TARGET_DIR/agents/"
    echo "[OK] Catálogo completo optimizado sincronizado."
    write_install_manifest "$PHASE"
    exit 0
    ;;
  infra|kakebo|cluster|token-hill)
    echo "[!] La fase '$PHASE' se retiró: usa los perfiles de stack (network-infra, java-spring, angular, go, python)." >&2
    exit 1
    ;;
  *)
    echo "Uso: $0 {status|generic|network-infra|java-spring|angular|go|python|all} [target_dir]"
    echo "     $0 --repo <ruta_repo>   # instala en <repo>/.agents/ los perfiles de <repo>/.governance/aagy-profiles.json"
    exit 1
    ;;
esac

for s in "${SKILLS[@]}"; do
  if [ -d "$REPO_ROOT/skills/$s" ]; then
    rm -rf "$TARGET_DIR/skills/$s"
    cp -R "$REPO_ROOT/skills/$s" "$TARGET_DIR/skills/"
    echo "[+] Skill instalada ($PHASE): $s"
  fi
done

for a in "${AGENTS[@]}"; do
  if [ -f "$REPO_ROOT/agents/$a" ]; then
    cp "$REPO_ROOT/agents/$a" "$TARGET_DIR/agents/"
    echo "[+] Agente instalado ($PHASE): $a"
  fi
done

if [ -d "$REPO_ROOT/rules" ]; then
  cp "$REPO_ROOT/rules/"*.md "$TARGET_DIR/rules/"
  echo "[+] Reglas sincronizadas -> $TARGET_DIR/rules/"
fi
if [ -f "$REPO_ROOT/plugin.json" ]; then
  cp "$REPO_ROOT/plugin.json" "$TARGET_DIR/plugin.json"
fi
if [ -f "$REPO_ROOT/hooks.json" ]; then
  cp "$REPO_ROOT/hooks.json" "$TARGET_DIR/hooks.json"
fi

echo "[OK] Sincronización completada exitosamente."
write_install_manifest "$PHASE"
