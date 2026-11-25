# Manual: CI Local y Presupuesto 0 $ (`MANUAL_ci_local.md`)

> **Motor**: [`ci_local.py`](../../../scripts/py/ci_local.py) | **Hook**: [`pre-push`](../../../scripts/py/hooks/pre-push) | **Regla**: `Budget $0` en `rules/AGENTS.md`

---

## 1. Qué cambia

Nada del repo cuesta dinero por defecto. Las comprobaciones de calidad se ejecutan
en el equipo antes de cada `git push`, no en GitHub Actions. Las Actions quedan como
plantillas opcionales en `templates/github-actions/`, apagadas, y la de calidad solo
llama a `ci_local.py`, así que lo local y lo remoto nunca divergen.

## 2. Puesta en marcha (una vez por clon)

```powershell
pwsh -File scripts/ps1/install-git-hooks.ps1   # pre-commit, commit-msg y pre-push
```

```bash
scripts/sh/install-git-hooks.sh
```

## 3. Uso

```text
python scripts/py/ci_local.py run            # todo (markdownlint, pytest, auditorías, plantillas, espejo, paridad)
python scripts/py/ci_local.py run --fast     # sin la suite de tests
python scripts/py/ci_local.py run --only pytest,sonar
python scripts/py/ci_local.py list           # pasos configurados
```

Un paso se salta (`SKIP`) si su herramienta o su script no existen. Un repo consumidor
puede declarar sus propios pasos en `.governance/aagy.json`:

```json
{ "ci": { "steps": ["npm test", "python -m pytest -q"], "private": true } }
```

Saltar el hook una vez: `GIT_HOOKS_BYPASS=1 git push`.

## 4. Actions opcionales

```text
python scripts/py/ci_local.py actions status
python scripts/py/ci_local.py actions on    # copia las plantillas a .github/workflows/
python scripts/py/ci_local.py actions off   # quita solo las copiadas por aagy
```

- `audit_plugin_parity.py` falla si la plantilla de calidad ejecuta algo que no sea `ci_local.py`.
- Con `ci.private: true`, DOC-17 avisa si hay workflows: en un repo privado gastan minutos.

## 5. Dependencias de pago

- Las skills que usen una API de pago deben declarar `cost: paid` en su frontmatter
  (actualmente el catálogo no incluye skills de pago). `audit_plugin_parity.py` lo comprueba.
- Con `AAGY_BUDGET` sin definir o `0` (`budget` en las capas de `aagy_config`), `aagy-sync`
  no las instala y `toggle_gemini_mcp.py --enable` se niega.
- `gemini_deep_ops.py` no usa la API de Gemini: análisis heurístico más el resumen del
  modelo local (`local_run`) si está disponible.

## 6. Sin referencias a proyectos consumidores

El plugin no nombra a ningún proyecto, máquina ni usuario que lo use (RF-14).
`scripts/py/consumer_refs.py` busca, en los ficheros versionados, los términos que el
repo declara en `consumer_refs` de `.governance/aagy.json` (o de la capa de entorno) y
falla si aparece alguno. El fichero que declara la lista es el único excluido.

```json
{ "projects": ["api", "web"], "consumer_refs": ["nombre-de-mi-proyecto", "mi-host"] }
```

Lo ejecutan `workspace_audit.py` (paso de auditoría de `ci_local.py`) y
`audit_plugin_parity.py` (solo en los árboles de los plugins). Sin términos declarados,
se salta. Los checks propios de un consumidor (paridad de SDK, bloqueos de migraciones,
rutas de ingress) viven en su repo y se declaran en `checks` de
`.governance/docs-map.json`; `complete_task_pr.py` los ejecuta sin conocerlos.
