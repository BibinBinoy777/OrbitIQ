# Pre-Phase 5: scientific-data readiness and controlled EOP maintenance

## Outcome and baseline

Implemented the backend readiness API, responsive dashboard and explicit
package-managed EOP acquisition/validation/selection/rollback workflow. **All 22
acceptance criteria pass within the documented local scope.** Production
operations and the unknown metadata listed below remain explicit limitations,
not claimed launch readiness. No Phase 5 historical investigation was started.

Engineering review: **2026-10-19 IST**. Science/verification artifacts retain UTC.
The repository began clean on `main` at `8bf431c`, with the earlier authorized
Phase 4 publication present. Read Phase 3/4 reports and inspected routes, schema,
storage, lockfiles, resource loading, strict policy, transformations/tracks,
React state/clients and testing conventions before implementation. Baseline
rerun: **268 backend tests and 96 frontend tests passed**. No deleted historical
repository, missing backup or old result was assumed available.

Existing real DB: schema **2**, **one ISS snapshot**, integrity **ok**, SHA-256
`c389d0f1d663957be70a32f846f8e968e70a4f46c37343a5b80ceca5954e5f59`.
The source snapshot has catalog **25544**, ID **1**, orbital epoch
`2026-10-18T11:12:47.040768+00:00`, retrieval
`2026-10-18T17:14:39.983172+00:00`, response SHA-256
`556827b7dc6cbccd0cbc3e40a9e0a0ed2205ad2d2006a8649e16ee8c0c143d4b`.
No new satellite ingestion or fabricated observation was introduced.

The implementation plan was recorded before coding in
[pre-phase-5-plan.md](pre-phase-5-plan.md). The latest uploaded mission governs
this task: no commit, push, deployment, publication or remote changes.

## Architecture and scientific-resource lifecycle

- Existing `GET /api/health` is a process liveness check with no DB dependency.
  The new `GET /api/readiness` is a separate informational assessment.
- SQLite uses an explicit absolute path. The snapshots table has immutable source
  payload/provenance, orbital epoch and retrieval time, but **no separate insertion
  time, persistent ingestion-failure history or global retrieval-time index**.
- Existing `earth_orientation.resources()` loads explicit installed paths supplied
  by `astropy_iers_data`, parses IERS-A/leap data, records SHA-256 and caches per
  process. No external runtime resource directory was assumed or created.
- `orientation()` serializes Astropy global context, disables auto-download and
  remote leap URLs, selects local leap/EOP data and forbids degraded accuracy.
  `parameters()` applies finite/source/coverage, ±0.5-second support, leap-expiry,
  measured-only and 30-day prediction-table-age guards. Equations, tolerances,
  policy and scientific loader were **not changed**.
- Coordinate and ground-track services still calculate on the backend. The
  frontend receives calculated positions and scientific metadata; no orbital
  calculation moved to JavaScript. Existing globe/map/timeline/source UI remains.
- Python pins remain **Astropy 7.2.3**, **astropy-iers-data
  0.2026.10.12.1.3.27**, **pyerfa 2.0.1.5**, **sgp4 2.27**. All dependency manifests
  and both lockfiles are byte-identical to HEAD. No dependencies were added or
  upgraded merely to obtain newer releases or suppress warnings.

Current bundled EOP identity/coverage:

| Fact | Actual value |
| --- | --- |
| First / last central epoch | 1973-01-02 UTC / 2027-10-04 UTC |
| First predicted MJD / UTC | 61315 / 2026-10-02 |
| EOP / leap rows | 19,999 / 28 |
| EOP SHA-256 | `9fbc14ae5e71de96cc1e6b43b54a547acc80c7a6ce910c0209ad6230ff3d30cd` |
| Leap SHA-256 | `6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7` |
| Parsed leap source expiry label / scale | `2027-06-28` / TAI |
| Effective existing policy cutoff in UTC | `2027-06-27T23:59:23+00:00`, plus velocity support guard |
| Package release timestamp | Not recorded; unknown, not inferred from version |

The leap scale detail was established from actual Astropy objects. Readiness
normalizes the instant while showing the source label/scale; it preserves the
existing conservative calculation policy rather than silently shifting it.

## Implemented behavior and contracts

`GET /api/readiness?at=<optional aware ISO time>` returns a typed HTTP 200
assessment with overall/component status, actual evaluation/requested UTC times,
explicit scope and `automatic_updates: false`. Bad times return the existing safe
422 contract. Successful assessments are `no-store`. Four sections report:

