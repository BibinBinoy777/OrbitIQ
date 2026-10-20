# Phase 10 and 10.1 publication status

20 October 2026 (IST). The user authorized publishing the verified work to GitHub
and checking CI. Phase 10 evidence replay and Phase 10.1 integrity hardening are
published on `phase-10-evidence-replay` in the existing **private** repository.
No merge to main, deployment, domain/DNS or infrastructure change was performed.

## Exact commits and remote verification

Original 24-file implementation commit:
[`f3f52894494731de5253b68a9301d85a345241c6`](https://github.com/BibinBinoy777/OrbitIQ/commit/f3f52894494731de5253b68a9301d85a345241c6).
Its [run 39461594700](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39461594700)
**failed**: frontend and release-images passed, while backend reported
**782 passed / 3 failed**. Scientific audit/lint steps after pytest were skipped;
that run is not an all-green baseline.

Correction commit:
[`ce695232506b3aedf641076b88bfdfec4133bf77`](https://github.com/BibinBinoy777/OrbitIQ/commit/ce695232506b3aedf641076b88bfdfec4133bf77).
The new push-triggered
[run 39462297299](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39462297299)
completed successfully for that exact SHA and branch. All three jobs and all
returned steps succeeded; no skipped steps were counted as passed.

| Job | Actual remote result for `ce69523` |
| --- | --- |
| backend | **785 tests passed**; 40 SGP4, six terrestrial, 32 expanded-science comparisons, 28 independent geodetic cases and 28 round-trips passed; five selected migration/backup checks passed; Ruff lint/format passed |
| frontend | **307 tests passed**; locked install, ESLint, Prettier, TypeScript/Vite build and artifact upload passed |
| release-images | Locked API/web image builds, nginx validation and isolated empty-database API smoke checks passed; no registry publication or deployment |

Counts were read from the remote logs, not inferred from local results. Full
three-engine browser/PDF checks remain the earlier local Phase 10.1 evidence;
the CI workflow does not run them. CI used Python 3.12.15; the local verification
used 3.12.14. Each replay test captures/checks its own exact runtime. This does not
make a saved bundle compatible with a different recorded Python patch version.

The watch command encountered HTTP 503 when fetching optional annotations after
jobs completed; the completed run/job JSON and actual logs were retrieved separately
and establish the results above. Existing action/runtime and runner-image advisories
are not test failures and were not suppressed. See the
[structured publication receipt](phase-10-remote-ci.json) for exact job/step metadata,
log hashes, failure evidence and preservation checks.

## Investigated fixture-clock failure

Three pre-existing Phase 6 monitoring tests assessed a fixed noon UTC timestamp
while SQLite generated insertion timestamps from the actual wall clock. The original
local run was before noon. CI ran after noon, so readiness correctly treated those
insertions as future and returned `ingestion_timestamp_unknown`. The three failures
were reproduced locally before correction.

Only `backend/tests/test_phase6_collection.py` changed. A scoped SQLite-clock fixture
now supplies the isolated test archive's insertion time before its fixed assessment
clock. It is used by those three tests, survives their explicit `monkeypatch.undo()`,
and leaves other databases and production clocks untouched. An additional assertion
checks the controlled insertion time. No readiness check, timestamp validity rule,
scientific calculation, tolerance or existing expected assertion was weakened.

After the correction, local collection tests passed **62/62**, and the complete
backend suite passed **785/785** with Ruff lint/format. The corrected commit's remote
run then independently passed all checks. The failed original run is preserved;
it was not rerun or relabelled as success.

## Review, preservation and status boundaries

Before publication, all **244** source hashes in the local Phase 10.1 evidence,
backend runtime fingerprint and ordinary database/schema/table fingerprint matched.
The reviewed 24 paths were staged explicitly and staged bytes checked against their
review hashes. No databases, replay bundles, credentials or caches were added.

After the correction and this status update, **242 of 244** historical source
manifest entries remain byte-identical. The two intentional differences are the
collection test fixture and README's publication link/status text. This receipt adds
two new tracking files. All backend application source hashes, lockfiles, migrations,
normal database bytes and previous phase reports/evidence remain unchanged. Historical
reports retain their original unpublished/local checkpoints rather than being rewritten.

Ordinary database SHA-256:
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Full schema/table fingerprints, snapshots and ingestion ledger match the earlier
verification. No upstream collection, database initialization or migration occurred.

| Milestone | Recorded state |
| --- | --- |
| Locally verified | Phase 10.1 evidence preserved; fixture correction passes 785 backend tests |
| Published | Feature branch; original implementation plus correction above |
| Remote CI verified | All three jobs passed for exact correction SHA `ce69523` |
| Merged to main | No; main remains `d9f85d5d6e28cea90f25965c761422f16705eea8` |
| Production deployed | No |
| Production infrastructure verified | No; separate Phase 8 gates remain open |

This status file is a later documentation-only update. It cannot embed its own
commit SHA/CI result without changing that commit. The final publication response
reports the actual CI result for the final documentation tip; do not infer it from
an earlier successful commit. No application code is changed by that tracking commit.

GitHub's current branch summary reports `main.protected=false`. Detailed protection
access returned HTTP 403, `Resource not accessible by integration`; required-check
enforcement is not established. No repository settings or visibility were changed.
Production hosting/public HTTPS, independent off-machine recovery and actual
production monitoring/alert delivery remain unverified. Observation-based prediction
validation remains blocked and prediction uncertainty unquantified. Publication and
CI do not certify physical orbital accuracy or public-launch readiness.
