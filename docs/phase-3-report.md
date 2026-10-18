# Phase 3: Earth-fixed coordinates and ground tracks

## Acceptance summary

**All 16 Phase 3 criteria PASS within the documented numerical/reference scope.**
Implemented read-only Astropy TEME -> ITRS -> WGS84 geodetic calculations,
explicit offline Earth-orientation policy, bounded deterministic sampling and an
accessible backend-driven ground-track map. Original TEME behavior, all 40 SGP4
comparisons, lockfiles and the actual database remain preserved.

This is not universal transformation accuracy, observation validation, quantified
prediction uncertainty or public-launch readiness. No commit, push, deployment,
publication or Phase 4 work occurred. Reported checks below actually executed in
this task on 2026-10-18 UTC, including a clean source install.

## Initial findings and plan

Read Phase 1/2 reports, Phase 2 per-case reference results and scientific
conventions; inspected repository/Git status, dependency versions, SGP4 engine,
OMM models, API schemas/routes, services, storage/migrations, original reference
tests and React viewer/styles. Branch `work` has no commits and the existing
project files are untracked. Existing files/data were preserved. No previous
repository, missing backup or test result was assumed available.

Before implementation, reran the baseline: **177 backend / 31 frontend tests
passed**. The 40 existing published comparisons remained intact. Astropy was
already installed but unused for runtime conversion; no Earth-fixed route,
ground-track service, globe or map existed. Schema 2 contained one real ISS
snapshot; its file SHA-256 was recorded. Ground tracks need no persistence.
The pre-code plan and acceptance gates are in [phase-3-plan.md](phase-3-plan.md).

Consulted official **v7.2.3** satellite, IERS and time documentation from Astropy's
versioned upstream source, installed public interfaces and transformation code,
plus the original Vallado Rev2 PDF. This avoids assuming generic ECI/TEME/GCRS
or generic ECEF/ITRS are interchangeable.

## Scientific implementation and versions

| Component | Actual locked version / convention |
| --- | --- |
| Astropy | 7.2.3 |
| pyerfa | 2.0.1.5 |
| astropy-iers-data | 0.2026.10.12.1.3.27 |
| NumPy | 2.5.4 |
| python-sgp4 | 2.27, unchanged WGS72 initialization |
| Python / uv | 3.12.14 / 0.12.23 |
| Node / npm | 24.19.0 / 11.9.0 |

No dependency or lockfile upgrade occurred. Both locks are byte-identical to the
retained Phase 2 clean-copy locks; `uv lock --check`, `uv sync --locked` and
`npm ci` succeeded. Existing FastAPI/React/Vite versions remain locked.

Separate conversion module constructs Astropy TEME Cartesian position plus
velocity differential and transforms to **geocentric ITRS at the same UTC
obstime**. Astropy's established Vallado path uses ERFA GMST82/UT1 and polar
motion; it omits the TIO s' term for this TEME convention. No hand-written
orbital rotation replaces it. Original TEME result/provenance is nested unchanged
in `teme`; derived ITRS position is km and rotating-frame velocity km/s. Astropy
uses a one-second finite difference (±0.5 s) for the velocity transformation;
resources are preflighted for those times too. Versions, method, input/output
frames, units, target/source epochs, EOP values/status/policy/hashes accompany
results. A numerical reference check does not identify a particular modern ITRF
station realization or prove real-world centimetre accuracy.

Geodetic extraction uses `EarthLocation.to_geodetic(ellipsoid="WGS84")`.
Latitude is geodetic degrees north [-90,90], longitude degrees east **[-180,180)**
and altitude **km above the WGS84 reference ellipsoid**. This is not sea-level
height, terrain clearance or geocentric radius. WGS84 geodesy does not change
SGP4's WGS72 gravitational constants. Pole longitude is conventional. Nonfinite,
malformed and near-geocentre inputs fail; no fabricated coordinates are returned.

UTC, UT1 and TAI are distinguished. The inherited SGP4 nominal UTC-day convention
and microsecond input resolution remain. Leap-second strings remain unsupported;
new Earth-fixed results reject epoch-to-target intervals spanning a leap step
because leap-crossing propagation accuracy has not been established. The existing
TEME endpoint was not rewritten.

## Earth-orientation policy and actual source

Explicit local `IERS_A.open(finals2000A.all)` from the locked data package plus
its `Leap_Second.dat`; no IERS-Auto, startup refresh or request download.
Parsed resources/hashes are cached until process restart. Application contexts
serialize Astropy's process-global table/configuration with an RLock, disable
automatic downloads, select the local leap file, clear remote leap URLs and
require errors rather than degraded-accuracy fallback. Other code using Astropy
global settings must respect this ownership; workers have independent state.

