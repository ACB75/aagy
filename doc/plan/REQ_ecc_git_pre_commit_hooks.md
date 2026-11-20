# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/git-pre-commit-hooks`  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Carbon (C6) / Git Operations Specialist`  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**: Actualmente, la validación de formato de commits (`format_commit.py`) y de sintaxis Markdown (`lint-markdown.ps1`) se ejecuta principalmente al invocar `complete-task-pr.ps1` o en pipelines de CI. Si un desarrollador o agente ejecuta un comando `git commit` manual directamente desde la terminal fuera de los scripts del arnés, es posible introducir commits de una sola línea sin formato `[type]-[projects]: <title>` o archivos `.md` con violaciones de markdownlint, obligando a correcciones posteriores.
- **Objetivo Principal**: Implementar una infraestructura determinista de Git hooks locales (`commit-msg` y `pre-commit`) con scripts de instalación y desinstalación idempotentes (`install-git-hooks.ps1` y `.sh`), interceptando commits no conformes en $<800\text{ ms}$ y soportando bypass de emergencia controlado (`--no-verify`).
- **Alcance (`In-Scope`)**:
  - `scripts/ecc-agy/hooks/pre-commit`: Validador de archivos `.md` en staging.
  - `scripts/ecc-agy/hooks/commit-msg`: Validador de Conventional Commits vía `format_commit.py --strict`.
  - `scripts/bin/ecc-agy/install-git-hooks.ps1` y `install-git-hooks.sh`: Instalador y desinstalador idempotente.
  - Manual operativo `doc/manual/MANUAL_git_hooks.md`.
  - Batería de pruebas unitarias en `scripts/ecc-agy/tests/test_git_hooks.py`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Forzar hooks en repositorios externos de GitHub sin clon local.
  - Bloquear commits que no toquen archivos Markdown ni mensajes de commit.

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01` (Hook `commit-msg`)**: Debe validar que el archivo temporal con el mensaje de commit contenga un título válido (`[type]-[projects]: <title>` o `type(project): <title>`) y un cuerpo explicativo de al menos 20 caracteres en modo estricto.
- **`RF-02` (Hook `pre-commit`)**: Debe inspeccionar únicamente los archivos `.md` modificados/añadidos en el staging area (`git diff --cached --name-only --diff-filter=ACM`) y verificar su conformidad con `lint-markdown.ps1` o `.sh`.
- **`RF-03` (Instalador Idempotente)**: `install-git-hooks.ps1` y `.sh` deben instalar los hooks en `.git/hooks/` de forma no destructiva (con backup si ya existen hooks de usuario) y ofrecer opción `-Uninstall` para retirarlos limpiamente.
- **`RF-04` (Soporte Dual Windows/Linux & Bypass)**: Ejecución transparente en Windows 11 (`pwsh`), Git Bash y Linux/WSL (`sh`). Respeto íntegro del flag estándar `git commit --no-verify`.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [x] **`CA-01`**: Dado un mensaje de commit inválido (ej. `"wip"`), cuando se intente comprometer en Git, entonces `commit-msg` rechaza la operación con código de salida `1` y un mensaje de ayuda claro.
- [x] **`CA-02`**: Dado un archivo Markdown staged con líneas en blanco consecutivas (`MD012`), cuando se ejecute el hook `pre-commit`, entonces la operación se detiene indicando la violación y el comando de corrección.
- [x] **`CA-03`**: Dado un repositorio clonado, cuando se invoque `install-git-hooks.ps1` repetidas veces, la operación es idempotente y los hooks quedan operativos en `.git/hooks/`.
- [x] **`CA-04`**: Tiempo de ejecución en ausencia de archivos `.md` staged $< 150\text{ ms}$.

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin impacto en SDKs. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin base de datos. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin cambios de red. |
| **Resolución Split-DNS** | `NO` | - | Sin cambios DNS. |
| **Restricciones de Hardware** | `NO` | Bajo | Hooks ultraligeros basados en shell/Python stdlib. |
| **Variables `.env` / Secretos** | `NO` | - | Sin secretos requeridos. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva (Non-Breaking)**:
  - Los hooks se instalan localmente en `.git/hooks/`.
  - El flag nativo `--no-verify` permite omitir las comprobaciones en situaciones de emergencia o rebase interactivo.
