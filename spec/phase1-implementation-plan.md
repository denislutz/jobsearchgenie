# Phase 1 Implementation Plan — JobSearchGenie

## Overview

Phase 1 delivers a working `GET /jobs/search` endpoint backed by the Indeed Publisher API, with all other endpoints returning 501 stubs. No database, no Redis, no auth. The goal is a deployable, testable slice of the full system that validates the core data flow.

**Scope boundary:** `src/` directory creation only. `pyproject.toml`, `mise.toml`, and `.gitignore` already exist and are correct.

---

## Project Structure

```
src/
├── main.py                        # FastAPI app factory, lifespan, router mount
├── config.py                      # Settings via pydantic-settings, get_settings()
├── api/
│   ├── __init__.py
│   ├── router.py                  # Aggregates all route sub-routers
│   └── routes/
│       ├── __init__.py
│       ├── jobs.py                # REAL: GET /jobs/search; STUB: GET /jobs/{id}, GET /jobs/filters
│       ├── analytics.py           # STUB: GET /analytics/trending, GET /analytics/salary-ranges
│       ├── saved_searches.py      # STUB: POST/GET/DELETE /saved-searches
│       └── auth.py                # STUB: POST /auth/signup, POST /auth/login
├── domain/
│   ├── __init__.py
│   ├── job.py                     # Job, Salary, SearchRequest, SearchResponse Pydantic models
│   └── errors.py                  # SourceUnavailableError, ValidationError, custom exceptions
├── services/
│   ├── __init__.py
│   └── job_service.py             # JobService.search() — orchestrates adapter calls
└── sources/
    ├── __init__.py
    └── indeed.py                  # IndeedAdapter — httpx calls, normalization, retry

tests/
├── conftest.py                    # pytest fixtures: test client, mock Indeed adapter
├── test_api/
│   ├── __init__.py
│   └── test_jobs.py               # API-level tests for GET /jobs/search
└── test_sources/
    ├── __init__.py
    └── test_indeed.py             # Unit tests for IndeedAdapter normalization + retry
```

Root-level files to add:

- `.env.example` — committed, documents all required vars
- `.env` — gitignored, never committed

---

## Environment Variables

### `.env.example` (commit this)

```dotenv
# Indeed Publisher API credentials
INDEED_API_KEY=your_publisher_key_here
INDEED_PUBLISHER_ID=your_publisher_id_here

# Application
APP_ENV=development
DEBUG=true
```

### `.env` (gitignore, never commit)

Copy from `.env.example`, fill in real values.

### `src/config.py` — Settings Class

`Settings` extends `BaseSettings`. Priority order (highest to lowest): environment variables → `.env` file → field defaults.

| Field                 | Type   | Default         | Source                              |
| --------------------- | ------ | --------------- | ----------------------------------- |
| `indeed_api_key`      | `str`  | — (required)    | `INDEED_API_KEY`                    |
| `indeed_publisher_id` | `str`  | — (required)    | `INDEED_PUBLISHER_ID`               |
| `app_env`             | `str`  | `"development"` | `APP_ENV` (also set in `mise.toml`) |
| `debug`               | `bool` | `False`         | `DEBUG`                             |

`model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)`

`get_settings()` is decorated with `@lru_cache()` so the `.env` file is read once per process. For Phase 1, the service and adapter call `get_settings()` directly. FastAPI `Depends(get_settings)` injection can be added in Phase 2.

---

## Architecture Layers

| Layer         | Owns                                                                                            |
| ------------- | ----------------------------------------------------------------------------------------------- |
| `api/routes/` | HTTP concerns only: parse query params, call service, serialize response, raise `HTTPException` |
| `services/`   | Business logic and orchestration: fan-out to adapters, merge results, apply sorting/pagination  |
| `domain/`     | Pure data models, no I/O. Pydantic `BaseModel` only, no imports from other layers               |
| `sources/`    | External I/O adapters: one class per data source, owns HTTP calls and field normalization       |

---

## Domain Models — `src/domain/job.py`

### `Salary`

`min: int | None`, `max: int | None`, `currency: str` (default `"EUR"`)

### `Job`

