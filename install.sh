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
    PY="$(command -v python3 || command -v python)"
    echo "[+] Syncing aagy-ecc mirror (skills, agents, rules, Python engines)..."
    "${PY}" "${SCRIPT_DIR}/scripts/py/sync_aagy_ecc.py" --repo-root "${SCRIPT_DIR}"
    "${PY}" "${SCRIPT_DIR}/scripts/py/install_manifest.py" write --dest "${SOURCE_DIR}" --harness claude --profile full --repo-root "${SCRIPT_DIR}" || true
    if [ "${AAGY_NO_PLUGIN:-0}" = "1" ]; then
      echo "[i] AAGY_NO_PLUGIN=1: skipping Claude Code plugin install."
    elif command -v claude >/dev/null 2>&1; then
      echo "[+] Registering local marketplace and installing aagy-ecc in Claude Code..."
      claude plugin marketplace add "${SOURCE_DIR}"
      claude plugin install aagy-ecc@aagy-ecc
    else
      echo "[!] 'claude' CLI not found. Install manually with:"
      echo "    claude plugin marketplace add \"${SOURCE_DIR}\""
      echo "    claude plugin install aagy-ecc@aagy-ecc"
    fi
    if [ -n "${DESTINATION}" ]; then
      echo "[+] Copying project template (CLAUDE.md + .claude/) to: ${DESTINATION}"
      mkdir -p "${DESTINATION}"
      cp -f "${SOURCE_DIR}/project-template/CLAUDE.md" "${DESTINATION}/"
      cp -rf "${SOURCE_DIR}/project-template/.claude" "${DESTINATION}/"
    fi
    echo "[✓] aagy-ecc (Claude Code) ready."
    ;;
  agy)
    DEST="${DESTINATION:-${HOME}/.gemini/config/plugins/aagy}"
    echo "[+] Deploying unified Anything Antigravity (aagy) plugin (Tier 1) to: ${DEST}"
    if [ -f "${SCRIPT_DIR}/scripts/sh/aagy-sync.sh" ]; then
      bash "${SCRIPT_DIR}/scripts/sh/aagy-sync.sh" generic "${DEST}"
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
