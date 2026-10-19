# Phase 5: satellite discovery and historical investigation

## Outcome and verified scope

Implemented stored-satellite discovery, complete cursor-based historical browsing,
direct source access, two-snapshot record/element/common-time state comparisons,
and integration with the existing explorer and globe. The implementation uses
existing storage, SGP4, Astropy, freshness, provenance and EOP policies. No new
runtime dependency, database migration, external ingestion, AI feature or future
phase was added.

Engineering review date: **2026-10-19 IST**; scientific timestamps remain explicit
UTC. The 27 requested acceptance criteria are assessed below against actual tests
and integration evidence. The application archive contains **one genuine ISS
snapshot**. Distinct genuine historical-pair validation is therefore **BLOCKED by
insufficient stored data**. This is a data-evidence limitation, not a fabricated
second record or a claimed historical finding. Separate, clearly labelled
reference-derived fixtures exercise multi-snapshot functionality without entering
the application's database.

Nothing was committed, pushed, deployed, published or staged. Repository remotes
were not changed. Prior uncommitted readiness/maintenance work was preserved.

## Inspection and baseline

Inspected the Phase 1–4 and pre-Phase 5 reports/evidence, readiness semantics,
maintenance runbook, ingestion and deduplication, schema/triggers, history/detail
routes, API errors/types, scientific services/guards, local React navigation,
source selection, globe, ground-track/timeline clients and tests. The plan was
recorded in [phase-5-plan.md](phase-5-plan.md) before implementation.

Git began on `main` at `8bf431c`, with the 22 files of completed pre-Phase 5 work
still uncommitted. The baseline rerun passed **337 backend / 125 frontend tests**.
No missing historical repository, database, backup or old test result was assumed.

The configured existing archive was inspected read-only: schema **2**, integrity
**ok**, **one** snapshot, byte SHA-256
`c389d0f1d663957be70a32f846f8e968e70a4f46c37343a5b80ceca5954e5f59`.
Source ID **1**, NORAD **25544**, epoch
`2026-10-18T11:12:47.040768+00:00`, retrieval
`2026-10-18T17:14:39.983172+00:00`, source response SHA-256
`556827b7dc6cbccd0cbc3e40a9e0a0ed2205ad2d2006a8649e16ee8c0c143d4b`.

## Historical model and the 100-record question

A schema-2 snapshot is **one satellite OMM record**, not a multi-satellite catalog
batch. Ingestion requests one NORAD ID and saves one immutable source response,
record, normalized elements, units and provenance. The unique integer snapshot
ID identifies that retrieval record. Repeated byte-identical responses for the
same satellite/source deduplicate to the retained existing snapshot; their later
retrieval attempts are not separate historical events.

The earlier `/api/satellites/{catalog_id}/snapshots` route already accepted
`before_id` and `limit` 1–100. The 100 limit was a **page cap**, not deletion or a
claim that only 100 snapshots existed. Its frontend loaded only 20, and its
response lacked continuation/count semantics. Independent `/api/snapshots/{id}`
and propagation routes already loaded older IDs without history-list membership.
The readiness service's separate 100-row assessment limitation was never a
storage/history limit and is deliberately unchanged.

Phase 5 adds accurate page envelopes and global browsing. The old optional-cursor
SQL predicate is now an explicit indexed `id < ?` range, with the bounded read
context; a query-plan test verifies catalog/index range use in an archive larger
than 1,000 snapshots. Legacy history response fields are extended additively,
with an updated exact empty-response contract test. Existing summaries/scientific
behavior remain available.

Insertion ID order does **not** establish retrieval or element-epoch chronology.
Separate insertion time, ingestion-attempt/failure history and catalog-wide batch
identity were never recorded. They cannot be recovered retrospectively without
additional trustworthy evidence; no migration/backfill invents them. Retrieval
and element epoch remain distinct, validated aware timestamps when present.

## API contracts and bounded work

