#!/usr/bin/env bash
# ==============================================================================
# aagy-sync.sh - Sincronizador de Anything Antigravity (aagy) para Linux (ADR-0001, perfiles de stack)
# Prepara la copia nueva en un directorio temporal y la aplica con install_manifest.py apply:
#   --hard     borra los ficheros que el perfil ya no trae
#   --force    pisa también los ficheros editados a mano
#   --dry-run  muestra qué cambiaría sin tocar nada
# ==============================================================================
set -euo pipefail

APPLY_FLAGS=()
POSITIONAL=()
for arg in "$@"; do
  case "$arg" in
    --hard|--force|--dry-run) APPLY_FLAGS+=("$arg") ;;
    *) POSITIONAL+=("$arg") ;;
  esac
done
set -- ${POSITIONAL[@]+"${POSITIONAL[@]}"}

PHASE="${1:-status}"
if [ "$PHASE" = "--repo" ]; then
  SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  py="$(command -v python3 || command -v python)"
  exec "$py" "$SCRIPT_DIR/../py/repo_profiles.py" install --repo "${2:?Falta la ruta del repositorio}"
fi
DEST_DIR="${2:-$HOME/.gemini/config/plugins/aagy}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if [ "$PHASE" = "status" ]; then
  TARGET_DIR="$DEST_DIR"
else
  # Copia nueva en un temporal; apply_install la lleva al destino.
  TARGET_DIR="$(mktemp -d)"
  trap 'rm -rf "$TARGET_DIR"' EXIT
fi
mkdir -p "$TARGET_DIR/skills" "$TARGET_DIR/agents" "$TARGET_DIR/rules"

apply_install() {
  # Lleva la copia nueva al destino y deja .aagy-install.json con la lista de ficheros y sus hashes.
  py="$(command -v python3 || command -v python || true)"
  if [ -z "$py" ] || [ ! -f "$REPO_ROOT/scripts/py/install_manifest.py" ]; then
    echo "[!] Python no disponible: no se puede aplicar la sincronización." >&2
    exit 1
  fi
  mkdir -p "$DEST_DIR/.data/instincts"
  "$py" "$REPO_ROOT/scripts/py/install_manifest.py" apply --stage "$TARGET_DIR" --dest "$DEST_DIR" \
    --harness agy --profile "$1" --repo-root "$REPO_ROOT" ${APPLY_FLAGS[@]+"${APPLY_FLAGS[@]}"}
}

case "$PHASE" in
  status)
    echo "=== Anything Antigravity (aagy) Status ($DEST_DIR) ==="
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
    SKILLS=(docker-patterns deployment-patterns kubernetes-patterns network-config-validation network-interface-health security-scan safety-guard sre-reliability)
    AGENTS=(network-architect.md network-config-reviewer.md network-troubleshooter.md)
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
    SKILLS=(golang-patterns golang-testing docker-patterns kubernetes-patterns postgres-patterns latency-critical-systems data-throughput-accelerator benchmark-optimization-loop sonarqube-quality-gate sre-reliability)
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
  infra)
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
  sed "s|\${AAGY_PLUGIN_ROOT}|$DEST_DIR|g" "$REPO_ROOT/hooks.json" > "$TARGET_DIR/hooks.json"
fi

mkdir -p "$TARGET_DIR/scripts/ps1" "$TARGET_DIR/scripts/sh" "$TARGET_DIR/scripts/py"
for ps in aagy.ps1 lint-markdown.ps1; do
  [ -f "$REPO_ROOT/scripts/ps1/$ps" ] && cp "$REPO_ROOT/scripts/ps1/$ps" "$TARGET_DIR/scripts/ps1/$ps"
done
for sh in aagy.sh lint-markdown.sh; do
  [ -f "$REPO_ROOT/scripts/sh/$sh" ] && cp "$REPO_ROOT/scripts/sh/$sh" "$TARGET_DIR/scripts/sh/$sh"
done
# Todos los motores Python (los hooks, el doctor y la fase 4 los usan desde el plugin).
cp "$REPO_ROOT/scripts/py/"*.py "$TARGET_DIR/scripts/py/"
mkdir -p "$TARGET_DIR/templates/lifecycle"
cp -R "$REPO_ROOT/doc/00-governance/templates/"* "$TARGET_DIR/templates/lifecycle/"

apply_install "$PHASE"
echo "[OK] aagy-sync terminado ($DEST_DIR)."