1. DB reachability, required schema/read support and newest inserted record's
   actual retrieval metadata, never a fabricated insertion timestamp.
2. Orbital data presence and genuine latest retrieval/epoch freshness when known.
   Epoch and retrieval age remain separate; defaults remain 24/72 hours.
3. EOP package/hash/coverage/prediction boundary, requested support/policy result,
   prediction-table age and separately unknown release age. Matching local
   operator receipts optionally provide actual acquisition/verification/selection
   times; absence/mismatch stays unknown.
4. Real leap source/version/hash, parsed expiry scale/UTC instant, requested-time
   support and current-time expiry. Missing validity is explicitly unknown.

Statuses mean `healthy` supported checks passed, `degraded` usable-with-warning
or missing/aging data, `unavailable` required check failed, `unknown` insufficient
metadata. Overall precedence is unavailable > unknown > degraded > healthy.
Readiness is neither an observation nor an orbit-accuracy guarantee. Per-operation
scientific validation is unchanged. See the full
[API/status/time contract](scientific-data-readiness.md).

The read-only SQL query examines at most **101 metadata rows**, retaining **100**,
with instruction/time/busy budgets. It reads no raw payload, full count, archive
integrity or unindexed timestamp sort. For complete small histories it computes
max actual retrieval time independently of insertion order. For larger/invalid
histories it explicitly withholds global latest/freshness. This avoids an
unbounded scan and a false claim of global recency; scaling that metadata is a
future explicit schema/storage task.

The dashboard has four semantic cards plus overall status, labelled UTC times,
coverage/freshness/source details, text indicators, optional calculation epoch,
manual refresh, loading, error/retry, partial-section handling, cancellation and
five-second request timeout. It links back to the preserved explorer. No timer,
decorative chart, maintenance HTTP route, admin UI or uncontrolled update exists.
Desktop/tablet use two columns above 800 px; mobile uses one.

## Maintenance and rollback

The operator-only `orbitiq.maintenance.eop` CLI follows the installed package
lifecycle. `prepare` exclusively creates an isolated backend source/environment
outside the checkout, uses official PyPI and uv to pin one exact supported
astropy-iers-data version, rejects changes to any other locked package version,
and records source/lock/resource identities and acquisition UTC.

`validate` requires complete bounded parseable files, finite/unit-correct daily
EOP coverage, known provenance/prediction metadata, coherent leaps, strict
out-of-range checks, actual application loading/current-time policy, full backend
tests and the 40/6 numerical audits. Failed latest validation cannot reuse an
older passing receipt. Source/lock/resource tampering prevents selection.

`activate` atomically selects a validated environment through a protected operator
manifest. It preserves prior selection/history, re-verifies the new selection
and automatically restores the prior state on activation verification or
bookkeeping failure. Explicit `rollback` restores a retained validated selection.
No installed active files or orbital DB are overwritten. Existing stale previous
resources can still be retained/identified for rollback; this never waives
current-time guards on new candidates or subsequent calculations.

Selection **does not restart or deploy a server**. Actual worker handoff remains
an explicit operator action using the selected Python/backend paths. A matching
receipt alone is not proof that every worker restarted. Full operator commands,
trust assumptions, interruption recovery and non-deploying local startup example
are in [eop-maintenance.md](eop-maintenance.md).

The actual rehearsal acquired **two fresh candidates at the existing exact pin**,
validated both, selected A then B, explicitly rolled back to A, verified status
and exercised the selected API/receipt in TestClient. The root server/environment
was unchanged. Both candidate source/lock digests matched. Fault injection stayed
in temporary tests: acquisition failure, truncation/units/metadata/coverage,
reference/suite failure, tampering, unvalidated selection, lock conflicts,
post-selection verification, atomic replace and bookkeeping failure.

Final test review also made prediction-boundary/expiry assertions derive from
actual resource metadata rather than assuming this one package's release dates.
That preserves meaningful policy checks when a reviewed supported version is
intentionally acquired. A final isolated candidate was acquired and fully
validated against the resulting final backend/test source; its provenance is
recorded with the earlier A/B lifecycle evidence.

## Verification commands and actual results

Commands ran in `/workspace/OrbitIQ` unless noted. Environment-specific writable
cache overrides were `UV_CACHE_DIR=/tmp/orbitiq-uv-cache` and
`npm_config_cache=/tmp/orbitiq-npm-cache`; TLS/proxy verification was retained.