- Default `ORBITIQ_EOP_POLICY=measured_or_predicted` permits measured/final values
  and explicitly labelled IERS-A predictions. Predicted results are marked
  `predicted_eop`, with a warning; they are not presented as final measurements.
- `measured_only` rejects any prediction. A prediction is rejected when current
  UTC MJD minus the table's first predictive MJD is greater than 30 days.
- DUT1 and both polar-motion parameters must be finite and in range at target
  and ±0.5 s support times. Missing resources/invalid parameters are safe 503;
  out-of-range dates or disallowed predictions are safe 422. No zero-DUT1,
  mean-polar-motion, clamped-date, extrapolated or degraded-result fallback.
- Local leap-file expiry is a hard target/support-time bound. Numerical
  Astropy/ERFA warnings during transformation fail explicitly.
- Network absence needs no substitute when local resources are valid. Updating
  requires an intentional official data-package/lock update, reference/regression
  checks and worker restart. This phase performed no data-package upgrade.

Actual IERS coverage: **1973-01-02..2027-10-04**, MJD 41684..61682;
first prediction **2026-10-02**, MJD 61315. Leap data expire **2027-06-28**.
The usable range is the intersection of these resources, policy/support-time
requirements and the source ±7-day epoch window. Historical final EOP are not
invalid merely because a table's prediction section ages. Production must monitor
resource expiry/coverage; this task does not establish a permanent data-update
service. The 30-day policy is not a satellite position-accuracy estimate.

Actual resource hashes:

```text
finals2000A.all
9fbc14ae5e71de96cc1e6b43b54a547acc80c7a6ce910c0209ad6230ff3d30cd
Leap_Second.dat
6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7
```

## Independent reference evidence

Exact source citations, original inputs, expected outputs, EOP assumptions,
tolerances and actual per-component results are in
[phase-3-reference-results.json](phase-3-reference-results.json) and the
[fixture provenance](../backend/tests/fixtures/README.md). Expected output is
transcribed from external reference material, never produced by OrbitIQ itself.
Relative tolerance is zero throughout.

| Executed case | Absolute tolerance | Actual largest error | Result |
| --- | --- | --- | --- |
| Vallado Rev2 Appendix C TEME -> ITRF/ITRS, published fixed EOP | 2e-5 km position; 1e-6 km/s velocity | 1.31737e-5 km; 7.09542e-8 km/s | PASS |
| Same published vector, actual bundled final IERS EOP | 3e-4 km; 1e-5 km/s | 2.83576e-4 km; 1.66431e-7 km/s | PASS |
| Astropy official v7.2.3 ISS example, 2019 epoch, full geodetic chain | 1e-5 deg angles; 1e-4 km height | 2.02316e-8 deg; 9.41890e-9 km | PASS |
| SOFA/ERFA published gc2gd WGS84 constants | 1e-10 deg; 1e-10 km height | 1.42109e-14 deg; 1.01208e-12 km | PASS |
| SOFA/ERFA published UTC -> TAI two-part JD | 1e-6 seconds | 0 seconds at this numerical precision | PASS |
| SOFA/ERFA published UTC -> UT1, specified DUT1 | 1e-6 seconds | 4.79616e-12 seconds | PASS |

Tolerances are transformation-specific, not copied from Phase 2. The bundled-EOP
Vallado thresholds follow Astropy's official 30-cm / 1-cm/s check and accommodate
updated EOP. The fixed-EOP check sets a narrower 2-cm / 1-mm/s acceptance target;
its **1.32-cm residual remains**, and its exact cause has not been isolated to
one rounding/convention term. No printed-digit, zero-residual or sub-centimetre
claim is made; the threshold was not relaxed. Official example tolerances allow
updated EOP, rounded example output and microsecond JD representation. Tight SOFA
limits test double-precision ellipsoid/time arithmetic, not geophysical accuracy.

The paper's literal TEME y=6127.64465950 and ITRF y=7901.29527540 km are retained;
they differ slightly from digits transcribed in Astropy's upstream test.
Published fixed EOP are explicitly **reference-only fixtures**, not an operational
fallback. The Astropy/SOFA cases use independently specified expected constants
but the same established library stack; they are not an alternate physical model
or independent observation campaign. Analytic WGS84 axes/poles, wrapping, negative/
fractional/offset times, numeric failures, EOP policy/range/age, concurrency and
sampling boundaries add contract checks, not new published orbit comparisons.

