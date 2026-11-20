---
trigger: always_on
---

# Regla de Ciclo Completo de PR, Autoresolución y Automerge (`pr-automerge-lifecycle.md`)

> **Invariante Canónico de Monorepo y Calidad de Integración**  
> Aplica a todas las ramas de tarea (`feat/*`, `fix/*`, `refactor/*`, `chore/*`, `infra/*`).

---

## 1. Flujo Automatizado de Cierre de Tarea

Por cada tarea que introduzca modificaciones o adiciones de código en el monorepo:

1. **Aviso de Revisión Manual Obligatoria (Pre-Flight Review)**:
   Antes de ejecutar cualquier mutación en git o GitHub, el sistema DEBE generar y presentar al usuario un aviso estructurado con:
   - Rama de origen y rama destino (`main`).
   - Título propuesto con formato `[type]-[projects]: <title>`.
   - Cuerpo explicativo del commit y la Pull Request.
   - Resumen de archivos modificados, añadidos y eliminados (`git status -s`).
   - Esperar confirmación explícita antes de fusionar.

2. **Commit Atómico y Push**:
   - Comprometer cambios pendientes con el título y mensaje estandarizado.
   - Publicar la rama en `origin`.

3. **Creación o Detección de Pull Request**:
   - Crear la Pull Request con `gh pr create` hacia `main` heredando el título y mensaje explicativo.

4. **Detección y Autoresolución de Conflictos**:
   - Comprobar divergencia contra `origin/main`.
   - Si existen conflictos mergeables, autoresolverlos favoreciendo los cambios de la tarea en conflicto y registrar el commit de resolución.

5. **Automerge y Limpieza de Ramas**:
   - Ejecutar squash-automerge de la PR (`gh pr merge <num> --squash --delete-branch`).
   - Retornar automáticamente a la rama `main` y sincronizar (`git pull origin main`).
   - Eliminar la rama local de la tarea (`git branch -D <branch>`).

---

## 2. Invocación Estandarizada

```powershell
# Revisión previa sin mutaciones
pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -ReviewOnly

# Ejecución tras confirmación del usuario
pwsh -File scripts/bin/ecc-agy/complete-task-pr.ps1 -Yes -Title "[type]-[projects]: <title>"
```
