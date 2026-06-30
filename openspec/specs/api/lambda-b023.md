# API: Lambda B023 — Loop Variable Capture by Reference Specification

## Purpose

Resolver la advertencia de análisis estático flake8-bugbear B023 que reporta una función lambda capturando una variable de bucle por referencia en `adapters/inbound/api/app.py` o en los paths de llamada asociados (`core/use_cases/event_generator.py`). La captura por referencia en lambdas dentro de bucles causa que todas las instancias de la lambda compartan el último valor de la variable de bucle, lo que constituye un comportamiento no determinista y potencialmente incorrecto.

## Requirements

### Requirement: No Lambda SHALL Capture a Loop Variable by Reference

Ninguna función lambda en el codebase de BankRange DEBE capturar una variable de iteración de bucle (`for x in iterable`) por referencia. Toda lambda definida dentro de un bucle que necesite capturar la variable de iteración DEBE hacerlo mediante el patrón de default argument binding (`lambda x=x: ...`).

#### Scenario: B023 warning is absent after fix

- GIVEN el codebase del proyecto tras aplicar el fix del bug #10
- WHEN se ejecuta `flake8 --select=B023` (o equivalente con bugbear) sobre los archivos `app.py` y `event_generator.py`
- THEN no se reportan advertencias B023
- AND el código pasa el análisis estático limpiamente

#### Scenario: Lambda with default argument binding is safe

- GIVEN una lambda necesita capturar una variable de iteración de un bucle `for`
- WHEN la lambda se define con default argument binding: `lambda captured=x: process(captured)`
- THEN la captura es por valor (el valor de `x` en el momento de la definición)
- AND cada lambda preserva el valor correcto de la variable para su iteración correspondiente
- AND flake8-bugbear B023 no emite advertencia para este patrón

#### Scenario: Lambda outside a loop does not trigger B023

- GIVEN una lambda se define dentro de una función o método, pero no dentro de un bucle `for` o `while`
- WHEN la lambda captura variables del ámbito enclosing (closure)
- THEN no se genera advertencia B023
- AND este es el caso de las lambdas en `_metadata_value_for()` de `event_generator.py`, que capturan `self` (no una variable de bucle)

#### Scenario: Investigation confirms no vulnerable lambda exists

- GIVEN el análisis estático original reportó B023 en `app.py`
- AND la inspección manual del código actual no encuentra ninguna lambda dentro de un bucle en `app.py` ni en `event_generator.py`
- WHEN se completa la investigación del bug #10
- THEN el resultado se documenta como "verificado: no existe lambda vulnerable en el código actual"
- AND el ticket se cierra con las notas de verificación
- AND no se realizan cambios de código innecesarios

### Requirement: Investigation MUST Cover All Lambda Usages in Affected Files

La investigación del bug #10 DEBE examinar todas las definiciones de lambda en `adapters/inbound/api/app.py` y `core/use_cases/event_generator.py`, así como cualquier generador o comprensión que pueda producir una lambda dentro de un contexto de bucle.

#### Scenario: All lambdas in event_generator.py are analyzed

- GIVEN `event_generator.py` contiene lambdas en el diccionario `generators` del método `_metadata_value_for()`
- WHEN se analiza el contexto de definición de estas lambdas
- THEN se verifica que el diccionario `generators` se define una sola vez por llamada (no dentro de un bucle)
- AND las lambdas capturan `self._rng` por closure legítimo (no por variable de bucle)
- AND el bucle `for key in template.metadata_keys:` en `_generate_metadata()` solo realiza lookups del diccionario, sin definir lambdas nuevas

#### Scenario: app.py is verified lambda-free

- GIVEN `app.py` es el archivo señalado en el reporte original de B023
- WHEN se inspecciona el archivo completo
- THEN se confirma que no existe ninguna definición de lambda (el archivo no contiene la palabra clave `lambda`)
- AND las funciones `_run_engine_loop`, `_sse_generator`, y las rutas de FastAPI no crean closures dentro de bucles

#### Scenario: Static analysis tooling is verified

- GIVEN el proyecto no tiene flake8 configurado como herramienta de linting en `openspec/config.yaml`
- WHEN se investiga el origen del reporte B023
- THEN se documenta qué herramienta exacta generó la advertencia
- AND si la herramienta ya no está disponible o el código cambió desde el reporte original, se registra esa conclusión

## Acceptance Criteria

- [ ] Investigación completada: todas las lambdas en `app.py` y `event_generator.py` han sido analizadas para determinar si capturan variables de bucle.
- [ ] Si existe una lambda vulnerable: se corrige con default argument binding o refactorización.
- [ ] Si no existe lambda vulnerable: se documenta el resultado de la verificación en el ticket y no se modifica el código.
- [ ] El análisis estático (flake8-bugbear B023) no reporta advertencias en los archivos afectados tras el cierre del bug.
- [ ] Prueba unitaria (si se modifica código): la lambda con default argument binding produce los valores esperados para cada iteración del bucle.

## Related Files

- `adapters/inbound/api/app.py` — archivo señalado en el reporte original B023
- `core/use_cases/event_generator.py` — contiene lambdas en `_metadata_value_for()` que deben ser verificadas
