# Fase 1: Toma de Requisitos, Análisis de Superficie e Impacto Home-Lab

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `<tipo>/<proyecto>/<id>` (ej. `feat/kakebo/export-csv`, `fix/cluster/oom-timeout`)  
> **Fecha**: `YYYY-MM-DD` | **Autor/Rol**: `<Nombre / Rol>`  
> **Estado**: `BORRADOR | EN REVISIÓN | APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**: Descripción precisa del problema a resolver, cuello de botella o funcionalidad requerida.
- **Objetivo Principal**: Resultado observable y medible en 1-2 líneas.
- **Alcance (`In-Scope`)**: Qué incluye explícitamente esta intervención.
- **Fuera de Alcance (`Out-of-Scope`)**: Qué queda explícitamente excluido para evitar *scope creep*.

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01`**: `<Descripción exacta de entradas, transformaciones, validaciones de negocio y salidas esperadas>`
- **`RF-02`**: `<Flujos alternativos, validación de fronteras y manejo de anomalías de dominio>`

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [ ] **`CA-01`**: Dado `<contexto inicial>`, cuando `<acción o llamada>`, entonces `<resultado observable y verificable>`.
- [ ] **`CA-02`**: Manejo de casos límite: entradas nulas, vacías, fuera de rango o caracteres malformados.
- [ ] **`CA-03`**: Cobertura de tests unitarios/integración $\ge 80\%$ sobre la nueva lógica.

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | ¿Afecta DTOs, endpoints o modelos compartidos en `home-lab-sdk`? Listar clientes (Java, Go, Python, TS). |
| **Persistencia PostgreSQL LTS** | `NO` | - | Migraciones DDL, tablas modificadas, volumen de datos o bloqueos (*locks*). |
| **Ingress Único (`cluster-lb`)** | `NO` | - | Rutas en Traefik / Apache (`*.home.lab`), certificados TLS, red interna `cluster-net`. |
| **Resolución Split-DNS** | `NO` | - | Nuevos hostnames en CoreDNS / WireGuard (`kakebo.home.lab`, `api.home.lab`). |
| **Restricciones de Hardware** | `NO` | - | Impacto en CPU/RAM en FRACTAL / NEO. Throttling de memoria configurado. |
| **Variables `.env` / Secretos** | `NO` | - | Nuevas variables de entorno requeridas en compose o secret manager. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

> **Invariante Canónico**: Queda terminantemente prohibido introducir cambios destructivos o de ruptura en contratos públicos, esquemas de bases de datos compartidas o bibliotecas SDK, salvo autorización expresa justificada.

- **¿Introduce Breaking Changes?**: `[ ] NO (100% Retrocompatible) | [ ] SÍ (Excepción Aprobada)`
- **Estrategia Aditiva (Non-Breaking)**:
  - Cómo se asegura que consumidores actuales de la API y datos persistidos continúen operando sin modificación (ej. campos opcionales con valores predeterminados, endpoints v1 coexistiendo con v2).
- **Si requiere Breaking Change (Ruta de Transición Obligatoria)**:
  - **Justificación**: ¿Por qué no es viable una solución aditiva?
  - **Estrategia de Migración Paralela**: Período de deprecación, soporte *dual-read / dual-write* y fechas de transición.

---

## 5. Compuertas SRE de Rendimiento y Persistencia Segura

### 5.1. Rendimiento y Throttling de Recursos

- **Latencia Objetivo**: p95 $< 100\text{ ms}$, p99 $< 250\text{ ms}$.
- **Complejidad Algorítmica**: Tiempo $O(\dots)$ y Espacio $O(\dots)$.
- **Límites de Memoria Home-Lab**:
  - *Go Services*: `GOMEMLIMIT=80%` del límite del contenedor (ej. 80MiB para 100MiB).
  - *JVM (Spring Boot 4)*: `-XX:MaxRAMPercentage=75.0` y liveness/readiness probes $< 3\text{ s}$.
- **Rotación de Logs en Docker**: `max-size: 10m`, `max-file: 3`.

### 5.2. Persistencia Segura en PostgreSQL LTS Compartido

- **Auditoría de Bloqueos DDL**: Prohibido ejecutar bloqueos exclusivos (`ACCESS EXCLUSIVE`) prolongados sobre tablas en producción.
- **Creación de Índices**: Obligatorio usar `CREATE INDEX CONCURRENTLY` para evitar bloqueo de lecturas/escrituras concurrentes.
- **Plan de Rollback DDL**: Disponibilidad garantizada de script `down-migration.sql` probado en entorno local.

---

## 6. Threat Modeling y Bastionado de Seguridad

| Vector de Ataque / Amenaza | Riesgo (`Bajo/Medio/Alto/N/A`) | Mitigación y Bastionado Aplicado |
| :--- | :---: | :--- |
| **Inyección (SQL, Command, Log)** | | Consultas 100% parametrizadas, APIs tipadas, validación estricta en frontera. |
| **XSS / CSRF / Path Traversal** | | Sanitización de HTML/URLs, resolución canónica de rutas (`resolve().relative_to()`). |
| **Autenticación y ReBAC/RBAC** | | Verificación de identidad y roles en capa de servicio contra `whoiam`. |
| **Exposición de Secretos / Traza** | | Credenciales vía `.env`, mensajes de error genéricos al cliente sin stack traces. |
| **Denegación de Servicio (DoS)** | | Límites de tamaño de payload, paginación obligatoria y timeouts en llamadas I/O (máx 2s-5s). |
