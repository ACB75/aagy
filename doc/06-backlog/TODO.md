# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | AAGY ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Analiza las dependencias entre tareas y resuélvelas en el orden secuencial óptimo (gobernanza/harness → tokens/contexto → guardrails de calidad → automatización de git/PRs).
> 2. **Flujo Git Automatizado:** Genera ramas atómicas por tarea, resuelve conflictos de forma contextual, ejecuta tests unitarios/e2e y realiza `auto-merge` continuo en la rama principal hasta agotar el presupuesto de tokens asignado.
> 3. **Tarea Final Obligatoria (Higiene y Meta-Herramientas):** Al completar el backlog funcional, ejecuta una fase final de limpieza: purgar dependencias huérfanas, eliminar código muerto, actualizar documentación técnica y desplegar el motor de autodescubrimiento para sintetizar `skills`, `rules`, `agents` y `git hooks` optimizados para los flujos repetitivos del repositorio.

---

## 1. Backlog Activo

## Épica: Plantilla genérica ampliable y paridad entre plugins (#91)

> Que todos los workflows y documentos salgan de una plantilla genérica ampliable y que aagy y aagy-ecc se comporten igual. REQ: doc/06-backlog/plans/REQ_aagy_generic_templates.md

- [ ] **Plantilla base genérica con puntos de extensión**
  <!-- aagy-task: id=generic-template-base epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=92 -->

- [ ] **Issues, PR y TODO con las mismas secciones y check de paridad issues ↔ TODO**
  <!-- aagy-task: id=generic-template-issues-todo epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=93 -->

- [ ] **Esqueleto común de workflows (skills, comandos, agentes) y su check**
  <!-- aagy-task: id=generic-template-workflows epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=94 -->

- [ ] **Fase 4 (complete-task-pr) con motor Python único en los dos plugins**
  <!-- aagy-task: id=parity-phase4-python epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=95 -->

- [ ] **Paridad de hooks entre plugins (relevo, compactación e inicio)**
  <!-- aagy-task: id=parity-hooks epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=96 -->

- [ ] **Sacar del repo todo lo referente a home-lab**
  <!-- aagy-task: id=remove-home-lab epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=100 -->

- [ ] **Hard sync con lista de ficheros instalados**
  <!-- aagy-task: id=hard-sync-manifest epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=101 -->

- [ ] **REVISAR Y ACTUALIZAR TODA LA DOCUMENTACIÓN Y ACTUALIZAR O BORRAR LO DESFASADO (última tarea)**
  <!-- aagy-task: id=docs-full-review epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=97 -->

## Épica: Flujo GitHub Issues y Projects v2 (cerrada 2026-11-21 por agy)