| Executed command/check | Actual result |
| --- | --- |
| Baseline `uv run --locked pytest -q` | 268 passed |
| Baseline `cd frontend`, `npm test` | 96 passed |
| Final `uv run --locked pytest -q` | **337 passed**, one known TestClient deprecation |
| `uv run --locked ruff check .` | PASS |
| `uv run --locked ruff format --check .` | PASS |
| `cd frontend`, `npm test` | **125 passed**, 13 files |
| `cd frontend`, `npm run lint` | PASS |
| `cd frontend`, `npm run format:check` | PASS |
| `cd frontend`, `npm run build` | PASS, TypeScript noEmit + Vite production build |
| `PYTHONPATH=backend uv run --locked python scripts/verify_scientific_references.py --output /tmp/orbitiq-readiness-sgp4.json` | **40 passed, 0 failed** |
| `PYTHONPATH=backend uv run --locked python scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-readiness-earth-fixed.json` | **6 passed, 0 failed** |
| Fresh source-only frontend copy: `npm ci`, `npm run build` | PASS, 248 packages installed, build completed |
| Candidate `uv sync --locked` and complete validation | PASS, fresh isolated environments; no orbital DB copied |
| Explicit read-only DB `check`, `verify-archive` | PASS, integrity ok / one real snapshot |
| Before/after byte SHA-256/schema/count/integrity | Identical; no data rewritten |
| `git diff --exit-code HEAD -- pyproject.toml uv.lock frontend/package.json frontend/package-lock.json` | PASS, dependency files unchanged |
| `git diff --check` | PASS |
| Actual HTTP/Vite proxy and Chromium browser | PASS; details below |
| Remote CI, public hosting, production host-loss recovery | **NOT RUN / NOT CLAIMED** |

New tests: **69 backend** (43 readiness/API and 26 operator/probe cases) and
**29 frontend**. They cover missing/invalid/schema/empty DB, out-of-order genuine
retrieval metadata, bounded large histories, age thresholds/future timestamps,
resource metadata/coverage/prediction/leap boundaries, safe partial errors,
no automatic maintenance/download, receipt mismatch, operator faults/provenance,
loading, all four statuses, stale/missing/partial data, retry, time editing,
cancellation, timeout and native keyboard control semantics. Temporary metadata
fixtures are clearly labelled test-only, never real satellite observations.

Exact rehearsal commands (each returned exit 0):

```sh
export PYTHONPATH=backend
export UV_CACHE_DIR=/tmp/orbitiq-uv-cache
uv run --locked python -m orbitiq.maintenance.eop prepare --destination /tmp/orbitiq-eop-rehearsal-a --version 0.2026.10.12.1.3.27
uv run --locked python -m orbitiq.maintenance.eop validate --candidate /tmp/orbitiq-eop-rehearsal-a
uv run --locked python -m orbitiq.maintenance.eop prepare --destination /tmp/orbitiq-eop-rehearsal-b --version 0.2026.10.12.1.3.27
uv run --locked python -m orbitiq.maintenance.eop validate --candidate /tmp/orbitiq-eop-rehearsal-b
uv run --locked python -m orbitiq.maintenance.eop activate --candidate /tmp/orbitiq-eop-rehearsal-a --state /tmp/orbitiq-eop-rehearsal-state
uv run --locked python -m orbitiq.maintenance.eop activate --candidate /tmp/orbitiq-eop-rehearsal-b --state /tmp/orbitiq-eop-rehearsal-state
uv run --locked python -m orbitiq.maintenance.eop rollback --state /tmp/orbitiq-eop-rehearsal-state
uv run --locked python -m orbitiq.maintenance.eop status --state /tmp/orbitiq-eop-rehearsal-state
uv run --locked python -m orbitiq.maintenance.eop prepare --destination /tmp/orbitiq-eop-rehearsal-final --version 0.2026.10.12.1.3.27
uv run --locked python -m orbitiq.maintenance.eop validate --candidate /tmp/orbitiq-eop-rehearsal-final
```

Existing Starlette/HTTPX and npm `whatwg-encoding` deprecations remain visible.
The existing lazy Three renderer chunk is **555.74 kB**, above Vite's 500 kB
warning threshold; main JavaScript is 265.50 kB. No check was suppressed or
scientific tolerance changed. Early test-fixture issues (round-off expectation
and replacing an Astropy unit column) were corrected; final suites passed.

## Actual integration evidence

Started only local verification processes:

