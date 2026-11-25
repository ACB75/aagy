# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | AAGY ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Resuelve las tareas en el orden de este fichero y respeta `deps=` (números de issue que tienen que estar cerrados antes). Las épicas #103, #80 y #91 están cerradas; queda la validación de la UI en Windows (#122).
> 2. **Flujo Git:** Una rama `<type>/<project>/<name>` y un PR por tarea, con tests unitarios/e2e en verde. Sin `auto-merge`: el merge lo hace una persona.
> 3. **Tarea Final Obligatoria:** Cada ronda de épicas termina con una tarea que revisa toda la documentación y borra lo desfasado (como #97). Depende de todas las demás: cualquier épica o tarea nueva se añade a su `deps=`.
> 4. **Paridad issues ↔ TODO:** Toda issue abierta tiene aquí su tarea con `issue=<N>`, y toda tarea con `issue=` apunta a una issue abierta. Las ideas en `Draft` de `IDEAS.md` no necesitan issue. Lo comprueba `python scripts/py/backlog.py gh-sync --check`; issues, PR y tareas comparten secciones (Motivación, Criterios de aceptación, Paridad, Artefactos).

---

## 1. Backlog Activo

## Épica: UI de Claude Code y Antigravity (#116)

> Status line, avisos de escritorio, `ccusage` opcional y extensiones de VS Code (#116, PR #119), con paridad hasta donde Antigravity lo permite. Runbook: doc/04-operations/runbooks/MANUAL_ui.md

- [ ] **Validar la UI en Windows 11 (status line, toast y CI local)**
  <!-- aagy-task: id=ui-windows-validation epic=ui-de-claude-code-y-antigravity-116 issue=122 deps=116 -->

## Épica: Flujo GitHub Issues y Projects v2 (cerrada 2026-11-21 por agy)
