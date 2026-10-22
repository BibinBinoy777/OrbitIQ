# Phase 11 extension — Observation validation and prediction discrepancy analysis

Local work on **20 October 2026 UTC**. The mathematical and local evidence workflow
is implemented and tested. **Genuine independent observation-based prediction
validation is not complete.** No independent observations were supplied/configured,
and CelesTrak GP fitting-observation lineage and prediction covariance remain
unavailable. Synthetic test results are not scientific observations.

The original [Phase 11 report](phase-11-report.md) and its integration artifact are
unchanged. This extension does not change the prior historical-analysis acceptance
record. See the [new methodology/operator guide](observation-validation.md),
[observation schema](observation-record.schema.json) and
[extension evidence](phase-11-extension-integration-results.json).

## Baseline, audit and actual data

Started on `phase-10-evidence-replay`, HEAD
`be3710dae9f21bae817637d7bfdb87509b3f6a34`, with **20 existing modified/new Phase 11
paths**, not a clean checkout. A 260-file baseline includes that uncommitted work,
old reports and source hashes. The original database byte hash and complete
schema/table fingerprints were saved before modifications. Fresh baseline suites
ran and passed: **828 backend / 330 frontend**, both exit 0.

Inspected current Phase 11 source/report/evidence, snapshot identity/validation/
deduplication and ledger, schema 1–3 migrations, SGP4/coordinates/EOP/freshness,
comparison/history services, Phase 9 schema/export/presentation, Phase 10/10.1
capture/preflight/replay, API composition/security boundary, frontend routing and
CI commands. The existing engine is **SGP4/WGS72**, Earth-centered TEME in km and
km/s; ITRS uses the existing Astropy/strict local EOP/leap transformations. No new
propagator or coordinate implementation was needed.

The entire archive was again paginated with one record per page through both
pages: **two genuine ISS GP snapshots**, NORAD 25544, IDs 1 and 2, with the same
payload hashes, epochs and retrieval timestamps reported in the original Phase 11
report. No observation table, independent observation archive or supported external
observation-ingestion integration exists. No historically issued prediction records
were assumed. New actual read-only audit propagated both genuine inputs in TEME
and ITRS at their element epochs and retained the exact state/model/resource
provenance. Those are calculated states, not observations. The observation API
correctly reported no configured evidence archive.

**Zero independent observations were acquired, supplied or validated.** No new
provider request was attempted. The scope explicitly forbids introducing external
observation ingestion without an existing appropriate integration, so no source
was downloaded or invented to fill this dependency.

## Newly implemented functionality

- A strict, bounded operator-normalized observation contract retains original
  bytes/records, source/record IDs, target, UTC timestamp/time scale, frame, unit,
  measurement/data type, quality, optional retrieval/organization/upstream hash and
  optional axis-sigma metadata. Missing metadata remains null; declared upstream
  hashes are not described as verified provider bytes.
- Backend compatibility checks require the same target and exact requested epoch,
  compatible Cartesian measurement definition/origin, UTC, supported frame/units,
  valid quality and nonfuture chronological metadata. Unsupported range/angular/
  element/covariance formats do not produce position errors.
- Supported discrepancy arithmetic provides observed-minus-predicted XYZ and norm
  in km. TEME supports explicitly defined radial/transverse/normal components;
  ITRS does not invent an inertial RAC basis. Metres are normalized explicitly.
- Same-frame descriptive component bias, MAE, RMSE, maximum/median absolute error,
  population dispersion and separate vector-norm summaries require at least two
  compatible samples. All exclusions and counts remain visible. No extrapolated
  error trend, population significance, independent accuracy score or outlier
  classification is produced.
- Independence safeguards exclude duplicated/ambiguous observation IDs and source
  records, including known payload/reference aliases, and known reuse of the GP
  input payload. Fitting-lineage uncertainty and temporal holdout candidates stay
  **unverified**. Different IDs/providers never establish independence. Independently
  verified counts remain zero and independent-error metrics null.
