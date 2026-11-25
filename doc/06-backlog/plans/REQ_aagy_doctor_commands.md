# Fase 1: Toma de Requisitos — Comandos `/aagy-doctor` y `/aagy-ecc-doctor`

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería AAGY
> **ID de Tarea**: `feat/aagy/doctor-commands`
> **Fecha**: `2026-11-20` | **Autor/Rol**: `Claude · aprobado por Master`
> **Estado**: `APROBADO` (2026-11-20, decisiones de la sección 9)
> **Ubicación en el repo**: `doc/06-backlog/plans/REQ_aagy_doctor_commands.md`

---

## 1. Contexto, Necesidad y Objetivos

- **Problema**: hoy no hay una forma única de saber si una instalación de aagy (Antigravity/Gemini) o de aagy-ecc (Claude Code) está sana. Los fallos se descubren tarde: hooks que apuntan a scripts inexistentes, espejos desfasados, versiones distintas entre repo e instalación, intérpretes ausentes (`pwsh`, `python`) o restos del legado `ecc`.
- **Objetivo**: dos comandos de diagnóstico, simétricos, que en menos de 10 s digan qué está bien, qué falla y cómo arreglarlo, con salida legible y JSON.
- **Alcance (`In-Scope`)**:
  - `/aagy-doctor`: diagnostica la instalación global de aagy en `~/.gemini/config/plugins/aagy` (ruta sobreescribible).
  - `/aagy-ecc-doctor`: diagnostica la instalación de aagy-ecc en Claude Code (marketplace, plugin instalado, hooks, comandos, espejo).
  - Dos doctors en Python stdlib, uno por harness y con catálogo 1:1, que reutilizan `audit_plugin_parity.py`, `sync_aagy_ecc.py` (`compare`) y `workspace_audit.py` (frontmatter de skills y agentes).
  - Manifiesto de instalación `.aagy-install.json` escrito por los instaladores.
  - Wrappers `scripts/ps1/` y `scripts/sh/` como el resto de scripts.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Reparaciones destructivas automáticas (borrar instalaciones, tocar `settings.json` del usuario fuera de la clave del plugin).
  - Diagnóstico de proyectos de negocio (app, cluster...) más allá de la plantilla de aagy.
  - Llamadas de red por defecto.

---

## 2. Hallazgos del Análisis de Superficie (estado actual del repo)

Rama `fix/aagy-ecc-paridad-claude`, revisada el 2026-11-20:

| # | Hallazgo | Implicación para los doctors |
| :- | :--- | :--- |
| H1 | `audit_plugin_parity.py` da `PASS` (169 skills / 49 agentes en ambos lados) y `sync_aagy_ecc.py --check` da `IN_SYNC`. | Base reutilizable para los checks de repo. Deben importarse como librería, no relanzarse como subproceso. |
| H2 | El `hooks.json` raíz (Antigravity) llama a `pwsh -File scripts/ps1/safety-check.ps1` y `hook-post-write.ps1` con **rutas relativas**, pero `aagy-sync` solo copia `skills/`, `agents/`, `rules/`, `plugin.json` y `hooks.json` a `~/.gemini/...`. Fuera del repo aagy esos scripts no existen. | Master confirma que no es un requisito (P5). `DOC-09` lo marca WARN. |
| H3 | La raíz **no tiene mecanismo de comandos** para Antigravity: `doc/01-architecture/GUIA_...md` cita `commands/` en la raíz, pero esa carpeta no existe. aagy-ecc sí tiene `aagy-ecc/commands/*.md`. | Decidido: skill más script (P1). La guía de arquitectura tiene una referencia obsoleta. |
| H4 | El instalador no deja constancia del perfil instalado (`minimal` → fase `generic`, `full` → fase `all`) ni de la versión/commit. | Se resuelve con `.aagy-install.json` (RF-07). |
| H5 | Los hooks de aagy-ecc ejecutan `P=$(command -v python \|\| command -v python3)`; en Windows dependen de un `bash` en el PATH y de que `python` no sea el alias de la Microsoft Store. | Check específico de intérprete en `/aagy-ecc-doctor`. |
| H6 | `instinct_manager.resolve_plugin_data_dir` usa `AGY_PLUGIN_DATA`, `CLAUDE_PLUGIN_DATA` o `~/.gemini/config/plugins/aagy/.data`. | Los dos doctors verifican que el directorio de datos resuelto existe y es escribible. |

