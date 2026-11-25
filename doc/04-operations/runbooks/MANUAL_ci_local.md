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

- Las skills que usan una API de pago declaran `cost: paid` en su frontmatter
  (`exa-search`, `deep-research`). `audit_plugin_parity.py` lo comprueba.
- Con `AAGY_BUDGET` sin definir o `0` (`budget` en las capas de `aagy_config`), `aagy-sync`
  no las instala y `toggle_gemini_mcp.py --enable` se niega.
- `gemini_deep_ops.py` no usa la API de Gemini: análisis heurístico más el resumen del
  modelo local (`local_run`) si está disponible.
