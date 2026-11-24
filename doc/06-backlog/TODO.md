# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | AAGY ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Resuelve las tareas en el orden de este fichero y respeta `deps=` (números de issue que tienen que estar cerrados antes). Orden de épicas: #103 → #80 → #91 → cierre (#97).
> 2. **Flujo Git:** Una rama `<type>/<project>/<name>` y un PR por tarea, con tests unitarios/e2e en verde. Sin `auto-merge`: el merge lo hace una persona.
> 3. **Tarea Final Obligatoria:** La última tarea de todo el backlog es #97 (revisar y actualizar toda la documentación y actualizar o borrar lo desfasado). Depende de todas las demás: cualquier épica o tarea nueva se añade a su `deps=`.
> 4. **Paridad issues ↔ TODO:** Toda issue abierta tiene aquí su tarea con `issue=<N>`, y toda tarea con `issue=` apunta a una issue abierta. Las ideas en `Draft` de `IDEAS.md` no necesitan issue.

---

## 1. Backlog Activo

## Épica: Plugin agnóstico, presupuesto 0 $ y sin duplicar (#103)

> Que el plugin no lleve datos de ningún proyecto, usuario ni máquina, no cueste dinero y no duplique lógica ni tokens. Propuesta P1..P6 de la auditoría del 2026-11-24. P2 y P3 van en #100 y los hooks de P5 en #96.

- [ ] **Presupuesto 0 $: CI local en pre-push y Actions opcionales apagadas (incluye la Idea 2)**
  <!-- aagy-task: id=budget-zero epic=plugin-agnostico-presupuesto-0-y-sin-duplicar-103 issue=105 deps=81 -->

- [ ] **Lanzador único y fuera duplicados (envoltorios, skills repetidas, nombres de usuario)**
  <!-- aagy-task: id=single-launcher epic=plugin-agnostico-presupuesto-0-y-sin-duplicar-103 issue=106 deps=95,96 -->

- [ ] **Topes de tokens en reglas, catálogo y mensajes de hooks**
  <!-- aagy-task: id=token-budget epic=plugin-agnostico-presupuesto-0-y-sin-duplicar-103 issue=107 deps=94,96 -->

## Épica: Modelo local con Ollama (auto/tool/only) (#80)

> Delegar tareas sencillas y repetitivas en un modelo local y poder trabajar solo con modelos locales, sin dependencias duras. La configuración se lee con `aagy_config` (#104). REQ: doc/06-backlog/plans/REQ_aagy_local_model.md

- [ ] **Reglas de delegación al modelo local y nivel local en /model-route**
  <!-- aagy-task: id=local-model-rules epic=modelo-local-con-ollama-auto-tool-only-80 issue=83 deps=81,82 -->

- [ ] **Guarda de ficheros privados que avisa y pregunta**
  <!-- aagy-task: id=local-model-private-guard epic=modelo-local-con-ollama-auto-tool-only-80 issue=84 deps=82 -->

- [ ] **Modo solo local en Claude Code con lanzador claude-local**
  <!-- aagy-task: id=local-model-claude-only epic=modelo-local-con-ollama-auto-tool-only-80 issue=85 deps=82 -->

- [ ] **Modo solo local en Antigravity con el SDK (agy-local)**
  <!-- aagy-task: id=local-model-agy-only epic=modelo-local-con-ollama-auto-tool-only-80 issue=86 deps=82 -->

- [ ] **Check DOC-16 del modelo local en los doctores**
  <!-- aagy-task: id=local-model-doctor epic=modelo-local-con-ollama-auto-tool-only-80 issue=87 deps=81,82 -->

- [ ] **Bench de modelos locales y registro de uso**
  <!-- aagy-task: id=local-model-bench epic=modelo-local-con-ollama-auto-tool-only-80 issue=88 deps=81 -->

- [ ] **Guía de autocompletado local en VS Code y Antigravity**
  <!-- aagy-task: id=local-model-editor-fim epic=modelo-local-con-ollama-auto-tool-only-80 issue=89 -->

## Épica: Plantilla genérica ampliable y paridad entre plugins (#91)

> Que todos los workflows y documentos salgan de una plantilla genérica ampliable y que aagy y aagy-ecc se comporten igual. REQ: doc/06-backlog/plans/REQ_aagy_generic_templates.md

- [ ] **Plantilla base genérica con puntos de extensión**
  <!-- aagy-task: id=generic-template-base epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=92 -->

- [ ] **Issues, PR y TODO con las mismas secciones y check de paridad issues ↔ TODO**
  <!-- aagy-task: id=generic-template-issues-todo epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=93 deps=92 -->

- [ ] **Esqueleto común de workflows (skills, comandos, agentes) y su check**
  <!-- aagy-task: id=generic-template-workflows epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=94 deps=92 -->

- [ ] **Fase 4 (complete-task-pr) con motor Python único en los dos plugins**
  <!-- aagy-task: id=parity-phase4-python epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=95 -->

- [ ] **Paridad de hooks entre plugins con un solo motor Python (relevo, compactación e inicio)**
  <!-- aagy-task: id=parity-hooks epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=96 -->

- [ ] **Sacar del repo todo lo referente a home-lab y el entorno (incluye P2 y P3 de #103)**
  <!-- aagy-task: id=remove-home-lab epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=100 -->

- [ ] **Hard sync con lista de ficheros instalados**
  <!-- aagy-task: id=hard-sync-manifest epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=101 -->

## Cierre del backlog (última tarea de todo el backlog)

> Va después de todas las épicas. Si se abre una épica o tarea nueva, su issue se añade a `deps=` de esta tarea y al cuerpo de #97.

- [ ] **REVISAR Y ACTUALIZAR TODA LA DOCUMENTACIÓN Y ACTUALIZAR O BORRAR LO DESFASADO (última tarea)**
  <!-- aagy-task: id=docs-full-review epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=97 deps=81,82,83,84,85,86,87,88,89,92,93,94,95,96,100,101,105,106,107 -->

## Épica: Flujo GitHub Issues y Projects v2 (cerrada 2026-11-21 por agy)
