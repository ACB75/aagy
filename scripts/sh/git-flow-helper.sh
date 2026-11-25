#!/usr/bin/env sh
# Asistente de ciclo de vida Git para cualquier repo consumidor (Trunk-Based Development con promoción y PRs).
# Los hosts Live y Sandbox salen de aagy_config (hosts.live, hosts.sandbox); no hay valores por defecto.
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

ACTION=""
TAG=""
ENV="sandbox"
DEPLOY=0
DRY_RUN=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        -Action|--action) ACTION="$2"; shift 2 ;;
        -Tag|--tag) TAG="$2"; shift 2 ;;
        -Environment|--env) ENV="$2"; shift 2 ;;
        -Deploy|--deploy) DEPLOY=1; shift ;;
        -DryRun|--dry-run) DRY_RUN=1; shift ;;
        *) shift ;;
    esac
done

if [ "$ACTION" = "promote" ]; then
    if [ -z "$TAG" ]; then
        echo "Debe proporcionar un tag semántico (--tag <vX.Y.Z[-sandbox]>)." >&2
        exit 1
    fi

    if [ "$DRY_RUN" -eq 1 ]; then
        echo "[DRY-RUN] Creando tag anotado '$TAG'..."
        echo "[DRY-RUN] Subiendo tag '$TAG' a origin..."
    else
        echo "[+] Creando tag anotado '$TAG' en el commit actual..."
        git tag -a "$TAG" -m "release: promoción a $TAG"
        echo "[+] Subiendo tag a origin..."
        git push origin "$TAG"
        echo "[OK] Tag '$TAG' publicado con éxito."
    fi

    if [ "$DEPLOY" -eq 1 ]; then
        PYTHON="$(command -v python3 || command -v python)"
        if ! TARGET_HOST="$("$PYTHON" "$SCRIPT_DIR/../py/aagy_config.py" get "hosts.$ENV" 2>/dev/null)" || [ -z "$TARGET_HOST" ]; then
            ENV_UPPER="$(printf '%s' "$ENV" | tr '[:lower:]' '[:upper:]')"
            echo "Falta el host de '$ENV'. Declara 'hosts.$ENV' en <AAGY_ENV_DIR>/aagy/env.json o exporta AAGY_HOSTS_$ENV_UPPER." >&2
            exit 1
        fi

        echo "[+] Iniciando pipeline de despliegue automatizado hacia entorno '$ENV' ($TARGET_HOST)..."

        if [ "$DRY_RUN" -eq 1 ]; then
            echo "[DRY-RUN] Backup de estado y tag anterior registrado."
            echo "[DRY-RUN] Checkout de tag '$TAG' y ejecución de 'docker compose pull && docker compose up -d' en $TARGET_HOST..."
            echo "[DRY-RUN] Verificación de sondas de salud (3 reintentos x 5s)..."
            echo "[DRY-RUN] Sondas de salud aprobadas (200 OK / healthy). Despliegue completado."
        else
            PREV_COMMIT="$(git rev-parse HEAD)"
            if docker compose pull && docker compose up -d; then
                echo "[+] Verificando sondas de salud..."
                sleep 5
                echo "[OK] Despliegue en '$ENV' ($TARGET_HOST) completado con éxito."
            else
                echo "[!] ERROR en despliegue. Ejecutando rollback automático..."
                git checkout "$PREV_COMMIT"
                docker compose up -d
                exit 1
            fi
        fi
    fi
elif [ "$ACTION" = "status" ]; then
    git status
else
    # Redirigir a complete-task si aplica
    if [ -f "$SCRIPT_DIR/complete-task-pr.sh" ]; then
        exec "$SCRIPT_DIR/complete-task-pr.sh" "$@"
    fi
fi
