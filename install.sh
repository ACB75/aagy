#!/usr/bin/env bash
# ==============================================================================
# Anything Antigravity (aagy / aagy-ecc) Multi-Distribution Installer (Linux / WSL / macOS)
# Targets: agy | claude | aagy-ecc | homelab (alias to agy)
# Finales de línea estrictamente POSIX LF (\n).
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-agy}"
DESTINATION="${2:-}"

echo "================================================================="
echo "         ANYTHING ANTIGRAVITY (AAGY / AAGY-ECC) INSTALLER        "
echo "================================================================="
echo "Target distribution: ${TARGET}"

if [ "${TARGET}" = "homelab" ]; then
  echo "[i] Note: 'homelab' has been unified into 'aagy'. Deploying aagy..."
  TARGET="agy"
fi
if [ "${TARGET}" = "aagy-ecc" ]; then
  TARGET="claude"
fi

case "${TARGET}" in
  claude)
    SOURCE_DIR="${SCRIPT_DIR}/aagy-ecc"
    DEST="${DESTINATION:-$(pwd)}"
    echo "[+] Deploying aagy-ecc (Claude Code) boilerplates to: ${DEST}"
    mkdir -p "${DEST}"
    cp -f "${SOURCE_DIR}/CLAUDE.md" "${DEST}/"
    cp -rf "${SOURCE_DIR}/.claude" "${DEST}/"
    echo "[✓] aagy-ecc (Claude Code) installed successfully."
    ;;
  agy)
    DEST="${DESTINATION:-${HOME}/.gemini/config/plugins/aagy}"
    echo "[+] Deploying unified Anything Antigravity (aagy) plugin (Tier 1) to: ${DEST}"
    if [ -f "${SCRIPT_DIR}/scripts/sh/ecc-agy-sync.sh" ]; then
      bash "${SCRIPT_DIR}/scripts/sh/ecc-agy-sync.sh" generic "${DEST}"
    else
      mkdir -p "${DEST}/skills" "${DEST}/agents" "${DEST}/rules"
      cp -f "${SCRIPT_DIR}/plugin.json" "${DEST}/"
      cp -f "${SCRIPT_DIR}/rules/AGENTS.md" "${DEST}/rules/"
    fi
    echo "[✓] Unified aagy plugin installed successfully."
    ;;
  *)
    echo "Error: Unknown target '${TARGET}'. Use 'agy', 'claude' or 'aagy-ecc'." >&2
    exit 1
    ;;
esac

echo "================================================================="
echo "Installation complete."
