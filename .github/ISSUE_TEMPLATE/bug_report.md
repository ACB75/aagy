---
name: Bug Report (fix)
about: Reportar un fallo o una regresión en aagy / aagy-ecc
title: "[fix]-[aagy,aagy-ecc]: "
labels:
  - bug
  - harness:both
---

# Bug Report (`fix/*`)

<!-- Mismas secciones que la PR y la tarea de TODO.md (plantilla base, #93). La tarea lleva issue=<N>. -->

## 1. Motivación

- **Síntoma**: error, mensaje y código de salida.
- **Pasos para reproducir**: comando o hook, harness (`aagy`, `aagy-ecc` o ambos) y sistema operativo.
- **Esperado**: resultado correcto.

## 2. Criterios de aceptación

- [ ] Test de regresión que falla sin la corrección y pasa con ella.

## 3. Paridad aagy ↔ aagy-ecc

- [ ] Comprobado en el otro plugin.

## 4. Artefactos

- Postmortem: `doc/05-post-mortems/PM_<rama>_<fecha>.md`
