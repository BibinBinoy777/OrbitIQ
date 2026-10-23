# Engineering milestone E7 — historical window integrity and recovery

Status: **E7 remains open** pending corrected-commit remote CI verification.
Local checks passed; the first published CI run failed as investigated below.
Local results alone do not close the remote gate.

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
  All three engines, seven PDFs and container/release verification must run in
  supported remote CI before E7 acceptance is complete.

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
Exact corrected-commit remote CI remains pending at this checkpoint.

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

- E7: remote CI/artifact verification pending before engineering closure.
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
