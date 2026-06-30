# Tasks: Security Hardening

**Change ID:** `security-hardening`
**Date:** 2026-05-18

---

## Review Workload Forecast

| Field                   | Value     |
| ----------------------- | --------- |
| Estimated changed lines | ~201      |
| 400-line budget risk    | Low       |
| Chained PRs recommended | No        |
| Delivery strategy       | single-pr |

---

## Dependency Graph

```
Phase 1: CORS (#4) — independent
  1.1 (test RED) → 1.2 (fix GREEN) → 1.3 (env doc)

Phase 2: Auth + Rate Limit (#19) — independent of Phase 1
  2.1 (test RED) → 2.2 (auth dep GREEN) → 2.3 (rate limit GREEN) → 2.4 (nginx + env + docker)

Phase 3: Verification
  3.1 (full suite) → 3.2 (manual check)
```

---

## Phase 1: CORS Fix (#4)

### Task 1.1: Write CORS test (RED)

**File:** `tests/unit/adapters/inbound/api/test_app.py`
**What:** Add test `test_cors_allow_credentials_is_false` — asserts `allow_credentials=False` in middleware config. Add test `test_cors_allowed_origins_respects_env` — verifies origin list from env var.
**TDD phase:** RED — tests fail because `allow_credentials=True` currently.
**Est. lines:** ~20

### Task 1.2: Fix allow_credentials → False (GREEN)

**File:** `adapters/inbound/api/app.py` line ~219
**What:** Change `allow_credentials=True` → `allow_credentials=False`
**TDD phase:** GREEN — Task 1.1 tests pass.
**Est. lines:** ~1

### Task 1.3: Document ALLOWED_ORIGINS in env configs

**Files:** `.env.example`, `docker-compose.yml` (bankrange-api env block)
**What:** Add `ALLOWED_ORIGINS=http://localhost:8080` with documentation comment.
**Est. lines:** ~4

---

## Phase 2: Auth + Rate Limiting (#19)

### Task 2.1: Write auth + rate limit tests (RED)

**File:** `tests/unit/adapters/inbound/api/test_app.py`
**What:** Add `TestApiKeyAuth` class with:

1. `test_control_returns_401_without_api_key` — POST /control without header → 401
2. `test_control_returns_401_with_wrong_api_key` — POST /control with wrong key → 401
3. `test_control_returns_200_with_valid_api_key` — POST /control with correct key → 200
4. `test_control_returns_429_when_rate_limited` — 6 rapid requests → 5th succeeds, 6th gets 429
5. `test_health_remains_public` — GET /health without key → 200
6. `test_status_remains_public` — GET /status without key → 200
   **TDD phase:** RED — tests for /control fail with 401 (endpoint still public).
   **Est. lines:** ~70

### Task 2.2: Implement verify_api_key dependency (GREEN auth)

**File:** `adapters/inbound/api/app.py`
**What:**

- Add `BR_API_KEY` env var loading
- Add `verify_api_key` FastAPI dependency using `HTTPBearer` or header check
- Apply dependency to `POST /control` only (not to /health, /status, /topology/\*, /events/stream)
- Log auth failures at WARNING level
  **TDD phase:** GREEN — Tasks 2.1-1,2,3,5,6 pass (401/200 tests pass).
  **Est. lines:** ~25

### Task 2.3: Implement sliding window rate limiter (GREEN rate limit)

**File:** `adapters/inbound/api/app.py`
**What:**

- In-memory dict: `{ip: [timestamps]}` per endpoint
- Sliding window: max 5 req per 60s window per IP
- Clean up expired entries periodically
- Return `429 Too Many Requests` with `Retry-After` header
- Apply as dependency to `POST /control`
  **TDD phase:** GREEN — Task 2.1-4 passes (429 test).
  **Est. lines:** ~30

### Task 2.4: Configure nginx + env vars + docker

**Files:** `config/nginx/nginx.conf`, `.env.example`, `docker-compose.yml`
**What:**

- nginx: add `proxy_set_header X-API-Key $API_KEY;` (or hardcoded from env)
- `.env.example`: add `BR_API_KEY=change-me-in-production`
- `docker-compose.yml`: add `BR_API_KEY` to bankrange-api env block
- docker-compose.yml: add `ALLOWED_ORIGINS` env var
  **Est. lines:** ~10

---

## Phase 3: Verification

### Task 3.1: Run full test suite

**Command:** `uv run pytest tests/ -v`
**What:** All tests pass, coverage ≥ 80%.
**Est. lines:** 0

### Task 3.2: Manual verification checklist

- [ ] `allow_credentials=False` confirmed in app.py
- [ ] `POST /control` returns 401 without `X-API-Key` header
- [ ] `POST /control` returns 200 with valid `X-API-Key`
- [ ] `GET /health` returns 200 without auth (Docker healthcheck)
- [ ] Rate limiter blocks 6th request within 60s window
- [ ] `curl -X POST http://localhost:8000/control -H 'Content-Type: application/json' -d '{"eps_multiplier":1}'` → 401
- [ ] `curl -X POST http://localhost:8000/control -H 'Content-Type: application/json' -H 'X-API-Key: test-key' -d '{"eps_multiplier":1}'` → 200

---

## Summary

| Phase     | Tasks       | Files                                                        | Est. Δ   |
| --------- | ----------- | ------------------------------------------------------------ | -------- |
| 1: CORS   | 1.1–1.3     | `app.py`, `.env.example`, `docker-compose.yml`               | ~25      |
| 2: Auth   | 2.1–2.4     | `app.py`, `nginx.conf`, `.env.example`, `docker-compose.yml` | ~135     |
| 3: Verify | 3.1–3.2     | None                                                         | ~0       |
| **Total** | **9 tasks** | **5 files**                                                  | **~160** |

**Well under 400-line review budget. Single PR.**