```sh
ORBITIQ_DATABASE_PATH=/workspace/OrbitIQ/data/orbitiq.sqlite3 UV_CACHE_DIR=/tmp/orbitiq-uv-cache uv run --locked uvicorn orbitiq.main:app --app-dir backend --host 127.0.0.1 --port 8041
# Separate terminal, frontend directory:
ORBITIQ_BACKEND_URL=http://127.0.0.1:8041 npm_config_cache=/tmp/orbitiq-npm-cache npm run dev -- --host 127.0.0.1 --port 5191 --strictPort
```

`python /tmp/orbitiq_readiness_integration.py` exercised actual HTTP through Vite
and Chromium **154.0.8037.57** using the available Playwright runtime and software
WebGL. No server response/canvas was mocked in this browser run. Requested:

- `/api/health`: original successful liveness response.
- `/api/readiness`: DB healthy, orbital data fresh, EOP degraded/predicted, leap
  healthy; overall degraded truthfully. Warm request took about **19 ms** in this
  run, not a latency SLO or a concurrency benchmark.
- Historical readiness `2004-04-06T07:51:28.386Z`: measured EOP healthy.
- Requested `2028-01-01T00:00:00Z`: unavailable, outside EOP/leap policy.
- Existing actual snapshot-1 **91-point** ITRS ground track over its epoch plus
  90 minutes: complete, preserving the scientific backend path.

Viewports **1440×1000**, **820×1180**, **390×844** passed four-card/status/date
rendering, responsive grid, manual refresh, time edit clearing, historical and
unsupported epochs, invalid input, keyboard Tab/focus, no horizontal overflow
and return to actual stored ISS exploration. **Zero JavaScript page errors and
zero external browser requests.** Desktop/mobile screenshots were inspected.
The first harness run waited for a control inside a collapsed provenance panel;
opening it fixed that harness expectation. App behavior was not weakened.
This task does not repeat every Phase 4 graphics benchmark or establish a device
matrix, physical GPU performance, screen-reader certification or public hosting.

[Machine-readable evidence](pre-phase-5-integration-results.json) contains actual
UTC response metadata, values, browser checks, acquisition/validation/selection
receipts, reference totals and preservation fingerprints. Mocked fault/presentation
tests and actual HTTP/rehearsal evidence are labelled separately. Original phase
artifacts remain untouched. Rehearsal receipts/reference outputs and screenshots
are in temporary workspace storage, not a durable production archive.

## Acceptance criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Architecture/resource lifecycle inspected | **PASS** | Baseline inspection, plan, package-managed loader findings above |
| 2 | Readiness separate from liveness | **PASS** | Separate typed route; liveness with missing/failed DB tested |
| 3 | DB reports supported facts accurately | **PASS** | Read-only schema/read tests; actual existing DB response |
| 4 | Genuine orbital timestamps/freshness | **PASS** | Stored epoch/retrieval, boundary/out-of-order/future/large-history tests |
| 5 | Coverage/prediction/freshness separated | **PASS** | Metadata-derived boundaries, strict parameters, release age explicitly unknown |
| 6 | Truthful leap metadata | **PASS** | Actual parsed TAI label/UTC cutoff; unknown/expired/history tests |
| 7 | Bounded safe endpoint | **PASS** | LIMIT 101/100, VM/time budget, safe exceptions, no-store, no paths/payloads |
| 8 | Responsive readiness dashboard | **PASS** | Implemented UI, automated tests, three actual viewports |
| 9 | Status/time semantics documented | **PASS** | Readiness contract and explicit units/time scales |
| 10 | Controlled acquisition | **PASS** | Actual isolated official-source same-pin acquisitions via uv |
| 11 | Validation before activation | **PASS** | Real full candidate suites/audits; rejected invalid/unvalidated candidates |
| 12 | Failed updates preserve working resource | **PASS** | Injected acquisition/validation/replace/verification/bookkeeping faults |
| 13 | Documented/tested rollback | **PASS** | Real A→B→A selection, fault restoration, operator runbook |
| 14 | Accepted update provenance | **PASS** | Acquisition/source/lock/EOP/leap digests and actual UTC validation/selection receipts |
| 15 | No ordinary-request refresh | **PASS** | No CLI call path; download/maintenance tripwire tests; offline existing context |
| 16 | Strict out-of-coverage preserved | **PASS** | Existing scientific code unchanged; numerical/policy/boundary regressions and actual out-of-range response |
| 17 | Reference/existing tests pass | **PASS** | Full 337/125 suites; 40/6 audits |
| 18 | Orbital data preserved | **PASS** | Byte-identical DB hash, schema/count/integrity/archive verification |
| 19 | New tests pass | **PASS** | 69 new backend / 29 new frontend cases included in green suites |
| 20 | Quality/type/build checks pass | **PASS** | Ruff, ESLint, Prettier, TypeScript, Vite; fresh locked installs |
| 21 | Coverage/leap gaps documented | **PASS** | Limitations below and API/runbook; unknowns not invented |
| 22 | Evidence-backed final report | **PASS** | This report plus required documentation and actual integration JSON |