All new endpoints are read-only GET requests, follow existing safe 404/422/503
error conventions and send `Cache-Control: no-store`. No admin/update endpoint
exists. SQL uses parameterized identifiers/cursors, fixed query fragments and no
user SQL wildcard interpolation.

| Endpoint | Contract |
| --- | --- |
| `GET /api/snapshots` | Global/filterable keyset history; metadata remains inspectable when scientific provenance is invalid. |
| `GET /api/discovery/satellites` | Same bounded stored-record query contract; name/NORAD/international-designator discovery, retaining historical duplicates. |
| `GET /api/satellites/{catalog_id}/snapshots` | Existing strict per-catalog history, now with lookahead, `has_more`, `next_before_id`, explicit ID order and uncomputed-count status. |
| `GET /api/snapshots/{snapshot_id}` | Existing independent strict source detail; provenance validation is retained. |
| `GET /api/comparisons` | Two fixed source IDs, classification, canonical element differences, provenance/chronology and optional common-time states. |

Listing query parameters:

- `q`: at most 64 printable characters, trimmed; literal exact/partial
  case-insensitive matching against stored name, NORAD text and supported normalized
  `OBJECT_ID`. Blank means browse. No request fetches external satellite data.
- `match`: `exact` or `partial`; `limit`: 1–100, default 20.
- `catalog_id`: optional NORAD filter, 1–339999.
- `snapshot_id`: optional direct snapshot filter; zero results means not found.
- `context_snapshot_id`: optional existing source context; missing context is 404.
  `selected_only=true` requires that context and rejects a conflicting direct ID.
- `before_id`, `anchor_id`: positive signed-64-bit snapshot cursors. An inconsistent
  cursor above its anchor is 422. Frontend IDs must also be safe JavaScript integers.

The first page captures a high-water insertion ID. Continuation carries that
anchor and an exclusive `before_id`, excluding subsequently appended records
above the anchor. Global/filtered queries use primary/catalog index ranges, no
OFFSET, full COUNT, unindexed timestamp ordering or full-history name scan.
Search inspects at most **250** candidate rows plus one lookahead; non-search
pages read only the requested page plus one. Metadata columns have explicit
substring bounds, including at most 8,193 normalized JSON characters (oversized
or malformed JSON is not treated as reliable metadata).

Each browsing transaction is query-only with a **250 ms** busy timeout and a
**50,000 VM-instruction / 250 ms** progress budget checked every 100 instructions.
Budget exhaustion returns a safe storage error; it is not misreported as an
empty/complete history. These are query-work limits, not a production latency SLO.

The envelope includes `snapshots`, actual `evaluated_at`, `order`, `anchor_id`,
`has_more`, `next_before_id`, `returned_count`, `scanned_count`, `scan_limit`,
`total_count`, `total_count_status`, `count_bound`, context and warnings.
An empty matching window can still have `has_more=true`; continue the cursor rather
than declaring the satellite absent. Pages never infer the globally oldest or
latest retrieval from ID order.

Counts are exact **within the anchor and non-text filters** only when the bounded
ID probe establishes at most **1,000** eligible snapshots. Above that, total is
null/`unknown_exceeds_bounded_count`; text-search totals are explicitly null/
`not_computed_for_search`. Cursor browsing still reaches the complete archive.
Counts mean stored single-record snapshots, not unique satellites or physical
objects in orbit. Existing per-catalog history leaves its total uncomputed and
points to the richer global browser. These semantics are tested with **1,004**
fixture snapshots, nonmatching scan windows, filters and newly appended records.

## Discovery, detail and source identity

Results display stored name, NORAD, international designator, snapshot ID,
epoch/retrieval, freshness/evaluation time, source, validator/model version,
validation metadata and missing-field explanations. Listing validation is explicitly
**metadata-only**, not a full source-byte/provenance audit. Public source links are
restricted to the supported credential-free CelesTrak GP provenance; unsafe URLs,
private paths and raw exception details are withheld.

