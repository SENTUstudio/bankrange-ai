# Tasks: Critical Data Integrity Fixes

**Change ID:** `critical-data-integrity`
**Date:** 2026-05-18

---

## Review Workload Forecast

| Field                   | Value                                                       |
| ----------------------- | ----------------------------------------------------------- |
| Estimated changed lines | ~120 total (25 tests + 56 implementation + ~40 docs/verify) |
| 400-line budget risk    | Low                                                         |
| Chained PRs recommended | No                                                          |
| Suggested split         | Single PR                                                   |
| Delivery strategy       | single-pr                                                   |
| Chain strategy          | pending                                                     |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

---

## Dependency Graph

```
┌───────────────────────────────────────────────────────────────┐
│  PHASE 1: INFRASTRUCTURE (#25)                                │
│                                                               │
│  1.1 (tests) ──► 1.2 (A: Loki healthcheck)                   │
│                       ──► 1.3 (B: Vector depends_on)          │
│                               ──► 1.4 (C: Sink healthcheck)   │
│                                                               │
│  PHASE 2: IMPLEMENTATION (API fixes)                          │
│                                                               │
│  2.1 (SSE tests RED) ──► 2.2 (SSE fix GREEN)                 │
│  2.3 (health tests RED) ──► 2.4 (/health endpoint GREEN)     │
│                                  ──► 2.5 (docker healthcheck) │
│                                                               │
│  PHASE 3: TESTING & VERIFICATION                              │
│                                                               │
│  3.1 (full suite) ──► 3.2 (#28 verify)                       │
│                    ──► 3.3 (#10 verify)                       │
│                    ──► 3.4 (docker smoke test)                │
└───────────────────────────────────────────────────────────────┘
```

**Phase 1 is independent of Phase 2.** Phase 1 tasks within #25 follow the **mandatory order A → B → C** (see ADR-3 in design.md). Phase 2 tasks follow strict TDD: test RED first, then implementation GREEN. Phase 3 is the final verification gate.

Within Phase 2, #26 (SSE) and #27 (health) are **independent** of each other (different functions in `app.py`, non-overlapping zones). They can be parallelized but share the same test file.

---

## Phase 1: Infrastructure (#25 — Vector/Loki Reliability)

### Task 1.1: Write config validation tests for Loki & Vector (#25)

**Files:** `tests/integration/test_vector_configs.py`

**What to do:**
Add test methods to `TestVectorConfigs` class that validate:

1. `docker-compose.yml` — Loki has a `healthcheck` block with `test` pointing to `/ready`
2. `docker-compose.yml` — All three Vector services (`vector-windows`, `vector-linux`, `vector-macos`) declare `loki: condition: service_healthy` (not `service_started`)
3. `config/vector/windows.yaml` — `sinks.out_loki.healthcheck.enabled` is `true`
4. `config/vector/linux.yaml` — `sinks.out_loki.healthcheck.enabled` is `true`
5. `config/vector/macos.yaml` — `sinks.out_loki.healthcheck.enabled` is `true`

**TDD phase:** RED — these tests will fail against current state (no Loki healthcheck, `service_started`, `enabled: false`).

**Acceptance criteria:**

- 5 new test methods added, all failing against current configs
- Tests use `yaml.safe_load()` for Vector configs and `yaml.safe_load()` for docker-compose.yml
- Tests validate both docker-compose and vector YAML structure
- Run with: `uv run pytest tests/integration/test_vector_configs.py -v`

**Estimated lines:** ~40 new in test file

---

### Task 1.2: Add Loki healthcheck to docker-compose.yml (Step A of #25)

**Files:** `docker-compose.yml` (lines ~167-173, `loki` service)

**Prerequisite:** Task 1.1 completed (tests fail)

**What to do:**
Add a `healthcheck` block to the `loki` service:

```yaml
healthcheck:
  test: ["CMD", "wget", "--spider", "-q", "http://localhost:3100/ready"]
  interval: 5s
  timeout: 5s
  retries: 5
```

