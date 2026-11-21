# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | AAGY ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Analiza las dependencias entre tareas y resuélvelas en el orden secuencial óptimo (gobernanza/harness → tokens/contexto → guardrails de calidad → automatización de git/PRs).
> 2. **Flujo Git Automatizado:** Genera ramas atómicas por tarea, resuelve conflictos de forma contextual, ejecuta tests unitarios/e2e y realiza `auto-merge` continuo en la rama principal hasta agotar el presupuesto de tokens asignado.
> 3. **Tarea Final Obligatoria (Higiene y Meta-Herramientas):** Al completar el backlog funcional, ejecuta una fase final de limpieza: purgar dependencias huérfanas, eliminar código muerto, actualizar documentación técnica y desplegar el motor de autodescubrimiento para sintetizar `skills`, `rules`, `agents` y `git hooks` optimizados para los flujos repetitivos del repositorio.

---

## 1. Backlog Activo

## Épica: Flujo GitHub Issues y Projects v2

- [ ] **Inyectar Closes #N, labels, assignee, milestone y projects en complete-task-pr (GH #61)**
  <!-- aagy-task: id=gh-61 epic=flujo-github-issues-y-projects-v2 -->
  GitHub Issue: <https://github.com/ACB75/aagy/issues/61> | Labels: enhancement, harness:both, area:scripts | Milestone: v4.2.0

- [ ] **Workflows GitHub Actions de auto-sincronizacion Team Planning <-> aagy (GH #62)**
  <!-- aagy-task: id=gh-62 epic=flujo-github-issues-y-projects-v2 -->
  GitHub Issue: <https://github.com/ACB75/aagy/issues/62> | Labels: enhancement, harness:both, area:infra | Milestone: v4.2.0

- [ ] **Sincronizador backlog.py <-> GitHub Issues para Claude y Antigravity (GH #63)**
  <!-- aagy-task: id=gh-63 epic=flujo-github-issues-y-projects-v2 -->
  GitHub Issue: <https://github.com/ACB75/aagy/issues/63> | Labels: enhancement, harness:both, area:scripts | Milestone: v4.2.0

- [ ] **Soporte de sub-issues y adjuntar artefactos de lifecycle en GitHub Issues (GH #64)**
  <!-- aagy-task: id=gh-64 epic=flujo-github-issues-y-projects-v2 -->
  GitHub Issue: <https://github.com/ACB75/aagy/issues/64> | Labels: enhancement, harness:both, area:scripts | Milestone: v4.2.0