Membership distinguishes the selected snapshot's record, historical records whose
satellite is also in that snapshot, historical-only satellites and unreliable or
unknown catalog identity. Missing names do not invalidate a scientifically valid
NORAD source. Missing/inconsistent NORAD linkage is disclosed and is never replaced
by a name match. An international designator can be searched, but comparison
matching uses validated NORAD identity; identical names/designators for different
NORADs are not paired.

Direct snapshot-ID access works independently of any page. Inspecting a source
reuses the strict existing detail endpoint and exposes canonical elements/units,
source epoch/retrieval/hash and provenance. A failed scientific detail read retains
safe listing metadata and offers retry; it never substitutes the newest source.
Searches leave an already inspected historical source fixed until explicitly
changed. Reloading that catalog in the existing explorer also preserves the
selected historical ID; if it is outside the bounded history page, it is retained
separately with an explicit notice and scientific requests recheck availability. Element freshness retains the established 24/72-hour policy and does not
convert recent retrieval into observational accuracy.

## Comparison semantics and scientific safeguards

`GET /api/comparisons?first_id=A&second_id=B` accepts two existing source IDs.
Optional `category` is `all`, `shared`, `added`, `removed` or `incompatible`;
optional `at` is an aware ISO timestamp and `frame` is TEME (default) or ITRS.
At most **two** source records and **two** propagated states are evaluated. No
trajectory sampling is added to this route.

Because snapshots each contain one satellite record, comparisons can contain one
shared record or one first-only and one second-only record. Missing/invalid
scientific provenance or identifiers are explicitly incompatible. Counts describe
the complete pair; category filtering changes displayed records, not those counts.
Both selected source summaries, source errors and provenance/epoch differences
remain available. A self-comparison is explicitly labelled a self-check, never
a distinct historical pair.

Retrieval chronology is `ordered`, `ambiguous_equal_retrieval_times`, or `unknown`.
Older/newer IDs are populated only from valid distinct retrieval instants; inputs
remain in selected A/B order. Chronology does not imply physical change time.
`added` means only in B and `removed` only in A, independent of older/newer order;
these are dataset differences, not launches, decay or absence from orbit.

Shared records use the existing complete `validate_snapshot` linkage: source
bytes/hash, exactly one raw record, normalized elements/units, catalog/epoch and
supported provenance. Invalid/missing/incompatible fields never yield invented
numeric differences. Numeric overflow withholds element subtraction while retaining
source/record inspection. Canonical unit definitions remain unchanged:

- Mean motion rev/day; eccentricity dimensionless; inclination deg.
- RAAN, argument of pericenter and mean anomaly deg, wrapped B−A into **[−180,180)**.
  Inclination uses ordinary subtraction, not cyclic wrap.
- BSTAR 1/Earth-radii; mean-motion derivatives rev/day² and rev/day³; revolution
  count rev. Epochs are shown separately with each source, not subtracted as angles.

Element sets can differ because of epochs, fitting and source updates. They are
not direct measurements of physical orbital changes. The mandated maneuver/anomaly
caution is displayed next to the results.

When `at` is supplied for a compatible shared NORAD, the service reuses
`analysis.position_from_snapshot` for each validated fixed source at the **same
UTC instant**, including microseconds. Existing SGP4/WGS72 and ±7-day epoch guards
remain. ITRS additionally reuses `earth_fixed`, strict local EOP/leap coverage,
prediction-age/measured-only policies, finite checks and leap-crossing rejection.
Both transformed states must use consistent EOP/leap resource hashes/version/policy.
No ordinary request refreshes any resource.

