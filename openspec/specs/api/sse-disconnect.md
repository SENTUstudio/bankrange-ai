# API: SSE Coroutine Leak on Client Disconnect Specification

## Purpose

Prevenir el leak de corrutinas asyncio en el generador SSE (`_sse_generator()`) cuando un cliente cierra la conexión. El generador actual ejecuta un bucle `while True` sin detección de desconexión del cliente, lo que deja corrutinas huérfanas consumiendo recursos del event loop.

## Requirements

### Requirement: SSE Generator MUST Detect Client Disconnection

La función `_sse_generator()` en `adapters/inbound/api/app.py` DEBE detectar cuando el cliente HTTP cierra la conexión y DEBE terminar la corrutina limpiamente en lugar de continuar iterando indefinidamente.

#### Scenario: Client disconnects mid-stream

- GIVEN un cliente SSE está conectado a `GET /events/stream`
- AND `_sse_generator()` está enviando actualizaciones de estado del motor a 1 Hz
- WHEN el cliente cierra la conexión (TCP FIN, timeout de red, o cierre del navegador)
- THEN la operación `yield` dentro de `_sse_generator()` recibe una señal de interrupción
- AND la corrutina termina su ejecución en menos de 1 segundo
- AND no queda ninguna corrutina huérfana referenciada en el event loop de asyncio

#### Scenario: Multiple clients connect and disconnect independently

- GIVEN dos clientes SSE (`cliente A` y `cliente B`) están conectados simultáneamente a `GET /events/stream`
- AND cada uno tiene su propia instancia de corrutina `_sse_generator()`
- WHEN el cliente A cierra la conexión
- THEN la corrutina del cliente A termina limpiamente
- AND el cliente B continúa recibiendo actualizaciones de estado sin interrupción
- AND el stream del cliente B no se ve afectado por la desconexión del cliente A

#### Scenario: Normal streaming continues without interruption

- GIVEN un cliente SSE está conectado a `GET /events/stream`
- WHEN el cliente permanece conectado por al menos 30 segundos
- THEN las actualizaciones de estado del motor se envían a una frecuencia de aproximadamente 1 Hz
- AND cada 15 actualizaciones se incluye un comentario de heartbeat (`:heartbeat\n\n`)
- AND el payload de datos contiene los campos `status`, `current_multiplier`, `estimated_eps`, `total_workstations`, y `timestamp`

#### Scenario: Client reconnection after disconnect

- GIVEN un cliente SSE estaba conectado y se desconectó
- AND la corrutina anterior terminó limpiamente
- WHEN el mismo cliente (o uno nuevo) se reconecta a `GET /events/stream`
- THEN se inicia una nueva corrutina `_sse_generator()` fresca
- AND las actualizaciones comienzan a fluir inmediatamente
- AND el Streamlit dashboard reconecta sin errores visibles para el usuario

### Requirement: SSE Generator MUST Handle asyncio Cancellation Signals

La función `_sse_generator()` DEBE manejar explícitamente las excepciones `asyncio.CancelledError`, `GeneratorExit`, y `RuntimeError` que pueden surgir al hacer `yield` hacia un consumidor desconectado. No DEBE suprimir estas excepciones sin limpiar el estado.

#### Scenario: CancelledError during yield is handled

- GIVEN `_sse_generator()` está dentro del bucle `while True` y ejecuta `yield`
- WHEN FastAPI/Starlette cancela la tarea asyncio porque el cliente se desconectó
- THEN la excepción `asyncio.CancelledError` es capturada
- AND la corrutina sale del bucle sin lanzar la excepción hacia arriba
- AND no se imprime un traceback no controlado en los logs

#### Scenario: GeneratorExit during yield is handled

- GIVEN `_sse_generator()` está dentro del bucle `while True` y ejecuta `yield`
- WHEN el consumidor del generador (StreamingResponse) cierra la iteración (GeneratorExit)
- THEN la excepción es capturada y manejada
- AND la corrutina termina sin error

#### Scenario: RuntimeError from closed transport is handled

- GIVEN `_sse_generator()` intenta hacer `yield` hacia el stream HTTP
- WHEN el transporte subyacente ya fue cerrado (RuntimeError por write a socket cerrado)
- THEN la excepción `RuntimeError` es capturada
- AND la corrutina termina limpiamente
- AND se registra un log a nivel DEBUG o INFO (no WARNING ni ERROR) indicando la desconexión

#### Scenario: Exceptions are not silently swallowed without cleanup

- GIVEN una excepción de desconexión es capturada dentro de `_sse_generator()`
- WHEN la corrutina va a terminar
- THEN cualquier recurso local pendiente es liberado
- AND el log incluye un mensaje informativo de desconexión del cliente
- AND la excepción no se propaga al event loop de FastAPI

## Acceptance Criteria

- [ ] `_sse_generator()` incluye un bloque `try/except` alrededor del `yield` que captura `asyncio.CancelledError`, `GeneratorExit`, y `RuntimeError`.
- [ ] Al capturar una excepción de desconexión, la corrutina termina (`break` o `return`) y no continúa iterando.
- [ ] Prueba unitaria: simular desconexión de cliente con `asyncio.wait_for` + cancel y verificar que la corrutina termina sin error.
- [ ] Prueba unitaria: simular streaming prolongado y verificar que los heartbeats y payloads se emiten correctamente.
- [ ] Prueba de integración: dos clientes concurrentes, desconectar uno y verificar que el otro sigue recibiendo.
- [ ] Dashboard Streamlit: reconectar sin errores tras desconexión de red.

## Related Files

- `adapters/inbound/api/app.py` — función `_sse_generator()` y endpoint `GET /events/stream`
- `tests/unit/adapters/inbound/api/test_app.py` — pruebas unitarias de SSE