---

## 3. Requisitos Funcionales

### 3.1. Comunes a ambos doctors

- **`RF-01` Dos doctors separados con paridad 1:1**: cada harness tiene su propio doctor, que se puede ejecutar y entregar por separado:
  - `scripts/py/aagy_doctor.py` para Antigravity/Gemini.
  - `aagy-ecc/scripts/py/aagy_ecc_doctor.py` para Claude Code.
  Los dos tienen el mismo catálogo de checks (`DOC-01` a `DOC-14`), con la misma numeración, nombre, severidad y formato de salida. Solo cambia la implementación específica de cada harness. Las utilidades neutrales (formato de resultados, lectura de JSON, comparación de contenido) pueden vivir en un módulo común espejado por `sync_aagy_ecc.py`.
- **`RF-02` Resultado por check**: cada check devuelve `PASS | WARN | FAIL | SKIP`, un mensaje de una línea, evidencia (ruta, valor encontrado frente al esperado) y, si existe, el comando de arreglo sugerido.
- **`RF-03` Solo lectura por defecto**: sin flags, el doctor no escribe nada en disco (ver sección 5).
- **`RF-04` Tres ámbitos**: instalación, repo y proyecto (decisión P3).
  - Los checks de repo se ejecutan dentro del repo aagy, o con `--repo-root`.
  - Los checks de proyecto se ejecutan en el directorio actual, o con `--project`.
  - Si no aplican, salen como `SKIP`.
- **`RF-05` Filtros**: `--only <ID,...>`, `--skip <ID,...>`, `--json`, `--strict` (un WARN cuenta como fallo), `--verbose`, `--fix`, `--yes`.
- **`RF-06` Timeouts**: cada check tiene un límite de 5 s. El conjunto tarda menos de 10 s en una instalación normal.
- **`RF-07` Manifiesto de instalación** (decisión P4): `install.ps1`, `install.sh` y `aagy-sync` escriben `.aagy-install.json` en el destino con `harness`, `profile`, `version`, `commit`, `installed_at` y `source_repo`. Los doctors lo usan para saber qué skills y agentes esperar. Si falta, el check sale WARN y se compara con el perfil `generic`.
- **`RF-08` Entrega**:
  - `/aagy-doctor` se entrega como skill `skills/aagy-doctor/SKILL.md` más el script (decisión P1).
  - `/aagy-ecc-doctor` se entrega como comando slash `aagy-ecc/commands/aagy-ecc-doctor.md` más el script.
  - Ambos tienen wrappers en `scripts/ps1/` y `scripts/sh/`.

### 3.2. Catálogo de checks 1:1

