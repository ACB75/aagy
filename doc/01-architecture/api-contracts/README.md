# Contratos y Esquemas del Ecosistema (`01-architecture/api-contracts/`)

Esta sección centraliza los contratos estructurales y de interfaz CLI del arnés `aagy` / `ecc`.

## Contratos Vigentes

| Contrato | Archivo Fuente | Validador / Consumidor |
| :--- | :--- | :--- |
| **Mapa Documental v2 y Fallback** | [`.governance/docs-map.json`](../../../.governance/docs-map.json) | [`scripts/py/docs_map.py`](../../../scripts/py/docs_map.py) y [`map_docs.py`](../../../scripts/py/map_docs.py) |
| **Manifiesto del Plugin AGY** | [`plugin.json`](../../../plugin.json) | [`audit_plugin_parity.py`](../../../scripts/py/audit_plugin_parity.py) |
| **Hooks Nativos de Sesión** | [`hooks.json`](../../../hooks.json) | [`security_audit.py`](../../../scripts/py/security_audit.py) |
| **Reglas Markdown (DavidAnson)** | [`.markdownlint.json`](../../../.markdownlint.json) | [`lint-markdown.ps1`](../../../scripts/bin/ecc-agy/lint-markdown.ps1) / `.sh` |

## Salidas `--json` Estandarizadas

- `python scripts/py/docs_map.py --repo-root . --validate --json`: emite `{ "valid": bool, "issues": list[str], "schema_version": 1|2 }`.
- `python scripts/py/audit_plugin_parity.py --repo-root . --json`: emite contrato `ParityAuditResult` verificando simetría `aagy` $\leftrightarrow$ `ecc`.
- `python scripts/py/format_commit.py --validate "<msg>" --strict --json`: emite `CommitValidationResult`.