`id: str`, `title: str`, `company: str`, `location: str`, `job_type: str | None`, `contract_type: str | None`, `salary: Salary | None`, `description: str`, `posted_at: datetime | None`, `url: str`, `source: str`, `extracted_skills: list[str]`, `normalized_level: str | None`, `confidence_score: float | None`

### `SearchRequest`

`keywords: str`, `location: str`, `salary_min: int | None`, `salary_max: int | None`, `job_type: str | None`, `contract_type: str | None`, `sources: list[str]` (default `["indeed"]`), `limit: int` (default 20, max 100), `offset: int` (default 0), `sort_by: str` (default `"relevance"`)

### `SearchResponse`

`total: int`, `limit: int`, `offset: int`, `jobs: list[Job]`

---

## Custom Exceptions — `src/domain/errors.py`

```
SourceUnavailableError(source: str, detail: str)  # → HTTP 503
InvalidSearchParamsError(detail: str)              # → HTTP 400
JobNotFoundError(job_id: str)                      # → HTTP 404 (used in Phase 2)
```

Plain Python exceptions. The route layer catches them and re-raises as `HTTPException`. No HTTP status codes in the domain layer.

---

## First Real Endpoint — `GET /jobs/search`

### Request Contract

| Parameter       | Type        | Required | Default       | Notes                                  |
| --------------- | ----------- | -------- | ------------- | -------------------------------------- |
| `keywords`      | `str`       | Yes      | —             | Passed as `q` to Indeed                |
| `location`      | `str`       | Yes      | —             | Passed as `l` to Indeed                |
| `salary_min`    | `int`       | No       | `None`        | Client-side filter in Phase 1          |
| `salary_max`    | `int`       | No       | `None`        | Client-side filter in Phase 1          |
| `job_type`      | `str`       | No       | `None`        | `full_time`, `part_time`, `internship` |
| `contract_type` | `str`       | No       | `None`        | `permanent`, `contract`, `freelance`   |
| `sources`       | `list[str]` | No       | `["indeed"]`  | Ignored in Phase 1 (always Indeed)     |
| `limit`         | `int`       | No       | `20`          | Max 25 (Indeed Publisher API ceiling)  |
| `offset`        | `int`       | No       | `0`           |                                        |
| `sort_by`       | `str`       | No       | `"relevance"` | `"relevance"` or `"date"`              |

Missing `keywords` or `location` → FastAPI raises 422 automatically (required `Query` params with no default).

### Response Shape

```json
{
  "total": 47,
  "limit": 20,
  "offset": 0,
  "jobs": [
    {
      "id": "indeed-abc123",
      "title": "Senior Python Developer",
      "company": "Acme GmbH",
      "location": "Berlin, DE",
      "job_type": null,
      "contract_type": null,
      "salary": null,
      "description": "...",
      "posted_at": "2026-03-10T00:00:00Z",
      "url": "https://de.indeed.com/viewjob?jk=abc123",
      "source": "indeed",
      "extracted_skills": [],
      "normalized_level": null,
      "confidence_score": null
    }
  ]
}
```

### Error Responses

| Scenario                                         | Status | Code                                                     |
| ------------------------------------------------ | ------ | -------------------------------------------------------- |
| Indeed API 5xx / timeout (all retries exhausted) | 503    | `SERVICE_UNAVAILABLE`                                    |
| Invalid `sort_by` value                          | 400    | `BAD_REQUEST`                                            |
| Indeed auth error                                | 503    | `SERVICE_UNAVAILABLE` (do not expose credential details) |

Error body format:

```json
{"error": {"code": "SERVICE_UNAVAILABLE", "message": "Indeed is temporarily unavailable", "details": {}}}
```

### Call Chain

```
GET /jobs/search
  → jobs.py route handler
    → JobService.search(request: SearchRequest)
      → IndeedAdapter.search(keywords, location, limit, offset, sort_by)
        → httpx GET to Indeed Publisher API
        → normalize Indeed response → list[Job]
      → apply salary_min/salary_max filters if provided
      → return SearchResponse(total=len(jobs), limit=..., offset=..., jobs=...)
  → serialize + 200
```

