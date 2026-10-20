# Phase 10 — Reproducible evidence replay: local verification

Recorded 2026-10-20 UTC. Implemented and locally verified on
`phase-10-evidence-replay`, based on
`d9f85d5d6e28cea90f25965c761422f16705eea8`. Phase 10 has **no new commit, remote
branch, remote CI result or deployment**. The backend source hashes in the
[structured verification record](phase-10-verification-results.json) identify the
locally tested implementation; HEAD alone does not identify these uncommitted edits.

## Published Phase 9 baseline

With authorization, Phase 9 was fast-forwarded into `main` at
`d9f85d5d6e28cea90f25965c761422f16705eea8`. The resulting push-to-main
[Actions run 39389781990](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39389781990)
completed successfully for **backend**, **frontend** and **release-images**.
The run's `headSha` and branch matched; a final remote-ref read still returned that
SHA. Earlier phase reports remain historical records and were not overwritten to
imply that Phase 10 ran in this remote workflow.

GitHub's `branches/main` API reports `protected: false`. Detailed protection/rules
reads were restricted by the available integration/repository plan; required-check
enforcement is not established. No repository settings or visibility were changed.

## Implementation and changed files

| Files | Purpose |
| --- | --- |
| `backend/orbitiq/replay_contract.py` | Versioned, bounded manifest/settings and fixed tolerances |
| `backend/orbitiq/replay.py` | Exclusive capture, regular-file/size/hash validation, source/software identity checks and replay orchestration |
| `backend/orbitiq/services/replay.py` | Reuse existing science services and compare defined result projections |
| `backend/orbitiq/maintenance/replay.py` | Operator `capture`/`verify` CLI and exclusive result output |
| `backend/orbitiq/orbits/earth_orientation.py` | Explicit local resource loader; locked historical replay scope restoring previous ERFA leap table/expiry |
| `backend/orbitiq/services/{analysis,investigations,reports}.py` | Optional internal policy/positioner injection; ordinary API callers retain defaults |
| `backend/tests/test_phase10_replay.py` | 55 isolated capture/replay/integrity/safety/policy tests |
| `scripts/verify_replay_offline.py` | Fresh-process socket/SQLite audit, starting before science imports |
| `.gitignore`, `README.md` | Ignore conventional local replay bundles; document feature and status |
| `docs/phase-10-plan.md`, `docs/evidence-replay.md`, this report, `docs/phase-10-verification-results.json` | Acceptance criteria, operator guide, actual verification and limitations |

No dependencies, migrations, ingestion, public API routes, frontend features or
scientific equations were added. Both dependency lockfiles are unchanged. The
installed science runtime was CPython 3.12.14, sgp4 2.27, Astropy 7.2.3,
pyerfa 2.0.1.5, NumPy 2.5.4 and astropy-iers-data 0.2026.10.12.1.3.27.

Bundles preserve exact archived source bytes, original validation provenance,
applicable EOP/leap files, lock, software/source hashes and settings. A separately
retained manifest checksum can pin a trusted capture; checksums are not provider
authentication. Verification never opens a database, fetches data or installs code.
Existing browser exports remain unchanged; capture a new bundle from the definition
rather than inventing metadata for an older execution.

## Executed local checks

| Check | Actual result |
| --- | --- |
| `uv sync --locked` | Passed; locked environment resolved/checked |
| Full `uv run --locked pytest -q` after final code edit | **730 passed**, 14.44 s; 55 new replay tests |
| Ruff lint and formatting | Passed |
| Frontend `npm test` | **307 passed** |
| Frontend ESLint and Prettier | Passed |
| Frontend TypeScript + Vite production build | Passed |
| Existing published SGP4 audit | **40 passed, 0 failed** |
| Existing terrestrial reference audit | **6 passed, 0 failed** |
| Existing Phase 6.1 scientific audit | **32 comparisons passed, 0 failed** |
| Existing geodetic audit | **28 independent cases + 28 separate round-trips passed** |
| `git diff --check` | Passed |

The existing Starlette/httpx TestClient deprecation warning and Vite globe chunk
warning (>500 kB) remain. They were not silenced. No existing test was edited,
skipped, removed or disabled. Early replay checks exposed a timestamp-contract
construction error and a Python-vs-NumPy scalar type mismatch; both were corrected
before the final full-suite run. Tolerances were not relaxed to obtain a pass.

