# Postmortem 5W: {{BRANCH}}

> **ID de Tarea**: `{{BRANCH}}`
> **Fecha**: `{{TIMESTAMP_UTC}}` | **Autor/Rol**: `{{AUTHOR}}`
> **Estado**: `BORRADOR | REVISADO`
> **Ubicación en el repo**: `<carpeta de postmortems>/PM_<rama>_<fecha>.md`

Sin culpables: el objetivo es reforzar sistemas, guardrails y procesos.

---

## 0. Estado actual

- **Entorno afectado**: `{{ENVIRONMENT}}`
- **Severidad**: `SEV-1 | SEV-2 | SEV-3`
- **Cambios (git diff)**: `{{DIFF_SUMMARY}}`

## 1. Contexto y objetivos

- **Problema**: qué falló y cómo se detectó.
- **Objetivo**: que no vuelva a pasar.
- **Alcance**: componentes afectados.
- **Fuera de alcance**: lo que no tuvo que ver.

## 2. Las 5W

- **Who**: componentes y dependencias implicados.
- **What**: síntomas e impacto.
- **When**: detección, diagnóstico, corrección y resolución (UTC).
- **Where**: módulos, endpoints o consultas.
- **Why / How**: mecanismo del fallo y por qué no se contuvo.

## 3. Causa raíz (5 porqués)

1. ¿Por qué falló? ->
2. ¿Por qué ocurrió esa condición? ->
3. ¿Por qué no lo detectaron los tests? ->
4. ¿Por qué no había un guardrail? ->
5. ¿Por qué el diseño permitió que se propagara? -> causa raíz

## 4. Acciones

| Tipo | Acción | Responsable | Prioridad | Estado |
| :--- | :--- | :--- | :--- | :--- |
| Mitigación | Corrección en `{{BRANCH}}` | `{{AUTHOR}}` | P0 | Resuelto |
| Prevención | Test de regresión | `<responsable>` | P1 | Planificado |

<!-- aagy-extensions -->

## 5. Criterios de aceptación

- [ ] **CA-01**: el test de regresión falla sin la corrección y pasa con ella.

## 6. Paridad aagy ↔ aagy-ecc

Si el fallo afecta a un plugin, comprobar el otro.

## 7. Preguntas abiertas

- **P-01**: `<pregunta>`. Por defecto: `<valor>`.

## 8. Referencias

- `<PR, issues, logs>`
