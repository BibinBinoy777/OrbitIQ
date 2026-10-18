# Phase 0 completion report

Date: 2026-10-18

## Outcome

Phase 0 is implemented and validated in this environment. The original checkout
was empty. Reinspection for the product-quality requirements found the Phase 0
files created earlier in this same session; these were preserved and extended,
not treated as a new empty checkout. The branch remains the unborn `work` branch.
No deleted-repository assets, databases or results were assumed. No commits,
pushes, deployment or application publication were performed. All Phase 0 project
files below remain untracked. Acceptance criteria and public-launch gates are
defined in `docs/product-foundation.md`.

## Implemented scope

- FastAPI app factory and separate API router with a literal-typed health response.
- React/TypeScript application that displays live backend connection status.
- Same-origin Vite API proxy, configurable backend URL, five-second request
  timeout, and cancellation when the status view unmounts.
- Explicit absolute SQLite database path; no database initialization on API startup.
- Opt-in initialization, integrity/schema validation, SQLite online backups, and
  restoration to a new path. Existing destination files are refused. Initial
  schema creation is an explicit versioned SQL migration; unsupported schema
  versions are rejected without modifying source data.
- Python and frontend tests, linting, formatting, type checking, and production build.
- Python and Node version guidance, locked dependencies, and ignore rules for
  databases, credentials, local configuration, build products, and caches.
- Installation, startup, database, backup, restoration, and check documentation.
- Separate backend/frontend GitHub CI jobs with read-only repository permissions
  and job time limits; no remote CI execution is claimed.
- Scientific provenance requirements, module boundaries, development/test/production
  separation, managed PostgreSQL evaluation and operational launch gates documented.

## Actual checks

| Check | Result |
| --- | --- |
| `uv sync --locked` | Passed, including a clean source copy with no virtual environment |
| `npm ci --no-audit --no-fund` | Passed in clean source copy with final lockfile |
| `uv run --locked pytest` | 6 tests passed, 1 dependency deprecation warning |
| `uv run --locked ruff check .` | Passed after correcting initial import order |
| `uv run --locked ruff format --check .` | Passed on all Python source files |
| `npm test` | 6 tests passed, including actual five-second timeout and caller cancellation |
| `npm run lint` | Passed using final ESLint version |
| `npm run format:check` | Passed after correcting initial formatting |
| `npm run build` | Passed TypeScript check and Vite production build |
| Live backend startup | Passed with current-source process on isolated port 8011 |
| Direct health request on port 8011 | HTTP 200, exact expected health JSON |
| Health request through frontend port 5175 | HTTP 200, exact expected health JSON |
| Frontend HTML request | HTTP 200, expected application entry module |
| SGP4 / Astropy imports | Passed; no orbital validation performed |
| Database CLI temporary init/check/backup/restore | Passed |
| Database CLI existing-path init/restore attempts | Correctly refused; original retained |
| Database automated safety tests | Backup/restore preserved fixture row; existing source unchanged; missing/invalid sources create no destination |
| Clean source copy checks | Both suites, both linters/format checks, frontend type check and build passed |
| CI workflow | YAML parsed locally; command equivalents passed; GitHub run NOT EXECUTED |
| Final `npm audit --audit-level=low` | Passed, zero reported vulnerabilities including development dependencies |
| Ignore rules | Confirmed for .env, .env.local, data, backups, .venv, node_modules and dist |

The clean-copy test used a separate temporary directory without `.git`, `.venv`,
node_modules, or generated builds, then installed from both lockfiles. This
validates source-level reproducibility; a Git-hosted fresh checkout cannot include
these files until a future authorized commit/push. No fresh cloud snapshot
restoration or publication is claimed. Live HTTP requests plus component tests
validate the frontend communication path; no real-browser automation was run.

Database tests created only disposable temporary databases. The checkout contains
no application database and startup does not require one. Test fixture data is
not a satellite observation.

## Tools

Python 3.12.14, uv 0.12.23, Node 24.19.0, npm 11.9.0.
Read-only home-directory cache failures were resolved using `/tmp` cache paths,
without changing TLS, artifact integrity verification, or package signatures.

## Locked direct dependencies

All transitive dependencies are recorded in `uv.lock` and
`frontend/package-lock.json`.

| Python package | Locked version | Use |
| --- | --- | --- |
| fastapi | 0.143.3 | Runtime |
| uvicorn | 0.54.0 | Runtime |
| sgp4 | 2.27 | Runtime |
| astropy | 7.2.3 | Runtime |
| pytest | 9.1.1 | Development |
| httpx | 0.28.1 | Development |
| ruff | 0.17.1 | Development |

