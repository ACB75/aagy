# Architecture Decision Records — AAGY / Anything Antigravity (`doc/02-adr/README.md`)

> **Registro Canónico de Decisiones de Arquitectura**  
> Mapa Documental: [`doc/INDEX.md`](../INDEX.md) | Contrato: [`.governance/docs-map.json`](../../.governance/docs-map.json)

---

## 1. Decisiones de Arquitectura Formales (ADR)

| ADR | Título | Estado | Fecha |
| :--- | :--- | :---: | :---: |
| [**0001**](ADR_aagy_0001_two_tier_global_plugin_and_project_scaffolding.md) | Arquitectura en dos niveles: Plugin Global (`aagy`) y Scaffolding por Proyecto (`.agents/`) | `superseded` (Nivel 2 → 0004) | 2026-10-24 |
| [**0002**](ADR_aagy_0002_multi_harness_architecture_and_agent_runtime_design.md) | Arquitectura Multi-Harness y Diseño de Runtimes de Agentes Autónomos (`aagy-ecc` vs `aagy`) | `accepted` | 2026-11-01 |
| [**0003**](ADR_aagy_0003_doc_structure_v2_and_manual_parity.md) | Arquitectura Documental `/doc` v2, `.governance/docs-map.json` Parametrizado y Paridad Manual | `accepted` | 2026-11-20 |
| [**0004**](ADR_aagy_0004_stack_profiles_declared_by_consumer_repo.md) | Perfiles de Stack Declarados por el Repositorio Consumidor (Plugin Desacoplado) | `accepted` | 2026-11-21 |

---

## 2. Informes y Planes Arquitectónicos Complementarios

| Documento | Descripción / Alcance | Estado |
| :--- | :--- | :---: |
| [**Plan de Documentación**](ADR_aagy_plan_documentacion_arquitectura_harness.md) | Plan de requisitos y diseño arquitectónico para la documentación integral del arnés | `accepted` |
| [**Informe de Abstracción Multi-Proyecto**](ADR_aagy_informe_abstraccion_reutilizable_n_proyectos.md) | Análisis de desacoplamiento para reutilización en $N$ proyectos o clientes externos | `accepted` |
| [**Informe de Funcionamiento AAGY**](ADR_aagy_informe_funcionamiento_aagy_homelab.md) | Especificación técnica previa del fork antes de su consolidación en `aagy` | `accepted` |
