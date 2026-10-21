# Phase 11.3.1-P — verified implementation publication baseline

Prepared on **21 October 2026** under the user's explicit authorization to commit
and push the reviewed implementation to a dedicated branch, then verify CI for
its exact commit. **This file records the pre-commit verification snapshot.** It
makes no advance claim that a push or remote check succeeded. Final publication
receipts identify the actual branch-tip SHA and GitHub Actions run separately;
local tests, publication, remote CI and scientific qualification are distinct.

Phase 11.3.1 remains **PARTIAL**, scientific pairing/evaluation **BLOCKED**.
No provider response, time correction, IGb08 alignment, KIN-quality approval,
operational adapter, real Swarm-A propagation or ESA residual was introduced.
The [provider inquiry tracker](phase-11.3.1-provider-inquiries.md) now records both
ESA and CelesTrak inquiries as **SUBMITTED, user-reported; AWAITING RESPONSE**.
Actual submission dates/times remain unknown. The assistant sent no messages and
no private mail body/contact information is included.

## Reviewed scope and preserved work

Starting branch `phase-11.3.1-readiness-hardening`, HEAD
`67abe1588bcada4fd30ee46134a71c4d27dcbd05`, empty index and **63** dirty paths.
Origin: `https://github.com/BibinBinoy777/OrbitIQ.git`.
The existing remote repository's visibility is unchanged. A detached worktree
from that exact HEAD received only the allowlisted publication files. It excludes
**42** earlier history/observation/UI/configuration/report paths. Their original
bytes remain in the main workspace, with no reset, discard, rebase or overwrite.

The publication contains 25 files (two previously tracked script modifications,
23 additions), including necessary reference-inspector/qualification dependencies:

- `scripts/inspect_historical_gp.py`
- `scripts/reconcile_historical_gp.py`
- `scripts/inspect_historical_csv.py`
- `scripts/inspect_swarm_reference.py`
- `scripts/qualify_swarm_inputs.py`
- `scripts/assess_swarm_pairing.py`
- `backend/tests/conftest.py`
- `backend/tests/test_historical_csv_intake.py`
- `backend/tests/test_phase113_swarm_inspection.py`
- `backend/tests/test_phase1131_qualification.py`
- `backend/tests/test_swarm_pairing_assessment.py`
- `docs/phase-11.3-dataset-provenance.md`
- `docs/phase-11.3.1-report.md`
- `docs/phase-11.3.1-integration-results.json`
- `docs/phase-11.3.1-frame-and-time-qualification.md`
- `docs/phase-11.3.1-historical-input-request.md`
- `docs/phase-11.3.1-historical-csv-intake.md`
- `docs/phase-11.3.1-csv-intake-report.md`
- `docs/phase-11.3.1-csv-verification.json`
- `docs/phase-11.3.1-scientific-pairing-report.md`
- `docs/phase-11.3.1-scientific-pairing-verification.json`
- `docs/phase-11.3.1-scientific-clarification-request.md`
- `docs/phase-11.3.1-provider-inquiries.md`
- `docs/phase-11.3.1-publication.md`
- `docs/phase-11.3.1-publication-verification.json`

The structured verification lists every excluded original path and included-file
hash. Earlier historical reports retain their original execution states and
full-workspace counts; they do not assert that excluded features ship in this
branch. The current inquiry tracker supersedes prior prepared/unsubmitted
statements for current inquiry status. No historical scientific result was
rewritten as a later provider answer or a successful residual evaluation.

## Reproducibility correction

Review found that three source-diagnostic tests imported an unpublished optional
observation-validation application module solely to install a failure sentinel.
Publishing that unrelated application feature would expand the milestone scope.
A shared test fixture now installs the same residual-failure guard against the
real module when present, or a test-only module sentinel when absent. All existing
assertions remain; no tests or scientific functions were disabled or skipped.
An extra test verifies that an attempted residual call still raises.

The fixture and three test files are the only implementation-related edits made
for this publication. Scientific/runtime services, CSV parsing, reconciliation,
source time semantics, source inputs, tolerances, EOP policy, dependencies,
lockfiles, API/UI, Docker configuration and CI workflows are unchanged. The entire
full-workspace and isolated-publication suites reran after this test portability
correction. No real residual calculation was enabled.

## Fresh local verification of both scopes

