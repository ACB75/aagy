# Fase 1: Toma de requisitos e impacto

> **ID de Tarea**: `<id_tarea>`
> **Fecha**: `YYYY-MM-DD` | **Autor/Rol**: `<autor / rol>`
> **Estado**: `BORRADOR | EN REVISIÓN | APROBADO`
> **Ubicación en el repo**: `<carpeta de planes>/REQ_<id_tarea>.md`

---

## 0. Estado actual

| Pieza | Dónde | Hoy | Problema |
| :--- | :--- | :--- | :--- |
| `<componente>` | `<ruta>` | `<comportamiento actual>` | `<qué falla o falta>` |

## 1. Contexto y objetivos

- **Problema**: qué se resuelve y por qué ahora.
- **Objetivo**: resultado observable en una o dos líneas.
- **Alcance**: qué entra.
- **Fuera de alcance**: qué no entra.

## 2. Requisitos funcionales

- **RF-01**: entradas, transformaciones, validaciones y salidas esperadas.
- **RF-02**: flujos alternativos, fronteras y errores.

## 3. Requisitos no funcionales

- **Rendimiento**: latencia o coste objetivo y complejidad esperada.
- **Seguridad**: entradas no confiables, secretos, permisos, rutas (amenaza y mitigación).
- **Coste**: 0 $ por defecto; cualquier servicio de pago se declara aquí.

## 4. Impacto y retrocompatibilidad

- **Contratos afectados**: APIs, esquemas, ficheros de configuración, CLIs.
- **¿Rompe algo?**: `NO` o `SÍ` con la ruta de transición (deprecación, doble lectura).
- **Rollback**: cómo se vuelve atrás.

<!-- aagy-extensions -->

## 5. Criterios de aceptación

- [ ] **CA-01**: Dado `<contexto>`, cuando `<acción>`, entonces `<resultado verificable>`.
- [ ] **CA-02**: Casos límite: entradas vacías, nulas, fuera de rango o malformadas.

## 6. Paridad aagy ↔ aagy-ecc

Cómo se comporta en los dos plugins. Si un harness no lo permite, declara la asimetría.

## 7. Preguntas abiertas

- **P-01**: `<pregunta>`. Por defecto: `<valor que se usa si nadie responde>`.

## 8. Referencias

- `<rutas, ADR, issues>`
