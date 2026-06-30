# Proposal: Security Hardening (CORS + API Authentication)

## Change ID

`security-hardening`

## Intent

Address two HIGH-severity security vulnerabilities discovered during comprehensive project health review:

1. **Bug #4 — CORS `allow_credentials=True` is unnecessary and risky.** The FastAPI `CORSMiddleware` is configured with `allow_credentials=True` despite the SvelteKit frontend making zero use of credentials (no cookies, no `credentials: 'include'` in fetch calls, no `Authorization` headers). This unnecessarily widens the CORS attack surface: with credentials enabled, the `Access-Control-Allow-Origin` header cannot be `*` and must reflect the exact origin, but the backend currently allows arbitrary comma-separated origins via the `ALLOWED_ORIGINS` env var. Dropping `allow_credentials` to `False` locks down this vector without any functional regression.

2. **Bug #19 — `POST /control` has no authentication or rate limiting.** Any party that can reach the API can stop or amplify the simulation engine via an unauthenticated `POST /control`. This is the only write endpoint; all six other endpoints are read-only and present negligible risk. The `/health` endpoint MUST remain public (Docker Compose healthcheck dependency).

The fixes are minimal, surgically targeted, and introduce no external dependencies — the rate limiter and API-key auth are implemented manually using only the Python standard library and FastAPI's built-in dependency injection.

## Motivation

- **CORS**: Configuring `allow_credentials=True` without a legitimate use case is a security anti-pattern. It forces the server to reflect specific origins instead of using a wildcard, and unnecessarily trusts that the browser credential model is being used correctly.
- **Auth**: An unauthenticated `POST /control` endpoint makes the simulation engine trivially disruptable by any network-adjacent actor. In a purple-team cyber range context, this undermines the entire simulation's integrity.
- **Defense in depth**: Even in a development/internal tool, write endpoints should require some form of authentication. The cost of adding it is minimal (manual FastAPI dependency, ~30 lines of Python).

## Scope

### In Scope

| Fix                  | Files                                                                            | Description                                                                                                          |
| -------------------- | -------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| CORS hardening       | `adapters/inbound/api/app.py`                                                    | Change `allow_credentials=True` → `False` in `CORSMiddleware`                                                        |
| CORS hardening       | `.env.example`                                                                   | Document `ALLOWED_ORIGINS` env var with explanation                                                                  |
| CORS hardening       | `docker-compose.yml`                                                             | Add `ALLOWED_ORIGINS` to `bankrange-api` service env vars                                                            |
| Auth & rate limiting | `adapters/inbound/api/app.py`                                                    | Add `X-API-Key` FastAPI dependency and sliding-window rate limiter (5 req/min per IP), apply only to `POST /control` |
| Auth & rate limiting | `.env.example`                                                                   | Document `BR_API_KEY` env var                                                                                        |
| Auth & rate limiting | `docker-compose.yml`                                                             | Add `BR_API_KEY` to `bankrange-api` service env vars                                                                 |
| Auth & rate limiting | `config/nginx/nginx.conf`                                                        | Inject `X-API-Key` header in `/api/` proxy location block                                                            |
| Tests                | `tests/unit/adapters/inbound/api/test_auth.py` (new) or `test_app.py` (extended) | Auth dependency, rate limiter, and CORS credential regression tests                                                  |

### Out of Scope

- Protecting read-only endpoints (`/status`, `/topology/*`, `/events/stream`) — these are intentionally left public as they power the monitoring dashboard.
- Protecting `/health` — MUST remain public for Docker Compose healthcheck (`curl -f http://localhost:8000/health`).
- CSRF protection — not applicable; no browser sends credentials, and the API key is injected server-side by Nginx.
- Full authentication system (OAuth2, JWT, sessions) — overkill for a development/internal simulation tool.
- TLS termination at the API — handled by the reverse proxy layer if needed.
- Audit logging of auth failures — deferred; can be added later by wrapping the dependency.

## Affected Areas

| Area                                           | Impact   | Description                                                                                                                                 |
| ---------------------------------------------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `adapters/inbound/api/app.py`                  | Modified | `CORSMiddleware` config changed; new `require_api_key` dependency; new `SlidingWindowRateLimiter` class; `POST /control` signature extended |
| `config/nginx/nginx.conf`                      | Modified | `/api/` location block gains `proxy_set_header X-API-Key $api_key;` (or hardcoded value via env substitution)                               |
| `.env.example`                                 | Modified | Two new vars: `BR_API_KEY`, `ALLOWED_ORIGINS`                                                                                               |
| `docker-compose.yml`                           | Modified | `bankrange-api` service gains `BR_API_KEY` and `ALLOWED_ORIGINS` env vars                                                                   |
| `tests/unit/adapters/inbound/api/test_app.py`  | Modified | CORS `allow_credentials` assertions updated; new test class for `POST /control` auth                                                        |
| `tests/unit/adapters/inbound/api/test_auth.py` | New      | Dedicated auth and rate limiter unit tests                                                                                                  |

## Risks

