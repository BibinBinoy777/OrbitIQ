# Engineering milestone E7 — historical window integrity and recovery

Status: **E7 engineering acceptance passed** on the published corrected
implementation commit below, with complete remote CI and retained-evidence
verification. This report records that baseline. The documentation receipt is a
separate commit and also requires its own exact-SHA CI before final handoff.

## Scope and baseline

Started from clean `engineering-e6-onboarding-recovery` at
`5aec8ec3a8ac70f2fe113aef017aa81d31074c62`. Dedicated branch:
`engineering-e7-history-contract`. The [plan](engineering-e7-plan.md) was recorded
before implementation. [Usage, contract and test commands](engineering-e7-guide.md)
explain the bounded workflow and limitations.

E5 prioritized contract drift after onboarding/portable recovery, which E6
implemented. E7 selects one useful, unblocked gap: exact requested historical
windows, failure/retry and captured export. It does not introduce another product
area or expand the historical scientific rules.

Previously the client accepted valid same-catalog reports without binding the
request's page size/cursor/anchor. Retry used the last successful parameters,
which could differ from the failed window. The fixes bind response/window/source
relationships and preserve failed parameter/navigation snapshots. Successful
windows retain their resolved anchor for Previous, and validation uses an immutable
copy of the sent query. Input edits cancel obsolete requests. Rejected windows expose neither findings nor exports;
recovery exports the capture without another request. An actual 320-pixel browser
check found comparison controls overflowing; a scoped history-screen CSS fix
retains their labels and keyboard access.

The existing backend API only gains an OpenAPI response envelope, without runtime
serialization/filtering of the already-hashed payload. Seven API-generated
synthetic window fixtures protect backend/frontend compatibility. Nullable and
unusable sources and unknown bounded counts remain explicit. No dependency,
lockfile, configuration, database migration, storage format, scientific protocol,
report version or orbital algorithm changes.

## Acceptance and actual local evidence

- Before fixes, all **10 new regression tests failed** against the original code,
  establishing wrong-window acceptance and wrong-window initial Retry. The
  original 23 history component tests passed at baseline.
- Initial tightened checks exposed two internally inconsistent old mocks. They
  now use actual API-generated partial/empty responses; existing behavior
  assertions are retained. Source-failure/nullable fixtures remain accepted.
- Backend: **1,306 passed**, zero failures/skips; two existing warnings (Starlette
  test-client deprecation and deliberate duplicate-ZIP-member rejection fixture).
  Nine new API/contract tests and eight E7 release failure probes are included.
- Frontend: **427 passed** across 30 files, including 22 new tests. Focused history
  tests: **45 passed**. Failed initial/Next/Previous Retry, navigation stack,
  wrong-window rejection, captured export, cancellation and late-response refusal
  are exercised. The full frontend suite was rerun after the CSS change.
- Ruff lint/format, ESLint, Prettier, TypeScript, production build, locked uv
  consistency and actionlint passed. The existing approximately 558.60 kB globe
  chunk warning remains visible; no threshold or test was weakened.
- Reference audits: 40 published SGP4 cases, six terrestrial transformations,
  32 expanded comparisons, 28 independent geodetic component cases and 28 separate
  algebraic round trips passed. These do not establish observation-based accuracy.
- Explicit migration/backup/restore selection: **five passed**. Fixtures and
  database operations target separate temporary archives.
- Focused local Chromium: **seven E7 scenarios**, two axe scans with zero reported
  violations, keyboard/native JSON export, exact response equality, and layout at
  320/1440 pixels passed. The isolated source archive digest remained unchanged.
- The container fixture seeder's UID-10001 ownership step was unsupported by
  local `/tmp` after creating its synthetic inputs. Native checks used the
  current-owner database in mode 0444; independent integrity/row checks confirmed
  exactly two synthetic records and its hash stayed unchanged. This native setup
  does not establish container ownership behavior; CI verifies that separately.
- Native local Firefox launch timed out with sandbox/font-cache/framebuffer errors;
  WebKit launch was refused for six missing host libraries. Their E7 flows were
  not locally verified. No browser assertion or application CSP was weakened.
- The complete local Docker browser/PDF/container release rehearsal was not rerun:
  the inherited VFS storage constraint left about 2.2 GiB on the root filesystem.
  Native Chromium was installed only under `/tmp` as an additional focused check.
  All three engines, seven PDFs and container/release verification subsequently
  passed in supported remote CI, as recorded below.