- Existing source/propagator/version/configuration/resource evidence is captured
  using **unchanged nested Phase 10/10.1 bundles**. TEME captures the existing
  position report; ITRS captures an exact source self-comparison solely to preserve
  the supported transformation. That self-comparison is not an observation.
- Version-1 deterministic findings retain exact observation/source/calculation/
  manifest references, checks, residuals, uncertainty and limitations. They assign
  no unsupported physical cause, severity, confidence or accuracy classification.
- Optional read-only APIs and **Discovery & history → Observation validation**
  inspect operator-approved captured runs. Loading, empty, error, invalid/excluded,
  insufficient and compatible-with-warnings states are distinct. The original
  history/comparison/detail views remain available. Captured JSON export reuses the
  Phase 9 serializer without frontend scientific recomputation.

Prediction generation is explicitly **retrospective propagation from an archived
input**, not a claim of a forecast historically issued before the observation.
Generation time, source epoch/retrieval, requested epoch, observation/retrieval time
and retrieval-relative intervals remain distinct.

## Architecture, persistence and access

New backend modules separate observation contract/math, evidence orchestration,
operator CLI and API handlers. The frontend adds one bounded captured-evidence
view and tests. The only Phase 9 presentation change generalizes its existing JSON
serializer's TypeScript argument; its output and strict report schema remain
unchanged. Historical-analysis scientific logic was not copied or replaced.

No SQL migration or dependency was needed. Original schema-3 storage, immutable
snapshot/ingestion constraints and collection safeguards are unchanged. New runs
are private, exclusively created **file evidence packages**, preserving input,
report, manifest and at most ten existing prediction bundles. There is no second
satellite database, observation download service, user-upload route or writable
HTTP interface. The local operator's filesystem permissions authorize captures;
existing destinations/concurrent same-ID captures are refused. Incomplete runs
without a final manifest are unavailable rather than successful evidence.

`ORBITIQ_VALIDATION_ARCHIVE` is an optional, existing absolute directory containing
only operator-approved fixed-name runs. API parameters cannot select arbitrary
paths. Source inputs and packages belong outside Git; `data/` and the new
`validation-evidence/` ignore rule cover recommended locations. Keep private inputs
separate from the package-listing root. `.env.example` documents opt-in setup.

`GET /api/observation-validations` lists at most 100 fixed-name run directories;
`GET /api/observation-validations/{32-hex-run-id}` inspects a bounded saved report.
Invalid IDs, unsafe paths, missing members, altered hashes and contradictory
lineage are refused with safe responses. GET does not capture, acquire or replay
orbital calculations. Existing runtime/gateway workload limits cover detail reads.
No account/authentication system or public-production authorization claim was added;
public access to private evidence requires a separate reviewed access policy.

The wrapper links observed/predicted values to the preserved input and nested
reports, recomputes inexpensive arithmetic for inspection, and validates member
hashes. Explicit CLI numerical replay enforces the existing exact code/runtime/
resource identity. Reading supported saved reports and proving a matching-runtime
propagation replay remain separate operations. A separately retained wrapper
manifest checksum anchors the whole package; checksums do not authenticate sources.

## Verification and actual results

Final checks ran against the final application source. Python uv commands used
`UV_CACHE_DIR=/tmp/orbitiq-phase11-extension/uv-cache`; scientific scripts used
`PYTHONPATH=backend`. npm commands ran in `frontend`. Exact commands, counts,
outputs/hashes, scientific cases, replay results, browser commands and preservation
proofs are retained in the JSON artifact.