| ID | Check | `/aagy-doctor` (Antigravity) | `/aagy-ecc-doctor` (Claude Code) | Severidad |
| :- | :--- | :--- | :--- | :---: |
| `DOC-01` | Runtime del harness | Antigravity/Gemini CLI localizable y versión. | CLI `claude` disponible y con la versión mínima. | FAIL |
| `DOC-02` | Plugin instalado | Existe `~/.gemini/config/plugins/aagy` (o `--plugin-dir`). | Marketplace `aagy-ecc` registrado y `aagy-ecc@aagy-ecc` instalado y habilitado. | FAIL |
| `DOC-03` | Manifiestos | `plugin.json` válido, con `name == "aagy"`. | `plugin.json` y `marketplace.json` válidos. | FAIL |
| `DOC-04` | Versión y manifiesto de instalación | `.aagy-install.json` presente. Versión igual a la del repo y a la de aagy-ecc. | Lo mismo para la copia instalada en la caché de plugins. | WARN |
| `DOC-05` | Reglas Tier 1 | `rules/AGENTS.md` existe, no está vacío, cabe en el presupuesto (≤ 24 KB / ≤ 20.000 tokens) y es idéntico al del repo. | El contexto que inyecta `session_start_rules.py` cabe en el mismo presupuesto y es idéntico al del repo. | FAIL / WARN deriva |
| `DOC-06` | Skills y agentes | Frontmatter válido (skill ≤ 140, agente ≤ 120). Recuento frente al perfil del manifiesto. | Lo mismo sobre la copia instalada de aagy-ecc. | WARN |
| `DOC-07` | Deriva frente al repo | Contenido instalado frente a `skills/`, `agents/` y `rules/` del repo. | Copia en caché frente a `aagy-ecc/` del repo (instalación sin refrescar tras un sync). | WARN |
| `DOC-08` | Comandos o puntos de entrada | La skill `aagy-doctor` y demás puntos de entrada tienen frontmatter válido. | `commands/*.md` con `description`, sin nombres duplicados ni choques con otros plugins. | WARN |
| `DOC-09` | Destinos de los hooks | `hooks.json` válido. Cada script referenciado existe donde Antigravity lo resuelve (ver H2 y P5). | `hooks.json` válido. Cada destino con `${CLAUDE_PLUGIN_ROOT}` existe. | FAIL / WARN |
| `DOC-10` | Intérpretes | Python ≥ 3.10 y `pwsh` ≥ 7. `markdownlint` es opcional. | `bash` (Git Bash en Windows) y un Python real ≥ 3.10, no el alias de la Store. `markdownlint` es opcional. | FAIL / WARN |
| `DOC-11` | Smoke test de hooks | Ejecutar el safety gate y el post-write con una entrada sintética. Se espera exit 0 y que bloquee un comando peligroso de prueba. | Ejecutar `session_start_rules.py`, `safety_check.py` y `post_write_lint.py` con stdin sintético. | FAIL |
| `DOC-12` | Datos y legado | El directorio `.data` (instintos) es escribible y se parsea. No hay restos del legado `ecc` ni huérfanos. | `CLAUDE_PLUGIN_DATA` (o la ruta de reserva) es escribible. No hay restos de `ecc` ni plugins que dupliquen aagy-ecc. | WARN |
| `DOC-13` | Proyecto | `.agents/` del proyecto: reglas y skills locales válidas, sin colisiones con las globales. | `CLAUDE.md` y `.claude/` de la plantilla no están desfasados frente a `project-template/`. | WARN |
| `DOC-14` | Repo | `audit_plugin_parity` en PASS y git hooks instalados. | `sync_aagy_ecc --check` en `IN_SYNC` y `audit_plugin_parity` en PASS. | WARN |

La auditoría de paridad añade un check nuevo: los dos doctors deben exponer exactamente los mismos IDs.

## 4. Formato de Salida

- **Humano (por defecto)**: cabecera con objetivo, ruta y versión; una línea por check `[PASS] DOC-05 rules/AGENTS.md (18,2 KB, idéntico al repo)`; para WARN/FAIL, una línea `→ Arreglo: <comando>`; resumen final `11 PASS · 2 WARN · 1 FAIL · 0 SKIP` (14 checks en total). Colores solo si la salida es una TTY.
- **JSON (`--json`)**: `{ "target", "plugin_dir", "version", "summary": {...}, "checks": [{ "id", "status", "message", "evidence", "fix" }] }`, estable para CI y para que el agente lo interprete.
- **Códigos de salida**: `0` sin FAIL (WARN permitidos), `1` hay algún FAIL (o WARN con `--strict`), `2` error interno del doctor.
- **Dentro del agente**: el comando slash ejecuta el motor con `--json` y el agente resume en lenguaje natural, listando primero los FAIL con su arreglo.