**Why `wget` not `curl`:** `grafana/loki:3.0.0` image includes `wget` (busybox) but not `curl`.

**TDD phase:** GREEN for Loki healthcheck presence test (1.1).

**Acceptance criteria:**

- `docker-compose.yml` — `loki` service has `healthcheck` block with `test` targeting `/ready`
- `docker compose up loki` → `docker ps` shows Loki transitioning from `starting` to `healthy`
- 1.1 test for Loki healthcheck passes

**Estimated lines:** +5 in docker-compose.yml

---

### Task 1.3: Change Vector depends_on loki to service_healthy (Step B of #25)

**Files:** `docker-compose.yml` (lines ~130-165, three Vector services)

**Prerequisite:** Task 1.2 completed (Loki has healthcheck)

**What to do:**
In all three Vector services (`vector-windows`, `vector-linux`, `vector-macos`), change:

```yaml
# Before:
loki:
  condition: service_started

# After:
loki:
  condition: service_healthy
```

**Important:** Do NOT modify the existing Kafka and kafka-init dependencies.

**TDD phase:** GREEN for Vector depends_on test (1.1).

**Acceptance criteria:**

- All three Vector services declare `loki: condition: service_healthy`
- Existing `kafka: condition: service_healthy` and `kafka-init: condition: service_completed_successfully` are preserved
- `docker compose up vector-windows` → Vector waits for Loki `healthy` before starting
- 1.1 test for depends_on passes

**Estimated lines:** +3 in docker-compose.yml (one per Vector service × changing 1 keyword)

---

### Task 1.4: Enable Vector sink healthcheck in config files (Step C of #25)

**Files:**

- `config/vector/windows.yaml` (line ~68, `sinks.out_loki.healthcheck.enabled`)
- `config/vector/linux.yaml` (line ~44, `sinks.out_loki.healthcheck.enabled`)
- `config/vector/macos.yaml` (line ~52, `sinks.out_loki.healthcheck.enabled`)

**Prerequisite:** Task 1.3 completed (Vector waits for healthy Loki)

**What to do:**
In all three Vector config files, change:

```yaml
# Before:
  healthcheck:
    enabled: false

# After:
  healthcheck:
    enabled: true
```

**TDD phase:** GREEN for sink healthcheck tests (1.1).

**Acceptance criteria:**

- All three configs have `enabled: true` under `sinks.out_loki.healthcheck`
- `docker compose up` (full stack) → zero 503 errors in Vector logs
- 1.1 tests for sink healthcheck pass
- All Integration tests pass: `uv run pytest tests/integration/test_vector_configs.py -v`

**Estimated lines:** +3 total (one per file × changing 1 value)

---

## Phase 2: Implementation (#26, #27 — API Fixes)

### Task 2.1: Write SSE disconnect tests (RED for #26)

**Files:** `tests/unit/adapters/inbound/api/test_app.py`

**Prerequisite:** None (can run in parallel with Phase 1)

**What to do:**
Add test methods to `TestSseGenerator` class (after line ~318):

1. **`test_sse_generator_handles_cancelled_error`** — Set up `_sse_generator()`, run in a task, cancel it via `task.cancel()`, verify no unhandled exception propagates and the coroutine terminates.

2. **`test_sse_generator_handles_generator_exit`** — Close generator via `await gen.aclose()`, verify it terminates without error.

