# E5 implementation and acceptance report

Assessment: **23 October 2026 (IST)**. E5 local audit and acceptance: **COMPLETE**.
Publication and remote CI are tracked separately below. OrbitIQ production
readiness remains **NOT VERIFIED**.
See the [architecture/capability audit](engineering-e5-product-audit.md) and
[prioritized roadmap](engineering-e5-roadmap.md).

## Repository and scope

Starting clean branch: `engineering-e4-final-closure`. Starting commit:
`6bab52b268e0e5950d70f9dd9e7f54760bd002ea`. Dedicated branch:
`engineering-e5-product-acceptance`. The configured remote is the private
`BibinBinoy777/OrbitIQ` repository; GitHub reports administrative viewer permission.
The original E4 branch is preserved. No reset, rebase, force push, default-branch
merge, release, public deployment, DNS change or paid provisioning is included.

Eight-file scope: `frontend/src/scientific-api.ts`, its existing test file,
`scripts/verify_browser_critical.py`, new
`backend/tests/test_e5_product_acceptance.py`, `README.md`, this report and the
new E5 audit/roadmap. No dependency, lockfile, database schema, scientific engine,
existing CI workflow or earlier phase/engineering report is changed.

## Findings and changes

The actual architecture supports stored, bounded, exact-source exploration;
operator-controlled acquisition; backend numerical calculations; local saved
parameters; reports/downloads; historical rule findings; and operator replay.
It does not implement a global live satellite catalog, automatic provider
scheduler, multi-device/account saves, server report archive, browser replay
import or qualified genuine independent accuracy assessment. The audit maps each
material capability and its limits to source, APIs, journeys and tests.
The audit has 22 bounded capability rows. A fresh development OpenAPI inspection
found 15 registered GET operations, with no ingestion or public write endpoint.
README's outdated present-tense CI description is corrected; phase reports retain
their historical scope and bytes.

A demonstrated client defect accepted an otherwise valid TEME response for a
different instant. Four new cases failed against the old implementation: different
second, different microsecond, missing timezone and malformed supplied time.
The fix compares canonical six-digit UTC instants, accepting equivalent offsets.
Absent legacy response metadata remains unknown rather than manufactured. The
existing identity/frame/unit/finite-vector checks and all earlier assertions remain.
Five added tests cover those refusals and valid offset equivalence.

Three new cross-workflow backend cases use temporary public-reference-derived
fixtures for position, ground-track and comparison definitions. They verify missing
storage startup without initialization, explicit creation, exact references,
newer input, application recreation and restoration to a new path. Source hashes,
configuration identity, numerical vectors, time, units and frames survive unchanged
software/resources. Export IDs/execution/freshness metadata remain fresh; EOP table
age legitimately advances. The initial new test incorrectly required identical
execution-dependent table age; it was corrected to check that age advances while
all remaining resource/numerical fields stay equal. No existing test was weakened.

The existing real-service critical browser journey now additionally checks TEME
calculation from an explicit offset, UTC display/source hash/limitations, invalid
input recovery, actual playback to the final sample, stop/reset and no additional
API requests. These are assertions within existing flows, not inflated new flow
counts. No API or canvas mocking is added.

## Actual verification

- Final full backend: **1,278 passed**, zero failed/skipped, two existing warnings
  (Starlette TestClient deprecation and an intentional duplicate-ZIP rejection
  fixture). This includes all three new lifecycle modes and E3/E4 unit checks.
- Frontend after the time-contract fix: **350 passed in 25 files**, zero
  failed/skipped. Focused network contract: **12 passed**, rerun after formatting.
  ESLint, Prettier, TypeScript and Vite production build: **passed**. Initial
  Prettier detected the new test's layout; it was formatted and rechecked.
- Numerical audits: **40 SGP4**, **6 Earth-fixed**, **32 expanded scientific**,
  **28 independent-component geodesy plus 28 round-trip cases passed**. These are
  numerical checks, not independent satellite observations or accuracy evidence.
- Explicit migration/backup/restore selection: **5 passed / 57 deselected**; the
  deselection is the documented focused command, not skipped full-suite tests.
  Ruff lint/format and actionlint: **passed**.
- E3 isolated Git-index checkout: new locked `uv sync` / `npm ci`, build, absent
  storage liveness/503 readiness without creation, explicit init, duplicate-init
  refusal, no-op migration, Vite-to-API proxy, fixture provider failure/recovery,
  backend restart and separate full restoration: **passed**. Restored schema,
  all-table/payload/audit fingerprints and representative APIs matched the source.