| Risk                                                                                        | Likelihood | Severity | Mitigation                                                                                                                                                                                                                                                                                                                                              |
| ------------------------------------------------------------------------------------------- | ---------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nginx fails to inject `X-API-Key` header** → UI calls to `/control` break with 401        | Low        | High     | Test e2e with `docker compose up`; the `proxy_set_header` directive is standard and reliable. Fallback: if Nginx substitution fails, the UI shows a user-visible error that is easy to diagnose.                                                                                                                                                        |
| **Rate limiter rejects legitimate requests during burst** (5 req/min may be too low)        | Low        | Low      | The `/control` endpoint is not designed for high-frequency calls (it toggles engine state). 5 req/min is generous. If needed, the threshold can be tuned via an env var later.                                                                                                                                                                          |
| **`BR_API_KEY` env var not set in production** → auth dependency rejects all requests (401) | Low        | Medium   | The FastAPI dependency will log a clear warning on startup if `BR_API_KEY` is missing; in development, a default value can be used via `os.getenv("BR_API_KEY", "dev-key")`. Docker Compose already sets a value for `bankrange-api`.                                                                                                                   |
| **CORS `allow_credentials=False` breaks existing integrations**                             | Very Low   | Low      | The SvelteKit frontend uses no credentials (confirmed via code audit of `api.service.ts`). The only fetch calls use `headers: { 'Content-Type': 'application/json', Accept: 'application/json' }` with no `credentials` option. Browser default is `omit` for same-origin and `same-origin` for cross-origin — neither triggers a credentialed request. |
| **Rate limiter state grows unbounded** (memory leak from IP tracking)                       | Low        | Low      | The sliding window implementation will use a `defaultdict[datetime]` and clean up entries older than the window on every request. A max size guard will be included.                                                                                                                                                                                    |
| **Nginx `X-API-Key` header reaches external consumers**                                     | Low        | Medium   | Nginx adds the header only in outbound proxy requests to `bankrange-api:8000`. The header is not exposed to the browser; only the backend receives it. No `add_header` directive for `X-API-Key` exists in the Nginx config.                                                                                                                            |

## Dependencies Between Fixes

```
Fix #4 (CORS) ── independent ──> can be deployed alone
Fix #19 (Auth) ── depends on ──> nginx.conf change + BR_API_KEY env var
```

- **CORS fix (#4)** has zero dependencies and can be deployed independently in a single commit.
- **Auth fix (#19)** requires coordination between three files: `app.py` (dependency + rate limiter), `nginx.conf` (header injection), and `docker-compose.yml` (env var). These must be deployed together to avoid 401 errors.
- The two fixes are **logically independent** but share the `app.py` file — merge order should be CORS first (simpler, no risk) then auth (more complex, requires Nginx coordination).

## Rollback Plan

### CORS Fix Rollback

- Revert `allow_credentials=False` → `True` in `app.py` line 219.
- No other changes needed. Can be done in seconds.

### Auth Fix Rollback

1. Remove `Depends(require_api_key)` from `POST /control` signature in `app.py`.
2. Remove the `SlidingWindowRateLimiter` class and `rate_limiter` global from `app.py`.
3. Remove `proxy_set_header X-API-Key` from `config/nginx/nginx.conf` `/api/` block.
4. Remove `BR_API_KEY` from `docker-compose.yml` and `.env.example`.
5. Redeploy.

All changes are additive (new dependency, new header, new env var) — rollback is a pure removal exercise.

## Estimated Changed Lines

| File                                           | Added    | Modified | Removed | Net      |
| ---------------------------------------------- | -------- | -------- | ------- | -------- |
| `adapters/inbound/api/app.py`                  | ~55      | ~3       | ~0      | ~58      |
| `config/nginx/nginx.conf`                      | ~2       | ~0       | ~0      | ~2       |
| `.env.example`                                 | ~5       | ~0       | ~0      | ~5       |
| `docker-compose.yml`                           | ~3       | ~0       | ~0      | ~3       |
| `tests/unit/adapters/inbound/api/test_app.py`  | ~0       | ~3       | ~0      | ~3       |
| `tests/unit/adapters/inbound/api/test_auth.py` | ~130     | ~0       | ~0      | ~130     |
| **Total**                                      | **~195** | **~6**   | **~0**  | **~201** |

Within the 400-line review budget.

## Success Criteria

- [ ] `allow_credentials` is `False` in `CORSMiddleware` configuration.
- [ ] `ALLOWED_ORIGINS` is documented in `.env.example` and set in `docker-compose.yml` for `bankrange-api`.
- [ ] `POST /control` returns `401 Unauthorized` when `X-API-Key` header is missing or incorrect.
- [ ] `POST /control` returns `200 OK` when `X-API-Key` header matches `BR_API_KEY`.
- [ ] `POST /control` returns `429 Too Many Requests` after 5 requests within a 60-second window from the same IP.
- [ ] `GET /health` remains public (no auth, returns `200` or `503` as before).
- [ ] `GET /status`, `GET /topology/*`, `GET /events/stream` remain public (no auth).
- [ ] Nginx injects `X-API-Key` header in proxied requests to `/api/` → SvelteKit UI `/control` calls succeed without code changes.
- [ ] All existing tests pass after modifications.
- [ ] New unit tests cover auth dependency, rate limiter, and CORS regression.
