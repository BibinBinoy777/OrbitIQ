# Phase 11.3.1 interim verification and publication review

Local verification on **21 October 2026**. The user authorized publication of the
completed receipt/readiness/reconciliation work and exact-commit CI verification.
**Correction request: SUBMITTED, according to the user's interim milestone
instruction. Corrected attachment: AWAITING RESPONSE. Real replacement
reconciliation: NOT STARTED. Scientific qualification: PARTIAL; evaluation BLOCKED.**
No correction-submission timestamp was supplied; it remains unknown. This task
did not send email, submit a form, authenticate to a provider or complete CAPTCHA.
No private correspondence or personal contact/IP information is reproduced.

## Scope and current state

Starting branch: `phase-11.3.1-readiness-hardening`, HEAD
`371ce35b577209401ba7961e5bd29c3bd65a9c4d`, matching the configured origin branch.
Origin is `https://github.com/BibinBinoy777/OrbitIQ.git`; the repository remains
private. The index was empty, with **57** modified/untracked paths. Saved a
**300-file** source/report baseline, all **23** private data hashes and complete
read-only database schema/table/integrity/foreign-key fingerprints. The prior
corrected-export verification's source manifest matched before the status update.

Reviewed the complete tracked diff and the selected source, tests, receipt,
readiness reports and structured evidence. The proposed commit includes exactly:

- `scripts/reconcile_historical_gp.py`
- `backend/tests/test_historical_gp_reconciliation.py`
- `docs/phase-11.3.1-historical-attachment-assessment.md`
- `docs/phase-11.3.1-corrected-export-request.md`
- `docs/phase-11.3.1-corrected-export-readiness.md`
- `docs/phase-11.3.1-corrected-export-results.json`
- `docs/phase-11.3.1-interim-publication.md`
- `docs/phase-11.3.1-interim-verification.json`

The first six paths were the unpublished receipt/corrected-export readiness work;
the last two record this review and fresh verification. The existing published
intake and scientific runtime are unchanged. **No new functionality** was added
in this milestone. Only the active correction-request document was updated from
prepared to user-reported submitted. Previous reports/evidence retain their
historical execution states; their earlier unsubmitted/local results are not
rewritten as if they occurred after the user's email or this publication.

The other **51** original dirty paths remain local: earlier Phase 11 history and
observation capabilities, their tests/docs, Swarm reference inspection and time
qualification, and associated shared runtime/UI/configuration changes. They are
outside this scoped milestone commit. The structured evidence lists their paths.
No reset, discard, rebase, force-push or overwrite is required.

The private inventory contains only the original rejected historical attachment:
1,227 bytes, SHA-256
`c55dc4cbb2331a162014833a1a354e6f62ff4572d5238954b8108f69cae3053c`.
There is no corrected export. The original GP attachment, private receipts,
ESA ZIPs, database and private validation products remain ignored and byte-identical.
No normal database initialization, migration, ingestion, restoration or write
occurred. Existing real-history/archive data was used only through separate
read-only disposable copies for UI regression checks.

## Fresh verification of both scopes

A separate detached worktree at the published starting HEAD received only the
six intended milestone paths. It excludes the 51 earlier uncommitted paths.
This tested what the proposed publication contains independently of the full
workspace. Source/test bytes match the reviewed originals; no fixture or test
was disabled to change the counts.

| Newly executed check | Full workspace | Isolated publication checkout |
| --- | --- | --- |
| Locked uv install and complete backend pytest | **1,073 passed**, no failures/errors/skips | **895 passed**, no failures/errors/skips |
| Frontend tests | **344 passed**, 25 files | **307 passed**, 23 files; fresh `npm ci` passed |
| Ruff lint/format, ESLint, Prettier, TypeScript, production build, Git whitespace | Passed | Passed |
| Published SGP4 / terrestrial / expanded-science audits | **40 / 6 / 32** passed | **40 / 6 / 32** passed |
| Geodesy | **28** independent mathematical cases + **28** round-trips | **28 + 28** passed |
| Golden lifecycle | **6** published components + **3** offline replays passed | **6 + 3** passed |
| Three-engine browser flows | **77 passed** | **35 passed** |
| Chromium application PDF checks | **7 passed**, including **361** maximum-track rows | **7 passed**, including **361** maximum-track rows |

The published baseline has 855 backend tests; this commit adds all **40** synthetic
reconciliation tests, giving 895. The full workspace has 178 additional tests in
the excluded earlier Phase 11 work. Similarly, its 37 additional frontend tests
belong to excluded history/observation UI work. Expected remote CI counts are
therefore **895 backend / 307 frontend**, rather than 1,073 / 344.