- Advisory lookup: **29 Python packages, zero known matches, zero skips**; npm
  **zero reported advisories**. An initial uvx tools-directory error on read-only
  home was resolved using task-local `UV_TOOL_DIR`; both audits then executed.
  Lookup success is not comprehensive security assurance.
- Release targets built; Nginx configuration, real local gateway/API, request
  bounds/Host/CORS/header controls, capacity/rate refusal, missing-storage outage,
  recovery and same-image replacement: **passed**. Local test-CA TLS 1.2/1.3,
  trusted chain and untrusted/wrong-host refusal: **passed**. Public HTTPS: **not
  verified**.
- Full local E1/E2 browser/PDF runner: **passed in 1,355.598 seconds** in this
  managed Docker/VFS environment. **77 flows**: Chromium 27, Firefox 25, WebKit 25;
  **five explicit failure-state cases**; **two deliberate diagnostic probes**
  returned their required exit 1; every ordinary stage returned 0. These probes
  are expected negative checks, not suppressed failures.
- E5's offset/UTC/provenance/invalid-input recovery and playback/end/reset/no-new-API
  assertions passed in **all three engines**, within the existing flow count.
- E2: **62 checks**, **18 axe scans**, **zero reported violations**. Nine scans
  retain incomplete findings. Four viewport widths and keyboard/focus, save/export
  denial/retry and renderer recovery passed; no complete conformance certification
  is claimed. Chromium/WebKit rendered WebGL2; Firefox used the documented 2D
  fallback. Real devices/screen readers/native Firefox 3D remain unverified.
- **Seven PDF content checks passed**, including all **361 maximum-track rows**,
  hashes, provenance/limitations and paired JSON. Chromium native PDF only;
  Firefox/WebKit printable preview is verified, their native PDFs are not. One
  actual generated comparison preview was visually inspected as well.
- E4 capture/seal/offline file-integrity verification: **passed** for reviewed
  index tree `31083e4cd3bec7886852c42a30545c871635f1a6`, before this results-only
  documentation/README reconciliation. The local record says `reviewed-index`,
  `release_candidate=false`, `production_approved=false`; it does not identify
  a committed Git release. No application, test, dependency or runner code changed
  after these checks. Remote CI must bind the final published commit separately.
- A bounded privacy scan checked all **197 local release-evidence files**,
  including trace contents, and found no credential/contact patterns or database
  files. The actual browser fixture archive/evidence remained unchanged. Traces
  and generated reports contain only labelled reference/synthetic inputs.

Local detailed receipts remain under `/tmp/orbitiq-e5/`: JUnit, reference/audit
results, fresh-checkout summary/recovery manifest, browser evidence, PDF pairs and
`release/verified-release.json`. These are temporary engineering evidence, not
durable application data. Reproduce with the existing [E1/E2 commands](engineering-e1-browser-pdf-ci.md),
[E3 installation procedure](engineering-e3-reliability-recovery.md#reproduce-verification)
and [E4 candidate procedure](engineering-e4-release-readiness.md#exact-source-release-verification).
No redundant workflow or test exclusion is introduced.

## Preservation and boundaries

The pre-edit manifest verifies 72 private files against the trusted earlier
baseline. The real SQLite file is hashed under a DELETE-mode shared read
transaction, with a separate logical consistent fingerprint: schema **3**, **two
snapshots**, SHA-256
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Final post-regression preservation checks confirmed the same bytes and logical
fingerprint for the real archive and all 72 private files. The tracked-file
manifest confirms every previous phase/E1–E4 report and files outside the eight-file
scope unchanged. Existing E1–E4 assertions are retained.
Eight-file content/syntax/local-link/privacy review passed; the staged diff is
limited to those files. Tests use separate fixtures; private data, credentials,
raw attachments and databases are excluded from publication and CI artifacts.

E4 remains **OPEN**: hosting/HTTPS/persistence, independent off-machine recovery,
actual alerts and branch protection/required enforcement remain blocked. E4's
bounded artifact-retention gate has previous exact-commit verification; this
milestone does not provision its missing infrastructure.

**Phase 11.3.1: PARTIAL. Scientific evaluation: BLOCKED.** ESA time clarification,
KIN-quality acceptance and frame alignment remain unresolved. Historical
availability/creation timestamps remain unknown; full fitting lineage and
statistical independence remain unestablished. No genuine Swarm-A propagation,
qualified residuals, independent-accuracy or historical-forecast claim is made.

## Publication milestones

Local checks: **PASS for the implementation and reviewed index recorded above**;
subsequent edits are documentation-only and receive link/privacy/whitespace review.
Publication: prepared on `engineering-e5-product-acceptance`; not yet committed
or pushed at this checkpoint. Remote CI: **pending exact published commit**.
Production deployed: **NO**. Production infrastructure verified: **NO**.