All **40** pre-existing published SGP4 comparisons passed unchanged at **1e-5 km**
position and **1e-8 km/s** velocity. The separate audit also reported **40 passed,
0 failed**; its current-run output is `/tmp/orbitiq-phase3-sgp4-results.json`.
The Phase 2 historical reference artifact remains unchanged.

## Sampling and API contract

No jobs, new infrastructure, schema change or derived-history storage.
One explicit immutable snapshot supplies every sample; provenance is validated
once per request and existing propagation/freshness metadata are reused.

- `GET /api/snapshots/{id}/earth-fixed?at=<aware ISO>&frame=ITRS`
- `GET /api/satellites/{catalog}/ground-track?snapshot_id=<id>&start=<aware ISO>&end=<aware ISO>&step_seconds=60&frame=ITRS`

Original TEME/list/detail/health routes remain compatible. New routes have typed
finite response models and safe structured errors. Catalog/snapshot mismatch and
missing snapshots return 404; invalid dates/frames/order/bounds, model-window or
calculation failures return 422; configuration/resource/storage failures return
503; invalid generated schemas return a safe structured 500. No stack traces,
submitted secrets or internal paths are returned.

Sampling defaults: **60-second step, 361 points, 24-hour maximum duration**.
Integer step 10..3600 s. Configurable maximum count 1..1000 and duration
10..86400 s; invalid policy fails. Count is floor(duration/step)+1. Equal start/
end returns one point; aligned samples only, never an irregular appended end.
Requested and actual bounds are explicit UTC. Interval ordering, both ±7-day
source bounds and request limits are checked before propagation.

Coordinates and chronological sample times are deterministic for fixed source
and resources; calculation-clock timestamps/current freshness are not fixed.
**One failed sample rejects the entire response.** No partial points escape and
no failed point becomes a zero/fabricated coordinate. Segment IDs break when
adjacent normalized longitudes differ by more than 180 degrees. High-latitude
and ±180 wrapping checks pass. A track does not establish observer visibility,
collision probability or safety.

## Frontend behavior and browser evidence

Extended the existing dark-blue snapshot viewer, preserving the original TEME
calculation. Added a responsive SVG longitude/latitude graticule map, actual
backend point markers, antimeridian-separated paths, selected sample control and
coordinate table. Steps above five minutes display unconnected points. The SVG
plot mapping is presentation only; no browser SGP4 or terrestrial transformation.
No globe, basemap asset, external tile service or visual redesign dependency.

Display includes UTC target/intervals, source epoch/retrieval/snapshot/hash,
source freshness, TEME/ITRS, WGS84 height semantics, EOP source/version/hash/policy,
measured/predicted status and limitations. Controls have labels, native keyboard
interaction and focus indicators; SVG title/description and the coordinate table
provide alternatives. Source/time/parameter edits abort and clear previous data.
Client validates finite ranges, units, frame, source identity, chronological
sampling, segment breaks and request/response time correspondence before drawing.
Loading, empty, failure and unsupported-partial-response states display clearly.
There is no supported partial result under the atomic API contract.

Actual Chromium **154.0.8037.57** / Playwright **1.62.0** checks at **1440x1000**
and **390x844** passed. The first browser attempt exposed an unstable accessible
name on the sample select; it was corrected to an explicit label association and
both viewport checks were rerun successfully. Checked keyboard focus/selection,
real ISS TEME and ground-track requests through Vite, backend coordinate display,
provenance, predicted EOP notice, actual antimeridian segmentation, limit-error
state clearing, **zero JavaScript page errors** and **no horizontal overflow**.
Screenshots were captured; the mobile layout was visually inspected.
These are smoke/layout/keyboard checks, not complete screen-reader, accessibility
standard, visual regression or cross-browser certification.

Actual integration: **2026-10-18T18:13:03 UTC**, catalog 25544, existing snapshot 1:

```text
source epoch:       2026-10-18T11:12:47.040768+00:00
first retrieval:    2026-10-18T17:14:39.983172+00:00
track start:        2026-10-18T11:12:47.040768+00:00
track end:          2026-10-18T12:42:47.040768+00:00
samples:           91 at 60 seconds, 2 antimeridian-separated segments
first lat/lon/h:    -0.0000106557 deg / -145.1251439203 deg / 419.8779106331 km
last lat/lon/h:     -8.8629220057 deg / -175.0474400970 deg / 420.5557260977 km
EOP status:        predicted (both UT1 and polar motion), no degraded fallback
```

