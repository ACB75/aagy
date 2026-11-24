---
name: aagy-doctor
description: "Diagnose global aagy plugin health (DOC-01..15, DOC-17) via aagy_doctor.py."
metadata:
  origin: AAGY
---

# aagy-doctor

Diagnóstico de la instalación de `aagy` en Google Antigravity / Gemini. Es el
equivalente de `/aagy-ecc-doctor` en Claude Code: los dos ejecutan el mismo
catálogo de checks `DOC-01` a `DOC-15` y `DOC-17` (paridad 1:1, ver `scripts/py/doctor_core.py`).

## Cuándo usarla

- El usuario pide `/aagy-doctor`, "diagnostica aagy", "¿está bien instalado aagy?" o "revisa el plugin".
- Después de instalar o actualizar `aagy` (`install.ps1 -Target agy`, `aagy-sync`).
- Cuando un hook, una skill o las reglas Tier 1 no se comportan como se espera.

## Reglas

1. **Delegar en el script**: nunca repitas los checks a mano con `find` o `grep`. Ejecuta el doctor.
2. **Solo lectura por defecto**: ejecuta primero sin `--fix`.
3. **Confirmación antes de arreglar**: si hay WARN o FAIL con arreglo, enséñaselos al usuario y pregunta antes de volver a ejecutar con `--fix --yes`.
4. **No ocultar fallos**: lista primero los FAIL, con su ID, el mensaje y el arreglo propuesto.

## Cómo ejecutarlo

El plugin instalado no incluye `scripts/`. Usa el repo de origen que registra el manifiesto de instalación:

1. Lee `~/.gemini/config/plugins/aagy/.aagy-install.json` y toma `source_repo`.
2. Ejecuta, con salida JSON:

```bash
python "<source_repo>/scripts/py/aagy_doctor.py" --json
```

Si no hay manifiesto (instalación anterior a esta versión), ejecútalo desde el
repo aagy o con el wrapper:

```powershell
pwsh -NoProfile -File scripts/ps1/aagy-doctor.ps1          # informe legible
pwsh -NoProfile -File scripts/ps1/aagy-doctor.ps1 -Json    # JSON
pwsh -NoProfile -File scripts/ps1/aagy-doctor.ps1 -Fix     # arreglos con confirmación
```

```bash
scripts/sh/aagy-doctor.sh [--json] [--fix] [--only DOC-05,DOC-09]
```

## Cómo presentar el resultado

1. Una línea de resumen: `N PASS · N WARN · N FAIL · N SKIP`.
2. Los FAIL y después los WARN, cada uno con su ID, el mensaje y la línea `Arreglo`.
3. Los SKIP solo si el usuario pregunta (suelen ser checks de repo o proyecto que no aplican).
4. Si hay arreglos, pregunta: "¿Aplico estos arreglos?". Solo con un sí, ejecuta `--fix --yes`.

Exit code: `0` sin FAIL, `1` con algún FAIL (o WARN con `--strict`), `2` error interno del doctor.
