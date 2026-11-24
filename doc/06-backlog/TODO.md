# PROTOCOLO DE EJECUCIÓN Y BACKLOG MAESTRO | AAGY ECOSYSTEM

> **Directiva de Agente Autónomo:**
>
> 1. **Orden Topológico:** Analiza las dependencias entre tareas y resuélvelas en el orden secuencial óptimo (gobernanza/harness → tokens/contexto → guardrails de calidad → automatización de git/PRs).
> 2. **Flujo Git Automatizado:** Genera ramas atómicas por tarea, resuelve conflictos de forma contextual, ejecuta tests unitarios/e2e y realiza `auto-merge` continuo en la rama principal hasta agotar el presupuesto de tokens asignado.
> 3. **Tarea Final Obligatoria (Higiene y Meta-Herramientas):** Al completar el backlog funcional, ejecuta una fase final de limpieza: purgar dependencias huérfanas, eliminar código muerto, actualizar documentación técnica y desplegar el motor de autodescubrimiento para sintetizar `skills`, `rules`, `agents` y `git hooks` optimizados para los flujos repetitivos del repositorio.

---

## 1. Backlog Activo

## Épica: Flujo GitHub Issues y Projects v2 (cerrada 2026-11-21 por agy)

## Épica: Modelo local con Ollama (auto/tool/only) (#80)

> Delegar tareas sencillas y repetitivas en un modelo local y poder trabajar solo con modelos locales, sin dependencias duras. REQ: doc/06-backlog/plans/REQ_aagy_local_model.md

- [ ] **Servidor MCP genérico aagy-local con catálogo de tareas declarativo**
  <!-- aagy-task: id=local-model-mcp epic=modelo-local-con-ollama-auto-tool-only-80 issue=81 -->

- [ ] **Interruptores del modelo local (auto/off/tool/only) y /aagy-local**
  <!-- aagy-task: id=local-model-switch epic=modelo-local-con-ollama-auto-tool-only-80 issue=82 -->

- [ ] **Reglas de delegación al modelo local y nivel local en /model-route**
  <!-- aagy-task: id=local-model-rules epic=modelo-local-con-ollama-auto-tool-only-80 issue=83 -->

- [ ] **Guarda de ficheros privados que avisa y pregunta**
  <!-- aagy-task: id=local-model-private-guard epic=modelo-local-con-ollama-auto-tool-only-80 issue=84 -->

- [ ] **Modo solo local en Claude Code con lanzador claude-local**
  <!-- aagy-task: id=local-model-claude-only epic=modelo-local-con-ollama-auto-tool-only-80 issue=85 -->

- [ ] **Modo solo local en Antigravity con el SDK (agy-local)**
  <!-- aagy-task: id=local-model-agy-only epic=modelo-local-con-ollama-auto-tool-only-80 issue=86 -->

- [ ] **Check DOC-16 del modelo local en los doctores**
  <!-- aagy-task: id=local-model-doctor epic=modelo-local-con-ollama-auto-tool-only-80 issue=87 -->

- [ ] **Bench de modelos locales y registro de uso**
  <!-- aagy-task: id=local-model-bench epic=modelo-local-con-ollama-auto-tool-only-80 issue=88 -->

- [ ] **Guía de autocompletado local en VS Code y Antigravity**
  <!-- aagy-task: id=local-model-editor-fim epic=modelo-local-con-ollama-auto-tool-only-80 issue=89 -->
