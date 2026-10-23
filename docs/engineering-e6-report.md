# Engineering milestone E6 — stored onboarding and portable recovery

Status: **E6 engineering acceptance passed** on the published implementation
commit below, with complete remote CI and retained-evidence verification. This
report records that implementation baseline. The documentation receipt is
published separately and its exact commit receives its own CI verification.

## Baseline and implementation

Started from clean `engineering-e5-product-acceptance` at
`7a0dc3de21aa0c18a44500edc5d924c484bef7fe`. Dedicated branch:
`engineering-e6-onboarding-recovery`. No new dependency, lockfile, API endpoint,
migration, server storage, cloud resource or telemetry was introduced.

Previously Explorer required a manual NORAD input and snapshot load. E6 adds a
catalog entry panel using existing `/api/snapshots?limit=5` and `/api/readiness`
contracts. It presents loading, populated, empty, stale, incomplete and unavailable
states; independent collection status; retained metadata after failure; and retry.
Selection validates the full exact source before opening it. Counts retain the
API's bounded history-anchor scope, not unique satellites or global usable-source
counts. Acquisition can deduplicate; recent retrieval does not refresh the epoch.
No browser provider collection or fixture substitution is introduced.

Local saves already use `orbitiq.saved-investigations.v1` in localStorage. They
contain inputs and exact references, not results/findings. E6 wraps one existing
saved record in a version-1 JSON bundle and supports `snapshot`, `position`,
`ground-track` and `comparison`. Notes are excluded by default, explicitly opt-in.
Validation precedes preview and confirmation. Existing content is idempotent;
UUID collisions require explicit copy, with a fresh UUID and original timestamps.
Web Locks, destination revalidation and an atomic write protect cooperating tabs.
Corrupt, unavailable or full storage is never cleared to make import succeed.

No source payloads, database, evidence results, findings or scientific qualification
are invented/restored. Exact missing sources fail honestly when opened, without
latest-source substitution. See [usage, schema example and limitations](engineering-e6-guide.md).

Browser testing found and fixed an offline lazy-report dependency failure when
the first restored save appeared. Saved investigations now loads its report
component with that screen; report generation semantics remain unchanged.

## Acceptance and actual local results

Acceptance requires truthful catalog states; backend source validation; native
export and confirmed recovery in independent browser storage; protection against
malformed/quota/collision/concurrent changes; honest missing-source errors;
responsive accessible controls; regression/CI coverage; and preservation of data.

- Backend: **1,286 passed**, zero failures/skips, two existing warnings (Starlette
  test-client deprecation and a deliberate duplicate-ZIP-member rejection fixture).
- Frontend: **405 passed** across 28 files, including 55 new E6 tests and the
  documentation example parsed by the production validator.
- ESLint, Prettier, TypeScript, production build, Ruff lint/format and actionlint:
  passed. Existing 558.60 kB globe-chunk size warning remains, not a build failure.
- Unchanged backend reference audits: 40 SGP4, six terrestrial transformations,
  32 expanded comparisons, 28 independent geodetic component cases plus 28 algebraic
  round trips passed. These are numerical checks, not observation-based accuracy.
- Migration/backup/restore selection: five passed. Fresh isolated Git-index
  checkout: locked uv/npm installs, build, live frontend/API proxy, missing-database
  safety, explicit initialization, duplicate-init refusal, no-op migration,
  injected collection failure/recovery, restart and separate restore all passed.
- Focused actual-browser E6: **13 scenarios in each of Chromium, Firefox and
  WebKit**, four supported-mode cross-context round trips per engine, 13 retained
  native downloads per engine, and four axe scans per engine with zero violations.
  Layout checks passed at 320, 390 and 1440 pixels. Native downloaded bytes were
  imported from retained files; original-context storage remained unchanged.
  Default note exclusion and explicit inclusion were checked for every mode.
  Eleven malformed/unsupported file cases per engine preserved destination saves;
  cancellation, collision copies, repeated import, concurrent tab edits, injected
  quota/persistence/export errors and missing exact sources were exercised.
- Chromium/Firefox used context offline mode. Playwright WebKit 1.62 rejected even
  new in-memory File reads with both arrayBuffer and FileReader under offline
  emulation (`NotReadableError`). WebKit instead denied all HTTP and proved a
  health request failed before the same native-file workflow. This does not
  certify physical Safari devices or offline application installation.
- Local release image capture, nginx configuration and isolated fixture TLS/API
  proxy checks passed. **Full local E1/E2/PDF regression and final seal did not
  complete**: first attempt exited 1 before Chromium launch (`ENOSPC` creating
  browser artifacts); a second attempt exited 125 during container creation due
  to the workspace Docker VFS filesystem filling. A bounded 1 GiB browser `/tmp`
  memory filesystem was added, but available disk still prevented the image copy.
  Only disposable E6 containers, synthetic volumes, known E6-generated build
  cache and superseded untagged E6 images were removed. Previous reports, private
  data, E1–E5 tagged images and branches were preserved. No earlier E5 browser/PDF
  success is claimed as a fresh E6 result.

The existing CI release job now runs E6 alongside the unchanged required E1
browser/PDF and E2 suites. The release gate requires E6 recovery/axe/layout
receipts and hashes the actual native bundle artifacts. Eight new failure probes
cover missing/failed E6 evidence. No redundant workflow was added. The exact
published commit must pass backend, frontend and release-images, including full
browser/PDF checks and a committed-source seal, before E6 can close.

## Published baseline and remote verification