Before subtraction the service checks identity, source hash/epoch/retrieval,
model, origin, exact evaluation time, frame, units and finite 3-vectors. It returns
B−A Cartesian position (km) and velocity (km/s), position-vector separation and
velocity-difference magnitude. These are differences between calculated models,
not covariance, observational residuals, collision claims or proof of anomalies.
Source epochs, actual calculation execution times, frames, units, source IDs and
assumptions remain visible. Different-time/frame/unit/source or non-finite output
cannot produce a difference. If one/both state calculations fail, errors and any
independently valid backend states are retained without a fabricated fallback;
record/element inspection remains usable.

## Frontend and existing explorer integration

**Discovery & history** adds lazy-loaded stored-data tools within the existing
local React navigation: search/context filters, cursor history/previous/restart,
direct ID detail and fixed A/B comparison controls. Loading, empty-with-continuation,
safe errors/retry, stale data, missing metadata, partial scientific failures and
cancellation are explicit. Editing comparison inputs clears old results/markers;
late or aborted responses cannot restore stale data. Requests have a ten-second
client timeout. No polling, implicit external ingestion or background comparison
is introduced.

Source links open the **exact selected snapshot** in `ScientificExplorer`, reusing
its `GroundTrack`, source details and exact-sample timeline. The latest-history
endpoint is not requested during this handoff. Return navigation retains comparison
IDs, requested time, result and search/detail context in memory. Reloading the
page does not persist this local investigation state; there is no new routing or
state-storage framework.

Valid common-time ITRS comparisons reuse the existing lazy Three renderer with
two **disconnected** markers: A sphere and B diamond, explicit source labels and
one Earth-relative scale. No line between them is called a trajectory. TEME stays
numerical until a supported ITRS request succeeds. Markers can overlap or be
occluded by Earth; their sizes are illustrative and numeric values authoritative.
The existing 400-Earth-radius display extent is retained; unsupported rendering
never removes independently valid numerical results. The existing per-source track/map/timeline remains available through source
navigation, rather than inventing a historical trajectory between two states.

Semantic tables/headings/regions, labelled inputs, native keyboard controls,
visible focus and text/shape differences avoid colour-only meaning. Comparison
source columns collapse below 800 px; long tables scroll in labelled keyboard-
focusable regions rather than overflowing the document. Missing WebGL/context
loss leaves numerical comparison and source metadata available. Physical GPU
performance, a full assistive-technology audit and browser-engine matrix remain
outside this local verification.

## Verification commands and actual results

Commands ran in the repository root unless `frontend` is specified. The writable
cache overrides were `UV_CACHE_DIR=/tmp/orbitiq-uv-cache` and
`npm_config_cache=/tmp/orbitiq-npm-cache`; standard TLS/proxy trust was preserved.

| Executed check | Actual result |
| --- | --- |
| Baseline `uv run --locked pytest -q` | 337 passed |
| Baseline `cd frontend`, `npm test` | 125 passed |
| Final `uv run --locked pytest -q` | **398 passed**, known TestClient deprecation only |
| Phase 5 cases included in the final full backend suite | **61 Phase 5 cases**, included in the final suite |
| `uv run --locked ruff check .` | PASS |
| `uv run --locked ruff format --check .` | PASS |
| Final `cd frontend`, `npm test` | **172 passed**, 15 files |
| `npm run lint` / `npm run format:check` in frontend | PASS / PASS |
| `npm run build` in frontend | PASS, TypeScript noEmit plus Vite production build |
| `PYTHONPATH=backend uv run --locked python scripts/verify_scientific_references.py --output /tmp/orbitiq-phase5-sgp4.json` | **40 passed / 0 failed** |
| `PYTHONPATH=backend uv run --locked python scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-phase5-earth-fixed.json` | **6 passed / 0 failed** |
| Source-only temporary copy: `uv sync --locked`, `uv run --locked pytest -q` | PASS, fresh virtual environment and complete suite |
| Source-only temporary frontend: `npm ci`, `npm run build` | PASS, 248 packages installed and build completed |
| Read-only database `check`, `verify-archive` and before/after hash/schema/count | PASS, integrity ok / one archived source / unchanged bytes |
| Dependency manifests/lockfiles against HEAD; previous report SHA-256s | Unchanged |
| `git diff --check` | PASS |
| Actual HTTP/browser integration | PASS, details below |
| Distinct genuine historical pair | **BLOCKED**, only one genuine stored snapshot; no invented replacement |
| Remote CI / public deployment / production recovery | NOT RUN / NOT CLAIMED |

