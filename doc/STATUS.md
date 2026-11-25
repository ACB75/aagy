# Estado de Salud y Métricas Operacionales | AAGY / `aagy` Ecosystem

> **Repositorio**: [ACB75/aagy](https://github.com/ACB75/aagy)
> **Versión**: `5.2.0` (`/doc` v2) | **Fecha de Auditoría**: 2026-11-25
> **Estado Operativo Global**: 🟢 **SALUDABLE (VERDE)**

---

## 1. Métricas de calidad

Todas salen de la CI local (`python scripts/py/ci_local.py run`, también en `pre-push`). No hay GitHub Actions
activas: el presupuesto es 0 $ ([`MANUAL_ci_local.md`](04-operations/runbooks/MANUAL_ci_local.md)).

| Paso de `ci_local.py` | Qué comprueba | Estado |
| :--- | :--- | :---: |
| `markdownlint` | `.markdownlint.json` en todo el repo | ✅ |
| `pytest` | 475 tests de `scripts/py/tests/` | ✅ |
| `workspace_audit` | Presupuesto de reglas, `docs-map.json`, descripciones ≤ 200 caracteres, esqueleto de workflows, `consumer_refs` | ✅ |
| `sonar` | Reglas locales tipo SonarQube (`S1192`, `S3776`, `S108`...) | ✅ |
| `security` | Secretos e inyecciones de comandos | ✅ |
| `templates` | Documentos generados desde la plantilla base | ✅ |
| `mirror` | `aagy-ecc` sin deriva respecto a la raíz (`sync_aagy_ecc.py --check`) | ✅ |
| `parity` | Paridad `aagy` ↔ `aagy-ecc`: skills, agentes, hooks y esqueleto común (`audit_plugin_parity.py`) | ✅ |

---

## 2. Presupuesto de tokens

| Tope | Valor | Dónde se comprueba |
| :--- | :--- | :--- |
| Índice de reglas que inyecta `SessionStart` (aagy-ecc) | ≤ 2 KB | `test_token_caps.py` |
| `description` de skills, agentes y comandos | ≤ 200 caracteres | `optimize_catalog_tokens.py --check` |
| Mensaje de un hook | una línea, ≤ 160 caracteres | `test_token_caps.py` |

Antigravity carga [`rules/AGENTS.md`](../rules/AGENTS.md) de forma nativa; el `AGENTS.md` de la raíz solo apunta a él.
Detalle en [`MANUAL_scripts_and_token_optimization.md`](04-operations/runbooks/MANUAL_scripts_and_token_optimization.md).

---

## 3. Catálogo

<!-- aagy-live-catalog:start -->
> Última sincronización de catálogo: `2026-11-25T22:08:54Z` | `aagy` `5.2.0` ↔ `aagy-ecc` `5.2.0`

| Pieza | `aagy` (Antigravity) | `aagy-ecc` (Claude Code) |
| :--- | :--- | :--- |
| Skills | 166 en `skills/` | 14 en núcleo (`generic`); packs opcionales: `angular`, `extras`, `go`, `java-spring`, `network-infra`, `python`, `shared` |
| Subagentes | 47 en `agents/` | 12 en núcleo (`generic`); resto distribuido en `packs/` |
| Comandos slash | Equivalentes por skill (sin `commands/`) | 28 en `aagy-ecc/commands/` |
| Reglas Tier 1 | `rules/AGENTS.md` (7,289 bytes, ~1,919 tokens) | Inyección condensada en `SessionStart` (≤ 2 KB) |
| Hooks activos | `PostToolUse`, `PreToolUse`, `SessionStart`, `Stop` | `Notification`, `PostToolUse`, `PreCompact`, `PreToolUse`, `SessionEnd`, `SessionStart`, `Stop` |
<!-- aagy-live-catalog:end -->

---

## 4. Trazabilidad Two-Tier (ADR-0001 -> ADR-0004)

<!-- aagy-live-traceability:start -->
Origen documentado en la sesión `cc240ae0-bb1b-4e71-8287-891d6f5ee2a0` (2026-10-24: `affaan-m/ecc` → `ecc-agy` → `aagy`):

| Hito / ADR | Fecha | Evolución arquitectónica desde Two-Tier |
| :--- | :---: | :--- |
| [**ADR-0001**](02-adr/ADR_aagy_0001_two_tier_global_plugin_and_project_scaffolding.md) | 2026-10-24 | **Two-Tier original**: Nivel 1 plugin global (`rules/AGENTS.md` + core) y Nivel 2 scaffolding `.agents/` por proyecto. |
| [**ADR-0002**](02-adr/ADR_aagy_0002_multi_harness_architecture_and_agent_runtime_design.md) | 2026-11-01 | **Multi-Harness**: distribución simétrica `aagy` (Antigravity) ↔ `aagy-ecc` (Claude Code) con espejo único. |
| [**ADR-0003**](02-adr/ADR_aagy_0003_doc_structure_v2_and_manual_parity.md) | 2026-11-20 | **Gobernanza `/doc` v2**: `.governance/docs-map.json`, esqueleto común y paridad manual CLI 1-a-1. |
| [**ADR-0004**](02-adr/ADR_aagy_0004_stack_profiles_declared_by_consumer_repo.md) | 2026-11-21 | **Supera Nivel 2 de ADR-0001**: perfiles de stack declarados por el repo consumidor; plugin 100 % agnóstico. |
| [**ADR-0005**](02-adr/ADR_aagy_0005_shared_backlog_multi_harness.md) | 2026-11-21 | **Backlog compartido**: `TODO.md` + estado en `.git/aagy-backlog/` y relevo entre agentes. |
| [**ADR-0006**](02-adr/ADR_aagy_0006_agent_worktrees.md) | 2026-11-22 | **Worktrees fijos**: `<repo>-aagy` y `<repo>-aagy-ecc` con guarda PreToolUse y reciclado post-merge. |
| `v5.0.0`–`v5.2.0` | 2026-11-25 | Motor único de hooks, LLM local (`local_model.py`), telemetría [`session_token_monitor`](04-operations/runbooks/MANUAL_session_token_telemetry.md) y [`aagy_ui`](04-operations/runbooks/MANUAL_ui.md). |
<!-- aagy-live-traceability:end -->

---

## 5. Telemetría y memoria de sesiones (Antigravity / Claude Code)

<!-- aagy-live-telemetry:start -->
> Actualizado: `2026-11-25T22:08:54Z` | Rama: `feat/aagy/live-status-telemetry` (`7ce3470`) | Worktrees activos: `sí`

### Antigravity (`session_token_monitor` / `aagy_ui usage --harness agy`)

- **Sesiones en `~/.gemini/antigravity/brain/`**: `27` (54,200 pasos, ~16,818,032 tokens estimados).
- **Sobre umbral `/compact` (`45,000` tokens)**: `20` sesión(es).

| Sesión (`brain/<id>`) | Última actividad | Pasos | Tokens (est.) | Estado |
| :--- | :---: | :---: | :---: | :---: |
| `dff68777-2b09-4147-b24c-bb1c188e4354` | `2026-11-25 22:08` | 331 | ~208,848 | ⚠️ `COMPACT` |
| `168ac2a1-48f7-4d2e-82a6-590eeab64bb1` | `2026-11-25 22:07` | 322 | ~127,253 | ⚠️ `COMPACT` |
| `0df01722-74cb-4bc6-baf6-9665a75a5357` | `2026-11-25 22:03` | 12929 | ~4,930,506 | ⚠️ `COMPACT` |
| `f1a43559-f071-4116-b53a-cd2a4bbda413` | `2026-11-25 21:54` | 2064 | ~614,313 | ⚠️ `COMPACT` |
| `cc240ae0-bb1b-4e71-8287-891d6f5ee2a0` | `2026-11-25 21:30` | 196 | ~91,971 | ⚠️ `COMPACT` |
| `6f11ad43-334a-4065-9dea-bbbe62fa366b` | `2026-11-22 18:12` | 18 | ~7,193 | ✅ `OK` |
| `471ee1fa-d55c-4751-ad5e-7a0ee7b1ef22` | `2026-11-22 18:05` | 626 | ~140,071 | ⚠️ `COMPACT` |
| `e97c3d04-fe03-468c-bd5a-ba0ea9ca77ea` | `2026-11-22 00:13` | 252 | ~80,067 | ⚠️ `COMPACT` |

### Claude Code (`~/.claude/projects/` / `aagy_statusline`)

- **Sesiones detectadas**: `33` (contexto último turno acumulado: 4,961,366 tokens; salida: 12,214).

| Sesión (`sessionId`) | Entorno | Última actividad | Modelo | Contexto | Salida |
| :--- | :---: | :---: | :--- | :---: | :---: |
| `d5f4797b-4540-4cd6-adff-7d9022eb4a78` | `external` | `2026-11-25 22:00` | `unknown` | 0 | 0 |
| `fa0b42ee-5ddc-42aa-a519-a0bfb718258e` | `external` | `2026-11-25 21:54` | `claude-haiku-5-5` | 49,680 | 410 |
| `d0e2e679-67e4-4146-b12c-af65dd900a6a` | `external` | `2026-11-25 21:23` | `claude-opus-5-5` | 84,422 | 588 |
| `8d3fbd2c-2c44-4a85-a3aa-1d446ee12ab0` | `external` | `2026-11-25 21:11` | `claude-opus-5-5` | 210,299 | 644 |
| `95a03ce8-7317-4fce-93f5-8575ca68a4a6` | `external` | `2026-11-25 21:03` | `gemma4:12b` | 25,063 | 110 |
| `5d5b4e53-8c75-4cbb-89f2-0f0b892a8a1e` | `external` | `2026-11-25 21:03` | `<synthetic>` | 0 | 0 |
| `4baac63b-6d88-4f87-bf3f-8358077515d0` | `external` | `2026-11-25 19:48` | `claude-opus-5-5` | 101,117 | 650 |
| `c1ebc713-1414-4e5c-871d-030fb89270c6` | `external` | `2026-11-25 17:57` | `claude-opus-5-5` | 82,569 | 658 |

Los hooks `SessionStart` y `Stop` refrescan automáticamente `.agents/LIVE_TELEMETRY.md` en el worktree del agente sin ensuciar git; ejecuta `python scripts/py/live_status.py sync` para volcar métricas en `doc/STATUS.md`.
<!-- aagy-live-telemetry:end -->

---

## 6. Backlog

[`doc/06-backlog/TODO.md`](06-backlog/TODO.md) está en paridad con las issues abiertas (`backlog.py gh-sync --check`).
Lo terminado se archiva en `doc/06-backlog/done/`. Historial de versiones en [`LOG.md`](LOG.md).
