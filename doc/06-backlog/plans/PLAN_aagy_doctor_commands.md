# Fase 2: Plan de Acción, Diseño Arquitectónico y Estrategia TDD — Comandos `/aagy-doctor` y `/aagy-ecc-doctor`

> **Referencia de Gobernanza**: Fase 2 del Workflow de Ingeniería AAGY
> **ID de Tarea**: `feat/aagy/doctor-commands`
> **Requisitos**: [`REQ_aagy_doctor_commands.md`](REQ_aagy_doctor_commands.md) (APROBADO 2026-11-20)
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Claude · aprobado por Master`
> **Estado**: `APROBADO` (2026-11-20, decisiones de la sección 10)
> **Ubicación en el repo**: `doc/06-backlog/plans/PLAN_aagy_doctor_commands.md`

---

## 1. Prerrequisitos

1. **La rama de paridad va primero.** El trabajo de los doctors reutiliza `sync_aagy_ecc.py`, el `audit_plugin_parity.py` estricto y los hooks Python. Todo eso está en `fix/aagy-ecc-paridad-claude` (commit `0267279`), que aún no está en `main`. Esa rama tiene que entrar en `main` antes de abrir `feat/aagy/doctor-commands` desde `main`.
2. **Entorno de pruebas**:
   - Los tests corren con `pytest` en Linux y en Windows.
   - Los tests que necesitan `pwsh` se saltan si no está instalado (`pytest.mark.skipif`).
   - La verificación final (sección 9) se hace en tu máquina Windows.

---

## 2. Inventario de Reutilización (DRY First)

- **Módulos reutilizados como librería** (sin duplicar lógica):
  - `scripts/py/sync_aagy_ecc.py`: `compare()` para la deriva del espejo (`DOC-07`, `DOC-14`) y `sync()` como acción de `--fix`.
  - `scripts/py/audit_plugin_parity.py`: `audit_parity()` y `_check_hook_targets` (`DOC-09` y `DOC-14` en Claude Code).
  - `scripts/py/workspace_audit.py`: `audit_skills()`, `audit_agents()` y `read_frontmatter()` (`DOC-06`, `DOC-08`).
  - `scripts/py/instinct_manager.py`: `resolve_plugin_data_dir()` y `redact_secrets()` (`DOC-12` y salida sin secretos).
  - `aagy-ecc/scripts/hooks/*.py`: se ejecutan tal cual en el smoke test (`DOC-11`).
  - `scripts/ps1/aagy-sync.ps1` y `scripts/sh/aagy-sync.sh`: acción de `--fix` en Antigravity, con el perfil del manifiesto.
- **Dependencias**: solo Python stdlib y `pytest`, que ya usa el repo. Ninguna dependencia nueva.

---

## 3. Arquitectura

```text
scripts/py/doctor_core.py        ← neutral: catálogo DOC-01..14, Status, CheckResult,
                                   runner con timeouts, render humano/JSON, plan de --fix
scripts/py/install_manifest.py   ← leer/escribir .aagy-install.json
scripts/py/aagy_doctor.py        ← checks de Antigravity (usa doctor_core)
aagy-ecc/scripts/py/doctor_core.py, install_manifest.py   ← espejo generado por sync_aagy_ecc
aagy-ecc/scripts/py/aagy_ecc_doctor.py                    ← checks de Claude Code (fuente propia, no espejo)
skills/aagy-doctor/SKILL.md                ← punto de entrada en Antigravity
aagy-ecc/commands/aagy-ecc-doctor.md       ← comando slash en Claude Code
scripts/{ps1,sh}/aagy-doctor.*, aagy-ecc-doctor.*   ← wrappers
```

**Cómo se garantiza la paridad 1:1**:

- El catálogo de checks (ID, nombre y ámbito) vive una sola vez en `doctor_core.py`. La severidad la decide cada check según lo que encuentra.
- Cada doctor registra una implementación por ID. El runner falla si falta algún ID o si sobra alguno.
- Así, los dos doctors son independientes (decisión P5), pero no pueden divergir en qué comprueban.

**Contratos de `doctor_core`**:

- `Status`: `PASS | WARN | FAIL | SKIP`.
- `CheckResult(id, status, message, evidence, fix: Optional[FixAction])`.
- `FixAction(description, argv, reversible: bool)`. Es solo una descripción de la acción: el core la muestra, pide confirmación y la ejecuta. Un check nunca escribe por sí mismo.
- `run(checks, ctx, timeout_s=5) -> Report`. Cada check corre en un hilo con límite de tiempo; si lo supera, sale `FAIL` con "timeout".
- `render_text(report)`, `render_json(report)`, `exit_code(report, strict)`. Los códigos son `0`, `1` y `2`.
- `--list-checks --json` imprime el catálogo, para la auditoría de paridad.

---

## 4. Plan por Fases

| Fase | Entregable | Archivos | Tests |
| :- | :--- | :--- | :--- |
| **F1** | Núcleo común | `scripts/py/doctor_core.py`; mapeo en `sync_aagy_ecc.py` para espejarlo | `tests/test_doctor_core.py`: runner, timeout, render, exit codes, `--fix` sin confirmación no ejecuta nada |
| **F2** | Manifiesto de instalación (RF-07) | `scripts/py/install_manifest.py`; llamadas desde `install.ps1`, `install.sh`, `aagy-sync.ps1`, `aagy-sync.sh` | Escritura y lectura; manifiesto ausente o corrupto devuelve `None` sin excepción |
| **F3** | `aagy_doctor.py` (DOC-01..14 para Antigravity) | `scripts/py/aagy_doctor.py` | Instalación falsa en `tmp_path` (sana, sin reglas, con deriva, con hook roto, con huérfanos); CA-01, CA-04, CA-05 |
| **F4** | `aagy_ecc_doctor.py` (DOC-01..14 para Claude Code) | `aagy-ecc/scripts/py/aagy_ecc_doctor.py` | `~/.claude` falso en `tmp_path`; smoke test real de los 3 hooks; CA-02, CA-03 |
| **F5** | Puntos de entrada | `skills/aagy-doctor/SKILL.md`, `aagy-ecc/commands/aagy-ecc-doctor.md`, wrappers ps1/sh | `workspace_audit` valida el frontmatter; los wrappers pasan los argumentos tal cual |
| **F6** | Paridad | Nuevo check en `audit_plugin_parity.py`: mismo conjunto de IDs en ambos doctors | CA-07 |
| **F7** | Documentación | `doc/04-operations/runbooks/MANUAL_aagy_doctor.md`; READMEs; quitar la referencia a `commands/` de la guía de arquitectura (H3); `LOG.md`, `STATUS.md`, `TODO.md` | `markdownlint` |

### 4.1. Detalles de implementación por check

- **`DOC-01` Runtime**:
  - Antigravity: buscar `antigravity` en el PATH (decisión Q1).
  - Claude Code: `claude --version`, con 5 s de límite.
- **`DOC-02` y `DOC-07` Estado del plugin en Claude Code**:
  - Fuente principal: los ficheros de `~/.claude/plugins/` (marketplaces conocidos, plugins instalados y la caché).
  - Alternativa: `claude plugin list`.
  - Los formatos no están documentados como estables. Se verifican al implementar y el check sale `WARN` ("no se pudo determinar") si cambian, nunca `FAIL` por un parseo.
- **`DOC-05` Presupuesto**: reutiliza los límites que ya usa el repo (24 KB / 20.000 tokens) y la estimación de tokens de `optimize_catalog_tokens.py`, si encaja.
- **`DOC-06`**: reutiliza `workspace_audit.audit_skills` y `audit_agents`.
- **`DOC-07`** en Antigravity y **`DOC-14`**: reutilizan `sync_aagy_ecc.compare` y `audit_plugin_parity.audit_parity` como librería, no como subproceso.
- **`DOC-09`** en Antigravity: detecta rutas relativas a `scripts/` que no existen en la instalación y lo marca `WARN` (decisión P5).
- **`DOC-11` Smoke test**: ejecuta cada hook como subproceso con stdin JSON sintético y `cwd` en un `tmp`.
  - El comando de prueba del safety gate es una cadena inocua que coincide con el patrón bloqueado; nunca se ejecuta un comando destructivo real.
- **`--fix`**: solo acciones de la sección 5 del REQ. Cada acción se lista y se confirma; con `--yes`, se aplican sin preguntar.

### 4.2. Exclusión del espejo

`sync_aagy_ecc.py` espeja toda `skills/` en aagy-ecc. Sin una exclusión, `skills/aagy-doctor/` aparecería también en Claude Code y lanzaría el doctor equivocado. **Propuesta**: añadir una lista de exclusión de skills específicas de Antigravity en `sync_aagy_ecc.py` (de momento solo `aagy-doctor`) y que la auditoría de paridad la tenga en cuenta. Aceptado (decisión Q2).

---

## 5. Orden de Entrega (PR)

Un solo PR, `feat/aagy/doctor-commands`, desde `main` y después del merge de `fix/aagy-ecc-paridad-claude` (decisión Q3). Dentro del PR, un commit por fase (F1 a F7) para que se pueda revisar por partes.

---

## 6. Riesgos y Mitigaciones

| Riesgo | Nivel | Mitigación |
| :--- | :---: | :--- |
| El formato interno de plugins de Claude Code cambia entre versiones | Medio | Parseo tolerante con `WARN`, alternativa con `claude plugin list` y tests con fixtures por versión. |
| Antigravity no expone un CLI identificable | Medio | `DOC-01` sale `SKIP` con un mensaje si `antigravity` no está en el PATH. |
| Los instaladores fallan al escribir el manifiesto | Bajo | El fallo al escribirlo solo avisa y nunca aborta la instalación. |
| Un smoke test deja efectos secundarios | Bajo | `cwd` temporal, entrada sintética y ningún comando destructivo real. |
| El pre-commit falla en la VM de Cowork (sin `pwsh` ni `markdownlint`) | Conocido | Los commits se hacen desde tu Windows, como en la rama de paridad. |

---

## 7. Estrategia TDD por Fase

Cada fase de la sección 4 sigue el mismo ciclo, y cada ciclo es un commit del PR:

1. **`RED`**: primero se escriben los tests de la fase con fixtures en `tmp_path` (instalación sana, rota, desfasada y ausente). Fallan.
2. **`GREEN`**: implementación mínima hasta que pasan.
3. **`REFACTOR`**: se extrae a `doctor_core` lo que se repita entre los dos doctors, sin cambiar el catálogo.
4. **`VERIFY`**: `pytest`, `audit_plugin_parity.py`, `sync_aagy_ecc.py --check` y `markdownlint` antes de pasar a la siguiente fase.

---

## 8. Coste de la Decisión y Fast-Rollback

- **Coste en contexto**: una skill y un comando más, con descripciones ≤ 140 caracteres. Los doctors no cargan nada en el prompt hasta que se invocan.
- **Coste de mantenimiento**: cada check nuevo hay que implementarlo en los dos doctors. La auditoría de paridad lo hace obligatorio, y es justo la simetría que pediste.
- **Rollback (< 2 min)**: todo es aditivo. Revertir el PR quita los doctors sin afectar a lo instalado. Un `.aagy-install.json` que se quede en una instalación lo ignora todo lo demás.

---

## 9. Verificación Final

1. `pytest` en verde, con cobertura ≥ 80 % sobre `doctor_core`, `install_manifest` y los dos doctors.
2. `audit_plugin_parity.py` en `PASS` (con el nuevo check de IDs) y `sync_aagy_ecc.py --check` en `IN_SYNC`.
3. En tu Windows:
   - `pwsh -File install.ps1 -Target agy` y después `aagy-doctor`.
   - `pwsh -File install.ps1 -Target aagy-ecc` y después `/aagy-ecc-doctor` dentro de Claude Code.
   - Los dos deben salir sin FAIL, en menos de 10 s.
4. Romper a propósito un hook y desincronizar el espejo; los doctors deben detectarlo, y `--fix` debe arreglar el espejo tras confirmar.

---

## 10. Decisiones de Master (2026-11-20)

1. **`Q1`**: el ejecutable de Antigravity es `antigravity`. `DOC-01` lo busca en el PATH y sale `SKIP` si no lo encuentra.
2. **`Q2`**: sí, `skills/aagy-doctor/` se excluye del espejo de aagy-ecc (sección 4.2).
3. **`Q3`**: un solo PR, con un commit por fase (sección 5).