3. **`test_sse_generator_continues_after_heartbeat`** — Iterate 30+ cycles, verify heartbeats appear every 15 iterations and data chunks continue flowing (regression: ensure the try/except doesn't break normal streaming).

4. **`test_sse_streaming_response_disconnects_cleanly`** — Use `TestClient` with `GET /events/stream`, close connection mid-stream, verify no log errors at WARNING/ERROR level.

**Test patterns to follow:** Existing tests use `asyncio.run()` with inner async functions, `MagicMock` for mocks, and `app_module.app.state.engine = EngineState(...)` for state injection. See `test_sse_generator_yields_running_when_deployed` (line 255) for SSE test patterns.

**TDD phase:** RED — these tests will fail because `_sse_generator()` has no try/except.

**Acceptance criteria:**

- 4 new test methods in `TestSseGenerator`
- All 4 tests FAIL when run: `uv run pytest tests/unit/adapters/inbound/api/test_app.py::TestSseGenerator -v`
- Failures are due to unhandled exceptions (not assertion errors)

**Estimated lines:** ~45 new in test file

---

### Task 2.2: Implement SSE try/except in \_sse_generator() (GREEN for #26)

**Files:** `adapters/inbound/api/app.py` (lines ~312-329, function `_sse_generator()`)

**Prerequisite:** Task 2.1 completed (tests fail)

**What to do:**
Wrap the `while True:` loop body in a try/except block that captures `asyncio.CancelledError`, `GeneratorExit`, and `RuntimeError`:

```python
async def _sse_generator():
    engine = app.state.engine
    heartbeat_counter = 0
    while True:
        try:
            payload = { ... }  # existing payload construction
            yield f"data: {json.dumps(payload)}\n\n"
            heartbeat_counter += 1
            if heartbeat_counter >= 15:
                yield ":heartbeat\n\n"
                heartbeat_counter = 0
            await asyncio.sleep(1)
        except (asyncio.CancelledError, GeneratorExit):
            logger.debug("SSE client disconnected")
            break
        except RuntimeError:
            logger.debug("SSE transport closed")
            break
```

**Critical design decisions (see ADR-4 in design.md):**

- `except (CancelledError, GeneratorExit)` catches asyncio cancellation and generator close
- Separate `except RuntimeError` catches closed-socket write errors
- Do NOT use bare `except Exception` — it would suppress legitimate bugs (JSON serialization failures, etc.)
- Log at `DEBUG` level — client disconnect is a normal event, not an error
- `break` exits the `while True` loop cleanly, terminating the coroutine

**TDD phase:** GREEN — Task 2.1 tests now pass.

**Acceptance criteria:**

- `_sse_generator()` has try/except covering both `yield` statements and the `await asyncio.sleep(1)`
- Catches exactly `CancelledError`, `GeneratorExit`, `RuntimeError` — no broad except
- All 4 tests from Task 2.1 pass: `uv run pytest tests/unit/adapters/inbound/api/test_app.py::TestSseGenerator -v`
- Existing SSE tests still pass (regression check)

**Estimated lines:** ~10 in app.py (add try/except + break, modify indentation)

---

### Task 2.3: Write /health endpoint tests (RED for #27)

**Files:** `tests/unit/adapters/inbound/api/test_app.py`

**Prerequisite:** None (can run in parallel with Phase 1 or 2.1–2.2)

**What to do:**
Add a new test class `TestHealthEndpoint` with:

1. **`test_health_returns_200_when_generator_initialized(self, client)`** — Inject `engine._generator` (mock or real `EventGenerator`), call `GET /health`, assert HTTP 200, assert body `{"status": "healthy"}`.

2. **`test_health_returns_503_when_generator_is_none(self, client)`** — Ensure `engine._generator is None`, call `GET /health`, assert HTTP 503, assert body contains `"unavailable"` or `"detail"`.

3. **`test_health_transitions_503_to_200(self, client)`** — Start with `_generator=None` (503), then inject a generator (200), verify transition.

4. **`test_status_endpoint_unchanged(self, client)`** — Call `GET /status`, assert HTTP 200, assert body has `status`, `current_multiplier`, `estimated_eps`, `total_workstations` fields (backward compatibility regression).

**Test pattern:** Use the existing `client` fixture which already injects `EngineState` with `_start_background_engine` mocked. For `/health` 503 case, the default `client` fixture leaves `_generator=None`. For `/health` 200 case, inject a mock generator.

**TDD phase:** RED — `/health` endpoint does not exist yet, so tests for it return 404.

**Acceptance criteria:**

- 4 new test methods in `TestHealthEndpoint` class
- Tests 1–3 fail with HTTP 404 (endpoint not found)
- Test 4 passes (verifies `/status` backward compatibility)
- Run: `uv run pytest tests/unit/adapters/inbound/api/test_app.py::TestHealthEndpoint -v`

**Estimated lines:** ~40 new in test file

---

### Task 2.4: Implement /health endpoint in app.py (GREEN for #27)

**Files:** `adapters/inbound/api/app.py` (insert new route after `/status` endpoint, ~line 234)

**Prerequisite:** Task 2.3 completed (tests fail)

**What to do:**
Add a new endpoint `GET /health` after the `/status` route:

```python
from fastapi.responses import JSONResponse

@app.get("/health")
async def health_check():
    """Operational health check for Docker and orchestrators."""
    engine = app.state.engine
    if engine._generator is not None:
        return {"status": "healthy"}
    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "detail": "Engine not initialized"},
    )
```

**Design decisions (see ADR-1 and ADR-2 in design.md):**

- **HTTP 503** when `_generator is None` — canonical "service temporarily unavailable"
- **HTTP 200** when `_generator is not None` — engine ready
- **`JSONResponse`** — needed because `@app.get(response_model=...)` doesn't support 503 naturally
- **Keep `/status` unchanged** — backward compatibility for dashboards

**Note:** The `from fastapi.responses import JSONResponse` import may need to be added at the top of the file if not already present. Check existing imports.

**TDD phase:** GREEN — Task 2.3 tests now pass.

**Acceptance criteria:**

- `GET /health` endpoint exists and is functional
- Returns HTTP 200 + `{"status": "healthy"}` when `engine._generator is not None`
- Returns HTTP 503 + body with `"unavailable"` when `engine._generator is None`
- `GET /status` behavior is completely unchanged
- All 4 tests from Task 2.3 pass: `uv run pytest tests/unit/adapters/inbound/api/test_app.py::TestHealthEndpoint -v`

**Estimated lines:** ~12 in app.py

---

### Task 2.5: Update docker-compose API healthcheck to /health

**Files:** `docker-compose.yml` (line ~93, `bankrange-api` service)

**Prerequisite:** Task 2.4 completed (/health endpoint implemented)

**What to do:**
Change the `bankrange-api` healthcheck test command:

```yaml
# Before:
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/status"]

# After:
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

Do NOT change `interval`, `timeout`, or `retries` — the existing values (`10s`, `5s`, `5`) allow ~50s for engine initialization.

**Acceptance criteria:**

- `docker-compose.yml` — `bankrange-api.healthcheck.test` points to `/health`
- `docker compose up bankrange-api` → Docker healthcheck uses `/health`
- Container transitions from `starting` to `healthy` only after engine initializes

**Estimated lines:** ~1 in docker-compose.yml

---

## Phase 3: Testing & Verification

### Task 3.1: Run full test suite

**Command:** `uv run pytest tests/ -v`

**Prerequisite:** All Phase 1 and Phase 2 tasks completed

**What to do:**
Run the full test suite and verify all tests pass with coverage ≥ 80%.

**Acceptance criteria:**

- `uv run pytest tests/ -v` exits with code 0
- All existing tests pass (no regressions)
- All new tests from Tasks 1.1, 2.1, 2.3 pass
- Coverage ≥ 80% (if coverage tooling is available — config.yaml says `coverage.available: false`, but verify visually that no major paths are untested)

**Estimated lines:** 0

---

### Task 3.2: Verify loop guard (#28 — documentation only)

**Files:** `adapters/inbound/api/app.py` (lines ~90-140, `_run_engine_loop()`)

**What to do:**
Confirm the design.md finding: the loop guard `if engine_state.deployed:` is already correctly positioned as the first operation inside `while engine_state.is_running:`. Document the verification result.

**Verification checklist:**

- [ ] `if engine_state.deployed:` is the first substantive check in the loop body (line ~103)
- [ ] `generate_tick`, `set_scale_multiplier`, `get_multiplier`, `estimated_eps` are all inside the `if` block
- [ ] The `else` branch only does `await asyncio.sleep(1)`
- [ ] Existing test `test_run_engine_loop_skips_generation_when_not_deployed` (line ~367) passes
- [ ] Record in this task that #28 required zero code changes

**Acceptance criteria:**

- Zero code changes for #28
- Confirmation documented in this task

**Estimated lines:** 0

---

### Task 3.3: Verify B023 lambda (#10 — documentation only)

**Files:** `adapters/inbound/api/app.py`, `core/use_cases/event_generator.py`

**What to do:**
Confirm the design.md finding: no lambda-within-loop pattern exists in the current code. Document the verification result.

**Verification checklist:**

- [ ] `app.py` contains zero `lambda` keywords (confirmed by grep)
- [ ] `event_generator.py` contains 28 lambdas in `_metadata_value_for()`, all defined in a static dict literal (not inside a loop)
- [ ] The `for key in template.metadata_keys:` loop in `_generate_metadata()` only calls `_metadata_value_for(key)` — does not define lambdas
- [ ] No lambda captures a loop iteration variable by reference
- [ ] Record in this task that #10 required zero code changes (false positive from static analysis or removed code)

**Acceptance criteria:**

- Zero code changes for #10
- Confirmation documented in this task

**Estimated lines:** 0

---

### Task 3.4: Docker Compose integration smoke test

**Prerequisite:** All Phase 1 and Phase 2 tasks completed

**What to do:**
Perform a lightweight integration check with Docker Compose:

1. `docker compose up -d` — all services start
2. `docker ps` — verify `bankrange-loki` is `healthy`, `bankrange-api` is `healthy`, three Vector services are running
3. `docker logs bankrange-vector-windows 2>&1 | grep -i "503\|error\|unhealthy"` — zero healthcheck-related errors
4. `curl -f http://localhost:8000/health` — returns HTTP 200 after initialization
5. `curl -s http://localhost:8000/status | jq .` — returns expected fields
6. `docker compose down` — clean shutdown

**Acceptance criteria:**

- All services reach healthy/running state
- No 503 errors in Vector logs during startup
- `/health` returns 200 once engine is initialized
- `/status` preserves backward compatibility
- Clean shutdown without orphaned resources

**Estimated lines:** 0

---

## Summary

| Phase             | Tasks        | Files Modified                                                         | Est. Δ Lines |
| ----------------- | ------------ | ---------------------------------------------------------------------- | ------------ |
| 1: Infrastructure | 1.1–1.4      | `docker-compose.yml`, `config/vector/*.yaml`, `test_vector_configs.py` | ~51          |
| 2: Implementation | 2.1–2.5      | `app.py`, `docker-compose.yml`, `test_app.py`                          | ~108         |
| 3: Verification   | 3.1–3.4      | None (verification only)                                               | ~0           |
| **Total**         | **13 tasks** | **7 files**                                                            | **~159**     |

**All estimates well under 400-line review budget.**

### Task Completion Order (recommended)

```
1.1 → 1.2 → 1.3 → 1.4      (Phase 1: infra, sequential)
2.1 → 2.2                    (Phase 2: SSE, TDD)
2.3 → 2.4 → 2.5              (Phase 2: health, TDD)
                              ← Phase 2 streams can run in parallel
3.1 → 3.2 + 3.3 + 3.4        (Phase 3: verification gate)
```

### TDD Cycle Summary

| Task | RED (test) | GREEN (impl)    | Test location                                 |
| ---- | ---------- | --------------- | --------------------------------------------- |
| #25  | 1.1        | 1.2 + 1.3 + 1.4 | `tests/integration/test_vector_configs.py`    |
| #26  | 2.1        | 2.2             | `tests/unit/adapters/inbound/api/test_app.py` |
| #27  | 2.3        | 2.4 + 2.5       | `tests/unit/adapters/inbound/api/test_app.py` |
| #28  | existing   | verify-only     | already passing                               |
| #10  | n/a        | verify-only     | n/a                                           |