---

## 5. Comportamiento de Arreglo (`--fix`)

- Por defecto, **solo lectura**: el doctor nunca escribe.
- Con `--fix`, aplica solo arreglos seguros e idempotentes, mostrando antes la lista exacta de acciones:
  - Re-sincronizar desde el repo (`aagy-sync` con el perfil detectado / `sync_aagy_ecc.py`).
  - Crear directorios de datos que falten.
  - Reinstalar/actualizar el plugin en Claude Code (`claude plugin marketplace add` + `install`).
- Nunca borra huérfanos ni toca configuración del usuario sin confirmación explícita por acción (`--fix --yes` para modo no interactivo).
- Desde el comando slash, el agente pregunta al usuario antes de lanzar `--fix`.

---

## 6. Requisitos No Funcionales

- Python stdlib, sin dependencias nuevas; Windows, Linux, macOS y WSL.
- Sin red por defecto; `--online` opcional (p. ej. comparar con la última release de GitHub).
- No imprime secretos (reutiliza `redact_secrets` si muestra contenido de configuración).
- Tests `pytest` ≥ 80 % sobre el motor, con instalaciones falsas en `tmp_path`. Los tests que necesiten `pwsh` se marcan para saltarse si no está disponible.
- Paridad: `audit_plugin_parity.py` pasa a exigir que existan ambos doctors con el mismo conjunto de IDs `DOC-*`.

---

## 7. Criterios de Aceptación

- [ ] **`CA-01`**: Dada una instalación sana, cuando se ejecuta cada doctor, entonces todos los checks salen PASS o SKIP y el exit code es 0 en menos de 10 s.
- [ ] **`CA-02`**: Dado un `hooks.json` de aagy-ecc que apunta a un script inexistente, entonces `DOC-09` sale FAIL con la ruta y un arreglo sugerido.
- [ ] **`CA-03`**: Dado un espejo desfasado, entonces `DOC-14` sale WARN y `--fix` (con confirmación) lo deja en `IN_SYNC`.
- [ ] **`CA-07`**: Los dos doctors devuelven el mismo conjunto de IDs `DOC-01` a `DOC-14`, y la auditoría de paridad falla si difieren.
- [ ] **`CA-04`**: Sin `--fix`, ningún fichero cambia (verificado por mtime en los tests).
- [ ] **`CA-05`**: `--json` produce un documento válido con el esquema de la sección 4.
- [ ] **`CA-06`**: Cobertura ≥ 80 %.

---

## 8. Impacto y Riesgos

| Dimensión | ¿Impactado? | Riesgo | Detalle |
| :--- | :---: | :---: | :--- |
| Paridad aagy ↔ aagy-ecc | SÍ | Bajo | Dos doctors con catálogo 1:1 y un check nuevo en la auditoría de paridad. |
| Instaladores | SÍ | Bajo | Escriben `.aagy-install.json` (RF-07). Es un cambio aditivo. |
| Presupuesto de contexto | SÍ | Bajo | Un comando/skill más; descripción ≤ 140 caracteres. |
| Breaking changes | NO | - | Todo es aditivo. |

---

## 9. Decisiones de Master (2026-11-20)

1. **`P1` Invocación en Antigravity**: skill más script. Aceptado.
2. **`P2` Arreglos**: solo lectura por defecto y `--fix` con confirmación. Aceptado.
3. **`P3` Alcance**: todo (instalación, repo y proyecto).
4. **`P4` Manifiesto de instalación**: sí, los instaladores escriben `.aagy-install.json`.
5. **`P5` Hooks y estructura**: "no, cada uno separado pero 1:1". Master confirmó esta lectura:
   - Los hooks de la instalación aagy no tienen que funcionar fuera del repo, así que H2 se marca WARN en `DOC-09` y no FAIL.
   - Cada harness tiene su propio doctor, en vez de un motor único, con un catálogo de checks idéntico (sección 3).
6. **`P6` Idioma de salida**: español.
