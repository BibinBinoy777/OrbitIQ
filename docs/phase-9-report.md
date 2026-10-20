# Phase 9 — Investigation Reports & Evidence Export

**20 October 2026 UTC: complete and verified locally. Public launch remains gated.**
The implementation was subsequently published with authorization on
`phase-9-investigation-reports` and its exact-commit CI passed. See the
[publication status](phase-9-publication-status.md) for commit/run evidence and
separate production milestones. The results below retain the local implementation
and pre-publication review history. No production deployment was performed.

## Delivered behavior and architecture

Existing snapshot, TEME position, ITRS ground-track/selected-sample and A/B
comparison investigations now have report actions, including browser-saved cards
and reconstructed read-only links. One backend generation produces the canonical
report; JSON, preview and standalone HTML reuse that capture. Downloads do not
request another calculation. Explicit regeneration creates a new report UUID/time.

The audit began on clean `main` at
`341812ae66409691e9cf07b15e50dba3ab894e26`. Investigations are browser-local
definitions, not server-owned records. Reports therefore use a documented
configuration identifier and a generated descriptive title. Browser UUID/title/
notes/creation time are excluded and explicitly marked unavailable on the backend.
No fictitious ownership, saved narrative, observation or creation date was added.

The service revalidates exact archived references through the existing scientific
loader, reuses current SGP4/ground-track/comparison services, rechecks source
identity after generation and checks calculation lineage. There is no migration,
export database, queue, AI, new environment variable or new dependency. Both
lockfiles, science algorithms/tolerances, EOP policy implementation, immutable
storage and ingestion/deduplication remain unchanged.

`GET /api/investigation-reports?definition=<URL-encoded schema-1 definition>` is
the only new endpoint. It returns an attachment with a versioned canonical JSON
model, safe errors, no-store headers, finite serialization and an 8 MiB bound.
It joins existing production calculation admission and gateway rate limits.
The development OpenAPI document exposes its report response schema.

## Files and contract

| Area | Important files |
| --- | --- |
| Canonical contract / orchestration | `backend/orbitiq/reporting.py`, `backend/orbitiq/services/reports.py` |
| API / ingress | `backend/orbitiq/api/reports.py`, `main.py`, `api/boundary.py`, `deploy/server-routes.conf` |
| UI / captured downloads | `frontend/src/InvestigationReport.tsx`, `report-api.ts`, existing investigation actions and saved list |
| Shared presentation / print | `report-presentation.ts`, `report-print.css`, small shared style additions |
| Automated tests | `backend/tests/test_phase9_reports.py`, production admission test, three report frontend test files and saved-view regression |
| Actual browser/PDF verification | `scripts/verify_report_browser.py`, `scripts/verify_report_pdf.py` |
| Documentation / example | [guide](investigation-reports.md), [JSON Schema](investigation-report-schema.json), [actual full export](phase-9-export-example.json), [design audit](phase-9-plan.md) |

The [structured evidence](phase-9-integration-results.json) contains file hashes,
changed-file inventory, actual browser versions/cases/timings, image IDs, archive
fingerprints, recovery results and acceptance status. Its manifest excludes itself
and this final report to avoid circular hashes.

The JSON example is a genuine ISS snapshot #1 TEME position export downloaded
through the local release gateway, with source orbital epoch
`2026-10-18T11:12:47.040768Z`. It retains its actual report UUID/time and values;
it is not a synthetic observation or a database backup.

Root fields are `schema_version`, `template_version`, `kind`, `report_id`,
`generated_at`, `status`, `investigation`, `sources`, `calculation`, `validation`,
`methodology`, `limitations` and `warnings`. Schema/template versions are both 1;
unknown versions are refused by the renderer. See the guide for the full field,
timestamp, unit, versioning, error and compatibility definitions.

## Report contents and scientific meaning

The printable output contains cover/identity, deterministic executive summary,
overview/inputs, results/comparisons, evidence/provenance, validation/data quality,
scientific limitations, methodology/reproducibility and footer. It has repeated
table headings, wrapping hashes/URLs, monochrome styles, A4 margins and page counters
where supported. All returned ITRS/geodetic track rows are printed. The selected
sample has full derivation metadata; complete per-point TEME/EOP metadata remain
in JSON, explicitly disclosed in the report.

