# Manual de los Doctors: `/aagy-doctor` y `/aagy-ecc-doctor`

> **Requisitos**: [`REQ_aagy_doctor_commands.md`](../../06-backlog/plans/REQ_aagy_doctor_commands.md) | **Plan**: [`PLAN_aagy_doctor_commands.md`](../../06-backlog/plans/PLAN_aagy_doctor_commands.md)
> **Versión**: `4.1.0` | **Fecha**: 2026-11-20

---

## 1. Qué Son

Dos comandos de diagnóstico, uno por harness, con el **mismo catálogo de 14 checks** (`DOC-01` a `DOC-14`):

| Harness | Punto de entrada | Motor |
| :--- | :--- | :--- |
| Antigravity / Gemini | Skill [`aagy-doctor`](../../../skills/aagy-doctor/SKILL.md) | [`scripts/py/aagy_doctor.py`](../../../scripts/py/aagy_doctor.py) |
| Claude Code | Comando [`/aagy-ecc-doctor`](../../../aagy-ecc/commands/aagy-ecc-doctor.md) | [`aagy-ecc/scripts/py/aagy_ecc_doctor.py`](../../../aagy-ecc/scripts/py/aagy_ecc_doctor.py) |

El catálogo vive una sola vez en [`doctor_core.py`](../../../scripts/py/doctor_core.py). Cada doctor tiene que implementar
todos sus IDs: si falta o sobra alguno, el doctor no arranca y [`audit_plugin_parity.py`](../../../scripts/py/audit_plugin_parity.py)
falla. Así los dos doctors van separados, pero no pueden comprobar cosas distintas.

---

## 2. Uso

```powershell
# Antigravity (desde el repo aagy)
pwsh -NoProfile -File scripts/ps1/aagy-doctor.ps1           # informe legible
pwsh -NoProfile -File scripts/ps1/aagy-doctor.ps1 -Json     # JSON
pwsh -NoProfile -File scripts/ps1/aagy-doctor.ps1 -Fix      # arreglos con confirmación

# Claude Code (fuera de una sesión)
pwsh -NoProfile -File scripts/ps1/aagy-ecc-doctor.ps1
```

```bash
scripts/sh/aagy-doctor.sh [--json] [--fix] [--yes] [--strict] [--only DOC-05,DOC-09]
scripts/sh/aagy-ecc-doctor.sh [--json] [--fix] [--yes] [--strict] [--only DOC-05,DOC-09]
```

Dentro de Claude Code basta con `/aagy-ecc-doctor` (o `/aagy-ecc-doctor --fix`).

| Opción | Efecto |
| :--- | :--- |
| `--json` | Salida JSON: `target`, `plugin_dir`, `version`, `summary` y `checks[]` (`id`, `name`, `scope`, `status`, `message`, `evidence`, `fix`). |
| `--strict` | Un WARN cuenta como fallo. |
| `--only` / `--skip` | Filtra por IDs. |
| `--fix` | Propone los arreglos de los WARN/FAIL y los aplica uno a uno tras confirmarlos. Sin terminal interactiva no aplica nada. |
| `--yes` | Con `--fix`, aplica sin preguntar. |
| `--repo-root`, `--project`, `--home` | Rutas alternativas (repo de origen, proyecto, home). |
| `--plugin-dir` | Plugin a revisar. `aagy_ecc_doctor.py` acepta además `--claude-home`. |
| `--list-checks` | Imprime el catálogo y sale. |

**Códigos de salida**: `0` sin FAIL, `1` con algún FAIL (o WARN con `--strict`), `2` error interno del doctor.

---

## 3. Catálogo de Checks

| ID | Check | `/aagy-doctor` | `/aagy-ecc-doctor` |
| :- | :--- | :--- | :--- |
| `DOC-01` | Runtime del harness | `antigravity` en el PATH (`SKIP` si no está) | `claude --version` |
| `DOC-02` | Plugin instalado | Existe `~/.gemini/config/plugins/aagy` | Marketplace registrado, plugin instalado y habilitado |
| `DOC-03` | Manifiestos | `plugin.json` con `name: aagy` | `plugin.json` y `marketplace.json` coherentes |
| `DOC-04` | Versión y manifiesto | `.aagy-install.json` y versión igual al repo | Lo mismo sobre la copia en caché |
| `DOC-05` | Reglas Tier 1 | `rules/AGENTS.md` ≤ 24 KB / ≤ 16.000 tokens e igual al repo | Las reglas que inyecta `SessionStart` |
| `DOC-06` | Skills y agentes | Frontmatter y recuento frente a la fase instalada | Frontmatter y recuento frente a `aagy-ecc/` |
| `DOC-07` | Deriva frente al repo | Contenido instalado frente al repo | Copia en caché frente a `aagy-ecc/` |
| `DOC-08` | Puntos de entrada | Skill `aagy-doctor` instalada | Comandos con `description`, sin colisiones con otros plugins |
| `DOC-09` | Destinos de los hooks | Intérpretes y scripts de `hooks.json` | Destinos `${CLAUDE_PLUGIN_ROOT}/...` |
| `DOC-10` | Intérpretes | Python ≥ 3.10 y `pwsh` ≥ 7 | `bash` y un Python real ≥ 3.10 (no el alias de la Store) |
| `DOC-11` | Smoke test de hooks | `safety-check.ps1` con entrada sintética | Los tres hooks Python con stdin sintético |
| `DOC-12` | Datos y legado | `.data` escribible, sin plugins `ecc` ni huérfanos | Directorio de datos escribible, sin plugins `ecc` |
| `DOC-13` | Proyecto | `.agents/` del proyecto | `CLAUDE.md` / `.claude/` frente a `project-template/` |
| `DOC-14` | Repo | Paridad y git hooks | Espejo `IN_SYNC` y paridad |

Los smoke tests usan una cadena que coincide con el patrón bloqueado; nunca se ejecuta un comando destructivo.

---

## 4. Manifiesto de Instalación (`.aagy-install.json`)

Los instaladores lo escriben con [`install_manifest.py`](../../../scripts/py/install_manifest.py):

- `aagy-sync.ps1` / `aagy-sync.sh` en `~/.gemini/config/plugins/aagy` (fase instalada).
- `install.ps1 -Target aagy-ecc` / `install.sh aagy-ecc` en `aagy-ecc/` antes de `claude plugin install`, para que viaje a la caché (ignorado por Git).

Campos: `harness`, `profile`, `version`, `commit`, `installed_at`, `source_repo` y `schema`. Si falta, `DOC-04` sale WARN
y el doctor asume la fase `generic`. Escribirlo nunca aborta una instalación.

El plugin de Antigravity no incluye `scripts/`, así que la skill `aagy-doctor` usa `source_repo` para encontrar el motor.

---

## 5. Avisos Conocidos

- **`DOC-09` en Antigravity**: el `hooks.json` raíz llama a `scripts/ps1/*.ps1` y `scripts/py/self_improve.py` con rutas
  relativas, que no se copian al plugin global. Solo funcionan en workspaces que contengan esos scripts. Se marca WARN
  porque no es un requisito que funcionen fuera del repo.
- **`skills/aagy-doctor`** no se espeja en aagy-ecc (`MIRROR_EXCLUDED` en `sync_aagy_ecc.py`): por eso la raíz tiene una
  skill más que aagy-ecc.
- **Formato interno de Claude Code**: `DOC-02` lee `~/.claude/plugins/installed_plugins.json` (v1 y v2),
  `known_marketplaces.json` y `settings.json`. Si el formato cambia, sale WARN, nunca FAIL por un error de lectura.
