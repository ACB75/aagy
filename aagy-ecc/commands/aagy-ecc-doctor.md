---
description: Diagnose the aagy-ecc install in Claude Code (plugin, hooks, commands, repo parity) with checks DOC-01..17.
---

# aagy-ecc-doctor

Diagnóstico de la instalación de `aagy-ecc` en Claude Code. Es el equivalente
de la skill `aagy-doctor` de Antigravity: los dos ejecutan el mismo catálogo de
checks `DOC-01` a `DOC-17` (paridad 1:1).

## Uso

```text
/aagy-ecc-doctor            # informe completo
/aagy-ecc-doctor --fix      # además, propone arreglos y los aplica tras confirmarlos
/aagy-ecc-doctor --only DOC-09,DOC-11
```

## Qué hacer

1. Ejecuta el doctor en solo lectura, con salida JSON, pasando los argumentos del usuario salvo `--fix`:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/py/aagy_ecc_doctor.py" --json $ARGUMENTS
   ```

   Si `python3` no existe (Windows), usa `python`. Si `${CLAUDE_PLUGIN_ROOT}` no está
   disponible y estás en el repo aagy, usa `aagy-ecc/scripts/py/aagy_ecc_doctor.py`.

2. Resume el resultado en español:
   - Una línea: `N PASS · N WARN · N FAIL · N SKIP`.
   - Los FAIL y después los WARN, cada uno con su ID, el mensaje y el arreglo (`fix`).
   - Los SKIP solo si el usuario lo pide.

3. Si el usuario pasó `--fix` y hay arreglos, enséñale la lista y pregunta antes de aplicar.
   Solo con un sí explícito ejecuta:

   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/py/aagy_ecc_doctor.py" --fix --yes
   ```

Nunca apliques arreglos sin confirmación. El doctor es de solo lectura sin `--fix`.

Exit code: `0` sin FAIL, `1` con algún FAIL (o WARN con `--strict`), `2` error interno del doctor.
