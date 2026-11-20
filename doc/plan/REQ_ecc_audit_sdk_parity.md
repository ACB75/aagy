# Fase 1: Requisitos e Impacto Home-Lab | Linter de Paridad Estática de Contratos SDK

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/audit-sdk-parity`  
> **Fecha**: 2026-11-20 | **Autor/Rol**: Argon ($Ar_{18}$) & Carbon ($C_6$) - Distributed Systems Contract Architect  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**:
  En la arquitectura distribuida de Home-Lab, los microservicios en `services/` (Go, Python, Java) y `cluster/` exponen contratos REST y modelos de datos consumidos por frontend (Angular/TypeScript) y otros servicios a través de la biblioteca cliente `home-lab-sdk/`. Si un desarrollador añade o modifica un endpoint o modelo en un microservicio sin sincronizar el cliente correspondiente en `home-lab-sdk/`, se producen errores de integración 404/400 en tiempo de ejecución. La regla canónica "Mandatory Microservice & SDK Contract Parity" requiere un linter estático determinista que certifique paridad y bloquee PRs divergentes.
- **Objetivo Principal**:
  Implementar un analizador estático en Python (`audit_sdk_parity.py`) con wrappers PowerShell (`audit-sdk-parity.ps1`) y Bash (`audit-sdk-parity.sh`), integrado en la Fase 4 del lifecycle (`complete-task-pr.ps1`), que extraiga endpoints y modelos de microservicios y certifique que el SDK cliente polyglot (TypeScript, Go, Python, Java) contiene los métodos y tipos correspondientes.
- **Alcance (`In-Scope`)**:
  1. Extracción estática de endpoints en controladores de microservicios: Go (Gin, Chi, gorilla/mux, http standard), Python (FastAPI `@app.*`, `@router.*`), Java (Spring `@GetMapping`, `@PostMapping`, etc.).
  2. Extracción estática de llamadas/métodos en clientes polyglot de SDK (`home-lab-sdk/`): TypeScript/Angular, Go SDK, Python SDK, Java SDK.
  3. Detección de divergencias: endpoints públicos expuestos sin correspondencia en el cliente SDK.
  4. Exclusión de rutas internas/diagnósticas: `/metrics`, `/health`, `/livez`, `/readyz`, `/debug/*`, `/ping`, `/favicon.ico`.
  5. Modos de ejecución: escaneo completo de directorio, escaneo de diff staged/working tree (`--diff`), y detección automática de omisión si el repositorio no contiene `services/` o `home-lab-sdk/`.
  6. Salida tabular legible y JSON (`--json`), con código de salida `0` (paridad aprobada) o `1` (divergencia detectada).
  7. Wrappers CLI en `scripts/bin/ecc-agy/audit-sdk-parity.ps1` y `.sh`.
  8. Integración como paso de Quality Gate en `complete-task-pr.ps1`.
  9. Suite de pruebas exhaustiva en `scripts/ecc-agy/tests/test_audit_sdk_parity.py`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Generación automática de código SDK (esto lo orquesta `sdk-synchronizer.md`).
  - Dependencias pesadas externas como parsers de compilador Go o Java nativos (se usa Python stdlib `ast`, `re`, `pathlib`).

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01 (Extracción de Endpoints en Microservicios)`**:
  El analizador debe procesar archivos en `services/` o `--services-dir` extrayendo el método HTTP (`GET`, `POST`, `PUT`, `DELETE`, `PATCH`) y la ruta normalizada (ej. `/api/v1/auth/login`), ignorando endpoints internos de infraestructura.
- **`RF-02 (Extracción de Cobertura en SDK)`**:
  El analizador debe inspeccionar los archivos cliente en `home-lab-sdk/` o `--sdk-dir` buscando métodos, URLs o llamadas HTTP que cubran las rutas expuestas por los microservicios.
- **`RF-03 (Detección de Divergencias y Bloqueo)`**:
  Si existen endpoints en microservicios no cubiertos en el SDK cliente, el analizador reportará el detalle de endpoints huérfanos y finalizará con código `1` (o advertencia si no es `--strict`).
- **`RF-04 (Omisión Elegante sin Entorno Microservicios)`**:
  Si el repositorio analizado no contiene carpetas `services/` ni `home-lab-sdk/`, el script emitirá un mensaje informativo y retornará `0` para no romper repositorios como `ecc`.
- **`RF-05 (Salida Estructurada JSON)`**:
  Soporte de bandera `--json` retornando un objeto con `parity_status` (`PASS` | `FAIL` | `SKIPPED`), `total_endpoints`, `covered_endpoints`, `missing_endpoints` y `details`.
- **`RF-06 (Integración en Lifecycle y complete-task-pr.ps1)`**:
  Invocación de `audit-sdk-parity.ps1` durante la verificación previa de `complete-task-pr.ps1`.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [ ] **`CA-01`**: Dado un microservicio en Go con `r.GET("/api/v1/users", ...)` y un SDK en TypeScript que incluye método con `/api/v1/users`, cuando se ejecuta `audit_sdk_parity.py`, entonces el resultado es `PASS` con código de salida `0`.
- [ ] **`CA-02`**: Dado un microservicio que añade `r.POST("/api/v1/users/export", ...)` sin método correspondiente en el SDK, cuando se ejecuta `audit_sdk_parity.py`, entonces el resultado es `FAIL` con código de salida `1` y detalle del endpoint huérfano.
- [ ] **`CA-03`**: Dado un microservicio con rutas `/metrics` y `/health`, cuando se ejecuta `audit_sdk_parity.py`, entonces dichas rutas internas son ignoradas y no se exige cliente SDK para ellas.
- [ ] **`CA-04`**: Dado un directorio sin `services/` ni `home-lab-sdk/`, cuando se ejecuta `audit_sdk_parity.py`, entonces retorna `0` con estado `SKIPPED`.
- [ ] **`CA-05`**: Cobertura de tests unitarios $\ge 80\%$ y SonarQube Rating A (0 violaciones, Cognitive Complexity $\le 15$).

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `SÍ` | `Bajo` | Proporciona la herramienta canónica de auditoría estática para hacer cumplir la paridad en CI/CD y en PRs locales. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin impacto en esquemas ni migraciones de base de datos. |
| **Ingress Único (`cluster-lb`)** | `NO` | - | No altera configuraciones de Traefik ni Apache. |
| **Resolución Split-DNS** | `NO` | - | Sin impacto en registros DNS ni CoreDNS. |
| **Restricciones de Hardware** | `NO` | - | Ejecución estática ligera en Python stdlib ($< 250\text{ ms}$). |
| **Variables `.env` / Secretos** | `NO` | - | No requiere secretos ni variables de entorno adicionales. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva**:
  La herramienta es puramente analítica y aditiva. Si no se detectan `services/` ni `home-lab-sdk/`, se omite silenciosamente sin fallar la integración en `main`.

---

## 5. Compuertas SRE de Rendimiento y Seguridad

- **Latencia Objetivo**: Tiempo de análisis estático $< 300\text{ ms}$ para proyectos de tamaño medio.
- **Complejidad Algorítmica**: $O(F \times L)$ donde $F$ es el número de archivos de controladores/SDK y $L$ el número de líneas.
- **Seguridad**: Análisis estrictamente local en solo lectura; sin ejecución de código dinámico (`eval`/`exec`) ni llamadas a red externa.