Implementation commit: `8825feec429cd28154dc7c42c9d55fe978dc37ac`.
Source tree: `117ddbd68d2032b360e29dbfb7ab701fc89c93cd`.
Published to `origin/engineering-e6-onboarding-recovery`.
[Exact-commit CI run 39994831581](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39994831581)
completed successfully. `backend`, `frontend` and `release-images` each passed;
all three check runs identify that exact SHA. Only the two optional manual
image-retention steps were skipped, as expected for a normal push.

Downloaded JUnit and sealed evidence confirm:

- **1,286 backend tests and 405 frontend tests**, zero failures/errors/skips.
- **77 E1 browser flows**: Chromium 27, Firefox 25, WebKit 25, plus five explicit
  transport/WebGL failure-state checks and two deliberate failing diagnostic probes.
- **62 E2 checks**, including 18 WCAG A/AA axe scans with zero violations;
  manual-review/incomplete items remain distinct from automatic passes.
- **39 E6 scenarios**, 12 independent-context round trips, 39 native downloaded
  bundles, 33 invalid-file rejection checks, 12 additional axe scans with zero
  violations, and mobile/desktop layout checks in all three engines.
- **Seven PDFs** passed text/provenance/layout checks, including the maximum
  361-row track. Compact and diagnostic artifact copies are the same seven PDFs,
  not additional independent checks.
- All numerical reference audits, migration/restore selection, fresh-checkout
  installation, failure/restart/recovery rehearsal, lint/format/types/build passed.
- Python advisory lookup covered 29 packages without skipped packages or matches;
  npm reported zero advisories. These are dependency checks, not OS assurance.
- Exact committed source hashes, image IDs, frontend artifact bytes, PDFs,
  recovery receipts and portable bundle files passed release-seal verification.
  Both full and compact retained evidence passed independent offline hash checks.
  `release_candidate` is true; **`production_approved` is false**.

Nine artifacts were downloaded and inspected. Content/trace/PDF scans found no
unexpected credentials/contact information or private database/research files.
Observed metadata confirms bounded 7/90-day retention for these artifacts only;
future expiry and repository-wide retention settings were not verified.

The final documentation update changes only this report. Application, tests,
locks and workflow behavior remain byte-identical to the named implementation.
Its independent exact-head CI result is reported at publication; this receipt
does not substitute an earlier run for a later commit's verification.

| Milestone                          | Evidence/status                                                       |
| ---------------------------------- | --------------------------------------------------------------------- |
| Local feature verification         | Passed; full local browser launch blocked by disk as documented above |
| Published software                 | Dedicated E6 branch, exact implementation commit above                |
| Remote CI                          | Full implementation run and retained evidence verified above          |
| Production deployed                | No                                                                    |
| Production infrastructure verified | E4 remains OPEN; external gates unresolved                            |

## Reviewed publication scope

Exactly 17 files:

- `README.md`
- `frontend/src/App.tsx`
- `frontend/src/SavedInvestigations.tsx`
- `frontend/src/StoredCatalog.tsx`
- `frontend/src/PortableInvestigations.tsx`
- `frontend/src/investigation-storage.ts`
- `frontend/src/portable-investigation.ts`
- `frontend/src/style.css`
- `frontend/src/StoredCatalog.test.tsx`
- `frontend/src/PortableInvestigations.test.tsx`
- `frontend/src/portable-investigation.test.ts`
- `scripts/verify_engineering_e6.py`
- `scripts/run_browser_regressions.py`
- `scripts/verify_release_evidence.py`
- `backend/tests/test_e4_release.py`
- `docs/engineering-e6-guide.md`
- `docs/engineering-e6-report.md`

Complete content, link/fragment, fenced-example, whitespace, syntax, private-data
and credential/contact-information scans passed. No unrelated files are included.
No raw attachments, research products, correspondence, credentials, databases,
private evidence manifests or diagnostic output are staged. Publication is to the
dedicated engineering branch only, without force-push, merge or deployment.

## Integrity, limitations and remaining gates

All **72 private files** match the trusted pre-existing E2 manifest and the E6
starting manifest. Database schema 3 and its two real ISS snapshots are unchanged;
raw SHA-256 under a SQLite shared read transaction remains
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Logical fingerprint checks passed. All previous phase and E1–E5 reports are
unchanged. Rehearsals used fresh synthetic databases, never the real archive.

E4 remains **OPEN**. Hosting/public HTTPS, independent off-machine recovery and
monitoring/actual alert delivery remain blocked. `main` remains at
`d9f85d5d6e28cea90f25965c761422f16705eea8` with `protected: false`; GitHub's ruleset
API returned 403 requesting a plan upgrade or public repository. Neither was
performed. Default-branch protection/required CI remains unresolved. Bounded
artifact retention is a separate previously verified gate. Portable files do not
replace database backup or disaster recovery. No public deployment, DNS change,
new paid service/account, private-data upload or default-branch modification.

Phase 11.3.1 remains **PARTIAL**; scientific evaluation remains **BLOCKED**.
ESA time clarification, KIN-quality qualification and frame alignment remain
unresolved. Historical availability/creation timestamps remain unknown. Complete
GP fitting lineage and statistical independence remain unestablished. No genuine
Swarm-A propagation or qualified Swarm-A residuals were calculated.

Remaining portability limits: one record per file, 16 KiB UTF-8 maximum, existing
50-save / 256 KiB browser-store limit, Web Locks required for safe import, optional
notes in plaintext, exact source archive still required for reconstruction. Direct
developer-tool/old non-cooperating writers are outside the cross-tab lock guarantee.
Automated axe passes do not replace manual accessibility assessment.
