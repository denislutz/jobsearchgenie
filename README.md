# JobSearchGenie

A unified REST API that aggregates job and freelance project listings from multiple DACH (Germany, Austria, Switzerland) job boards into a single, searchable interface.

## What it does

Instead of checking multiple job boards separately, you query one API and get deduplicated, normalized results across all sources — covering permanent positions, contracts, and freelance projects in the DACH IT/tech market.

## Key Features

- **Unified search** across multiple job boards with a single API call
- **Normalized data** — consistent fields regardless of source
- **Smart deduplication** — same job posted to multiple boards appears once
- **Flexible filtering** — by location, salary range, job type, contract type
- **Skill extraction** — automatically parsed from job descriptions
- **Trending analytics** — most in-demand skills and locations over time
- **Salary insights** — distribution data by role and location
- **Saved searches** — set up alerts for new matching jobs

## Quick Start

```bash
# 1. Install mise (manages Python + uv)
curl https://mise.run | sh

# 2. Install tools and dependencies
mise install
mise run install

# 3. Start dev server
mise run dev
```

API is now live at `http://localhost:8000` — docs at `http://localhost:8000/docs`.

## Other Commands

```bash
mise run test        # Run tests
mise run test-cov    # Tests with coverage report
mise run lint        # Lint with ruff
mise run fmt         # Format code
mise run typecheck   # Type check with mypy
mise run migrate     # Run DB migrations
mise run migration -- "add users table"  # Create new migration
```

## Tooling

This project uses **mise** + **uv** instead of the classical Python toolchain. Here's why.

### The classical approach and its problems

The traditional setup involves several separate tools with overlapping responsibilities:

- `pyenv` — manage Python versions
- `virtualenv` / `venv` — create isolated environments
- `pip` — install packages
- `pip-tools` or `pip freeze` — pin dependency versions
- `Makefile` — wrap common commands

This works, but has real friction: no single lockfile format, `pip freeze` captures everything including transitive deps making diffs noisy, activating virtualenvs manually is error-prone, and onboarding a new developer means following a multi-step setup guide where one wrong step breaks everything.

### mise — tool version manager + task runner

[mise](https://mise.jdx.dev) pins the exact versions of language runtimes and CLI tools per project, defined in `mise.toml`. When you `cd` into the project, you automatically get Python 3.12 and the correct `uv` — not whatever happens to be on the system. No more "works on my machine" from Python version mismatches.

It also replaces `Makefile` for task shortcuts (`mise run dev`, `mise run test`, etc.) with a cleaner syntax and cross-platform compatibility.

**Replaces:** `pyenv`, `Makefile`

### uv — dependency manager + virtualenv

[uv](https://docs.astral.sh/uv) is a single Rust binary that handles everything pip+virtualenv did, 10-100x faster. It reads `pyproject.toml`, auto-creates `.venv`, and writes `uv.lock` — a deterministic lockfile that pins every transitive dependency to exact versions.

`uv run <cmd>` executes commands inside the venv without manual activation, which is what the mise tasks use internally.

**Replaces:** `pip`, `pip-tools`, `virtualenv`, `venv`

### How they fit together

```text
mise         →  which Python, which uv, task aliases
  └── uv     →  which packages, lockfile, .venv
        └── .venv  →  actual installed code
```

`mise install` fetches Python + uv. `mise run install` calls `uv sync`, which reads `pyproject.toml`, writes `uv.lock`, and populates `.venv`. Every subsequent `mise run <task>` calls `uv run` under the hood — no activation needed, always the right environment.

### Commit `uv.lock`, not `requirements.txt`

`uv.lock` is the modern equivalent of a pinned `requirements.txt`, but it's machine-generated, covers all dependency groups (prod + dev), and includes hashes. Commit it. Never manually edit it.

### Tooling diagram

```text
┌─────────────────────────────────────────────────────┐
│                      mise                           │
│         (tool version manager + task runner)        │
│                                                     │
│  mise.toml                                          │
│  ├── [tools]  python = "3.12", uv = "latest"       │
│  │    └── downloads & pins exact binaries           │
│  └── [tasks]  dev, test, lint, migrate...           │
│       └── shortcuts for uv run <cmd>                │
└───────────────────┬─────────────────────────────────┘
                    │ invokes
                    ▼
┌─────────────────────────────────────────────────────┐
│                       uv                            │
│        (dependency manager + venv + lockfile)       │
│                                                     │
│  pyproject.toml                                     │
│  ├── [project.dependencies]   prod packages         │
│  └── [dependency-groups.dev]  dev-only packages     │
│                                                     │
│  uv.lock  ◄── exact versions of every dep (commit)  │
│  .venv/   ◄── local isolated Python environment     │
└───────────────────┬─────────────────────────────────┘
                    │ installs into / runs from
                    ▼
┌─────────────────────────────────────────────────────┐
│                    .venv                            │
│              (isolated environment)                 │
│                                                     │
│  fastapi    sqlalchemy    alembic    httpx           │
│  pydantic   redis         jose       passlib         │
│  pytest     ruff          mypy       ...             │
└─────────────────────────────────────────────────────┘
```

## API Overview

```text
GET /jobs/search              Search jobs across all sources
GET /jobs/{id}                Get full job details
GET /jobs/filters             Available filter options
GET /analytics/trending       Trending skills and locations
GET /analytics/salary-ranges  Salary distribution data
POST /saved-searches          Save a search with email alerts
POST /auth/signup             Create an account
POST /auth/login              Authenticate
```