No requested criterion is marked FAIL or BLOCKED. These results apply to the
implemented informational API and local controlled maintenance workflow, not a
claim that public deployment, durable recovery or every date is scientifically
ready.

## Changed files

New:

- `backend/orbitiq/api/readiness.py`: typed informational route.
- `backend/orbitiq/services/readiness.py`: bounded DB and actual scientific policy
  assessment; optional matching receipt metadata.
- `backend/orbitiq/maintenance/__init__.py`, `eop.py`, `probe.py`: isolated operator
  workflow, structural/current-policy checks, provenance and atomic selection.
- `backend/tests/test_readiness.py`, `test_eop_maintenance.py`: API/policy/read-only
  and isolated maintenance fault/provenance tests.
- `frontend/src/ReadinessDashboard.tsx`, `readiness-api.ts`: page and bounded fetch/
  partial contract parsing.
- `frontend/src/ReadinessDashboard.test.tsx`, `readiness-api.test.ts`,
  `test-fixtures/readiness.ts`: presentation/API tests with labelled synthetic data.
- `docs/pre-phase-5-plan.md`, `scientific-data-readiness.md`, `eop-maintenance.md`,
  `pre-phase-5-readiness-report.md`, `pre-phase-5-integration-results.json`.

Modified: `backend/orbitiq/main.py` (router registration), `frontend/src/App.tsx`
(view navigation), `frontend/src/style.css` (responsive/status presentation),
`.env.example` (optional verification receipt path), `README.md` (feature/runbook
links). No scientific equation/loader, database schema, dependency/lock, CI workflow
or original phase evidence file was modified.

## Remaining scientific and operational limits

- Readiness of an archive larger than 100 insertions deliberately cannot assert
  global latest retrieval. Add reviewed indexed/maintained recency metadata before
  scaling this guarantee; invalid timestamps remain unknown.
- Insertion time, persistent source/ingestion failure history and actual upstream
  release times are absent. No source network availability or full archive
  provenance/integrity is implied by readiness; explicit archive checks remain.
- Predictions are labelled, limited by 30-day table-age policy, not independently
  measured orbit error. An in-range central epoch alone is insufficient: support
  samples, leap validity, configured policy and per-calculation guards still apply.
- Parsed leap expiry is known for this package, with the conservative existing
  TAI/UTC cutoff explicitly exposed. No post-expiry validity, future leap knowledge
  or timeless EOP availability is claimed. Refresh deliberately when necessary.
- Same-pin rehearsal proves the procedure, not improved/new scientific data.
  Trusted reference agreement is finite validation, not certification of arbitrary
  future resources or observation accuracy. New releases require explicit review.
- Operator manifests assume protected durable storage and trusted writers. Atomic
  individual file rename is not a distributed transaction or host-power-loss
  guarantee. A retained stale previous resource is not automatically current-ready.
  Multi-worker process handoff, recovery drills, receipt archival/retention and
  crash interruption recovery remain launch work.
- This read-only API uses no privileged maintenance HTTP access. Authentication,
  authorization for protected functions, rate limiting, concurrency/load testing,
  monitoring/alerts and scheduling remain explicit public-launch evaluations.
- Root DB and rehearsal data reside on a cloud-task filesystem; persistence beyond
  this task is not a production storage plan. Preserve backups separately and
  evaluate managed PostgreSQL before public launch. Existing safe DB backup/restore
  routines are unchanged and covered by the regression suite; no live restore or
  overwrite was performed here.
- Remote CI and public deployment were not triggered or verified. Existing
  deprecation/bundle warnings remain. Browser results concern tested local
  viewports/runtime only.

Nothing was staged, committed, pushed, deployed or published. Repository remotes
were not modified. Existing orbital data and historical phase artifacts were
preserved. Stop here before Phase 5.
