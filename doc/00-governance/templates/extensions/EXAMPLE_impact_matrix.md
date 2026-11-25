## Matriz de impacto del proyecto

Ejemplo de extensión. Un repo consumidor copia este fichero a su repo y lo declara en `.governance/docs-map.json`:

```json
{ "template_extensions": { "REQ": ["doc/00-governance/extensions/impact_matrix.md"] } }
```

| Dimensión | ¿Impactada? | Riesgo | Detalle y mitigación |
| :--- | :---: | :---: | :--- |
| Contratos compartidos | `NO` | - | `<APIs, SDK, esquemas>` |
| Persistencia | `NO` | - | `<migraciones, bloqueos>` |
| Red y despliegue | `NO` | - | `<rutas, DNS, certificados>` |
| Recursos | `NO` | - | `<CPU, memoria, límites>` |