Fresh processes captured and replayed new reports from the ordinary archive's
**genuine ISS snapshots #1 and #2**, without new acquisition. These are calculated
states from archived mean elements, not observations:

| Case | Replay result | Numeric values checked | Bundle bytes |
| --- | --- | ---: | ---: |
| Snapshot | `verified_source_only` | 0 | 63,395 |
| TEME position | `matched` | 9 | 65,813 |
| Three-point ITRS ground track | `matched` | 93 | 3,855,450 |
| Common-time ITRS comparison | `matched` | 100 | 3,863,255 |
| Maximum 361-point track | `matched` | 11,191 | 6,115,612 |

Each fresh-process replay used a separately passed manifest checksum, removed
`ORBITIQ_DATABASE_PATH`, and installed the socket/SQLite audit hook before imports:
**zero network attempts and zero database attempts** in all five cases. Ordinary
source and maximum-track captures were performed through the CLI. Full artifacts
are task-local under `/tmp/orbitiq-phase10/final`; compact IDs, checksums, policy
times and replay results are retained in the structured verification record.
These task artifacts are not durable backups.

Isolated tests also exercised: all four modes and both comparison frames;
source-only comparisons; unavailable original calculations; numerical mismatch
after recomputed file checksums; trusted-manifest rejection; altered/missing EOP
and leap files without installed-file substitution; altered source metadata,
lock/runtime/code identity; duplicate/nonfinite/invalid JSON; traversal, symlink,
FIFO, directory and oversized inputs; existing destination/result refusal; all
track rows; fixed tolerances; current environment changes; historical prediction
expiry/measured-only behavior; and ERFA/default-resource restoration on success
and failure. The offline test runs in a subprocess through the existing backend CI
test command. No redundant workflow was added.

## Data preservation and acceptance

The ordinary database was neither initialized nor migrated nor restored. Its
before/after byte hash and complete read-only logical fingerprint match:

`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`

All **44 historical phase-document files** checked against the initial tracked-file
hash baseline are unchanged. Existing migrations, tests and both lockfiles are
unchanged; there are no missing tracked files. Verification also checks that bundle
bytes are unchanged. Intended tracked edits are limited to README, Git ignore,
resource scoping and the three small internal service injection points listed above.

All local acceptance criteria P10-01 through P10-09 in the
[plan](phase-10-plan.md) are supported by these checks. Remote publication/CI is a
separate pending milestone. Interactive browser/PDF checks and Docker image builds
were not rerun for Phase 10; their prior results are not relabeled as current.
No frontend or deployment files changed.

## Limits and remaining gates

Numerical agreement reproduces the captured calculation within the
[documented fixed tolerances](evidence-replay.md). It does not establish observed
orbit accuracy, source authentication, current prediction freshness, collision
safety or a universal scientific certification. Observation-based validation
remains blocked and prediction uncertainty unquantified. Historical policy uses
the captured evaluation clock; normal API freshness/EOP checks remain current.

Replay requires matching trusted code, Python/package versions and lock; bundled
library binaries are not supplied or automatically installed. Preserve the exact
trusted code separately for captures from an uncommitted checkout. Unrelated future
backend changes intentionally block version-1 replay. A future archival/runtime
compatibility policy can be evaluated independently after this baseline is reviewed.

| Milestone | Status |
| --- | --- |
| Phase 9 local verification | Previously recorded; preserved |
| Phase 9 published to `main` | Yes, exact SHA above |
| Phase 9 CI on resulting `main` SHA | All three jobs passed |
| Phase 10 local implementation/verification | Complete for the scoped acceptance criteria |
| Phase 10 committed/published | No; local work awaits review and authorization |
| Phase 10 remote CI | Pending publication; no result claimed |
| Production deployment | Not performed |
| Production infrastructure verified / Phase 8 closed | No |

Phase 8 still separately tracks public hosting/HTTPS, independent backups with
demonstrated off-machine recovery, actual production monitoring/alert delivery and
branch-protection/required-check enforcement. Localhost development can continue
while a real domain/hosting is deferred. No DNS, domain, infrastructure or production
settings were changed. The next publication action would be to review and commit
these Phase 10 files, publish the branch/PR, and verify exact-SHA remote CI; that
requires explicit authorization.