| Frontend package | Locked version | Use |
| --- | --- | --- |
| react | 19.3.1 | Runtime |
| react-dom | 19.3.1 | Runtime |
| @eslint/js | 10.0.1 | Development |
| @testing-library/jest-dom | 6.9.1 | Development |
| @testing-library/react | 16.3.3 | Development |
| @types/node | 24.19.2 | Development |
| @types/react | 19.3.0 | Development |
| @types/react-dom | 19.3.0 | Development |
| @vitejs/plugin-react | 5.2.0 | Development |
| eslint | 10.13.0 | Development |
| eslint-plugin-react-hooks | 7.1.1 | Development |
| globals | 16.5.0 | Development |
| jsdom | 26.1.0 | Development |
| prettier | 3.9.10 | Development |
| typescript | 5.9.3 | Development |
| typescript-eslint | 8.71.2 | Development |
| vite | 7.3.7 | Development |
| vitest | 5.0.5 | Development |

## Changed files

The following files comprise the uncommitted Phase 0 foundation. Existing Phase 0
files were preserved and updated where needed; no application database was created
or overwritten. Dependency manifests and lockfiles were unchanged in this review.

- `.env.example`
- `.github/workflows/ci.yml`
- `.gitignore`
- `.nvmrc`
- `.python-version`
- `README.md`
- `backend/orbitiq/__init__.py`
- `backend/orbitiq/api/__init__.py`
- `backend/orbitiq/api/health.py`
- `backend/orbitiq/database.py`
- `backend/orbitiq/main.py`
- `backend/orbitiq/migrations/001_initial.sql`
- `backend/tests/test_foundation.py`
- `docs/phase-0-report.md`
- `docs/product-foundation.md`
- `frontend/.prettierignore`
- `frontend/eslint.config.js`
- `frontend/index.html`
- `frontend/package-lock.json`
- `frontend/package.json`
- `frontend/src/App.test.tsx`
- `frontend/src/App.tsx`
- `frontend/src/api.ts`
- `frontend/src/main.tsx`
- `frontend/src/style.css`
- `frontend/src/test-setup.ts`
- `frontend/tsconfig.json`
- `frontend/vite.config.ts`
- `pyproject.toml`
- `uv.lock`

## Reusable cloud configuration

Saved `install_script` and `start_skill` to the environment configuration draft.
They contain locked install commands, working directories, service restart and
health checks, explicit database handling, and the existing-checkout guidance.
The draft save does not execute or publish the configuration. Environment settings
must be reviewed/saved and the environment published by the user to activate a
snapshot; the OrbitIQ application has not been published or deployed.

## Remaining issues and limits

- Starlette warns that its HTTPX-backed TestClient is deprecated in favor of
  httpx2. Current tests execute and pass; no warning was suppressed.
- jsdom brings a deprecated `whatwg-encoding` dependency. Final npm audit reports
  no vulnerabilities. Initial test-tool advisories were resolved by upgrading
  Vitest to 5 and ESLint to supported version 10 and regenerating the lockfile.
- No Python vulnerability scanner was run; import/test success is not a security
  audit. The zero-vulnerability result above applies to npm's reported audit.
- Health indicates service liveness only. Persistence is deliberately not wired
  into the API yet. SQLite schema version 1 contains only schema metadata.
- No CelesTrak ingestion, SGP4 calculations, Astropy coordinate transformations,
  satellite snapshots, historical comparisons, 3D explorer, or AI features exist
  yet. Their correctness requires separate implementation and scientific tests.
- The initial migration is implemented; upgrades of existing databases require
  a future explicit migration command and tests before a schema change ships.
- No production hosting/routing configuration or browser end-to-end suite was
  added. GitHub CI is configured but has not run remotely. Managed PostgreSQL,
  durable storage, production backups, observability and public security controls
  remain documented launch gates, not verified capabilities. Phase 1 has not started.
- Frontend cancellation/timeout uses modern AbortSignal browser APIs; compatibility
  and accessibility in real browsers have not been audited.

## Failures investigated during this review

One frontend command was initially invoked from the repository root, which has no
package.json; it failed before tests ran. It was rerun from `frontend/` and all
checks passed. No failure was relabeled as a pass. No dependencies were added or
updated during this requirements review.
