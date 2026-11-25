# Estado de Salud y Métricas Operacionales | AAGY / `aagy` Ecosystem

> **Repositorio**: [ACB75/aagy](https://github.com/ACB75/aagy)
> **Versión**: `5.1.1` (`/doc` v2) | **Fecha de Auditoría**: 2026-11-25
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

| Pieza | `aagy` (Antigravity) | `aagy-ecc` (Claude Code) |
| :--- | :--- | :--- |
| Skills | 168 en `skills/` | Perfil `generic` en el núcleo; el resto en `packs/` |
| Subagentes | 47 en `agents/` | Perfil `generic` en el núcleo; el resto en `packs/` |
| Comandos slash | No tiene (equivalen a skills) | `aagy-ecc/commands/` |
| Hooks | `SessionStart`, `PreToolUse`, `PostToolUse`, `Stop` | Los mismos, más `PreCompact`, `SessionEnd` y `Notification` |

Todos los workflows siguen el esqueleto común (Cuándo usarlo, Uso, Qué hacer, Reglas, Paridad), comprobado por
`workflow_skeleton.py`.

---

## 4. Backlog

[`doc/06-backlog/TODO.md`](06-backlog/TODO.md) está en paridad con las issues abiertas (`backlog.py gh-sync --check`).
Lo terminado se archiva en `doc/06-backlog/done/`. Historial de versiones en [`LOG.md`](LOG.md).