New frontend coverage is **47 cases** above baseline, including contract/source/
unit/time validation, search/scope/pagination, empty continuations, direct history
access, missing metadata, stable selection, record filters, state failures,
cancellation/late response protection, exact-source App round-trip, keyboard
semantics and paired-marker lifecycle. Backend additions are **61 cases**, including
large history/count/cursor/query-plan/budget behavior, direct old IDs, malformed
metadata, source matching, units/wrapping, exact common time/frame/provenance,
actual EOP coverage/measured-only errors, finite subtraction, read-only integrity
and unchanged deduplication. The previous globe/ground-track/timeline/fallback and
scientific suites all remain included.

Investigated initial failures: an old empty-response equality assertion needed the
intentional additive pagination envelope; a missing-display-name fixture should
not invalidate a valid NORAD source; a query-budget clock stub had to be isolated
from the test client's own clock; two frontend test helper options needed their
proper TypeScript signatures; one file needed a second formatting pass. The first
browser selector assumed Playwright's exact label text excluded select options;
using its supported label matching fixed the harness. Final checks passed without
removing scientific cases, changing tolerances, disabling tests or concealing
regressions.

## Actual HTTP/browser evidence

Two independent local backend/Vite pairs were used: existing real DB on backend
8045 / frontend 5195; a newly created **reference-derived test-only** DB under
`/tmp` on backend 8046 / frontend 5196. No normal DB configuration or file was
replaced. Example actual startup commands:

```sh
ORBITIQ_DATABASE_PATH=/workspace/OrbitIQ/data/orbitiq.sqlite3 UV_CACHE_DIR=/tmp/orbitiq-uv-cache uv run --locked uvicorn orbitiq.main:app --app-dir backend --host 127.0.0.1 --port 8045
# From frontend, separate terminal:
ORBITIQ_BACKEND_URL=http://127.0.0.1:8045 npm_config_cache=/tmp/orbitiq-npm-cache npm run dev -- --host 127.0.0.1 --port 5195 --strictPort
```

`python /tmp/orbitiq_phase5_browser.py` exercised actual HTTP through Vite and actual
Chromium WebGL, without mocked network responses or canvas. Six flows cover both
data contexts at **1440×1000**, **820×1180**, **390×844**. They passed name search,
metadata/detail/units, keyboard Tab, no document overflow, common-time ITRS states,
visible disconnected A/B markers, exact-source navigation without a latest-list
request, real backend **91-point** tracks and keyboard timeline advancement,
retained comparison on return, input clearing, safe unavailable-state inspection
and unknown-ID errors. Separate browser execution forced missing WebGL and proved
numerical/source inspection remained available. Unsupported render extents also
retain numerical results with a specific explanation. A separate actual browser
check confirmed that reloading a catalog retains the explicitly selected historical
source, while manual selection of another source still works.

The real archive's self-check returns zero difference and is visibly identified as
self-comparison. The reference-derived archive returns nonzero calculated common-
time differences, explicitly labelled test data in evidence. These are not claimed
observed historical changes. The browser reported **zero JavaScript page errors**
and **zero external browser requests**. Desktop/mobile comparison screenshots were
visually inspected; actual rendered sphere/diamond markers and wrapped numerical
layouts were visible. ANGLE/SwiftShader is software WebGL, not physical-GPU
certification. Temporary screenshots/harnesses are verification artifacts, not
production persistence or a newly declared application dependency.

[phase-5-integration-results.json](phase-5-integration-results.json) records actual
UTC responses, source identities, model/frame/units, reference totals, browser
checks, fingerprints and separated real/fixture evidence. No benchmark or success
metric was invented. Original phase artifacts remain byte-identical.

