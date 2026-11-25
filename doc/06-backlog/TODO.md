# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | AAGY ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Resuelve las tareas en el orden de este fichero y respeta `deps=` (números de issue que tienen que estar cerrados antes). Orden de épicas: #103 → #80 → #91 → UI (#116) → cierre (#97).
> 2. **Flujo Git:** Una rama `<type>/<project>/<name>` y un PR por tarea, con tests unitarios/e2e en verde. Sin `auto-merge`: el merge lo hace una persona.
> 3. **Tarea Final Obligatoria:** La última tarea de todo el backlog es #97 (revisar y actualizar toda la documentación y actualizar o borrar lo desfasado). Depende de todas las demás: cualquier épica o tarea nueva se añade a su `deps=`.
> 4. **Paridad issues ↔ TODO:** Toda issue abierta tiene aquí su tarea con `issue=<N>`, y toda tarea con `issue=` apunta a una issue abierta. Las ideas en `Draft` de `IDEAS.md` no necesitan issue. Lo comprueba `python scripts/py/backlog.py gh-sync --check`; issues, PR y tareas comparten secciones (Motivación, Criterios de aceptación, Paridad, Artefactos).

---

## 1. Backlog Activo

## Épica: Plugin agnóstico, presupuesto 0 $ y sin duplicar (#103)

> Que el plugin no lleve datos de ningún proyecto, usuario ni máquina, no cueste dinero y no duplique lógica ni tokens. Propuesta P1..P6 de la auditoría del 2026-11-24. P2 y P3 van en #100 y los hooks de P5 en #96.

- [ ] **Lanzador único y fuera duplicados (envoltorios, skills repetidas, nombres de usuario)**
  <!-- aagy-task: id=single-launcher epic=plugin-agnostico-presupuesto-0-y-sin-duplicar-103 issue=106 deps=95,96 -->

- [ ] **Topes de tokens en reglas, catálogo y mensajes de hooks**
  <!-- aagy-task: id=token-budget epic=plugin-agnostico-presupuesto-0-y-sin-duplicar-103 issue=107 deps=94,96 -->

## Épica: Modelo local con Ollama (auto/tool/only) (#80)

> Delegar tareas sencillas y repetitivas en un modelo local y poder trabajar solo con modelos locales, sin dependencias duras. La configuración se lee con `aagy_config` (#104). REQ: doc/06-backlog/plans/REQ_aagy_local_model.md

## Épica: Plantilla genérica ampliable y paridad entre plugins (#91)

> Que todos los workflows y documentos salgan de una plantilla genérica ampliable y que aagy y aagy-ecc se comporten igual. REQ: doc/06-backlog/plans/REQ_aagy_generic_templates.md

## Épica: UI de Claude Code y Antigravity (#116)

> Status line, avisos de escritorio, `ccusage` opcional y extensiones de VS Code (#116, PR #119), con paridad hasta donde Antigravity lo permite. Runbook: doc/04-operations/runbooks/MANUAL_ui.md

- [ ] **Validar la UI en Windows 11 (status line, toast y CI local)**
  <!-- aagy-task: id=ui-windows-validation epic=ui-de-claude-code-y-antigravity-116 issue=122 deps=116 -->

- [ ] **Uso de tokens en Antigravity con /aagy-ui usage (equivalente a ccusage)**
  <!-- aagy-task: id=ui-agy-usage epic=ui-de-claude-code-y-antigravity-116 issue=123 deps=116 -->

- [ ] **Cerrar las asimetrías de UI de Antigravity cuando la plataforma lo permita**
  <!-- aagy-task: id=ui-agy-asymmetries epic=ui-de-claude-code-y-antigravity-116 issue=124 deps=116,122 -->

## Cierre del backlog (última tarea de todo el backlog)

> Va después de todas las épicas. Si se abre una épica o tarea nueva, su issue se añade a `deps=` de esta tarea y al cuerpo de #97.

- [ ] **REVISAR Y ACTUALIZAR TODA LA DOCUMENTACIÓN Y ACTUALIZAR O BORRAR LO DESFASADO (última tarea)**
  <!-- aagy-task: id=docs-full-review epic=plantilla-generica-ampliable-y-paridad-entre-plugins-91 issue=97 deps=81,82,83,84,85,86,87,88,89,92,93,94,95,96,100,101,105,106,107,116,122,123,124 -->

## Épica: Flujo GitHub Issues y Projects v2 (cerrada 2026-11-21 por agy)
