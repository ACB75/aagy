# Autopsia Post-Incidente (Post-Mortem 5W): fix/aagy/doctor-windows-store-python

> **Guía de Gobernanza SRE (ADR-0008):**
>
> - Esta autopsia es estrictamente **sin culpables (blameless)**. Su propósito es fortalecer los sistemas, guardrails y procesos defensivos de ingeniería.
> - Se genera automáticamente tras la resolución de ramas `fix/*`.

---

## 1. Metadatos del Incidente

- **Identificador de Rama / Incidente**: `fix/aagy/doctor-windows-store-python`
- **Fecha y Hora de Cierre (UTC)**: `2026-11-21T00:08:35Z`
- **Ingeniero Responsable / Autor**: `ACB75`
- **Entorno Afectado**: `LOCAL / DEV`
- **Severidad Preliminar**: `SEV-2 (Degradación Parcial)`
- **Impacto en Error Budget (SLO)**: `Agotamiento < 0.1% del presupuesto mensual`
- **Resumen de Cambios (Git Diff)**:
  `.gitignore                                         |   3 +
 README.md                                          |   4 +
 aagy-ecc/README.md                                 |   4 +-
 aagy-ecc/commands/aagy-ecc-doctor.md               |  44 ++
 aagy-ecc/scripts/py/aagy_ecc_doctor.py             | 564 ++++++++++++++++++++
 aagy-ecc/scripts/py/doctor_core.py                 | 572 +++++++++++++++++++++
 aagy-ecc/scripts/py/install_manifest.py            | 149 ++++++
 .../GUIA_ARQUITECTURA_HARNESS_Y_ENTORNO_AGY.md     |   2 +-
 doc/04-operations/runbooks/MANUAL_aagy_doctor.md   | 102 ++++
 doc/06-backlog/plans/PLAN_aagy_doctor_commands.md  | 154 ++++++
 doc/06-backlog/plans/REQ_aagy_doctor_commands.md   | 149 ++++++
 doc/INDEX.md                                       |   1 +
 doc/LOG.md                                         |  11 +
 install.ps1                                        |   3 +
 install.sh                                         |   1 +
 scripts/ps1/aagy.ps1 aagy-doctor                        |  43 ++
 scripts/ps1/aagy.ps1 aagy-ecc-doctor                    |  43 ++
 scripts/ps1/aagy-sync.ps1                          |  20 +-
 scripts/ps1/tests/test_scripts_ps1.py              |   2 +
 scripts/py/aagy_doctor.py                          | 501 ++++++++++++++++++
 scripts/py/audit_plugin_parity.py                  |  31 ++
 scripts/py/doctor_core.py                          | 572 +++++++++++++++++++++
 scripts/py/install_manifest.py                     | 149 ++++++
 scripts/py/sync_aagy_ecc.py                        |  11 +
 scripts/py/tests/test_aagy_doctor.py               | 292 +++++++++++
 scripts/py/tests/test_aagy_ecc_doctor.py           | 292 +++++++++++
 scripts/py/tests/test_doctor_core.py               | 302 +++++++++++
 scripts/py/tests/test_doctor_parity.py             |  75 +++
 scripts/sh/aagy.sh aagy-doctor                          |  19 +
 scripts/sh/aagy.sh aagy-ecc-doctor                      |  19 +
 scripts/sh/aagy-sync.sh                            |  14 +-
 scripts/sh/tests/test_scripts_sh.py                |   2 +
 skills/aagy-doctor/SKILL.md                        |  58 +++
 33 files changed, 4204 insertions(+), 4 deletions(-)`

---

## 2. Resumen Ejecutivo (Blameless Summary)

Breve resumen descriptivo del fallo observado, cómo fue detectado por las sondas o tests, y la estrategia aplicada para mitigar y solventar la anomalía.

---

## 3. Análisis Exhaustivo de las 5W

### 3.1. Who (Quién / Qué Componentes)

- **Microservicios afectados**: Componentes o módulos involucrados en la degradación.
- **Actores y dependencias**: Clientes, proxies Ingress, colas o bases de datos que interactuaron con el fallo.

### 3.2. What (Qué Ocurrió)

- **Síntomas observables**: Códigos de error HTTP 5xx, timeouts, memory leaks o excepciones no controladas.
- **Impacto**: Número de peticiones degradadas o impacto en la experiencia de usuario.

### 3.3. When (Cronología de Eventos UTC)

- `HH:MM:SS UTC` - **Detección**: Activación de alarma o fallo en tests de integración.
- `HH:MM:SS UTC` - **Diagnóstico**: Aislamiento del componente causante y reproducción del error.
- `HH:MM:SS UTC` - **Mitigación / Fix**: Commit correctivo en rama `fix/*` y validación de tests.
- `HH:MM:SS UTC` - **Resolución**: Fusión en `main` y verificación verde del Ingress.

### 3.4. Where (Dónde)

- **Localización técnica**: Módulos, controladores, endpoints o consultas SQL afectadas.
- **Entorno de ejecución**: Contenedores Docker, pods o servicios en red local `*.home.arpa`.

### 3.5. Why & How (Por Qué y Cómo)

- **Mecanismo de fallo**: Descripción técnica exacta de la condición de carrera, desbordamiento o excepción no capturada.
- **Propagación del blast radius**: Por qué el fallo no fue contenido por circuit breakers o bulkheads.

---

## 4. Análisis de Causa Raíz (5 Porqués / 5-Whys)

1. **¿Por qué falló el servicio?** ->
2. **¿Por qué ocurrió esa condición?** ->
3. **¿Por qué no se detectó en tests previos?** ->
4. **¿Por qué no existía un guardrail defensivo?** ->
5. **¿Por qué la arquitectura permitió la propagación?** -> *(Causa Raíz Fundamental)*

---

## 5. Acciones Preventivas y Correctivas

| Tipo | Acción Concreta | Responsable | Prioridad | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **Mitigación** | Corrección aplicada en rama `fix/aagy/doctor-windows-store-python` | `ACB75` | P0 | Resuelto |
| **Prevención** | Test de regresión automatizado añadido | Equipo Dev | P1 | Planificado |
| **Monitoreo** | Ajuste de métricas SLI y alertas tempranas | Equipo SRE | P1 | Planificado |