## Acceptance criteria

| # | Criterion | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Architecture/prior reports inspected | **PASS** | Recorded baseline, plan and lifecycle findings |
| 2 | 100-snapshot limitation investigated | **PASS** | Existing cursor/page cap distinguished from readiness window and archive size |
| 3 | Accurate pagination/count semantics | **PASS** | 1,004-record cursor, anchors, bounded count and scan-window tests |
| 4 | Independent older snapshot access | **PASS** | Direct oldest ID/detail with history beyond 100; browser direct-source flow |
| 5 | Discovery uses stored records | **PASS** | Read-only SQL; genuine ISS search plus no-ingestion tripwire tests |
| 6 | Supported name/catalog search | **PASS** | Exact/partial name, NORAD and international-designator tests and actual browser |
| 7 | Selected vs historical membership | **PASS** | Single-record context/scope and historical-only classifications |
| 8 | Missing metadata disclosed | **PASS** | Malformed timestamps/names/identifiers/provenance tests, explicit nulls/issues |
| 9 | Snapshot detail/provenance | **PASS** | Existing strict detail reuse, source hashes, units, direct API/browser access |
| 10 | Shared/added/removed classification | **PASS** | Stable-ID pair tests and explicit single-record dataset semantics |
| 11 | Appropriate identifier matching | **PASS** | Validated NORAD linkage; same-name/designator different-NORAD cases |
| 12 | Scientific element units/conventions | **PASS** | Canonical units, signed/wrapped differences, invalid/overflow withholding |
| 13 | Invalid/incompatible comparisons | **PASS** | Source/unit/ID/body/frame/time/number failures retain safe inspection |
| 14 | Common-time compatible state comparison | **PASS** | Actual reference-derived SGP4/ITRS pair, exact time/unit/frame/lineage guards; genuine distinct-pair evidence blocked separately |
| 15 | Visible provenance/time/units/assumptions | **PASS** | API payload, semantic tables, actual calculation/evaluation/source labels |
| 16 | No unsupported maneuver/anomaly claim | **PASS** | Required caution, dataset-only additions/removals, no anomaly classification |
| 17 | Discovery/comparison/explorer navigation | **PASS** | App tests and six real browser flows with fixed source and retained return context |
| 18 | Keyboard/semantic/responsive UI | **PASS** | Native controls, semantic tables/regions, 3 viewports, focus and overflow checks |
| 19 | Loading/error/empty/stale/incomplete states | **PASS** | Unit, API and actual failure browser checks; missing-WebGL fallback |
| 20 | Bounded requests/computation | **PASS** | Cursor/index/scan/count/VM/time limits, max two source/state comparisons |
| 21 | Strict readiness/EOP policies retained | **PASS** | Actual out-of-range/measured-only tests, 40/6 references; scientific policy unchanged |
| 22 | Existing data/integrity preserved | **PASS** | Identical real DB hash/schema/count, integrity/archive verification, dedup tests |
| 23 | New backend/frontend tests | **PASS** | 61 / 47 additions included in final 398 / 172 green suites |
| 24 | Scientific regression tests | **PASS** | Full regression suite, published 40 SGP4 and 6 transformation audits |
| 25 | Quality/type/build/browser checks | **PASS** | Ruff/ESLint/Prettier/TypeScript/Vite, clean install, six browser flows |
| 26 | No concealed unresolved regression | **PASS** | Failures investigated above; final actual outcomes and data blockers separated |
| 27 | Report and structured evidence | **PASS** | This report, plan, actual integration JSON and preservation evidence |

No feature acceptance criterion remains FAIL or BLOCKED. **A supplemental distinct
genuine historical-pair integration check remains BLOCKED** until actual distinct
validated source data are explicitly ingested. Fixture success and the real
self-check are not substituted for that historical evidence.