### Stub Pattern (all other routes)

```python
raise HTTPException(status_code=501, detail="Not implemented yet")
```

Applied to: `GET /jobs/{job_id}`, `GET /jobs/filters`, all analytics routes, all saved-searches routes, all auth routes.

---

## Health Endpoint

`GET /health` → `{"status": "ok"}` with no auth, no service calls. Define in `main.py` directly.

---

## Indeed Adapter — `src/sources/indeed.py`

### HTTP Call

Base URL: `https://api.indeed.com/ads/apisearch`

| Param       | Value                                                           |
| ----------- | --------------------------------------------------------------- |
| `publisher` | `settings.indeed_publisher_id`                                  |
| `q`         | `keywords`                                                      |
| `l`         | `location`                                                      |
| `co`        | `"de"` (hardcoded Phase 1; expand to `"at"`, `"ch"` in Phase 2) |
| `v`         | `"2"`                                                           |
| `format`    | `"json"`                                                        |
| `limit`     | `limit` (max 25 per Indeed Publisher API)                       |
| `start`     | `offset`                                                        |
| `sort`      | `"date"` if `sort_by == "date"` else omit                       |

### Field Normalization: Indeed → `Job`

| Indeed field        | Internal field     | Notes                                            |
| ------------------- | ------------------ | ------------------------------------------------ |
| `jobkey`            | `id`               | Prefix with `"indeed-"`                          |
| `jobtitle`          | `title`            |                                                  |
| `company`           | `company`          |                                                  |
| `formattedLocation` | `location`         |                                                  |
| `url`               | `url`              |                                                  |
| `snippet`           | `description`      | HTML snippet; strip tags or keep raw for Phase 1 |
| `date`              | `posted_at`        | Parse Indeed date string → `datetime`            |
| hardcoded           | `source`           | `"indeed"`                                       |
| —                   | `job_type`         | `None` (not in free API)                         |
| —                   | `contract_type`    | `None` (not in free API)                         |
| —                   | `salary`           | `None` (not in free API)                         |
| —                   | `extracted_skills` | `[]` (Phase 2)                                   |
| —                   | `normalized_level` | `None` (Phase 2)                                 |
| —                   | `confidence_score` | `None` (Phase 2)                                 |

### Retry Logic (tenacity)

Wrap the httpx call:

- Retry on: `httpx.TimeoutException`, `httpx.ConnectError`, HTTP 5xx response status
- Strategy: `wait_exponential(multiplier=1, min=1, max=10)`
- Max attempts: 3
- On `RetryError`: raise `SourceUnavailableError("indeed", ...)`

Isolate the HTTP call in a `_fetch_raw()` method to make it easy to mock in tests and to swap transport for local development.

### MCP Tool Alternative

The environment includes `mcp__claude_ai_Indeed__search_jobs` as a Claude Code MCP tool. It can substitute for the Publisher API during local development when credentials are unavailable or to avoid rate limits. Because `_fetch_raw()` is isolated, swapping it is a one-method change.

---

## `src/main.py` — App Factory

- `FastAPI(title="JobSearchGenie", version="0.1.0")`
- `lifespan` context manager: create shared `httpx.AsyncClient` on startup, store on `app.state.http_client`, close on shutdown
- Mount `router.py` (no version prefix for Phase 1)
- `GET /health` defined directly in `main.py`
- Global exception handlers:
  - `SourceUnavailableError` → 503 with error body
  - `InvalidSearchParamsError` → 400 with error body

The `IndeedAdapter` receives the shared `httpx.AsyncClient` via constructor injection (passed down from `main.py` via `app.state`). `JobService` receives the adapter via constructor. In Phase 1 this can be wired manually in the route handler using `request.app.state`; switch to FastAPI `Depends` in Phase 2.

---

## Order of Implementation

