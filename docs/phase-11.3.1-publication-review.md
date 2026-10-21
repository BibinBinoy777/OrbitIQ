# Phase 11.3.1 readiness publication review

Pre-publication review executed locally on **21 October 2026** under the user's
explicit safe-publication request. This is a new checkpoint; prior implementation
reports and their structured evidence remain unchanged as historical records.
Publication does not complete scientific qualification or production readiness.

## Scope and preservation

Starting branch: `phase-10-evidence-replay`, HEAD
`be3710dae9f21bae817637d7bfdb87509b3f6a34`. The configured remote is
`https://github.com/BibinBinoy777/OrbitIQ.git`; GitHub reports the repository private.
The starting index was empty, with **56** modified/untracked paths. Saved source
hashes for **293** nonignored files and **16** private data files. The previous
readiness verification's source manifest matched before changes.

Created `phase-11.3.1-readiness-hardening` at that HEAD without resetting, rebasing
or discarding the working tree. The proposed publication includes exactly:

- `scripts/inspect_historical_gp.py`
- `backend/tests/test_historical_gp_intake.py`
- `docs/phase-11.3.1-historical-intake.md`
- `docs/phase-11.3.1-readiness-report.md`
- `docs/phase-11.3.1-readiness-results.json`
- `docs/phase-11.3.1-publication-review.md`

The first five paths are the reviewed readiness implementation and its original
local evidence. This sixth path records the publication-specific review. The
other **51** original modified/untracked paths belong to earlier Phase 11 work
and remain local, excluded from this commit. This is deliberately a scoped
readiness publication, not publication of every locally implemented Phase 11
feature. The older ESA inspector, time qualifier, observation extension, history
features and their reports are not added by this commit.

Original database, private source ZIPs, receipts and qualification outputs remain
unchanged and ignored. No historical GP attachment is present. Reviewed source,
tests, documentation and structured metadata contain no private correspondence,
personal contact/IP information from the request confirmation, source XYZ data,
credentials, tokens, private keys, database or licensed ESA product bytes. Existing
tracked paths were also checked for prohibited database/archive/email/key artifacts.
No private file was removed or edited to obtain a clean publication scope.

## Isolated-checkout dependency correction

The original readiness test imported `orbitiq.observation_validation`, which is
part of the separate, still-unpublished Phase 11 extension. Publishing only these
five readiness paths would otherwise fail test collection on a fresh checkout.

Changed **only that readiness test**: it now uses published baseline dependencies,
forbids importing observation/residual modules while freshly loading the intake
tool, and retains the real residual-call sentinel when the larger local suite has
already loaded the extension. Existing propagation, satellite-initialization,
database-load and dynamic-parser sentinels and all result assertions remain.
No test is skipped, weakened or removed. The intake application script is unchanged.
The original local evidence retains the prior test hash; the executions below
verify the corrected final test rather than relabelling that earlier evidence.

All **292** other starting nonignored files are byte-preserved, including every
previous report and lockfile; all 16 private files are byte-preserved. No backend
application code, dependency, migration, frontend or deployment configuration
was changed for publication.

## Actual local verification

Constructed a separate detached worktree at the published base HEAD and copied
only the five intended readiness paths into it. This proves that tests can run
without borrowing the earlier untracked Phase 11 implementation. The publication
review itself is documentation only. Commands used locked dependencies and task
caches under `/tmp/orbitiq-publication`, with `PYTHONPATH=backend` for scripts.

| Execution scope | Actual result |
| --- | --- |
| Full original workspace, final corrected test: `uv run --locked pytest -q` | **1,033 passed**, zero failures/errors/skips |
| Original workspace intake + time qualification + ESA inspector tests | **159 passed** |
| Original workspace Ruff check / format check | Both passed |
| Isolated proposed publication: `uv sync --locked` and full pytest | **855 passed**: 785 published-baseline tests plus all 70 new intake tests; zero failures/errors/skips |
| Isolated frontend: `npm ci`, `npm test` | Locked installation passed; **307 tests passed**, the published frontend baseline |
| Isolated Ruff lint/format, ESLint, Prettier, TypeScript, Vite build | All passed |
| Isolated published SGP4 / terrestrial / expanded-science audits | **40 / 6 / 32** passed |
| Isolated geodesy audit | **28** independent mathematical cases plus **28** round-trips passed |
| Isolated golden evidence lifecycle | **6** published components and **3** offline replays passed |
| Git whitespace review | Passed |

The full workspace still contains 344 frontend tests from its earlier Phase 11
work, as reported in the preserved readiness evidence. Those changes are excluded;
the proposed publication and remote CI should therefore have **307 frontend tests**,
not 344. Similarly, isolated/remote backend counts should be 855, not the original
workspace's 1,033. This is a scope difference, not disabled functionality or tests.

The first isolated `npm ci` attempt exited 254 because its default cache directory
`/home/agent/.npm/_cacache` was unavailable in this environment. Retained the
failure log and reran with `npm_config_cache=/tmp/orbitiq-publication/npm-cache`;
installation and all frontend checks passed. No registry, lock, dependency, TLS,
proxy or test configuration was changed. Existing deprecation/bundle advisories
remain visible. Browser and PDF flows were **not rerun** in this publication review.
The original 77-flow/seven-PDF evidence remains prior evidence only.

## Expected remote verification and authorization boundary

The existing `.github/workflows/ci.yml` runs on pushes to the dedicated branch.
No workflow change or redundant workflow is needed. Its permissions are
`contents: read`; no secrets are required by these jobs. Expected checks:

- `backend`: locked uv install, full pytest, four scientific/geodesy audits,
  selected migration/backup/restore fixture tests, Ruff lint/format.
- `frontend`: Node 24, `npm ci`, tests, lint, formatting, TypeScript/Vite build
  and frontend artifact upload.
- `release-images`: locked API/web image builds, nginx validation and isolated
  fixture API checks; no registry publication or deployment.

Tests initialize only explicit disposable fixtures. The workflow does not use or
migrate the ordinary local archive, need real ESA/GP inputs, or run browser/PDF
regressions. No CI result is recorded here before a push. Exact published SHA,
workflow run and actual job outcomes must be obtained after authorized publication
and reported against the latest tip. This document is the pre-publication review,
not a remote success receipt.

Authorization permits an explicit six-path commit, normal push of this dedicated
branch, and checking its CI. It does not authorize force-push, merge, release tags,
visibility/settings changes, DNS, hosting or deployment. GitHub's current `main`
summary reports `protected=false`, with SHA
`d9f85d5d6e28cea90f25965c761422f16705eea8`; required-check enforcement has not been
established or changed. Main and the prior Phase 10 branch remain untouched.

## Scientific and production status

Historical GP acquisition is still pending; request confirmation is not delivery.
Actual temporal pairing is unverified, IGb08 alignment is blocked, and no qualified
operational Swarm adapter exists. No real ESA residual was generated, independent
prediction accuracy is unestablished and uncertainty remains unquantified. The
original acceptance criteria 5, 7, 12 and 16 remain BLOCKED. Time anomalies,
reference-quality approval and actual-pair lineage also remain unresolved.

Code publication, exact-commit remote CI, scientific qualification, production
deployment and production-infrastructure verification are separate milestones.
Phase 8 public hosting/HTTPS, independent off-machine recovery, actual production
alert delivery and branch protection remain open. This task does not deploy or
declare OrbitIQ production-ready.