| Check | Exit | Actual result |
| --- | ---: | --- |
| `uv run --locked pytest -q --junitxml=/tmp/orbitiq-phase11-extension/backend-final-state.xml` | 0 | **874 passed**, including **46 new extension cases**; no failures/errors/skips |
| `npm test` | 0 | **344 passed**, including **14 new extension cases** |
| `uv sync --locked` | 0 | Existing locked environment checked; manifests/locks unchanged |
| Ruff check / Ruff format check | 0 / 0 | Pass |
| ESLint / Prettier / TypeScript noEmit | 0 / 0 / 0 | Pass |
| `npm run build` | 0 | TypeScript/Vite production build passes |
| Original SGP4 reference script | 0 | **40** comparisons pass |
| Original terrestrial reference script | 0 | **6** cases pass |
| Expanded Phase 6.1 science script | 0 | **32** numerical comparisons pass; observation validation remains blocked |
| Phase 6.1.1 geodesy script | 0 | **28** independent mathematical cases and **28** separate round-trips pass |
| Existing golden evidence lifecycle | 0 | **6** published reference components and **3** exact offline replays pass |
| Extension controlled offline wrapper verification | 0 | **6** fresh-process runs, three each for TEME/ITRS; zero network/database/process attempts |
| Separate package backup/restore into new destination | 0 | Every copied member hash matches; original unchanged; existing destination refused; offline replay succeeds |
| Actual genuine archive readiness audit | 0 | Two real GP inputs propagated in TEME/ITRS; zero independent observations; database preserved |
| Browser regression / new-view matrix | 0 | **77 flows**: 24 historical + 21 critical + 14 Phase 9 reports + 6 genuine-empty observation views + 12 controlled synthetic views; three engines |
| Seven Chromium PDF text/pagination inspections | 0 | **7 pass**, including all 361 maximum-track rows |
| `git diff --check` and preservation | 0 | Original archive, reports, locks and historical scientific modules retained |

Mathematical oracles include literal 3/−4/0 residual → norm 5, an orthogonal
right-handed RAC basis, signed-pair bias/MAE/RMSE/dispersion and vector RMS norm.
These verify formulas, not satellite measurements. Integration fixtures use the
existing Vallado source in isolated archives, with explicitly synthetic position
offsets and source IDs. They never enter the ordinary database. Actual genuine
states are separately labelled calculated and have no observation counterpart.

Tests cover compatibility and unsupported measurement types; zero/one/multiple
samples; every duplicate/reuse path; absent uncertainty and sigma normalization;
ITRS/strict resources and RAC refusal; invalid records/nonfinite inputs/oversized
batches; no overwrite; source/hash/lineage tampering; scoped read-only API and
filesystem links; failed propagation; unavailable replay versus matched replay;
empty evidence; browser cancellation/errors; and JSON export without recalculation.
The complete prior Phase 11, investigation, Phase 9 and Phase 10/10.1 suites pass.

Failed attempts were investigated rather than counted as passes: an initial test
root also contained its fixture DB and correctly failed the dedicated-root
restriction; the fixture was moved to a dedicated root. New DOM assertions were
scoped to avoid duplicate explanatory text. Browser startup found the Nginx
route's `{32}` expression needed quoting; the actual gateway configuration was
fixed and syntax/startup rerun. A provenance assertion initially selected a hidden
explorer `<details>`; the runner was scoped to the observation section and the
three affected fixture-browser runs were rerun. No mathematical tolerance, CSP,
scientific readiness check or product feature was weakened to satisfy tests.

Existing warnings remain: Starlette/httpx TestClient deprecation and the
558.60-kB globe bundle. WebKit native PDF printing, physical printers, complete
screen-reader/WCAG audits, native GPU behavior and universal cross-host bitwise
agreement are outside this evidence. Local test containers/images are controlled
verification runtimes, not a newly built or published production release. Exact
backend and built frontend copies matched current bytes. Genuine-history browsers
used a separate read-only actual archive copy; observation-example browsers used
only a separate synthetic fixture archive/package root. Chromium 151.0.7922.34,
Firefox 153.0 and WebKit 26.5 passed with no page errors/CSP violations in final
runs. The owned containers/internal network were removed; no ports were published.

## Preservation and execution boundaries

Ordinary database before/after SHA-256:

`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`