The full local Chromium history journey also passed all eight original cases plus
seven E7 cases, with no page/CSP errors. A fresh isolated Git-index checkout also
passed locked uv/npm installation, build,
frontend/API proxy, missing-database safety, explicit/duplicate initialization,
no-op migration, injected collection failure/recovery, restart and separate restore
rehearsal. Its tree was `02e9e0bdc2e1235647e7d8866b2c6f72307922cd`; subsequent
changes before the first publication were documentation-only. The later correction
changes browser harness/tests/documentation, with application code/dependencies
unchanged; exact corrected-tree setup is rechecked by remote CI. CI/publication
results are appended only when observed.

## First remote run and correction

Implementation commit `188d05201dd789c1d6429d3b1886a9a86d97114a` was pushed to the
engineering branch. [Run 40001685504](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/40001685504)
passed backend/frontend but failed the browser release step. Downloaded traces
showed Firefox's final E7 history request and WebKit's ground-track report request
returning actual gateway HTTP 429, not a contract or orbital-calculation failure.
No sealed successful release record was produced for that run.

The denser test traffic exhausted the unchanged one-calculation-per-second burst
budget. History/report journeys now explicitly schedule fixture calculation
requests at 1.05-second intervals, shared across their contexts. They never retry
responses, raise timeouts, bypass the gateway, relax production limits or change
assertions. Other browser journeys and E2 performance measurements remain
unchanged. Report-generation timing includes this deliberate test overhead.
Three deterministic fake-clock tests cover spacing, elapsed budgets, read-only
metadata exclusions and all calculation route families. The affected focused
backend/API/release selection passed **48 tests**. The revised full backend suite
passed **1,306 tests** and the complete local Chromium history journey passed
again, with and without trace recording. Twelve real calculation requests were
scheduled in the traced run, with nonzero waits retained in diagnostics. Frontend
application source/dependencies are unchanged from its 427-test passing state.
The corrected-commit remote results are recorded below.

## Published corrected implementation and remote evidence

- Implementation commit: `5d234c07ccea605acea381a8d3a3b02b8804c797`.
- [Exact-commit CI run](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/40003693468): **backend, frontend and release-images all
  succeeded**. Expected required execution steps passed; only the two optional
  manual image-retention steps were skipped on this ordinary push.
- Remote JUnit: **1,306 backend / 427 frontend tests passed**,
  zero failures/errors/skips. Locked dependency installation, lint/format,
  TypeScript/build, numerical references and migration/recovery checks passed.
- Original E1 **77 flows** (27 Chromium, 25 Firefox, 25 WebKit), E2 **62 checks**,
  and E6 **39 scenarios** / 12 cross-context round trips / 39 native portable
  downloads passed. Existing suites and assertions were retained.
- E7: **21 scenarios** (seven in each engine), three native captured-history JSON
  downloads, exact response/request equality, unchanged browser storage, keyboard
  interaction, and 320/1440-pixel layouts passed. The original read-only fixture
  archive remained unchanged. Transport/wrong-window injections used separate
  contexts; recovered responses came from the actual fixture API.
- Axe: E2 18 + E6 12 + E7 six = **36 scans**, zero reported violations. Manual
  review items remain; this is not full WCAG/screen-reader/device certification.
- **Seven PDFs passed**, including all 361 rows of the maximum-track PDF.
- Gateway configuration, loopback TLS/API smoke, exact frontend artifact/image
  comparison and source/image sealing passed. All **369 tracked source files**
  were independently matched against the published Git blobs. Both full and
  compact release records verified all **69 sealed evidence files** and the
  frontend artifact offline. Production approval remains false.
- Fresh remote checkout matched the exact commit tree. Locked installs,
  live proxy/startup/restart, safe initialization, failure recovery and separate
  backup/restore rehearsal passed, with unchanged source and equal restored
  fingerprints. These disposable local-container checks are not off-machine
  production recovery.
- Actual advisory lookup: **29 Python packages / zero matches / zero skipped**;
  npm **zero reported vulnerabilities**. This is lookup evidence at execution,
  not a permanent vulnerability or operating-system assurance.
- All nine expected artifacts belonged to this SHA and were unexpired when
  inspected. GitHub metadata confirmed configured seven-/90-day retention bounds;
  future expiration/global settings were not tested. Text/trace content and
  extracted PDF text passed the established secret/contact scan; database/key
  filenames were absent, ZIP integrity and PNG/PDF signatures passed. Browser
  inputs were restricted to declared public/synthetic fixtures. Image OCR was not
  performed. Existing synthetic URL-rejection canaries and Playwright image
  references were identified by the established narrow rules.