Workspace browser coverage: 24 historical-analysis, 21 critical saved/share flows,
14 report/export flows, six empty observation-archive checks and 12 controlled
synthetic observation checks. The publication checkout has the applicable 21
critical and 14 report/export flows; it does not contain the excluded UI features.
Each suite ran in Chromium, Firefox and WebKit, without API/canvas mocks, against
loopback services inside separate internal Docker networks with no published ports.
No public service was deployed. The controlled 6251 fixture contains explicitly
synthetic arithmetic discrepancies and **zero independently verified observations**;
it is not real Swarm-A evidence.

Tests mounted owned copies of exact backend, built frontend, gateway and lockfile
bytes; the ordinary database was copied read-only. Source and runtime fingerprints
were recorded. Seven Chromium-generated PDFs per scope were checked against their
captured JSON, pagination, warnings/source identity and all maximum-track rows.
Firefox/WebKit checks cover report/download/print presentation, not their native
PDF generators. This does not validate physical printers or observational accuracy.

Initial browser **preflight** attempts stopped before browser flows because the
cached local API image's `/app/uv.lock` was unreadable to its non-root user.
The final test setup added a read-only, readable **owned copy of the unchanged
lockfile**. No image, application, repository permission, scientific guard, test
assertion or deployment configuration was changed. Retained both failed preflight
logs and fresh final browser/PDF evidence. Startup health probes may fail before
the service is ready; all actual final test commands succeeded. Owned containers
and internal test networks were removed.

Existing Starlette/httpx, intentional duplicate-ZIP fixture and globe bundle-size
advisories remain visible. They did not fail checks. Previous temporary execution
directories were unavailable at task start, so verification was run afresh rather
than inferred from old log references. Repository reports and private source data
were present and preserved.

## Publication safety, CI and preservation

Source/test review confirms strict JSON acceptance is unchanged. Leading-decimal
malformed input stays rejected. The reconciliation helper cannot accept sources
or enable scientific evaluation even when a synthetic comparison matches; absent
replacement bytes stop it before original assessment replay. No real replacement
was parsed or reconciled, no original was repaired and no real Swarm residual
was generated in this milestone.

Reviewed files contain public-safe source/test code, diagnostic metadata, hashes,
limitations and status only. No raw GP attachment, ESA source XYZ/product bytes,
database, email export, private evidence package, credentials, tokens, key material
or submitted-correspondence contact/IP data is included. Existing tracked paths
were checked for prohibited artifacts; all 23 private files remain ignored.
Browser reports, screenshots/PDFs, fixture archives and raw execution logs stay
in the task's private `/tmp` verification directory, not in the commit.

All **299** other starting source/report files and all 23 starting private files
are unchanged; the active correction-request status is the sole intentional
starting-file edit. Original database SHA-256 remains
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`, with matching
full schema/table/integrity/foreign-key fingerprints.

Existing `.github/workflows/ci.yml` runs on pushes, pull requests and manual
dispatch with `contents: read`. It already covers locked backend/frontend
installation, full tests, science/geodesy audits, selected migration/backup fixture
checks, lint/format/build, frontend artifacts and locked release-image smoke tests.
No workflow change or extra secrets are required. Expected jobs: `backend`,
`frontend`, `release-images`. Image checks do not publish to a registry or deploy.
Browser/PDF checks above are local checks; the existing CI does not run them.

This document records the **pre-publication** verification checkpoint. A normal
explicit eight-path commit and push of the existing dedicated branch are authorized.
Exact final SHA, triggered run and actual job/step outcomes must be checked after
the push and reported against that latest tip; earlier successful CI cannot verify
this commit. No merge, tag/release, visibility/settings, DNS or infrastructure
change is authorized. Main still reports `protected=false`, at
`d9f85d5d6e28cea90f25965c761422f16705eea8`; required-check enforcement is not
established or changed by this task.

## Scientific and production milestones

The corrected attachment is awaiting the provider response. Actual replacement
strict parsing/reconciliation, temporal pairing and selection are NOT STARTED or
BLOCKED. Time handling remains qualified only for the prior supported subset;
**5,118** conversions and **2,529** exclusions are preserved prior diagnostics,
not a new full-source approval. IGb08 alignment, reference-quality acceptance,
source authentication/availability, actual-pair provenance and independence,
operational-adapter qualification, real residuals and independent prediction
accuracy remain unresolved. Uncertainty is not quantified. No current GP was
downloaded as a substitute and no transformation parameters were invented.

The next data action is to wait for and preserve the original corrected export,
not repeatedly resubmit the request. Keep unknown availability unknown and any
future permitted comparison explicitly retrospective where supported.

Local verification, code publication, exact-commit CI, scientific qualification,
production deployment and production-infrastructure verification are separate.
Phase 11.3.1 is not complete. Phase 8 public hosting/HTTPS, off-machine recovery,
actual production alert delivery and branch protection remain open. No production
deployment or infrastructure verification is performed by this milestone.