Every source retains exact IDs, catalog, epoch, retrieval, URL, validated OMM
elements/units and recorded validation provenance. Its SHA-256 covers the **exact
stored uncompressed CelesTrak GP JSON HTTP response-body bytes**, not normalized
fields, headers or a provider signature. It is independently recomputed against
stored bytes, not independently authenticated against CelesTrak. Provider hash and
publication time are unrecorded; observation time is not applicable. Legacy insertion
time is unknown where not recorded. No absent field is invented.

The configuration SHA-256 covers the validated definition with UTC-normalized
timestamps, sorted JSON keys, compact separators, ASCII escaping and UTF-8
encoding. It is distinct from payload hashes, browser saved IDs and report UUIDs.
Neither identifier is an export-package signature or accuracy certificate.

Reports distinguish source epoch, first retrieval, insertion, evaluation,
calculation execution and report generation times. TEME and ITRS vectors retain km
and km/s; WGS84 geodetic values retain degrees/ellipsoidal km. Existing SGP4/WGS72
and Astropy transformation conventions remain authoritative. Actual ITRS EOP/leap
hashes, versions, prediction flags, policy and expiry metadata are retained.

Missing/mismatched/corrupt sources refuse export without substitution. A failed
calculation can return a partial report with verified source evidence and explicit
unavailable reasons; failed tracks contain no partial coordinate series or zero
substitutes. Source-only and element-only modes do not claim a calculated state.
`complete` describes content coverage. Independent observation-based validation
remains **BLOCKED** and prediction uncertainty **unquantified**. Differences do not
establish maneuvers, anomalies, collision risk or safety.

This captures current recomputation. Exact historical replay requires matching
source, software and EOP/leap resources; the report does not embed original HTTP
bodies, resource binaries or an isolated replay environment.

## Security and access

The existing archive is public and read-only. There are no private server
investigation records or accounts. Both exact comparison sources are checked;
unknown/private ownership/local-metadata inputs are rejected. Browser notes remain
local, and saved-card JSON, HTML and PDF checks confirm their exclusion. This is
not a claim that cross-account authorization exists. Add access checks before
introducing protected records.

Inputs, methods, body/URI/header sizes, samples, response size and calculation
admission retain bounded behavior. HTML interpolations are escaped; React renders
text, and offline HTML has a restrictive CSP with no scripts or external resources.
Application CSP was retained. Existing logs exclude query content and credentials.
Requests can be cancelled/retried; stale results and duplicate generation are
suppressed. Modal focus, Escape, focus return and 390 px layout were exercised.

## Executed verification

| Check | Actual final result |
| --- | --- |
| `uv run --locked pytest -q` | **675 passed**, including 41 new report cases; one existing Starlette/httpx deprecation warning |
| `npm test` | **307 passed**, including 32 new report cases |
| Ruff check / format | PASS |
| ESLint / Prettier | PASS |
| TypeScript / Vite production build | PASS; existing Three.js chunk advisory above 500 kB remains |
| Trusted SGP4 audit | 40 passed, 0 failed |
| Terrestrial reference audit | 6 passed, 0 failed |
| Expanded science audit | 32 passed, 0 failed; observation validation still blocked |
| High-altitude geodesy audit | 28 independent cases and 28 separate round trips passed |
| Actual report browser flows | **14 cases passed**: Chromium 6, Firefox 4, WebKit 4; no API mocks, page errors or CSP violations in final runs |
| Existing critical browser workflows | **21 cases passed**, 7 each in Chromium/Firefox/WebKit |
| Offline printable HTML | PASS in all three engines; no network resources requested |
| Chromium PDF content/pagination | **7 PDFs passed**; required sections, exact source identities, warnings, all track positions/geodetic rows and every page counter checked |
| Local release images | API/web builds succeeded; same-origin health/readiness/UI/empty-archive smoke checks passed with a separate explicit fixture |
| Data preservation / recovery | Normal database byte hash and every schema/table fingerprint unchanged; separate backup/restore verified; runtime restored copy unchanged |
| Diff / credential checks | Whitespace check passed; no private-key/credential signatures, database files or private-key files in changes |

