#!/usr/bin/env sh
# Instala o desinstala los Git hooks nativos (pre-commit, commit-msg, pre-push) en .git/hooks/

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
GIT_HOOKS_DIR="$REPO_ROOT/.git/hooks"
SOURCE_HOOKS_DIR="$REPO_ROOT/scripts/py/hooks"

if [ ! -d "$GIT_HOOKS_DIR" ]; then
    echo "[ERROR] Directorio .git/hooks no encontrado en $REPO_ROOT" >&2
    exit 1
fi

HOOKS="pre-commit commit-msg pre-push"

if [ "$1" = "--uninstall" ] || [ "$1" = "-u" ]; then
    echo "[+] Desinstalando Git hooks en $GIT_HOOKS_DIR..."
    for name in $HOOKS; do
        if [ -f "$GIT_HOOKS_DIR/$name" ]; then
            rm -f "$GIT_HOOKS_DIR/$name"
            echo "  [-] Eliminado: $name"
        fi
    done
    echo "[OK] Git hooks desinstalados."
    exit 0
fi

echo "[+] Instalando Git hooks en $GIT_HOOKS_DIR..."
for name in $HOOKS; do
    src="$SOURCE_HOOKS_DIR/$name"
    dst="$GIT_HOOKS_DIR/$name"
    if [ -f "$src" ]; then
        cp -f "$src" "$dst"
        chmod +x "$dst"
        echo "  [+] Instalado y ejecutable: $name"
    fi
done

echo "[OK] Git hooks (pre-commit, commit-msg, pre-push) instalados con éxito."
exit 0