| Step | File                                                          | Reason                                                       |
| ---- | ------------------------------------------------------------- | ------------------------------------------------------------ |
| 1    | `src/domain/errors.py`                                        | No dependencies                                              |
| 2    | `src/domain/job.py`                                           | No dependencies; everything else imports from here           |
| 3    | `src/config.py` + `.env.example`                              | Needed by adapter and service                                |
| 4    | `src/sources/indeed.py`                                       | Depends on domain models, config, httpx, tenacity            |
| 5    | `src/services/job_service.py`                                 | Depends on domain models + IndeedAdapter                     |
| 6    | `src/api/routes/jobs.py`                                      | Depends on JobService + domain models                        |
| 7    | `src/api/routes/analytics.py`, `auth.py`, `saved_searches.py` | Stub files, no logic                                         |
| 8    | `src/api/router.py`                                           | Imports all route modules                                    |
| 9    | `src/main.py`                                                 | Imports router, configures app, lifespan, exception handlers |
| 10   | `tests/conftest.py`                                           | Fixtures for app, mock adapter, sample jobs                  |
| 11   | `tests/test_api/test_jobs.py`                                 | API tests                                                    |
| 12   | `tests/test_sources/test_indeed.py`                           | Adapter unit tests                                           |

---

## Test Plan for Phase 1

### `tests/conftest.py` Fixtures

- `async_client`: `AsyncClient(app=app, base_url="http://test")` via `httpx.ASGITransport`
- `mock_indeed_adapter`: `AsyncMock` returning a pre-built `list[Job]`
- `sample_jobs`: factory producing 3–5 `Job` instances with known field values

Override `IndeedAdapter` via FastAPI dependency override or by injecting `mock_indeed_adapter` into `JobService` constructor during test setup.

### `tests/test_api/test_jobs.py`

| Test                             | Assertion                                                                            |
| -------------------------------- | ------------------------------------------------------------------------------------ |
| `test_search_returns_200`        | Happy path `keywords=python&location=Berlin` → 200, valid `SearchResponse` shape     |
| `test_search_missing_keywords`   | Omit `keywords` → 422                                                                |
| `test_search_missing_location`   | Omit `location` → 422                                                                |
| `test_search_default_pagination` | Response `limit=20`, `offset=0` when not specified                                   |
| `test_search_custom_pagination`  | `limit=5&offset=10` reflected in response                                            |
| `test_search_indeed_unavailable` | Adapter raises `SourceUnavailableError` → 503, body contains `"SERVICE_UNAVAILABLE"` |
| `test_stub_job_detail`           | `GET /jobs/abc123` → 501                                                             |
| `test_stub_filters`              | `GET /jobs/filters` → 501                                                            |
| `test_health`                    | `GET /health` → 200, `{"status": "ok"}`                                              |

### `tests/test_sources/test_indeed.py`

| Test                                           | Assertion                                                                                               |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `test_normalize_job_fields`                    | Given raw Indeed response dict, `_normalize()` returns `Job` with correct field mapping                 |
| `test_id_prefixed_with_indeed`                 | `job.id` starts with `"indeed-"`                                                                        |
| `test_posted_at_parsed`                        | `posted_at` is a `datetime` instance                                                                    |
| `test_retry_on_timeout`                        | Mock `_fetch_raw` raises `TimeoutException` twice then succeeds; assert result returned, called 3 times |
| `test_raises_source_unavailable_after_retries` | Mock raises `TimeoutException` all 3 times; assert `SourceUnavailableError` raised                      |
| `test_http_500_retried`                        | Mock returns HTTP 500 twice then 200; assert success on third attempt                                   |

Use `AsyncMock` for `httpx.AsyncClient.get`. Patch at the `httpx.AsyncClient` level.

---

## Key Constraints and Decisions

**No DB in Phase 1.** `alembic` and `sqlalchemy` are installed but no migrations created until Phase 2.

**No Redis in Phase 1.** `redis` is installed but unused.

**`PYTHONPATH` is `src/`.** Set in `mise.toml` `[env]`. All imports are absolute from `src/`: `from config import get_settings`, `from domain.job import Job`, `from sources.indeed import IndeedAdapter`.

**Indeed free Publisher API limit.** Returns max 25 results per request. Cap `limit` at 25 in Phase 1. Phase 2 can add multi-page aggregation if needed.

**`*-internal-spec.md` is gitignored.** This plan file (`phase1-implementation-plan.md`) does not match that pattern and will be tracked by git.
