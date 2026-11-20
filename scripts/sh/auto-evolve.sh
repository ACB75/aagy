#!/usr/bin/env bash
# ==============================================================================
# Script: auto-evolve.sh (Debian 12 / Linux / WSL)
# Descripción: Motor unificado y agnóstico de autodescubrimiento y automejora (aagy / ecc).
# Finales de línea estrictamente POSIX LF (\n).
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
CLI_SCRIPT="$ROOT_DIR/scripts/py/self_improve.py"

if [[ ! -f "$CLI_SCRIPT" ]]; then
    echo "Error: No se encontró el motor unificado en $CLI_SCRIPT" >&2
    exit 1
fi

ARGS=()
SHOW_HELP=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --help|-h|-Help)
            SHOW_HELP=1
            shift
            ;;
        --discover|-d|-Discover)
            ARGS+=("--discover")
            shift
            ;;
        --review|-Review)
            ARGS+=("--review" "${2:-}")
            shift 2 || shift
            ;;
        --promote|-Promote)
            ARGS+=("--promote" "${2:-}")
            shift 2 || shift
            ;;
        --confirm|-Confirm)
            ARGS+=("--confirm")
            shift
            ;;
        --capture-stop|-CaptureStop)
            ARGS+=("--capture-stop")
            shift
            ;;
        --evaluate|-Evaluate)
            ARGS+=("--evaluate" "${2:-}")
            shift 2 || shift
            ;;
        --task|-Task)
            ARGS+=("--task" "${2:-}")
            shift 2 || shift
            ;;
        --repo-root|-RepoRoot)
            ARGS+=("--repo-root" "${2:-.}")
            shift 2 || shift
            ;;
        --plugin-data|-PluginData)
            ARGS+=("--plugin-data" "${2:-}")
            shift 2 || shift
            ;;
        --scope|-Scope)
            ARGS+=("--scope" "${2:-all}")
            shift 2 || shift
            ;;
        --write|-w|-Write)
            ARGS+=("--write")
            shift
            ;;
        --dry-run|-DryRun)
            ARGS+=("--dry-run")
            shift
            ;;
        --json|-Json)
            ARGS+=("--json")
            shift
            ;;
        --limit|-l|-Limit)
            ARGS+=("--limit" "${2:-5}")
            shift 2 || shift
            ;;
        --min-occurrences|-MinOccurrences)
            ARGS+=("--min-occurrences" "${2:-2}")
            shift 2 || shift
            ;;
        --tier|-t|-Tier)
            ARGS+=("--tier" "${2:-skill}")
            shift 2 || shift
            ;;
        *)
            ARGS+=("$1")
            shift
            ;;
    esac
done

if [[ $SHOW_HELP -eq 1 ]]; then
    echo "Uso: $(basename "$0") [--repo-root PATH] [--discover] [--review ID] [--promote ID] [--confirm] [--capture-stop] [--evaluate TEXT] [--scope SCOPE] [--tier TYPE] [--limit N] [--json] [--help]"
    exit 0
fi

python3 "$CLI_SCRIPT" "${ARGS[@]}"
