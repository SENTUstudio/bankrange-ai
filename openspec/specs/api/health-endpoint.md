# API: Health Endpoint Specification

## Purpose

Eliminar el falso positivo del healthcheck actual (`GET /status` retorna HTTP 200 incluso cuando el motor de simulación no está inicializado). Se introduce un endpoint dedicado `GET /health` que verifica el estado real del motor y se actualiza el healthcheck de Docker para usarlo.

## Requirements

### Requirement: API MUST Expose a Dedicated /health Endpoint

La API de BankRange DEBE exponer un endpoint `GET /health` distinto de `GET /status`, cuyo único propósito es verificar que el motor de simulación está correctamente inicializado y listo para operar.

#### Scenario: Healthy engine returns 200

- GIVEN la API está corriendo
- AND `app.state.engine._generator` no es `None` (el motor fue inicializado exitosamente)
- WHEN se realiza una solicitud `GET /health`
- THEN la respuesta tiene HTTP status 200
- AND el cuerpo de la respuesta es `{"status": "healthy"}`
- AND el Content-Type es `application/json`

#### Scenario: Uninitialized engine returns 503

- GIVEN la API está corriendo
- AND `app.state.engine._generator` es `None` (el motor no ha sido inicializado, o la inicialización falló)
- WHEN se realiza una solicitud `GET /health`
- THEN la respuesta tiene HTTP status 503 Service Unavailable
- AND el cuerpo de la respuesta contiene un campo indicando que el motor no está listo

#### Scenario: Engine becomes uninitialized at runtime

- GIVEN el motor estaba inicializado (`_generator` no es `None`)
- WHEN ocurre un fallo catastrófico que resulta en `_generator = None` (por ejemplo, reinicio del lifespan, error fatal)
- THEN `GET /health` transiciona de 200 a 503 en la siguiente solicitud

### Requirement: Docker Healthcheck MUST Use /health

El servicio `bankrange-api` en `docker-compose.yml` DEBE usar `GET /health` en su comando de healthcheck en lugar de `GET /status`.

#### Scenario: Docker healthcheck fails when engine not initialized

- GIVEN el contenedor `bankrange-api` está iniciando
- AND el motor de simulación no ha completado su inicialización (`_generator` es `None`)
- WHEN el healthcheck de Docker ejecuta `curl -f http://localhost:8000/health`
- THEN `curl -f` recibe HTTP 503 y retorna código de salida distinto de cero
- AND Docker marca el contenedor como `unhealthy` o `starting`
- AND los servicios que dependen de `bankrange-api: service_healthy` (como `bankrange-ui`) no inician prematuramente

#### Scenario: Docker healthcheck passes when engine is healthy

- GIVEN el contenedor `bankrange-api` está corriendo
- AND el motor de simulación está correctamente inicializado
- WHEN el healthcheck de Docker ejecuta `curl -f http://localhost:8000/health`
- THEN `curl -f` recibe HTTP 200 y retorna código de salida 0
- AND Docker marca el contenedor como `healthy`

#### Scenario: Healthcheck interval and retries provide startup tolerance

- GIVEN la inicialización del motor puede tomar varios segundos (creación de topología, conexión a Kafka)
- WHEN la API está iniciando
- THEN el healthcheck de Docker con `interval: 10s`, `timeout: 5s`, `retries: 5` permite hasta ~50 segundos para que el motor se inicialice
- AND el contenedor no se marca como `unhealthy` durante el arranque normal

### Requirement: /status Endpoint MUST Be Preserved for Backward Compatibility

El endpoint `GET /status` existente DEBE preservarse sin cambios en su comportamiento actual. Su función es informativa para dashboards y no debe usarse como healthcheck operacional.

#### Scenario: /status returns 200 regardless of engine state

- GIVEN la API está corriendo
- WHEN se realiza una solicitud `GET /status`
- THEN la respuesta siempre tiene HTTP status 200
- AND el cuerpo contiene los campos `status`, `current_multiplier`, `estimated_eps`, y `total_workstations`
- AND `status` es `"running"` si `engine.deployed` es `True`, o `"stopped"` en caso contrario
- AND este comportamiento no cambia respecto a la versión actual

#### Scenario: /status is not used for Docker healthcheck

- GIVEN el `docker-compose.yml` modificado
- WHEN se revisa el bloque `healthcheck` del servicio `bankrange-api`
- THEN el comando `test` apunta a `http://localhost:8000/health` y NO a `http://localhost:8000/status`

## Acceptance Criteria

- [ ] `GET /health` implementado como nuevo endpoint en `app.py`.
- [ ] `GET /health` retorna HTTP 200 con `{"status": "healthy"}` cuando `engine._generator is not None`.
- [ ] `GET /health` retorna HTTP 503 cuando `engine._generator is None`.
- [ ] `GET /status` no sufre modificaciones en su comportamiento.
- [ ] `docker-compose.yml`: healthcheck de `bankrange-api` cambia `test` a `curl -f http://localhost:8000/health`.
- [ ] Prueba unitaria: verificar que `/health` retorna 503 con motor no inicializado.
- [ ] Prueba unitaria: verificar que `/health` retorna 200 con motor inicializado.
- [ ] Prueba unitaria: verificar que `/status` preserva su comportamiento actual.

## Related Files

- `adapters/inbound/api/app.py` — nuevo endpoint `GET /health`
- `docker-compose.yml` — healthcheck del servicio `bankrange-api`