Source SHA-256:
`556827b7dc6cbccd0cbc3e40a9e0a0ed2205ad2d2006a8649e16ee8c0c143d4b`.
[Machine-readable integration evidence](phase-3-integration-results.json) records
actual endpoint results, resource metadata, checks and database fingerprint.
This is a real application request using genuine stored CelesTrak input and real
configured local IERS data. It is **not a new live satellite download**, direct
observation or live online IERS retrieval. Phase 3 orbital/EOP downloads: **0**.
Published PDFs/versioned documentation were retrieved for reference research.
Temporary-DB/mock-transport unit/API tests are separately labelled and are not
called live integration. No required scientific resource was network-blocked:
the intentional offline policy used already installed locked data.

## Actual verification results

| Check | Result |
| --- | --- |
| Baseline before implementation | 177 backend / 31 frontend PASS |
| Final full backend suite | **256 passed**, original 177 + 79 additional cases |
| Phase 3 test distribution | 60 science/policy/sampling + 19 API cases |
| Published SGP4 comparisons / audit | **40 passed / 0 failed**, unchanged |
| New per-case numerical transform/geodesy/time audit | **6 passed / 0 failed** |
| Final frontend suite | **61 passed**, original 31 + 30 additional cases |
| Ruff lint / formatting | PASS; 41 Python files formatted |
| Frontend ESLint / Prettier | PASS |
| TypeScript / production Vite build | PASS |
| Clean source `uv sync --locked` + backend tests/lint/format | PASS, **256 tests** |
| Clean source `npm ci` + tests/lint/format/build | PASS, **61 tests** |
| `uv lock --check` / preserved lockfile byte comparison | PASS |
| Actual desktop/mobile browser requests | PASS; 91-point ISS track and original TEME route |
| Database CLI `check` / `verify-archive` | PASS; integrity ok / 1 snapshot |
| Database fingerprint/schema/count | PASS; unchanged / 2 / 1 |
| Remote GitHub CI | **NOT RUN**; no commit/push authorized |
| Deployment/production recovery | **NOT RUN**, outside this phase |

Fresh source copy excluded `.git`, real data/backups/secrets, virtual environment,
node_modules, build outputs and caches. It installed from both preserved locks
and passed checks. The newly added missing-EOP/mid-track propagation tests and
final selector fix were included in the final clean checks.

The known Starlette TestClient HTTPX deprecation remains visible; npm ci reports
the existing deprecated transitive `whatwg-encoding`. Neither was suppressed or
used to justify a dependency upgrade. Initial lint/format findings were fixed.
One lock-check command omitted the documented writable cache override and failed
on the read-only home cache; it passed when rerun with `UV_CACHE_DIR=/tmp/orbitiq-uv-cache`.
Initial local-file loading used a Path where this Astropy API requires str, and
first-use time conversion attempted a remote-cache lookup; both were corrected
before acceptance. A fresh-process test denies downloads/URL opens and confirms
normal conversion without cache warnings. No scientific assertion was weakened,
no failed test was hidden and no unexecuted remote check is reported as passed.

## Database preservation and files

The application database was never initialized, migrated, ingested into, reset,
restored or written by Phase 3. All ground calculations are read-only. Existing
migrations, triggers, real snapshot and backups remain. Temporary DB tests are
isolated. SQLite integrity and archive checks succeeded. Original and final
SHA-256 are identical:

`c389d0f1d663957be70a32f846f8e968e70a4f46c37343a5b80ceca5954e5f59`

Schema is **2** in OrbitIQ's `schema_version` table, with **1** snapshot. SQLite
`user_version` is not OrbitIQ's schema registry. No migration/rollback/restore is
needed for this phase. Existing backup/restore tests remain in the passing suite.
Databases, backups, credentials and caches remain Git-ignored.

Inspected files include the Phase 1/2 reports and references, scientific guide,
README, pyproject/uv lock, frontend manifest/lock/Vite/TypeScript/CI configuration,
engine/elements/freshness, analysis service, API schemas/routes/composition,
storage/database/migrations, existing tests/reference provenance and viewer/styles.

New Phase 3 files:

- `backend/orbitiq/orbits/earth_orientation.py`, `coordinates.py`, `sampling.py`
- `backend/orbitiq/services/ground_tracks.py`, `backend/orbitiq/api/ground_tracks.py`
- `backend/tests/test_phase3_science.py`, `test_phase3_api.py`, `fixtures/earth-fixed.json`
- `frontend/src/ground-track-api.ts`, `GroundTrack.tsx`, `time-presentation.ts`
- `frontend/src/ground-track-api.test.ts`, `GroundTrack.test.tsx`, `test-fixtures/ground-track.ts`
- `scripts/verify_earth_fixed_references.py`
- `docs/phase-3-plan.md`, `phase-3-reference-results.json`, `phase-3-integration-results.json`, this report

