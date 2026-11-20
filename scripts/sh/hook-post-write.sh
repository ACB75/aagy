#!/usr/bin/env bash
# Hook determinista ejecutado tras write_file y edit_file (PostToolUse).
set -euo pipefail

TARGET_PATH="${1:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ -n "$TARGET_PATH" && "$TARGET_PATH" == *.md && -f "$TARGET_PATH" ]]; then
    LINTER="$REPO_ROOT/scripts/bin/ecc-agy/lint-markdown.sh"
    if [[ -f "$LINTER" ]]; then
        bash "$LINTER" --fix "$TARGET_PATH" >/dev/null 2>&1 || true
    fi
fi
exit 0