Complete schema/table fingerprints preserve two genuine snapshots, one ingestion
attempt, one insertion record and one gate, with all triggers and constraints.
No normal initialization, migration, restore, collection or data write occurred.
Both original Phase 11 report/artifact and prior scientific reports remain
byte-for-byte unchanged. Existing algorithm/reference fixtures, dependency locks,
storage/ingestion code and migrations are unchanged. Shared API composition,
request/gateway classification, investigation navigation and JSON serialization
were extended intentionally; pre-existing local work was preserved.

No commit, push, merge, GitHub publication, remote workflow, deployment, DNS or
production-infrastructure change was performed. New packages, copies and restored
fixtures are task-local evidence, not independent production backups. Phase 8
hosting/domain/HTTPS, off-machine recovery, actual monitoring/alert delivery and
branch-protection gates remain independent and unverified here.

## Acceptance and next task

**9 PASS, 3 PARTIAL, 1 BLOCKED**. Mathematical implementation tests do not
substitute for genuine observation validation.

| Criterion | Status | Actual evidence / limitation |
| --- | --- | --- |
| AC-01 — Existing functionality preserved | PASS | All prior historical/investigation/export tests pass; 24 historical, 21 critical and 14 Phase 9 report browser flows plus seven PDF inspections. |
| AC-02 — Observation provenance | BLOCKED | Normalized contract and preserved input/source metadata tested, but zero genuine independent observations supplied or authenticated; no real observation provenance validation can be claimed. |
| AC-03 — Prediction provenance | PASS | Existing scientific propagation reused; two genuine GP inputs independently audited in TEME/ITRS with exact source/model/resource metadata. Controlled validation runs retain nested prediction evidence. |
| AC-04 — Independence handling | PARTIAL | Reuse/duplicate/unknown/conditional temporal candidates are explicit and tested. No automatic authenticated independence establishment or complete GP fitting lineage is available. |
| AC-05 — Scientific compatibility | PASS | Target/epoch/UTC/frame/origin/units/measurement/quality checks tested; unsupported inputs do not yield residuals; strict ITRS transformations preserved. |
| AC-06 — Error calculations | PASS | Literal independent mathematical oracles for signed XYZ/norm/RAC and descriptive bias/MAE/RMSE/median/max/dispersion; no physical prediction-accuracy validation claim. |
| AC-07 — Uncertainty handling | PARTIAL | Axis sigma metadata preserved and normalized; missing prediction uncertainty explicit. Covariance propagation, weighted inference and significance are unavailable without scientific inputs/method. |
| AC-08 — Explainable findings | PASS | Versioned deterministic templates link exact input/source/calculation/manifest references, checks, residuals, uncertainty and limits; synthetic reproduction tested. |
| AC-09 — Historical coverage | PASS | Actual two GP records and zero independent observations disclosed; absent/insufficient metrics null; no interpolated or manufactured history. |
| AC-10 — Evidence export | PARTIAL | Captured authoritative JSON export works in all three engines through shared Phase 9 serialization and retains references. No genuine independent-error report can yet be produced. |
| AC-11 — Regression safety | PASS | 874/344 full suites, original history/detail/investigation/replay/source tests, three browser engines and actual Phase 9 printable outputs pass. |
| AC-12 — Documentation | PASS | Separate methodology, generated observation schema, extension report and structured evidence; original Phase 11 report/artifact unchanged. |
| AC-13 — Verification | PASS | Actual final-state commands/results/source hashes, 46+14 new cases, mathematical/scientific audits, browser/PDF/offline replay/recovery and preservation evidence retained. |


The next task is to select and review an authentic independently measured or
observation-derived **position** dataset with suitable target/epoch coverage,
source references/original bytes, time scale/frame/units, quality and uncertainty.
Document its relationship to the GP fitting inputs and review authenticity/lineage
before approving any provider-specific adapter or acquisition. At least one genuine
compatible sample is needed for an actual discrepancy; at least two per frame for
these descriptive aggregates, and substantially more qualified data for broader
historical conclusions. A trusted independence-assessment method and prediction
uncertainty/covariance inputs remain additional scientific dependencies.

Until those gates are met, this is a tested local **discrepancy/evidence workflow**,
not completed independent prediction-accuracy validation or production readiness.
