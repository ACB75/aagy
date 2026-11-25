# Índice Maestro de Documentación y Gobernanza (`/doc` v2)

> **Espina Dorsal Documental**: Repositorio [ACB75/aagy](https://github.com/ACB75/aagy) (`aagy` en transición a `aagy`)  
> **Versión del Esquema**: `2.0.0` | **Última Actualización**: 2026-11-20

---

## 1. Raíz Operativa y Contrato Documental (`doc/`)

- 📑 **[`doc/INDEX.md`](INDEX.md)**: Este índice maestro de navegación (sustituye al antiguo README duplicado en `doc/`).
- 🧭 **[`doc/CONTEXT.md`](CONTEXT.md)**: Vocabulario estable de dominio, arquitectura Two-Tier y límites de módulos.
- 🚦 **[`doc/STATUS.md`](STATUS.md)**: Métricas de calidad, SonarQube Rating A, cobertura `pytest` y presupuesto de tokens.
- 📜 **[`doc/LOG.md`](LOG.md)**: Registro histórico append-only de hitos arquitectónicos e incidentes materiales.
- ⚙️ **[`.governance/docs-map.json`](../.governance/docs-map.json)**: Contrato v2 de rutas resuelto por [`scripts/py/docs_map.py`](../scripts/py/docs_map.py) (con fallback retrocompatible para `app`).

---

## 2. Gobernanza, Estándares y Guías Manuales (`doc/00-governance/`)

- 📏 **[`doc/00-governance/DOC_STANDARDS.md`](00-governance/DOC_STANDARDS.md)**: Especificación canónica de `/doc` v2, `<folder>/dgrms/` (`.puml`, `.bpmn`, `.mmd`) y compuertas de validación.
- 🛠️ **[`doc/00-governance/MANUAL_WORKFLOW.md`](00-governance/MANUAL_WORKFLOW.md)**: Guía de paridad 1-a-1 Manual CLI $\leftrightarrow$ Plugin y puntos de entrada flexibles (`IDEAS` $\rightarrow$ `REQ` $\rightarrow$ `PLAN` $\rightarrow$ `TODO`).
- 🛡️ **[`doc/00-governance/references/the-security-guide.md`](00-governance/references/the-security-guide.md)**: Guía de bastionado de seguridad, secretos y límites en entornos asistidos por agentes.
- 🏛️ **[`doc/00-governance/references/google-modern-stack.md`](00-governance/references/google-modern-stack.md)**: Alineación con los 5 Pilares de Ingeniería de Google.
- 📋 **[`doc/00-governance/templates/README.md`](00-governance/templates/README.md)**: Índice del ciclo de vida de 4 fases, [`TEMPLATE_ADR.md`](00-governance/templates/TEMPLATE_ADR.md) y [`TEMPLATE_POSTMORTEM.md`](00-governance/templates/TEMPLATE_POSTMORTEM.md).

---

## 3. Arquitectura y Diagramas Estructurales (`doc/01-architecture/`)

- 📘 **[`GUIA_ARQUITECTURA_HARNESS_Y_ENTORNO_AGY.md`](01-architecture/GUIA_ARQUITECTURA_HARNESS_Y_ENTORNO_AGY.md)**: Manual maestro sobre los arneses de IA, runtime Google Antigravity y Gemini 3.8.
- 🤝 **[`MANUAL_aagy_ecc_parity_and_migration.md`](01-architecture/MANUAL_aagy_ecc_parity_and_migration.md)**: Arquitectura y paridad multi-harness entre `aagy` y `aagy`.
- 🔌 **[`doc/01-architecture/api-contracts/README.md`](01-architecture/api-contracts/README.md)**: Contratos JSON y salidas estandarizadas `--json`.
- 📐 **Diagramas de Arquitectura (`doc/01-architecture/dgrms/`)**:
  - **[`DGRM_aagy_doc_v2_structure.mmd`](01-architecture/dgrms/DGRM_aagy_doc_v2_structure.mmd)**: Resolución de `/doc` v2 vs fallback clásico en `docs_map.py`.
  - **[`DGRM_aagy_harness_anatomy_and_lifecycle.mmd`](01-architecture/dgrms/DGRM_aagy_harness_anatomy_and_lifecycle.mmd)**: Anatomía del arnés y ciclo de razonamiento/ejecución.
  - **[`DGRM_aagy_agy_environment_architecture.mmd`](01-architecture/dgrms/DGRM_aagy_agy_environment_architecture.mmd)**: Capas de descubrimiento, disclosure progresivo y wakeup reactivo.
  - **[`DGRM_aagy_harness_dual_claude_vs_agy.mmd`](01-architecture/dgrms/DGRM_aagy_harness_dual_claude_vs_agy.mmd)**: Comparativa Claude Code CLI vs Google Antigravity.
  - **[`DGRM_aagy_actors.mmd`](01-architecture/dgrms/DGRM_aagy_actors.mmd)**: Mapa de actores y límites del ecosistema.

---

## 4. Decisiones de Arquitectura (`doc/02-adr/`)

- 📑 **[`doc/02-adr/README.md`](02-adr/README.md)**: Índice consolidado de ADRs:
  - **[`ADR-0001`](02-adr/ADR_aagy_0001_two_tier_global_plugin_and_project_scaffolding.md)**: Arquitectura Two-Tier (Plugin Global + Scaffolding por Proyecto).
  - **[`ADR-0002`](02-adr/ADR_aagy_0002_multi_harness_architecture_and_agent_runtime_design.md)**: Arquitectura Multi-Harness (`aagy` vs `aagy`).
  - **[`ADR-0003`](02-adr/ADR_aagy_0003_doc_structure_v2_and_manual_parity.md)**: Arquitectura documental `/doc` v2, `.governance/docs-map.json` parametrizado y paridad CLI manual.
  - **[`ADR-0005`](02-adr/ADR_aagy_0005_shared_backlog_multi_harness.md)**: Backlog compartido entre Claude Code y Antigravity (`backlog.py`, relevos y épicas).

---

## 5. Dominio, Procesos de Negocio y Secuencias (`doc/03-domain-and-flows/`)

- 🔄 **[`doc/03-domain-and-flows/business-processes/`](03-domain-and-flows/business-processes/README.md)**: Procesos de negocio y ciclo de entrega ([`BP_aagy_task_delivery.bpmn`](03-domain-and-flows/dgrms/BP_aagy_task_delivery.bpmn), [`UC_aagy_lifecycle_parity.puml`](03-domain-and-flows/dgrms/UC_aagy_lifecycle_parity.puml)).
- 🧩 **[`doc/03-domain-and-flows/domain-models/`](03-domain-and-flows/domain-models/README.md)**: Modelos de calidad, presupuesto de tokens y 7 fases ([`doc/03-domain-and-flows/dgrms/`](03-domain-and-flows/dgrms/DGRM_aagy_business_flow.mmd)).
- 🔁 **[`doc/03-domain-and-flows/sequences/`](03-domain-and-flows/sequences/README.md)**: Recuperación autónoma de bucles, smoke-test al sintetizar, formato de commits y sync-clean-align.

---

## 6. Operaciones SRE y Guías de Entorno (`doc/04-operations/`)

### Runbooks Operativos (`doc/04-operations/runbooks/`)

- 🚢 **[`MANUAL_multitier_deployment.md`](04-operations/runbooks/MANUAL_multitier_deployment.md)**: Despliegue automatizado multi-tier por etiquetas en equipo local y servidor Live.
- 🧠 **[`MANUAL_gemini_deep_ops_multimodal.md`](04-operations/runbooks/MANUAL_gemini_deep_ops_multimodal.md)**: Diagnósticos multimodales bajo demanda con Gemini MCP.
- 📊 **[`MANUAL_session_token_telemetry.md`](04-operations/runbooks/MANUAL_session_token_telemetry.md)**: Telemetría de tokens en sesión y política de auto-compactación.
- 🧹 **[`MANUAL_scripts_and_token_optimization.md`](04-operations/runbooks/MANUAL_scripts_and_token_optimization.md)**: Arquitectura multi-runtime en `scripts/` y poda agresiva de reglas.
- 🩺 **[`MANUAL_aagy_doctor.md`](04-operations/runbooks/MANUAL_aagy_doctor.md)**: Doctors `/aagy-doctor` y `/aagy-ecc-doctor` con catálogo común `DOC-01..14`, manifiesto `.aagy-install.json` y `--fix` con confirmación.
- 🧬 **[`MANUAL_unified_self_improvement.md`](04-operations/runbooks/MANUAL_unified_self_improvement.md)**: Motor unificado de autodescubrimiento, hook `Stop` pasivo, instintos a doble nivel y promoción con *budget gate*.

### Guías de Configuración (`doc/04-operations/setup-guides/`)

- ⚡ **[`MANUAL_gemini_prompt_caching.md`](04-operations/setup-guides/MANUAL_gemini_prompt_caching.md)**: Estructuración de prefijos invariantes para KV-cache prompt caching en Gemini 3.8.
- 🎣 **[`MANUAL_git_hooks.md`](04-operations/setup-guides/MANUAL_git_hooks.md)**: Instalación y uso de hooks Git locales (`pre-commit` y `commit-msg`).
- 🚀 **[`MANUAL_skill_promotion.md`](04-operations/setup-guides/MANUAL_skill_promotion.md)**: Promoción on-demand de skills Tier-2 a Tier-1.

---

## 7. Post-Mortems SRE 5W (`doc/05-post-mortems/`)

- 🩺 **[`PM_fix_scripts_install_dir_creation_20261120_203232.md`](05-post-mortems/PM_fix_scripts_install_dir_creation_20261120_203232.md)**: Incidente de creación de directorio destino en instalador `install.ps1`.
- 📄 **Plantilla Canónica**: [`doc/00-governance/templates/TEMPLATE_POSTMORTEM.md`](00-governance/templates/TEMPLATE_POSTMORTEM.md).

---

## 8. Backlog y Demanda Activa (`doc/06-backlog/`)

- 💡 **[`doc/06-backlog/IDEAS.md`](06-backlog/IDEAS.md)**: Registro estructurado de ideas candidatas (`Draft` / `Approved`).
- 📋 **[`doc/06-backlog/TODO.md`](06-backlog/TODO.md)**: Backlog activo y asignación de modelos/compactación.
- 🗂️ **[`doc/06-backlog/plans/`](06-backlog/plans/REQ_aagy_unified_self_improvement.md)**: Requisitos y planes en curso (`REQ_doc_structure_v2_and_manual_parity.md`, `REQ_aagy_unified_self_improvement.md`, `REQ_aagy_clean_docs_and_repo_migration.md`).
- ⚡ **[`doc/06-backlog/quick/README.md`](06-backlog/quick/README.md)**: Notas ligeras para entradas directas vía `--phase TODO` y notas de relevo `HANDOFF_<id>.md`.
- 🤝 **[`MANUAL_shared_backlog.md`](04-operations/runbooks/MANUAL_shared_backlog.md)**: Backlog compartido entre Claude Code y Antigravity (`backlog.py`).
- 🦙 **[`MANUAL_local_model.md`](04-operations/runbooks/MANUAL_local_model.md)**: Modelo local con Ollama (`local_model.py`, servidor MCP `aagy-local`, modo solo local y autocompletado).
- 💶 **[`MANUAL_ci_local.md`](04-operations/runbooks/MANUAL_ci_local.md)**: CI local en `pre-push`, Actions opcionales apagadas y presupuesto 0 $ (`ci_local.py`).
- 🖥️ **[`MANUAL_ui.md`](04-operations/runbooks/MANUAL_ui.md)**: UI de Claude Code y Antigravity (status line, avisos de escritorio, `ccusage` opcional y extensiones de VS Code).
- 🗄️ **[`doc/06-backlog/done/`](06-backlog/done/TODO_Ejecutar_optimizacion_maxima_de_tokens_purgar_archivos_no_us_20261120_215458.md)**: Histórico inmutable de tareas completadas y archivadas.
