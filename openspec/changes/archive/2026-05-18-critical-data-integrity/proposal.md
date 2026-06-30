# Proposal: Critical Data Integrity Fixes

**Change ID:** `critical-data-integrity`

**Date:** 2026-05-18

**Status:** Draft

---

## Intent

Reparar cinco bugs críticos y de alta severidad identificados durante la revisión integral de salud del proyecto (auditoría estática + arquitectónica). Cuatro de los cinco bugs residen en `adapters/inbound/api/app.py`, el archivo central de la API de comando y control. El quinto afecta la capa de infraestructura de observabilidad (Vector + Loki en Docker Compose), donde la pérdida de eventos puede pasar desapercibida debido a healthchecks falsos positivos y dependencias de inicio de contenedores mal configuradas.

**Motivación (por qué ahora):** La pérdida de logs de Vector hacia Loki representa un agujero silencioso de observabilidad. El leak de corrutinas SSE degrada recursos en producción. El healthcheck falso positivo de la API oculta que el motor de simulación nunca arrancó. Estos bugs comprometen la integridad de datos y la confiabilidad operativa del pipeline BankRange. La cohesión del archivo `api/app.py` (4 de 5 bugs) justifica agruparlos en un solo cambio para evitar conflictos de merge y permitir pruebas integradas.

---

## Scope

### In Scope

| #   | Bug                                                             | Severidad    | Archivos                                                                                                   |
| --- | --------------------------------------------------------------- | ------------ | ---------------------------------------------------------------------------------------------------------- |
| 25  | Vector pierde eventos si Loki arranca lento o crashea           | **CRITICAL** | `docker-compose.yml`, `config/vector/windows.yaml`, `config/vector/linux.yaml`, `config/vector/macos.yaml` |
| 26  | Leak de corrutina SSE al desconectar cliente                    | **HIGH**     | `adapters/inbound/api/app.py`                                                                              |
| 27  | Healthcheck falso positivo cuando el motor no está inicializado | **HIGH**     | `adapters/inbound/api/app.py`, `docker-compose.yml`                                                        |
| 28  | Loop llama `generate_tick` incluso con `deployed=False`         | **MEDIUM**   | `adapters/inbound/api/app.py`                                                                              |
| 10  | B023: lambda captura `effective_multi` por referencia           | **MEDIUM**   | `adapters/inbound/api/app.py`                                                                              |

### Out of Scope

- Refactorización profunda del motor de simulación (`core/use_cases/event_generator.py`).
- Migración de dashboards de Grafana.
- Cambios en la topología de red interna de Docker.
- Implementación de métricas de observabilidad adicionales (más allá del healthcheck).
- Corrección de los 5 bugs ya resueltos en el codebase (confirmados durante la fase de exploración).

---

## Affected Modules / Packages

| Módulo                              | Tipo de impacto   | Descripción                                                                                                                            |
| ----------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `adapters/inbound/api/app.py`       | **Modificado**    | 4 bugs corregidos: SSE leak, healthcheck falso positivo, loop CPU, B023 lambda. Cambio de mayor superficie.                            |
| `docker-compose.yml`                | **Modificado**    | Loki healthcheck añadido, Vector `depends_on` cambiado a `service_healthy`, healthcheck de API cambiado a `/health`.                   |
| `config/vector/windows.yaml`        | **Modificado**    | Sink Loki: `healthcheck.enabled` de `false` → `true`.                                                                                  |
| `config/vector/linux.yaml`          | **Modificado**    | Sink Loki: `healthcheck.enabled` de `false` → `true`.                                                                                  |
| `config/vector/macos.yaml`          | **Modificado**    | Sink Loki: `healthcheck.enabled` de `false` → `true`.                                                                                  |
| `core/use_cases/event_generator.py` | **No modificado** | El bug B023 puede requerir cambios menores si la lambda reside aquí en lugar de `app.py`. Se investigará en la fase de implementación. |

---

## Risk Assessment

| Riesgo                                                                           | Probabilidad | Impacto | Mitigación                                                                                                                                                                                                                                                                                                                                     |
| -------------------------------------------------------------------------------- | ------------ | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Re-habilitar `healthcheck.enabled` en Vector Loki sink reintroduce ruido 503** | Media        | Medio   | El fix #25 es atómico: solo se habilita el healthcheck DESPUÉS de (A) añadir healthcheck a Loki y (B) cambiar `depends_on` a `service_healthy`. Esto garantiza que Loki esté realmente listo antes de que Vector intente publicar. Si aún hay falsos positivos 503, se documentará como deuda técnica y se revertirá solo el sink healthcheck. |
| **Nuevo endpoint `/health` rompe healthcheck de Docker existente**               | Baja         | Alto    | Se actualiza simultáneamente el `healthcheck.test` en `docker-compose.yml` para apuntar a `/health` en lugar de `/status`. El viejo `/status` se preserva sin cambios para compatibilidad con consumidores externos.                                                                                                                           |
| **Cambios en SSE (`_sse_generator`) rompen el stream en navegadores**            | Baja         | Alto    | El fix (try/except para `CancelledError`/`GeneratorExit`) es un patrón estándar de asyncio. Se probará con `curl` y con el dashboard Streamlit.                                                                                                                                                                                                |
| **Conflicto de merge en `app.py` (4 fixes en 1 archivo)**                        | Media        | Bajo    | Todos los fixes son en este cambio, no hay riesgo de conflicto externo. Internamente son ortogonales (tocan funciones distintas).                                                                                                                                                                                                              |
| **B023: el código actual no contiene una lambda visible en `app.py`**            | Media        | Bajo    | El bug fue reportado por análisis estático (flake8-bugbear). La lambda puede estar en `event_generator.py` o en un path de llamada indirecto. Se investigará durante la fase de spec/design. Si la lambda ya no existe, el fix se reduce a verificación y documentación.                                                                       |