| Check | Full workspace | Isolated publication checkout |
| --- | --- | --- |
| Complete backend suite | **1,178 passed** | **1,089 passed** |
| Focused GP/CSV/source/qualification/pairing suite | **304 passed** | **304 passed** |
| Frontend tests | **344 passed**, 25 files | **307 passed**, 23 files |
| Locked Python installation | PASS | PASS |
| Fresh frontend `npm ci` | Not rerun; existing installation | PASS |
| Ruff lint/format, ESLint, Prettier, TypeScript, Vite build, Git whitespace | PASS | PASS |
| SGP4 / earth-fixed / expanded-science audits | **40 / 6 / 32 passed** | **40 / 6 / 32 passed** |
| Independent geodesy / separate round-trips | **28 / 28 passed** | **28 / 28 passed** |
| Golden published components / exact offline replays | **6 / 3 passed** | **6 / 3 passed** |
| Fresh Chromium/Firefox/WebKit browser flows | **77 passed** | **35 passed** |
| Fresh Chromium PDF checks, including 361-row maximum track | **7 passed** | **7 passed** |

The **89 backend / 37 frontend** count differences belong to excluded older
application work; none is a deleted/skipped publication test. The existing
published baseline had 895 backend cases; adding the reviewed source/qualification,
CSV and pairing cases plus the guard test yields 1,089. Expected remote CI counts
are therefore **1,089 backend / 307 frontend**, not the full workspace counts.
Starlette/httpx deprecation, intentional duplicate-ZIP fixture and bundle-size
advisories remain visible rather than being suppressed.

Browser checks use exact owned copies of each scope's backend, built frontend,
lockfile and scripts, on separate internal Docker networks with no published
ports and unmocked APIs. The original ordinary database is read only to make
isolated copies. Full-workspace observation checks use explicitly synthetic
6251 arithmetic/UI fixtures, with zero independent-observation claims; these are
not genuine Swarm-A calculations. Firefox/WebKit exercise browser/report/download
flows; native PDF generation/inspection is through Chromium. Test containers and
networks are removed after completion. These local checks do not deploy the app.

## Publication safety and persistence

Every allowlisted file was read and reviewed by content, including JSON structure
and referenced numerical vectors. Automated checks for private contact details,
email addresses, credentials and key/token patterns returned no matches. Detailed
older numerical results are published mathematical reference/synthetic-fixture
audit outputs with existing source notices, not actual private ESA coordinates
or source attachments. Actual intake sections contain hashes, timestamps,
identifiers, diagnostic counts and unresolved qualification status only.

Original GP JSON/CSV, ESA ZIP/SP3/PDF products, private correspondence, raw or
private replay bundles, database files, environment/configuration secrets,
research document captures and files lacking source redistribution clearance are
excluded. They remain in existing ignored private storage; none was deleted to
clean Git. The starting 56 private-file hashes and complete read-only ordinary
database schema/rows/integrity fingerprint are checked again before publication.
The database remains schema 3, two genuine ISS snapshots, no Swarm-A snapshot and
SHA-256 `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
No initialization, migration, ingestion, restore or ordinary database write occurs.

## CI review and exact publication plan

The unchanged `.github/workflows/ci.yml` runs on push and pull requests with
read-only `contents` permission and three jobs:

- **backend**: Python 3.12 / uv 0.12.23, locked installation, full pytest, SGP4,
  terrestrial/scientific/geodetic audits, five selected migration/backup/restore
  fixture tests, Ruff lint and formatting.
- **frontend**: Node 24, `npm ci`, tests, lint, formatting, TypeScript/build and
  built frontend artifact upload.
- **release-images**: locked local Docker builds, Nginx validation and isolated
  empty-fixture API checks. It does not publish images or deploy infrastructure.

No provider credentials, real database or private source evidence is required by
CI. Missing private input must never be replaced with fabricated observations.
Golden replays and browser/PDF checks are additional local verification; the
unchanged workflow does not run those checks remotely. No redundant workflow or
manual dispatch is added. Push should naturally trigger the existing workflow.

After all checks succeed, create `phase-11.3.1-verified-publication`, stage only
the 25 allowlisted paths, inspect the complete staged diff, commit, record its
SHA and push normally to origin. Do not force-push, merge to `main`, create a
release, change visibility, deploy, modify DNS or alter production infrastructure.
Verify the actual pushed branch tip and every expected job against that SHA;
a result for the old starting commit is insufficient. Publication credentials
were exercised successfully through ordinary read-only GitHub/git requests.

GitHub reports `main` **protected=false**, at
`d9f85d5d6e28cea90f25965c761422f16705eea8`. The repository ruleset query returned
**HTTP 403**, explaining that this feature requires GitHub Pro or a public
repository. Required-rule details are therefore not independently verified; no
protection/ruleset setting was changed and no upgrade or visibility change was
attempted. Successful CI will not close the branch-protection production gate.

Local logs/snapshots are under `/tmp/orbitiq-publication-1131p/`; they are not
independent backups. The 120-s and 37.12-ns source time conflicts, unsupported
time conventions, KIN quality, IGb08 alignment, historical selection/availability,
provenance and independence remain unresolved. Phase 8 public hosting/HTTPS,
off-machine recovery, actual alert delivery and production verification remain
separate open milestones. The next scientific action is to review provider
responses when supplied; publication does not wait for or replace that review.
