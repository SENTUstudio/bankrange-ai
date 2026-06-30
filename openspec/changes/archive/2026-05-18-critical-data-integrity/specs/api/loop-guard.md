# API: Engine Loop Guard Specification

## Purpose

Garantizar que la función `_run_engine_loop()` en `adapters/inbound/api/app.py` no ejecute ninguna lógica de simulación cuando el motor no está desplegado (`engine_state.deployed = False`). El loop debe verificar el estado `deployed` antes de cualquier operación costosa o con efectos secundarios.

## Requirements

### Requirement: Loop MUST Skip All Simulation Logic When deployed Is False

La función `_run_engine_loop()` DEBE evaluar `engine_state.deployed` como la primera operación dentro del cuerpo del bucle `while engine_state.is_running`. Cuando `deployed` es `False`, el loop NO DEBE ejecutar ninguna llamada a métodos del generador o del publicador.

#### Scenario: Loop idle when not deployed

- GIVEN el engine loop está corriendo (`engine_state.is_running` es `True`)
- AND `engine_state.deployed` es `False` (el motor no ha sido activado vía `/control`)
- WHEN el loop completa una iteración
- THEN no se realizó ninguna llamada a `generator.generate_tick()`
- AND no se realizó ninguna llamada a `generator.set_scale_multiplier()`
- AND no se realizó ninguna llamada a `BANK_WORKDAY_PROFILE.get_multiplier()`
- AND no se realizó ninguna llamada a `generator.estimated_eps()`
- AND el loop únicamente ejecuta `await asyncio.sleep(1)` antes de la siguiente iteración

#### Scenario: Loop active when deployed

- GIVEN el engine loop está corriendo
- AND `engine_state.deployed` es `True`
- WHEN el loop completa una iteración
- THEN `generator.set_scale_multiplier()` fue llamada con el multiplicador efectivo
- AND `generator.generate_tick()` fue llamada exactamente una vez con el timestamp de simulación
- AND `generator.estimated_eps()` fue llamada para actualizar la métrica EMA
- AND la pausa entre iteraciones (`asyncio.sleep`) respeta el pacing de tiempo real

#### Scenario: Loop transitions from idle to active on /control deployment

- GIVEN el engine loop está corriendo en estado idle (`deployed = False`)
- WHEN un cliente invoca `POST /control` con `eps_multiplier > 0`
- THEN `engine_state.deployed` cambia a `True` en la siguiente evaluación
- AND la siguiente iteración del loop ejecuta la lógica completa de simulación
- AND el comportamiento de simulación es idéntico al de un loop que inició con `deployed = True`

#### Scenario: Loop transitions from active to idle on /control stop

- GIVEN el engine loop está corriendo en estado activo (`deployed = True`)
- WHEN un cliente invoca `POST /control` con `eps_multiplier = 0`
- THEN `engine_state.deployed` cambia a `False` en la siguiente evaluación
- AND la siguiente iteración del loop omite toda la lógica de simulación
- AND solo ejecuta `await asyncio.sleep(1)`

#### Scenario: Loop does not call generate_tick before deployed check

- GIVEN el engine loop está en ejecución
- WHEN `engine_state.deployed` es `False`
- THEN el bucle no evalúa ninguna expresión que dependa de `generator` o `publisher` antes de verificar `deployed`
- AND `BANK_WORKDAY_PROFILE.get_multiplier()` no es invocada innecesariamente
- AND `datetime.now(UTC)` no es invocado innecesariamente cuando `deployed = False`

### Requirement: Guard MUST Be Positioned at Top of Loop Body

La verificación `if engine_state.deployed:` DEBE ser la primera instrucción dentro del `while engine_state.is_running:` (después de las asignaciones de variables locales del loop). Ninguna lógica de simulación, cálculo de tiempo, o llamada a `get_multiplier` DEBE ejecutarse antes de esta verificación.

#### Scenario: Early return pattern is the first check

- GIVEN el código fuente de `_run_engine_loop()`
- WHEN se inspecciona el cuerpo del `while engine_state.is_running:`
- THEN la primera operación sustantiva es `if engine_state.deployed:` (o su equivalente negativo como guard clause)
- AND no existe código de simulación fuera del bloque `if engine_state.deployed:`
- AND el bloque `else` (o la ruta de `not deployed`) contiene únicamente `await asyncio.sleep(1)`

#### Scenario: Loop respects is_running even when idle

- GIVEN el engine loop está en estado idle (`deployed = False`)
- AND `engine_state.is_running` es `True`
- WHEN se establece `engine_state.is_running = False` (por ejemplo, durante el shutdown de la aplicación)
- THEN el loop sale del `while engine_state.is_running:` en la siguiente evaluación
- AND ejecuta el bloque `finally` (flush del publisher)

## Acceptance Criteria

- [ ] `_run_engine_loop()` evalúa `engine_state.deployed` como primera operación dentro del bucle.
- [ ] Ninguna llamada a `generate_tick`, `set_scale_multiplier`, `get_multiplier`, `estimated_eps`, o `_compute_ema_eps` ocurre cuando `deployed = False`.
- [ ] Cuando `deployed = False`, la única operación realizada es `await asyncio.sleep(1)`.
- [ ] Prueba unitaria: mock de `generator` verifica cero llamadas a `generate_tick` cuando `deployed = False`.
- [ ] Prueba unitaria: mock de `generator` verifica que `generate_tick` es llamada cuando `deployed = True`.
- [ ] Prueba unitaria: verificar transición idle → active vía cambio de `engine_state.deployed`.

## Related Files

- `adapters/inbound/api/app.py` — función `_run_engine_loop()`
