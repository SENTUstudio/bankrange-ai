# Infra: Loki Healthcheck & Vector Sink Reliability Specification

## Purpose

Garantizar que los servicios Vector no pierdan eventos cuando Loki arranca lentamente o crashea, mediante una cadena de tres sub-fixes aplicados en orden obligatorio A → B → C.

## Requirements

### Requirement: Loki Container Healthcheck

El contenedor Loki en `docker-compose.yml` DEBE incluir un `healthcheck` basado en su endpoint nativo `/ready`, que verifica que Loki está completamente operativo antes de aceptar tráfico.

#### Scenario: Loki healthcheck reports healthy when ready

- GIVEN el contenedor Loki está iniciando tras un `docker compose up`
- WHEN el endpoint `/ready` de Loki responde HTTP 200
- THEN el healthcheck de Docker marca el contenedor como `healthy`
- AND los servicios dependientes pueden comenzar a publicar eventos

#### Scenario: Loki healthcheck reports unhealthy during startup

- GIVEN el contenedor Loki está iniciando pero el motor de almacenamiento aún no está listo
- WHEN el endpoint `/ready` de Loki no responde o devuelve un código distinto a 200
- THEN el healthcheck de Docker marca el contenedor como `unhealthy` o `starting`
- AND los servicios con `depends_on: service_healthy` esperan antes de iniciar

#### Scenario: Loki healthcheck detects crash

- GIVEN Loki está corriendo y en estado `healthy`
- WHEN Loki crashea o deja de responder en `/ready`
- THEN el healthcheck de Docker transiciona el estado a `unhealthy` tras el número configurado de reintentos
- AND los servicios dependientes pueden ser reiniciados por el orchestrator

### Requirement: Vector depends_on Loki service_healthy

Los tres servicios Vector (`vector-windows`, `vector-linux`, `vector-macos`) en `docker-compose.yml` DEBEN declarar `depends_on: loki: condition: service_healthy` en lugar de `condition: service_started`.

#### Scenario: Vector waits for Loki healthy before starting

- GIVEN se ejecuta `docker compose up`
- WHEN Loki aún no ha pasado su healthcheck (`/ready` no responde 200)
- THEN los tres servicios Vector (`vector-windows`, `vector-linux`, `vector-macos`) permanecen en estado `waiting`
- AND no intentan conectarse al endpoint de Loki

#### Scenario: Vector starts once Loki is healthy

- GIVEN se ejecuta `docker compose up`
- WHEN Loki pasa su healthcheck y Docker lo marca como `healthy`
- THEN los tres servicios Vector inician inmediatamente
- AND el sink Loki de cada Vector se conecta exitosamente al endpoint `http://loki:3100`

#### Scenario: Existing Kafka dependencies are preserved

- GIVEN los servicios Vector en `docker-compose.yml`
- WHEN se modifica la condición de dependencia para Loki
- THEN las dependencias existentes hacia `kafka` (`service_healthy`) y `kafka-init` (`service_completed_successfully`) no son alteradas
- AND los tres servicios Vector dependen correctamente de Kafka, kafka-init, y Loki

### Requirement: Vector Sink Healthcheck Enabled

Los tres archivos de configuración de Vector (`config/vector/windows.yaml`, `config/vector/linux.yaml`, `config/vector/macos.yaml`) DEBEN tener `healthcheck.enabled: true` en el bloque `sinks.out_loki`.

#### Scenario: Vector sink healthcheck validates Loki connectivity

- GIVEN Vector está corriendo con `healthcheck.enabled: true` en el sink Loki
- WHEN el sink Loki intenta publicar eventos
- THEN Vector verifica activamente la disponibilidad del endpoint `http://loki:3100`
- AND reporta el estado del sink como healthy o unhealthy en sus métricas internas

#### Scenario: Vector sink healthcheck detects Loki failure

- GIVEN Vector está publicando eventos a Loki con `healthcheck.enabled: true`
- WHEN Loki se vuelve inaccesible (crash, red, timeout)
- THEN el healthcheck del sink detecta la caída
- AND el sink entra en estado `unhealthy`
- AND Vector aplica la política de reintentos y buffering en lugar de descartar eventos silenciosamente

#### Scenario: No false 503 errors at startup with correct fix order

- GIVEN los tres sub-fixes se aplican en el orden obligatorio (A: Loki healthcheck, B: depends_on service_healthy, C: sink healthcheck enabled)
- WHEN se ejecuta `docker compose up` desde cero
- THEN Loki pasa su healthcheck antes de que Vector intente iniciar
- AND Vector inicia solo después de que Loki está healthy
- AND el sink healthcheck de Vector se habilita cuando Loki ya está respondiendo
- AND no aparecen errores 503 en los logs de Vector causados por intentos de conexión a un Loki no disponible

### Requirement: Mandatory Fix Order A → B → C

Los tres sub-fixes DEBEN aplicarse en el orden A → B → C. Invertir el orden o aplicar C sin A y B genera ruido 503 que anula el propósito de la corrección.

#### Scenario: Fix C alone without A and B causes 503 noise

- GIVEN solo se habilita `healthcheck.enabled: true` en los sinks Vector (fix C)
- AND Loki no tiene healthcheck propio (fix A ausente)
- AND Vector usa `service_started` para Loki (fix B ausente)
- WHEN se ejecuta `docker compose up`
- THEN Vector intenta conectarse a Loki antes de que esté listo
- THEN el sink healthcheck reporta el endpoint como `unhealthy`
- AND los logs de Vector muestran errores 503
- AND puede ocurrir pérdida de eventos durante la ventana de startup

#### Scenario: Fixes A and B without C reduces observability

- GIVEN Loki tiene healthcheck (fix A) y Vector usa `service_healthy` (fix B)
- AND los sinks Vector tienen `healthcheck.enabled: false`
- WHEN Loki crashea en tiempo de ejecución (no durante startup)
- THEN Vector no detecta la caída mediante healthcheck del sink
- AND los eventos pueden perderse sin alerta hasta que el orchestrator externo detecte el problema

## Acceptance Criteria

- [ ] `docker-compose.yml`: El servicio `loki` tiene un bloque `healthcheck` con `test` apuntando a `http://localhost:3100/ready`.
- [ ] `docker-compose.yml`: Los tres servicios `vector-windows`, `vector-linux`, `vector-macos` declaran `loki: condition: service_healthy`.
- [ ] `config/vector/windows.yaml`: `sinks.out_loki.healthcheck.enabled` es `true`.
- [ ] `config/vector/linux.yaml`: `sinks.out_loki.healthcheck.enabled` es `true`.
- [ ] `config/vector/macos.yaml`: `sinks.out_loki.healthcheck.enabled` es `true`.
- [ ] `docker compose up` arranca todos los servicios sin errores 503 en los logs de Vector.
- [ ] El orden de los commits o cambios respeta A → B → C dentro del PR.

## Related Files

- `docker-compose.yml` — Loki healthcheck, Vector depends_on
- `config/vector/windows.yaml` — Loki sink healthcheck
- `config/vector/linux.yaml` — Loki sink healthcheck
- `config/vector/macos.yaml` — Loki sink healthcheck
