# Fase 1: Requisitos e Impacto Home-Lab | Validador de Rutas Ingress, Split-DNS y Portal

> **Referencia de Gobernanza**: Fase 1 del Workflow de Ingeniería ECC / Home-Lab  
> **ID de Tarea**: `feat/ecc/validate-ingress-routes`  
> **Fecha**: 2026-11-20 | **Autor/Rol**: Carbon ($C_6$) - Edge Ingress & Network Infrastructure Architect  
> **Estado**: `APROBADO`  

---

## 1. Contexto, Necesidad y Objetivos de Negocio

- **Problema de Negocio / Técnico**:
  En Home-Lab rige el Pilar 2 de Ingeniería de Google ("Single Ingress & Unified TLS"): todos los microservicios deben exponer su tráfico exclusivamente a través de la compuerta central Traefik (`cluster-lb`), sin exponer puertos crudos externamente. Cada servicio publicado bajo `*.home.lab` requiere congruencia trilateral:
  1. Configuración de etiquetas Traefik en `docker-compose.yml` (`traefik.http.routers.<router>.rule=Host(...)`).
  2. Registro Split-DNS correspondiente en CoreDNS (`Corefile` o archivos de zona).
  3. Entrada en el catálogo central de `/portal` para visibilidad y navegación unificada.
  La configuración manual suele provocar desalineaciones sutiles (ej. un subdominio Traefik sin registro en CoreDNS o ausente en el portal de servicios).
- **Objetivo Principal**:
  Desarrollar un analizador estático en Python (`validate_ingress_routes.py`) y sus wrappers CLI (`validate-ingress-routes.ps1` / `.sh`) que certifique estáticamente la coherencia entre etiquetas Traefik, registros CoreDNS y el catálogo de `/portal`, reportando discrepancias y generando sugerencias de remediación.
- **Alcance (`In-Scope`)**:
  1. Extracción de hosts y routers Traefik desde archivos `docker-compose*.yml` (buscando `traefik.http.routers.*.rule=Host(...)` y `traefik.enable=true`).
  2. Extracción de registros de hostnames desde archivos de zona CoreDNS / `Corefile`.
  3. Extracción de servicios registrados en el catálogo de `/portal` (servidor Go en `cluster/cmd/server/main.go` o JSON de catálogo).
  4. Cruce de congruencia y detección de:
     - Hosts Traefik sin registro DNS en CoreDNS.
     - Servicios publicados ausentes en el catálogo de `/portal`.
  5. Soporte de servicios aislados intencionalmente (ej. PostgreSQL, Redis, exportadores de métricas) que tengan `traefik.enable=false` o sin etiquetas Traefik.
  6. Modo `--fix` que genera las líneas sugeridas para añadir a CoreDNS y al mapa de `/portal`.
  7. Modo `--json` para integración estructurada.
  8. Omisión limpia (`SKIPPED`, código 0) si el repositorio analizado no contiene archivos compose ni CoreDNS.
  9. Wrappers CLI `scripts/bin/ecc-agy/validate-ingress-routes.ps1` y `validate-ingress-routes.sh`.
  10. Suite de pruebas en `scripts/ecc-agy/tests/test_validate_ingress_routes.py`.
- **Fuera de Alcance (`Out-of-Scope`)**:
  - Modificación destructiva automática de archivos de infraestructura en caliente.
  - Conexión dinámica a daemons Docker o servidores DNS en tiempo de ejecución.

---

## 2. Requisitos Funcionales (`RF`) y Criterios de Aceptación (`CA`)

### 2.1. Requisitos Funcionales

- **`RF-01 (Extracción de Hosts Traefik)`**:
  El validador debe parsear `docker-compose*.yml` extrayendo los hostnames declarados en `Host(`...`)`.
- **`RF-02 (Extracción de Hosts CoreDNS)`**:
  El validador debe leer el archivo `Corefile` o archivos de zona DNS extrayendo los dominios locales asignados a la red del clúster.
- **`RF-03 (Extracción de Catálogo Portal)`**:
  El validador debe inspeccionar el mapa o lista de servicios del `/portal` identificando qué URLs están catalogadas.
- **`RF-04 (Reporte de Congruencia y Sugerencias --fix)`**:
  Debe detallar cualquier discrepancia indicando qué host falta en DNS o en el catálogo, y en modo `--fix` emitir el fragmento de configuración para copiar y pegar.
- **`RF-05 (Omisión Elegante)`**:
  Si no se encuentran archivos de compose ni CoreDNS, retornar `0` con estado `SKIPPED`.

### 2.2. Criterios de Aceptación Verificables (Given / When / Then)

- [ ] **`CA-01`**: Dado un `docker-compose.yml` con `Host(`kakebo.home.lab`)`, un `Corefile` con `kakebo.home.lab`, y un portal con `kakebo.home.lab`, cuando se ejecuta `validate_ingress_routes.py`, retorna `PASS` con código 0.
- [ ] **`CA-02`**: Dado un `docker-compose.yml` con `Host(`whoiam.home.lab`)` pero ausente en CoreDNS, cuando se ejecuta el validador, retorna `FAIL` con código 1 indicando el hostname huérfano.
- [ ] **`CA-03`**: Dado un repositorio sin archivos compose ni CoreDNS, retorna código 0 con estado `SKIPPED`.
- [ ] **`CA-04`**: Cobertura de tests unitarios $\ge 80\%$ y SonarQube Rating A (0 violaciones, Cognitive Complexity $\le 15$).

---

## 3. Matriz de Impacto en Arquitectura Home-Lab

| Dimensión Arquitectónica | ¿Impactado? (`SÍ/NO`) | Nivel de Riesgo (`Bajo/Medio/Alto`) | Detalle de la Afectación y Mitigación |
| :--- | :---: | :---: | :--- |
| **Paridad `home-lab-sdk`** | `NO` | - | Sin impacto en SDKs clientes. |
| **Persistencia PostgreSQL LTS** | `NO` | - | Sin impacto en base de datos. |
| **Ingress Único (`cluster-lb`)** | `SÍ` | `Medio` | Certifica la correcta publicación de rutas en Traefik eliminando puertos crudos y rutas rotas. |
| **Resolución Split-DNS** | `SÍ` | `Medio` | Garantiza que todo servicio publicado bajo `*.home.lab` resuelva correctamente en CoreDNS. |
| **Restricciones de Hardware** | `NO` | - | Script ultraligero de análisis estático ($< 150\text{ ms}$). |
| **Variables `.env` / Secretos** | `NO` | - | No maneja secretos. |

---

## 4. Garantía Estricta de Retrocompatibilidad (Zero-Breaking Policy)

- **¿Introduce Breaking Changes?**: `[x] NO (100% Retrocompatible)`
- **Estrategia Aditiva**:
  Herramienta puramente analítica y de verificación estática preventiva.

---

## 5. Compuertas SRE de Rendimiento y Seguridad

- **Latencia Objetivo**: Tiempo de análisis estático $< 150\text{ ms}$.
- **Seguridad**: Análisis estrictamente local en solo lectura; sin ejecución de contenedores ni sockets Docker.