Updated files:

- `backend/orbitiq/main.py`: registers separate terrestrial routes.
- `backend/orbitiq/api/scientific_schemas.py`: finite terrestrial/track contracts.
- `backend/orbitiq/services/analysis.py`: reusable validated-snapshot propagation,
  preserving old single-position behavior.
- `frontend/src/ScientificExplorer.tsx`, `App.tsx`, `style.css`: additive track
  integration and phase label; UTC formatter moved to a shared module, retaining
  its existing export/tests and source microsecond display.
- `.env.example`, `README.md`, `docs/scientific-conventions.md`, fixture README:
  configuration, scientific scope and reproducible checks.

Original SGP4 engine/fixtures/assertions, ingestion/storage/migrations,
dependency declarations/locks and earlier phase reports remain unchanged.
Cloud runtime/onboarding skills were consulted; no new service, credential,
network rule or environment-draft change was required beyond the existing setup.

## Every requested acceptance criterion

| Criterion | Status | Evidence |
| --- | --- | --- |
| Phase 1 functionality remains intact | **PASS** | All original regressions, immutable real input and TEME/browser path |
| All 40 original SGP4 comparisons pass | **PASS** | Full pytest and 40/0 published audit |
| Established-library TEME -> Earth-fixed transform | **PASS** | Astropy TEME/ITRS, explicit same obstime |
| Explicit time/Earth-orientation conventions | **PASS** | UTC/UT1/TAI, local resources, statuses, coverage/age/expiry policy |
| Independent transformation references pass | **PASS** | Vallado fixed/bundled and official example within stated limits; 6-case audit |
| Latitude/longitude/altitude semantics documented | **PASS** | Geodetic degrees, [-180,180), WGS84 ellipsoidal km |
| Wrapping and antimeridian crossings handled | **PASS** | Boundary tests, segment contract/UI tests and actual browser crossing |
| Bounded deterministic ground-track sampling | **PASS** | Integer grid, count/duration/epoch bounds and repeated-result checks |
| Failed samples never valid coordinates | **PASS** | Whole-request failure; mid-track propagation and transform failure tests |
| API validation/structured errors correct | **PASS** | Invalid inputs/identity/limits/resource failures and finite response schemas |
| Frontend tracks reflect actual backend results | **PASS** | Runtime response validation, UI tests and actual ISS browser display |
| Traceable source provenance | **PASS** | Fixed validated snapshot/hash/epoch/retrieval in original TEME and track |
| Existing database preserved | **PASS** | Identical SHA-256, schema 2, count 1, integrity/archive checks |
| Backend/frontend regressions pass | **PASS** | 256 / 61 current and clean-source tests |
| Lint/format/TypeScript/build pass | **PASS** | Current and clean-source checks |
| Documentation records evidence/limitations | **PASS** | Plan, conventions, exact reference/integration artifacts and this report |

No in-scope item remains FAIL or BLOCKED. Passing within these stated limits is
not a claim that broader scientific or launch requirements are complete.

## Remaining limitations and next phase

No uncertainty/covariance model, direct-observation validation, universal transform
accuracy, observer visibility, anomaly/collision/safety analysis, terrain/geoid,
publicly reviewed authentication/rate limiting, production monitoring or durable
managed persistence is delivered. Leap-crossing propagation is explicitly rejected
for the new service. Numerical validation covers selected cases, not every orbit,
polar/EOP condition or frame realization. The nonzero fixed-EOP Vallado residual
is documented above. Browser checks cover one browser and two sizes only.

For hosting, pin and review resource updates, monitor EOP/leap expiry, plan worker
concurrency/rate limits and resource-readiness checks, retain persistent managed
storage/verified independent backups, and configure same-origin API routing.
The existing health endpoint remains liveness-only. A cloud-task filesystem and
successful local build do not establish deployment durability or disaster recovery.
The existing CI workflow includes new tests automatically but has not run remotely.

Recommended next phase, **only with authorization**: an interactive 3D explorer
and timeline consuming the validated Earth-fixed contract, with clear source/EOP
freshness and scientific labels. Keep production security, persistence and
operational readiness as explicit launch gates. Do not start Phase 4 automatically.
