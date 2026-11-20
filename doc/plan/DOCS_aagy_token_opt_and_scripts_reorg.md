# Fase 3: Documentación Técnica y Release Notes

> **Referencia de Gobernanza**: Fase 3 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `refactor/aagy/token-opt-and-scripts-reorg` (`Tarea 0.1`)  
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Principal Agentic Runtime & Token Budget Optimizer`  
> **Estado**: `APROBADO`

---

## 1. Resumen Ejecutivo del Refactor

Se ha completado con éxito la reestructuración arquitectónica y optimización integral de tokens de Anything Antigravity (`aagy`), logrando:

1. **Deduplicación de `AGENTS.md`**: El archivo raíz se ha transformado en un puntero ligero ($< 1\text{ KB}$) que preserva los marcadores invariantes de *context-caching*, eliminando la duplicación de ~5.500 tokens por turno cuando el espacio de trabajo activo es el propio repositorio del plugin.
2. **Poda y Consolidación de `rules/`**: Se han purgado 37 reglas estáticas de lenguaje/stack de `rules/` (`angular`, `golang`, `java`, `python`, `typescript`, `web`, `common`), dejando estrictamente los 2 archivos de gobierno global: `rules/AGENTS.md` y `rules/pr-automerge-lifecycle.md`. Las guías se cargan ahora bajo demanda (*lazy-loaded*) mediante `skills/`, habiéndose añadido la skill formal `typescript-patterns`.
3. **Purga de Artefactos Muertos**: Se ha retirado la carpeta redundante `commands/` (97 archivos) de la raíz de `aagy`, conservando la colección oficial de comandos para Claude Code dentro de `aagy/ecc/commands/`.
4. **Reestructuración Canónica de Scripts**:
   - `scripts/py/`: Scripts Python operativos junto con su suite de pruebas en `scripts/py/tests/`.
   - `scripts/pwsh/`: Scripts PowerShell 7 operativos junto con su suite de pruebas en `scripts/pwsh/tests/`.
   - `scripts/sh/`: Scripts POSIX Bash junto con su suite de pruebas en `scripts/sh/tests/`.
   - Proxies de retrocompatibilidad en `scripts/bin/ecc-agy/` y `scripts/ecc-agy/` que aseguran cero rupturas para invocaciones heredadas.
5. **Invocaciones Canónicas**: Actualización de `hooks.json`, `complete-task-pr.ps1`, `complete-task-pr.sh`, `ecc-agy-sync.ps1`, `ecc-agy-sync.sh` e `install.ps1`.

---

## 2. Release Notes SemVer (`v2.2.0-token-opt`)

- **Optimizaciones de Rendimiento y Contexto**:
  - Ahorro de más de ~5.500 tokens por turno en el harness Antigravity.
  - Reducción del tamaño agregado de `rules/` a ~6.164 tokens (presupuesto máximo: 16.000 tokens).
  - 100% de skills activas con `description` $\le 140$ caracteres y agentes $\le 120$ caracteres.
- **Arquitectura de Scripts y Testing**:
  - Desacoplamiento por runtime en `py/`, `pwsh/` y `sh/`.
  - Cobertura de pruebas unitarias ampliada a 120 tests pasando en verde ($100\%$).
- **Garantía de No Ruptura**:
  - Todos los scripts históricos en `scripts/bin/ecc-agy/*.ps1`, `.sh` y `scripts/ecc-agy/*.py` operan como proxies hacia la nueva estructura.

---

## 3. Matriz de Promoción Multi-Tier

| Nivel de Entorno | Estado | Procedimiento de Despliegue |
| :--- | :--- | :--- |
| **LOCAL (`main`)** | Verificado | Integración continua mediante squash-automerge vía `complete-task-pr.ps1`. |
| **GLOBAL (`aagy` Plugin)** | Desplegado | Sincronizado en `~/.gemini/config/plugins/aagy` y `~/.gemini/config/plugins/ecc-agy` vía `install.ps1`. |
| **SANDBOX / LIVE** | Preparado | Etiquetado semántico según `ADR-0006`. |