---

## Rollback Plan

Cada fix es independiente y reversible:

1. **#25 (Vector ↔ Loki):** Revertir `docker-compose.yml` y los tres archivos `config/vector/*.yaml` desde Git. Volver a `healthcheck.enabled: false` en los sinks de Vector y `depends_on: service_started` para Loki.

2. **#26 (SSE leak):** Revertir `_sse_generator()` al estado actual (sin bloque try/except). El impacto del leak es gradual; la reversión no causa pérdida inmediata de funcionalidad.

3. **#27 (Healthcheck):** Revertir endpoint `/health` y restaurar healthcheck de Docker a `curl -f http://localhost:8000/status`. El endpoint `/health` puede dejarse en su lugar (no causa daño) si se prefiere.

4. **#28 (Loop CPU):** Revertir el movimiento del guard `deployed` al tope del loop. El comportamiento actual (guard dentro del `if`) es correcto pero subóptimo; la reversión no rompe nada.

5. **#10 (B023):** Revertir el cambio de lambda. Si se introdujo un default argument binding, revertir a la versión original.

**Estrategia de rollback atómico (recomendada):** Revertir el commit completo del cambio `critical-data-integrity`. Todos los fixes fueron diseñados para ser desplegados juntos; revertirlos juntos es seguro.

---

## Dependencies Between Fixes

### Cadena atómica interna de #25

```
┌─────────────────────────────────────────────────────────┐
│ A: Añadir healthcheck a Loki (docker-compose.yml)       │
│         ↓                                               │
│ B: Cambiar Vector depends_on loki: service_started      │
│    → service_healthy (docker-compose.yml)               │
│         ↓                                               │
│ C: Habilitar Vector sink healthcheck.enabled: true      │
│    (windows.yaml, linux.yaml, macos.yaml)               │
└─────────────────────────────────────────────────────────┘
```

**El orden A → B → C es obligatorio.** Si se habilita C sin A y B, el sink reintentará publicar a un Loki no disponible, generando ruido 503 exactamente como lo que el commit `0fd397e` intentó suprimir.

### Dependencias cruzadas

- **#27 depende de #25 parcialmente:** El nuevo endpoint `/health` usa `curl` como cliente HTTP (ya instalado en `Dockerfile.api`). El cambio en `docker-compose.yml` para #27 (apuntar healthcheck a `/health`) es una sola línea que puede coexistir con los cambios de #25 en el mismo archivo.
- **#26, #28 y #10 son independientes entre sí y de #25/#27.** Solo comparten archivo (`app.py`). La implementación debe respetar el orden de las funciones dentro del archivo para evitar conflictos de edición.

---

## Estimated Changed Lines

| Archivo                       | Fix(es)                                                   | Líneas estimadas |
| ----------------------------- | --------------------------------------------------------- | ---------------- |
| `docker-compose.yml`          | #25 (Loki healthcheck, depends_on), #27 (API healthcheck) | ~20              |
| `config/vector/windows.yaml`  | #25 (sink healthcheck)                                    | ~2               |
| `config/vector/linux.yaml`    | #25 (sink healthcheck)                                    | ~2               |
| `config/vector/macos.yaml`    | #25 (sink healthcheck)                                    | ~2               |
| `adapters/inbound/api/app.py` | #26 (SSE), #27 (/health), #28 (loop), #10 (B023)          | ~30              |
| **Total**                     |                                                           | **~56 líneas**   |

El cambio está por debajo del presupuesto de revisión de 400 líneas.

---

## Success Criteria

- [ ] **#25:** Loki tiene healthcheck funcional (`/ready` endpoint). Vector services usan `depends_on: loki: service_healthy`. Vector sinks tienen `healthcheck.enabled: true`. `docker compose up` arranca todos los servicios sin errores 503 en los logs de Vector.
- [ ] **#26:** `_sse_generator()` maneja `CancelledError`, `GeneratorExit`, y `RuntimeError` limpiamente. Cliente que cierra conexión no deja corrutina huérfana. Streamlit dashboard reconecta sin errores.
- [ ] **#27:** `GET /health` retorna HTTP 503 cuando `engine._generator is None`. `GET /health` retorna HTTP 200 con `{"status": "healthy"}` cuando el motor está inicializado. Docker healthcheck usa `/health` y falla correctamente si el motor no arrancó.
- [ ] **#28:** Cuando `deployed=False`, el loop no ejecuta ninguna lógica de simulación (cero llamadas a `generate_tick`, `set_scale_multiplier`, `get_multiplier`). Solo duerme 1 segundo.
- [ ] **#10:** El análisis estático (flake8-bugbear B023) no reporta lambda capturando variable de loop por referencia en `app.py` ni en los paths de llamada asociados.
- [ ] **Test suite:** `uv run pytest tests/ -v` pasa con cobertura ≥ 80%.
- [ ] **Strict TDD:** Cada fix tiene tests escritos antes de la implementación (verificado en fase `sdd-verify`).
