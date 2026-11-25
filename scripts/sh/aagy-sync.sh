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
    SKILLS=(tdd-workflow search-first verification-loop security-review git-workflow conventional-commit-review docs-governance sonarqube-quality-gate todo-lifecycle safety-guard engineering-lifecycle shared-backlog agent-worktrees agent-self-evaluation aagy-doctor aagy-local)
    AGENTS=(planner.md architect.md tdd-guide.md code-reviewer.md security-reviewer.md build-error-resolver.md silent-failure-hunter.md refactor-cleaner.md doc-updater.md todo-archiver.md sync-aligner.md lifecycle-coordinator.md)
    ;;
  network-infra)
    SKILLS=(docker-patterns deployment-patterns kubernetes-patterns homelab-network-readiness homelab-network-setup homelab-pihole-dns homelab-vlan-segmentation homelab-wireguard-vpn network-config-validation network-interface-health security-scan safety-guard sre-reliability)
    AGENTS=(homelab-architect.md network-architect.md network-config-reviewer.md network-troubleshooter.md)
    ;;
  java-spring)
    SKILLS=(springboot-patterns springboot-security springboot-tdd springboot-verification java-coding-standards postgres-patterns database-migrations api-design sonarqube-quality-gate sync-microservice-sdk)
    AGENTS=(java-reviewer.md java-build-resolver.md database-reviewer.md)
    ;;
  angular)
    SKILLS=(angular-developer e2e-testing sonarqube-quality-gate sync-microservice-sdk)
    AGENTS=(typescript-reviewer.md e2e-runner.md)
    ;;
  go)
    SKILLS=(golang-patterns golang-testing docker-patterns kubernetes-patterns postgres-patterns latency-critical-systems data-throughput-accelerator benchmark-optimization-loop sonarqube-quality-gate sync-microservice-sdk sre-reliability)
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
    # Presupuesto 0 $: sin budget > 0 (AAGY_BUDGET), las skills con cost: paid no se instalan.
    PYB="$(command -v python3 || command -v python)"
    if [ -n "$PYB" ] && ! "$PYB" "$REPO_ROOT/scripts/py/aagy_config.py" paid-allowed >/dev/null 2>&1; then
      for paid in $("$PYB" "$REPO_ROOT/scripts/py/aagy_config.py" paid-skills "$REPO_ROOT/skills"); do
        rm -rf "$TARGET_DIR/skills/$paid"
        echo "[-] Skill de pago omitida (presupuesto 0 \$): $paid"
      done
    fi
    echo "[OK] Catálogo completo optimizado sincronizado."
    SKILLS=()
    AGENTS=()
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

for s in ${SKILLS[@]+"${SKILLS[@]}"}; do
  if [ -d "$REPO_ROOT/skills/$s" ]; then
    rm -rf "$TARGET_DIR/skills/$s"
    cp -R "$REPO_ROOT/skills/$s" "$TARGET_DIR/skills/"
    echo "[+] Skill instalada ($PHASE): $s"
  fi
done

for a in ${AGENTS[@]+"${AGENTS[@]}"}; do
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
  # Los hooks llaman a los .py del plugin con ruta absoluta (como ${CLAUDE_PLUGIN_ROOT} en aagy-ecc).
  sed "s|\${AAGY_PLUGIN_ROOT}|$TARGET_DIR|g" "$REPO_ROOT/hooks.json" > "$TARGET_DIR/hooks.json"
fi

mkdir -p "$TARGET_DIR/.data/instincts" "$TARGET_DIR/scripts/ps1" "$TARGET_DIR/scripts/sh" "$TARGET_DIR/scripts/py"
for ps in safety-check.ps1 hook-post-write.ps1 lint-markdown.ps1 auto-evolve.ps1 manage-instincts.ps1 backlog.ps1 new-lifecycle-task.ps1 complete-task-pr.ps1 archive-todo.ps1 format-commit.ps1; do
  [ -f "$REPO_ROOT/scripts/ps1/$ps" ] && cp "$REPO_ROOT/scripts/ps1/$ps" "$TARGET_DIR/scripts/ps1/$ps"
done
for sh in safety-check.sh hook-post-write.sh lint-markdown.sh auto-evolve.sh manage-instincts.sh backlog.sh new-lifecycle-task.sh complete-task-pr.sh archive-todo.sh format-commit.sh; do
  [ -f "$REPO_ROOT/scripts/sh/$sh" ] && cp "$REPO_ROOT/scripts/sh/$sh" "$TARGET_DIR/scripts/sh/$sh"
done
# Todos los motores Python (los hooks, el doctor y la fase 4 los usan desde el plugin).
cp "$REPO_ROOT/scripts/py/"*.py "$TARGET_DIR/scripts/py/"
mkdir -p "$TARGET_DIR/templates/lifecycle"
cp -R "$REPO_ROOT/doc/00-governance/templates/"* "$TARGET_DIR/templates/lifecycle/"

echo "[OK] Sincronización completada exitosamente."
write_install_manifest "$PHASE"
