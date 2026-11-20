# Fase 1: Requisitos e Impacto Home-Lab | Analizador Estático de Bloqueos DDL en PostgreSQL LTS

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/audit-pg-locks`  
> **Fecha**: 2026-11-20 | **Autor/Rol**: Argon ($Ar_{18}$) & Carbon ($C_6$) - Principal Database Reliability Engineer  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**:
  En el Home-Lab, todos los microservicios convergen en una única instancia endurecida de PostgreSQL LTS (Pilar 3: Centralized Multi-Database Persistence). En bases de datos en producción o de persistencia compartida, ciertas sentencias DDL adquieren bloqueos pesados como `ACCESS EXCLUSIVE` (ej. `DROP TABLE`, `TRUNCATE`, `ALTER TABLE ... DROP COLUMN`, `ALTER TABLE ... ALTER COLUMN TYPE`, `CREATE INDEX` sin `CONCURRENTLY`, o adición de constraints sin `NOT VALID`). Estos bloqueos congelan todas las lecturas y escrituras en la tabla afectada, encolando transacciones y agotando el pool de conexiones de todos los microservicios en minutos.
- **Objetivo Principal**:
  Construir un analizador estático determinista (`audit_pg_locks.py`) y sus wrappers CLI (`audit-pg-locks.ps1` / `.sh`) que clasifique las sentencias de migraciones SQL en 3 niveles de riesgo (Verde/Seguro, Amarillo/Precaución, Rojo/Crítico), sugiera alternativas seguras de concurrencia y se integre en la compuerta de PR de `complete-task-pr.ps1`.
- **Alcance (`In-Scope`)**:
  1. Análisis léxico de archivos SQL (`*.sql`) buscando operaciones DDL peligrosas:
     - Bloqueos `ACCESS EXCLUSIVE` (Rojo): `DROP TABLE`, `TRUNCATE`, `DROP COLUMN`, `ALTER COLUMN TYPE`, `ADD CONSTRAINT` sin `NOT VALID`, adición de columnas con valores por defecto volátiles (`now()`, `random()`), `VACUUM FULL`, `REINDEX` sin concurrencia.
     - Bloqueos `SHARE` (Amarillo): `CREATE INDEX` estándar sin `CONCURRENTLY`, `DROP INDEX` sin `CONCURRENTLY`.
     - Operaciones Seguras (Verde): `CREATE INDEX CONCURRENTLY`, `DROP INDEX CONCURRENTLY`, `ADD COLUMN` nullable o constante en PG11+, constraints con `NOT VALID` seguido de `VALIDATE CONSTRAINT`.
  2. Sugerencias automáticas de remediación y buenas prácticas de concurrencia para cada hallazgo crítico.
  3. Modos de escaneo: archivo individual (`--file`), directorio (`--dir`), repositorio raíz (`--root`), y diff en Git (`--diff`).
  4. Omisión limpia (`SKIPPED`, código 0) si no se encuentran archivos `.sql`.
  5. Salida estructurada JSON (`--json`) y formato tabular legible.
  6. Wrappers CLI `scripts/bin/ecc-agy/audit-pg-locks.ps1` y `audit-pg-locks.sh`.
  7. Integración en `complete-task-pr.ps1` ante la presencia de archivos `.sql` modificados.
  8. Suite exhaustiva de pruebas en `scripts/ecc-agy/tests/test_audit_pg_locks.py`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Conexión directa a base de datos en ejecución (el análisis es puramente estático sobre los archivos de migración).

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01 (Clasificación de Riesgos DDL)`**:
  El analizador debe categorizar cada sentencia DDL en `HIGH` (Rojo: `ACCESS EXCLUSIVE` prolongado / table rewrite), `MEDIUM` (Amarillo: `SHARE` lock / bloqueo de escrituras), o `LOW` (Verde: concurrente o metadata-only).
- **`RF-02 (Catálogo de Remediaciones)`**:
  Para cada sentencia clasificada como `HIGH` o `MEDIUM`, el reporte debe indicar la alternativa segura recomendada (ej. cambiar `CREATE INDEX` a `CREATE INDEX CONCURRENTLY`, o añadir constraint con `NOT VALID`).
- **`RF-03 (Bloqueo en Modo Estricto)`**:
  En modo `--strict` (activado por defecto en PRs), si se detectan hallazgos `HIGH`, el proceso debe finalizar con código de error `1`.
- **`RF-04 (Omisión Elegante)`**:
  Si el directorio o cambios analizados no contienen archivos `.sql`, el script debe retornar `0` con estado `SKIPPED`.
- **`RF-05 (Integración en Lifecycle y PRs)`**:
  `complete-task-pr.ps1` debe invocar `audit-pg-locks.ps1` si detecta archivos `.sql` en el commit o área de trabajo.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [ ] **`CA-01`**: Dado un archivo SQL con `CREATE INDEX idx_user ON users(email);`, cuando se analiza con `audit_pg_locks.py`, entonces se clasifica como `MEDIUM` indicando sugerencia de usar `CONCURRENTLY`.
- [ ] **`CA-02`**: Dado un archivo SQL con `ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id);`, cuando se analiza, se clasifica como `HIGH` indicando que requiere `NOT VALID`.
- [ ] **`CA-03`**: Dado un archivo SQL con `CREATE INDEX CONCURRENTLY idx_user ON users(email);` y `ALTER TABLE orders ADD CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id) NOT VALID;`, cuando se analiza, entonces el resultado es `PASS` con código de salida `0`.
- [ ] **`CA-04`**: Dado un repositorio sin archivos `.sql`, cuando se ejecuta `audit_pg_locks.py`, retorna código `0` con estado `SKIPPED`.
- [ ] **`CA-05`**: Cobertura de tests unitarios $\ge 80\%$ y SonarQube Rating A (0 violaciones, Cognitive Complexity $\le 15$).

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin impacto en interfaces ni clientes SDK. |
| **Persistencia PostgreSQL LTS** | `SÍ` | `Alto` | Protege activamente la base de datos central multitenant frente a bloqueos no planificados y agotamiento de conexiones. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Sin impacto en Traefik ni TLS. |
| **Resolución Split-DNS** | `NO` | - | Sin impacto en DNS. |
| **Restricciones de Hardware** | `NO` | - | Script estático ultraligero ($< 100\text{ ms}$). |
| **Variables `.env` / Secretos** | `NO` | - | No requiere secretos ni variables adicionales. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva**:
  Herramienta de auditoría estática preventiva; no altera sentencias SQL ni bases de datos activas.

---

## 5. Compuertas SRE de Rendimiento y Seguridad

- **Latencia Objetivo**: Tiempo de análisis estático $< 200\text{ ms}$ por cada 1.000 líneas SQL.
- **Seguridad**: Análisis estrictamente local en solo lectura; sin ejecución de SQL dinámico ni conexiones remotas.
