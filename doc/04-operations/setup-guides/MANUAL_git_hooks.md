# Manual de Operación: Git Hooks Nativos e Infraestructura de Calidad

> **Referencia de Gobernanza**: Automatización y Aseguramiento de Calidad en Git  
> **Ámbito**: Repositorio Local `ACB75/aagy`, Monorepo `home-lab` y Arneses de Desarrollo  
> **Fecha de Publicación**: `2026-11-20`  

---

## 1. Propósito y Arquitectura de Hooks

Para garantizar que ningún desarrollador o agente introduzca commits mal formateados o documentación Markdown que viole las compuertas de calidad, el arnés provee hooks nativos que se ejecutan localmente en la máquina del desarrollador antes de que los cambios salgan hacia el repositorio remoto.

### 1.1. Hooks Implementados

1. **`pre-commit`**:
   - Inspecciona los archivos Markdown (`.md`) que se encuentran en el área de preparación (*staging*).
   - Ejecuta `lint-markdown.ps1 -CheckOnly` o `lint-markdown.sh --check-only` exclusivamente sobre los archivos modificados (`git diff --cached --name-only --diff-filter=ACM`).
   - Si no hay archivos `.md` en preparación, el hook finaliza en $< 50\text{ ms}$.
   - Si se detectan violaciones de formato (por ejemplo `MD012` o `MD022`), aborta la confirmación informando el comando exacto para auto-formatear con `-Fix`.

2. **`commit-msg`**:
   - Intercepta el archivo temporal con el mensaje de confirmación generado por Git.
   - Ejecuta `format_commit.py --validate-file <path> --strict`.
   - Exige formato estandarizado `[type]-[projects]: <title>` o `type(project): <title>` y un cuerpo explicativo obligatorio de al menos 20 caracteres.

---

## 2. Instalación y Desinstalación

Los hooks se distribuyen en `scripts/py/hooks/` y se vinculan a `.git/hooks/` mediante scripts idempotentes.

### 2.1. Instalación

En Windows 11 (`pwsh`):

```powershell
pwsh -File scripts/ps1/install-git-hooks.ps1
```

En Linux o WSL (`bash` / `sh`):

```sh
./scripts/sh/install-git-hooks.sh
```

### 2.2. Desinstalación

En caso de requerir la retirada de los hooks:

```powershell
pwsh -File scripts/ps1/install-git-hooks.ps1 -Uninstall
```

O en Linux:

```sh
./scripts/sh/install-git-hooks.sh --uninstall
```

---

## 3. Mecanismos de Bypass en Emergencias

En situaciones excepcionales (por ejemplo, resolución de conflictos en vivo, rebases interactivos complejos o parches urgentes de infraestructura):

1. **Bypass Nativo de Git**:

   ```sh
   git commit --no-verify -m "[hotfix]-[net]: correccion de gateway"
   ```

2. **Variable de Entorno de Bypass**:

   ```sh
   GIT_HOOKS_BYPASS=1 git commit -m "..."
   ```

---

## 4. Métricas de Rendimiento y Rendimiento SRE

- **Overhead sin Markdown**: $< 50\text{ ms}$ (ejecución POSIX sh inmediata).
- **Overhead con Markdown Staged**: $< 600\text{ ms}$ (invocación dirigida a un solo archivo).
- **Aislamiento**: Zero dependencias externas; utiliza el entorno local de Python y herramientas ya instaladas en el repositorio.