## Files and dependency/schema changes

Phase 5 added:

- `backend/orbitiq/api/investigations.py`: validated read-only list/search/comparison routes.
- `backend/orbitiq/services/investigations.py`: bounded discovery metadata, source matching,
  chronology, element differences and reused scientific state comparison.
- `backend/tests/test_phase5.py`: isolated query/API/scientific/failure tests.
- `frontend/src/Investigations.tsx`, `investigation-api.ts`: lazy tools, strict wire
  validation, source details, fixed comparisons and exact-source handoff.
- `frontend/src/Investigations.test.tsx`, `investigation-api.test.ts`,
  `test-fixtures/investigations.ts`: frontend tests and clearly test-only contracts
  derived from the actual backend in an isolated reference fixture archive.
- `docs/phase-5-plan.md`, `phase-5-report.md`, `phase-5-integration-results.json`.

Phase 5 modified: `backend/orbitiq/storage.py` (bounded/read-only queries),
`services/analysis.py` and `api/scientific_schemas.py` (additive legacy pagination),
`main.py` (router), `backend/tests/test_phase2_api.py` (explicit new envelope),
`frontend/src/App.tsx`, `ScientificExplorer.tsx` (navigation/exact source),
`ScientificExplorer.test.tsx` (historical-selection retention),
`Globe.tsx`, `globe-renderer.ts`, `globe-geometry.ts`, `Globe.test.tsx` (paired
markers/lifecycle), `style.css` (responsive tools), `README.md` (feature links).
Previously uncommitted readiness/maintenance files and their reports remain.
No dependency manifest/lockfile, migration, orbital propagation/transformation
formula, strict EOP/leap policy, ingestion deduplication or CI workflow changed.

## Remaining limitations and launch work

- Only one genuine source snapshot exists locally. This task produces no actual
  historical maneuver/change finding and adds no data to populate the browser.
  Ingestion must stay explicit; distinct real-pair validation remains pending.
- History remains single-record snapshots. Catalog-wide batch membership or a
  multi-satellite catalog comparison cannot be reconstructed from this schema.
  Comparisons therefore have at most two one-record datasets; no fictitious
  batch grouping is inferred from similar retrieval times.
- Search is a bounded literal scan with cursors, not a global indexed search
  engine or unique satellite catalog. Sparse searches may need many continuations.
  Large-history totals and text-match totals remain explicitly unknown where not
  computed. Readiness still uses its earlier conservative 100-row assessment;
  complete browsing does not claim complete readiness metadata.
- Insertion/observation times and ingestion-attempt histories remain absent.
  Invalid/equal retrieval timestamps cannot establish older/newer order.
  Deduplicated repeated retrievals do not create historical attempts retroactively.
- Investigation state survives in-app navigation only. No persistent saved
  investigation or shareable frontend deep-link state was added.
- Model differences have no quantified covariance/uncertainty or observational
  validation and prove no maneuver, anomaly or collision. The ±7-day and EOP/leap
  guards can make common-time comparison impossible for widely separated epochs;
  record/element inspection remains useful. TEME values are never plotted as ITRS.
- Existing TestClient/HTTPX and npm `whatwg-encoding` deprecations and the Vite
  lazy-renderer chunk warning remain visible. No dependency was upgraded or warning
  suppressed to hide them. New investigation code is a separate lazy chunk; no
  large library was introduced. Local UI/browser checks do not establish a global
  device/screen-reader/GPU matrix or production capacity.
- Public launch still needs durable managed persistence/backup verification,
  monitored resource coverage/expiry, deployment/recovery drills, concurrency and
  rate/abuse controls, protected-operation authentication/authorization decisions,
  security/accessibility review and actual remote CI/deployment results. A cloud-
  task filesystem and passing local checks do not satisfy those operational gates.

Stop after this implementation, verification and documentation. Nothing was
committed, pushed, deployed or published; remotes and existing scientific data
were preserved.
