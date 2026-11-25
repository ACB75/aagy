#!/usr/bin/env bash
# Linter Markdown (PostToolUse): envoltorio fino de scripts/py/hook_post_write.py --format agy.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$(command -v python3 || command -v python)"
if [[ $# -gt 0 ]]; then
    "$PYTHON" -c 'import json,sys; print(json.dumps({"toolCall": {"args": {"Path": sys.argv[1]}}}))' "$1" \
        | "$PYTHON" "$SCRIPT_DIR/../py/hook_post_write.py" --format agy
else
    "$PYTHON" "$SCRIPT_DIR/../py/hook_post_write.py" --format agy
fi