The API tests cover exact references, all modes, missing/corrupt sources, mid-request
source changes, wrong lineage, partial EOP/propagation failures, malformed/duplicate/
oversized definitions, nonfinite output, output cap, sampling and no writes. Frontend
tests cover contract/metadata consistency, escaping, captures/downloads, cancellation,
duplicate suppression, context changes, safe errors/retry and cleanup.

Initial checks caught a duplicate `nosniff` response header and stylesheet stubbing
in the test environment; both were fixed and the suites rerun. Verification harness
issues were also resolved: selectors tracked the correct accessible context, maximum
tracks wait for actual completion, a TypeScript test used supported query options,
and PDF checks use print media and cell reading order. WebKit screenshot automation
injects inline CSS blocked by CSP; screenshot capture is omitted for that engine
while export, actual layout, keyboard, print CSS and offline HTML remain checked.
No application CSP was weakened and no failing assertion was converted to a pass.

At tested defaults, the detailed 361-point track produced about 2.28 MB JSON,
137 KB HTML and a **72-page PDF**, with report generation about seven seconds on
this local container. These are observed single-run measurements, not a capacity
or latency guarantee. The evidence records exact final sizes/timing.

Actual temporary downloads, PDFs, screenshots and logs remain under
`/tmp/orbitiq-phase9`; they are not Git files or durable backups. Screenshot/first
page appearance was inspected. PDF text extraction validates content and pagination,
not physical print quality. Native Firefox/WebKit PDF output, printer drivers,
assistive technologies and every browser/version remain unverified.

## CI, acceptance and Phase 8 boundaries

At the local implementation checkpoint, Phase 9 remote CI had **NOT RUN**. The
later authorized publication and successful exact-commit run are recorded in the
[publication status](phase-9-publication-status.md). The
previously verified [published CI run](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39377033436)
passed backend/frontend/release jobs for the baseline commit; it is not Phase 9 CI.

| Criterion | Status | Evidence / scope |
| --- | --- | --- |
| AC-01 JSON export | PASS | Actual API/browser downloads for existing exact configurations; schema/example documented |
| AC-02 printable report | PASS | Actual preview, offline HTML and seven Chromium PDFs; native-engine compatibility limits explicit |
| AC-03 traceability | PASS | Reference/hash/provenance tests, actual downloads and PDF checks |
| AC-04 scientific metadata | PASS | Backend-value tests and TEME/ITRS/units/EOP identity checks |
| AC-05 validation honesty | PASS | Refusal/partial/error tests and explicit missing/blocked/unquantified status |
| AC-06 consistency | PASS | One capture, no second download calculation, same IDs/evidence/values and PDF checks |
| AC-07 authorization | PASS | Current public read-only policy only; rejected private/local fields, both references checked, notes excluded; future per-user access unimplemented |
| AC-08 regressions | PASS | Full suites, scientific audits, 21 actual browser cases and unchanged archive/protected files |
| AC-09 documentation | PASS | Guide, schema, actual example, design, evidence and this report |
| AC-10 build verification | PASS | Actual local test/lint/type/build/container results; remote Phase 9 CI explicitly not run |
| AC-11 honest status | PASS | Compatibility, replay, uncertainty, access and infrastructure gaps explicitly retained |

Phase 8 still needs actual hosting/domain/public HTTPS, independent off-machine
backup and host-loss recovery evidence, production monitoring/real alert delivery,
and branch protection/required checks. Phase 9 publication and exact-commit CI are
now verified as linked above; they do not close the remaining infrastructure gates.
The last available read-only repository summary
showed protection/check requirements disabled. No settings were changed. Local
container/recovery success does not verify public HTTPS or independent disaster
recovery. Refer to the existing Phase 8 closure documents for those separate gates.

Recommended next development task: **reproducible evidence replay** with retained,
identified EOP/leap resources and an isolated replay verifier. Keep independent
observation-based accuracy validation a separate evidence requirement; do not
invent observations or turn numerical reference agreement into prediction certainty.

## Publication gate review

See the [pre-publication review snapshot](phase-9-publication-review.md) and its linked
evidence for fresh checks, the isolated test correction, CI/protection findings
and the exact proposed branch publication actions. Those actions were subsequently
authorized and executed; see the [publication status](phase-9-publication-status.md).
The earlier implementation evidence is retained without rewriting its original results.