- GitHub annotated the existing `ubuntu-latest` migration and upload-artifact
  runtime transition; neither was a failed check. No workflow or runner setting
  was changed in E7.

| Plan criterion                         | Actual evidence                                                                | Result |
| -------------------------------------- | ------------------------------------------------------------------------------ | ------ |
| 1. Establish original failures         | Ten new regressions failed before fixes                                        | PASS   |
| 2. Preserve valid/partial/unknown data | Seven real-API shared fixtures accepted                                        | PASS   |
| 3. Refuse mismatches, preserve clocks  | Validator/UI tests, offset/microsecond cases, browser refusal/export checks    | PASS   |
| 4. Exact Retry and cancellation        | Initial/Next/Previous, stack/anchor and late-response tests                    | PASS   |
| 5. Actual browser recovery/export      | Seven E7 cases in all three engines, layouts/axe/native downloads              | PASS   |
| 6. Document compatible envelope        | API/OpenAPI/golden-payload/report-hash tests                                   | PASS   |
| 7. Complete relevant checks and CI     | All three jobs at the exact implementation SHA; full/compact evidence verified | PASS   |
| 8. Preserve/publish safe scope         | 22 reviewed files, 72 private files and earlier reports/branches preserved     | PASS   |

## Reviewed files and preserved boundaries

Runtime/documented API:
`backend/orbitiq/api/history.py`, `backend/orbitiq/api/history_schemas.py`,
`frontend/src/history-api.ts`, `frontend/src/HistoricalAnalysis.tsx`,
`frontend/src/style.css`.

Regressions/shared fixtures:
`backend/tests/test_history_contract.py`, `backend/tests/test_e4_release.py`,
`backend/tests/test_browser_pacing.py`,
`frontend/src/history-api.test.ts`, `frontend/src/HistoricalAnalysis.contract.test.tsx`,
`frontend/src/HistoricalAnalysis.test.tsx`,
`frontend/src/test-fixtures/history-windows.json`,
`scripts/verify_history_window.py`, `scripts/verify_history_browser.py`,
`scripts/browser_diagnostics.py`, `scripts/verify_report_browser.py`,
`scripts/run_browser_regressions.py`, `scripts/verify_release_evidence.py`.

Documentation: `README.md`, this report, `docs/engineering-e7-plan.md`,
`docs/engineering-e7-guide.md`. Earlier phase/E1–E6 reports are preserved.

The 72 private files, including the schema-3 two-snapshot application archive,
were verified unchanged against the trusted existing manifest before publication.
Raw database
hashing uses a SQLite DELETE-mode shared read transaction; logical fingerprints
are also compared. The database SHA-256 remained
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
The 22-file content/privacy, documentation links, syntax and whitespace review
passed; all previously tracked files outside E7 remained byte-identical.
Raw attachments, private research products/correspondence, databases, environment
files, credentials, caches and test artifacts are excluded from source publication.

GitHub currently reports the configured repository as public with ADMIN viewer
permission. `main` is reported unprotected; rulesets list is empty and the detailed
protection API returns 403. Required status enforcement is not established.
Repository visibility/settings were not changed. Publication targets only this
engineering branch; no merge, release, image registry publication or deployment.

## Remaining work and separate statuses

- E7: **engineering complete** for the selected history-window workflow on the
  implementation baseline above; final documentation publication receives its
  own exact-SHA CI verification. No merge or deployment is authorized by this status.
- E4: **OPEN**. Authorized hosting/public HTTPS, independent off-machine backup
  recovery, real monitoring alert delivery, exact authorized release verification
  and required-check enforcement remain separate production gates.
- Phase 11.3.1: **PARTIAL**; scientific evaluation **BLOCKED**. ESA time, KIN-quality
  qualification, frame alignment and temporal pairing remain unresolved.
  Historical availability/creation timestamps remain unknown; complete fitting
  lineage/statistical independence are not established. No genuine Swarm-A
  propagation or qualified real ESA residuals were calculated.
- Human screen-reader/physical-device acceptance, provider-specific collection
  scheduling/bulk policy and later product capabilities remain separately scoped.
  Browser-local investigations still require separate source archive recovery;
  no cloud-synchronized accounts/saves or global catalog completeness is claimed.
