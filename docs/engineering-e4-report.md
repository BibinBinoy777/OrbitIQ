# Engineering milestone E4 execution report

Checkpoint: **23 October 2026 (IST)**. E4 prepares release engineering; it is not
production readiness certification or deployment authorization.

## Repository and release integrity

Started from clean `engineering-e3-reliability-recovery`, exact expected commit
`235e91ad7f29504bf394bebcebde1a74d163486d`, verified locally and against the
configured private `BibinBinoy777/OrbitIQ` remote. Its three CI jobs were freshly
inspected as successful; those are E3 evidence, not E4 results. Current work uses
`engineering-e4-release-readiness`. No reset, rebase or default-branch update occurs.

The pre-edit assessment found existing security/recovery controls, a missing
persistent link between tested source/images/frontend artifacts, dated operational
CI statements, and open repository/infrastructure gates. The initial production,
operations and E3 recovery selection passed **61 tests**. The source inventory
contained 338 tracked files and 72 private files. Prior phase reports are preserved.

E4 adds exact-source OCI labels and a before/after image/source/artifact record,
compares the web image's complete static contents to the successful frontend
artifact, and retains hashes of source/locks/configuration, image IDs/platform,
PDFs/captured JSON and test evidence. The existing workflow requires successful
backend/frontend jobs before image verification. Partial/cancelled/missing evidence
fails closed. Records explicitly prohibit production approval; local index-mode
records cannot become committed release candidates. No image registry or release
object is published. Image-byte retention/transfer remains a future owner action.

The existing release smoke now checks gateway headers/CORS/Host/body/method/URI
bounds, forwarded-IP rate-limit resistance, missing-storage liveness versus
readiness, same-release replacement and ephemeral local-CA TLS positive/negative
cases. It uses only new empty fixture storage and loopback endpoints and removes
its own resources. It never selects the ordinary archive. The PDF validator adds
hashes without relaxing its text/provenance/pagination/sample checks.

## Security findings and fixes

**Critical, corrected in the lockfile:** GitHub advisory
[GHSA-6q48-6c7w-9gw2](https://github.com/advisories/GHSA-6q48-6c7w-9gw2)
confirms the initial `certifi 2026.7.22` is affected by a CA trust-store issue.
E4 selects the first patched version `2026.10.19` and its distribution hashes.
No other locked Python package, frontend dependency or base-image digest changes.
No actual traffic interception is asserted. API images must be rebuilt; old E3
images retain the vulnerable bundle and are not approved rollback artifacts.

An initial pip-audit invocation failed because its default cache was read-only;
that is an environment failure, not a passed audit. Rerunning with an explicit
writable cache found one advisory in one of 29 packages. After the targeted update,
pip-audit 2.9.0 strict lookup reported **zero matches across 29 packages, none
skipped**. `npm audit --json` reported **zero matches** for the locked frontend
tree. CI adds these existing advisory checks/reports without adding an application
dependency. Advisory errors fail their step; limited advisory coverage is never
presented as complete security assurance. No OS/base-image scan or penetration
test has been executed in this checkpoint.

The old web root also contained stock `50x.html`, outside the Vite build artifact.
The final web stage removes that stock HTML before copying the exact build and
returns to UID/GID 101. This closes the artifact-identity gap; it is not labelled
a proven exploitable vulnerability. Existing anonymous/read-only semantics, CORS,
CSP, admission limits, safe errors, disabled docs and operator-only actions remain.
The tracked-file credential-pattern scan found no matches in 338 files; final
candidate review must also inspect the added files and complete staged diff.
No credentials or actual environment values were printed or committed.

Public access still requires dataset disclosure/redistribution approval and target
abuse/capacity review. Validation archives are opt-in public evidence, not private
account storage; private ESA inputs must not be mounted for anonymous serving.
Private/cloud-owned features need a separate identity/authorization design. No
authentication system was invented for this anonymous archive milestone.

## Operations and data recovery

The [E4 decisions/runbook](engineering-e4-release-readiness.md) records the retained
single-host architecture, runtime/configuration requirements, exact-source checks,
repository recommendations, release approval, rollback and operational signal
ownership. Current operating runbooks are corrected; historical reports remain
untouched. Logging/health/ingestion/freshness/resource behavior is reviewed and
retained; no external monitoring product, alert destination or scheduler is added.

Mandatory storage unavailability must produce readiness 503 while liveness remains 200. Optional provider failures retain eligible old records and their actual age.
Informational readiness HTTP 200 is not an all-healthy declaration. Metrics/logs
must distinguish route/export errors, request latency, provider attempts, epoch
freshness, EOP/leap readiness, backup jobs, host resources and lifecycle events.
Host log collection, retention, alert policies and actual delivery remain external.

E3's engine backup, no-overwrite publication, migrations and full schema/table/
payload/audit/API restore verification are reused, with new tests using disposable
storage only. No E4 migration is introduced. The real schema-3 database and all
72 private inputs initially match the trusted E3/E2 baseline. Its main-file SHA256
is `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`, checked
only under a verified DELETE-mode SQLite shared read transaction; logical table
fingerprints are also recorded. Final preservation checking matches all 72 private inputs, the database shared-lock
checksum and its logical fingerprint to the pre-edit baseline.

Independent backup storage, approved retention/encryption/key recovery, RPO/RTO,
schedules and replacement-host recovery are not established. No real database
is initialized, migrated, restored over or used for interruption experiments.
Same-release container replacement is distinct from a different approved-release
rollback. A prior patched production artifact has not been selected, so an actual
different-release/target rollback is not claimed.

## Actual verification

Local candidate verification completed against reviewed index tree
`d2a8c5311177d9e8deb9f87a7f67fe57eba63f1f` (base revision
`235e91ad7f29504bf394bebcebde1a74d163486d`). The evidence record explicitly
sets `release_candidate=false` and `production_approved=false`. This report update
is documentation only; independent exact published-source verification is recorded below.

Results actually executed:

| Check                                              | Actual result                                                                            |
| -------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Initial production/operations/E3-recovery baseline | 61 passed                                                                                |
| New release-integrity and failure probes           | 20 passed                                                                                |
| Patched Python advisory lookup                     | 29 audited, no matches, no skipped packages                                              |
| Frontend advisory lookup                           | No matches                                                                               |
| Frontend tests                                     | 345 passed                                                                               |
| Frontend lint/format/TypeScript/build              | Passed; existing renderer-size warning retained                                          |
| Ruff and workflow syntax                           | Passed before final source review                                                        |
| Full backend / reference audits                    | 1,254 passed; SGP4 40, terrestrial 6, expanded 32, geodesy 28 plus 28 round-trips passed |
| Local labelled image and exact frontend capture    | Passed; 14 frontend files match the complete web root                                    |
| Local proxy/TLS/outage/replacement                 | Passed; TLS 1.2/1.3 and negative trust/hostname cases                                    |
| E1/E2/PDF against patched images                   | 77 flows, 62 E2 checks, 18 axe scans with zero violations, seven PDFs passed             |
| E3 isolated checkout and recovery                  | Passed; same index tree, fresh locked installs, restart and separate restore             |
| Published E4 SHA and exact remote CI               | Implementation SHA below; all three jobs passed                                          |

The local gateway probe initially failed because the restrictive host umask made
its generated test-certificate directory/certificate unreadable to the non-root
gateway. Explicit permissions for those disposable fixtures corrected that failure.
A subsequent load probe encountered the existing documented capacity-busy 503
alongside edge 429; the harness now requires that exact safe capacity envelope and
retry header, still requires both input validation and edge refusal, and checks
health/readiness afterward. No application limits or existing tests were relaxed.
The final rerun passed. Failure logs are retained locally, not reported as passes.

The two new E4 Markdown files pass Prettier. README and the two existing operational
runbooks retain formatting warnings also reproduced against their unchanged E3
versions; no unrelated wholesale formatting was applied. Link/anchor, syntax,
credential-pattern, exact-scope, whitespace and earlier-report preservation checks
pass. Axe incomplete/manual-review results remain in evidence. Firefox uses its
actual fallback; no native-GPU, physical-device or screen-reader certification is
claimed. Seven PDF/paired-JSON digests match their validator results, including the
361-row maximum track. All expected-failure probes exit 1; other commands exit 0.

Existing Starlette/httpx TestClient and intentional duplicate-ZIP warnings are
retained. No tests, physics, science gate, tolerance, CSP or functionality is
disabled to obtain success. Local draft/index verification must remain labelled
as such; remote CI must verify the actual published commit independently.

## Reviewed publication scope

- `.github/workflows/ci.yml`
- `Dockerfile`
- `README.md`
- `backend/tests/test_e4_release.py`
- `docs/engineering-e4-release-readiness.md`
- `docs/engineering-e4-report.md`
- `docs/production-deployment-runbook.md`
- `docs/production-infrastructure-decisions.md`
- `scripts/verify_release_containers.py`
- `scripts/verify_release_evidence.py`
- `scripts/verify_report_pdf.py`
- `uv.lock`

Exactly these twelve implementation/test/workflow/lock/documentation files are
reviewed. Private inputs, database files, local evidence, credentials and earlier
phase/E1/E2/E3 reports are excluded. The reviewed implementation is published only
to its dedicated engineering branch, with exact-commit verification below.

## Verified implementation publication

**E4 repository-side milestone complete, with the external gates below open.**
Published branch: `engineering-e4-release-readiness`.
Implementation commit: `15c5a51103cf26824dd8214ba5806e7261f91c4e`.
Source tree: `5986931b92a8ff1650ed96da0682ebd2c780fd6d`.

[Exact-commit CI run](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39910094140) completed successfully. The three expected jobs
`backend`, `frontend` and `release-images` and every reported step passed. The
check-runs API independently identifies those same three successes on that SHA.
Actual remote logs confirm **1,254 backend tests** and **345 frontend tests**,
scientific reference audits, migration/recovery, lint/format/TypeScript/build,
strict Python audit (29 packages, none skipped, no matches) and npm audit (no
matches). The release job verifies local gateway/TLS/outage/replacement behavior,
77 browser flows, five fault-injection cases, two expected-failure probes, 62 E2
checks, 18 axe scans with zero violations and seven PDFs.

Downloaded release identity/evidence and frontend artifacts pass `verify-files`.
Every recorded source-file hash matches its blob in the exact commit, including
locks and build/proxy configuration. All 14 frontend files match the tested web
root; the PDF/paired-report hashes match validation results. The record is
`committed`, `release_candidate=true`, `production_approved=false`. The retained
image IDs identify that CI run's Linux/amd64 images:

- API: `sha256:4311818074c39273ec45e5c4c75b530c8d5882796933c324ad0daaafc61c0bff`.
- Web: `sha256:648e5c1e7cf11e701cd8520306348b67a8b7506335afb5a8501ecd747696e945`.

These IDs do not preserve the image bytes or authorize a rebuild/deployment. The
future approved artifact store/transfer and explicit production approval remain
open. Metadata/browser diagnostics have seven-day CI retention. No image registry
push or GitHub release object is created.

The remote isolated-installation summary matches the exact source tree above.
Its separate restoration matches every backup-point schema/table/payload/audit
fingerprint, with one synthetic snapshot and three ingestion audit attempts;
the source fixture remains unchanged. The 16 recovery artifact files, 14 frontend
files, advisory reports, release records and 194 browser/PDF files were inspected.
Trace ZIP integrity and expected screenshots/PDFs pass; no private attachments,
databases, credentials or personal email content were found. Playwright's hashed
`page` image-reference filenames are the only allowed email-like trace matches.

This documentation-only receipt records the implementation SHA above. Its own
publication is a separate subsequent commit, with no application, dependency,
test or workflow changes. The final handoff records that commit and its own
independently verified CI; earlier results are not substituted for it. Existing
renderer-size and TestClient/duplicate-ZIP warnings remain documented limitations,
not suppressed test failures.

| Milestone                          | Evidence at this receipt                                          |
| ---------------------------------- | ----------------------------------------------------------------- |
| Locally verified                   | Passed against the explicit reviewed index tree above             |
| Published                          | Implementation SHA above; dedicated branch only                   |
| Remote CI verified                 | All three jobs and retained artifacts for that implementation SHA |
| Production deployed                | No                                                                |
| Production infrastructure verified | No; separate Phase 8 gates remain open                            |

## Production readiness and scientific status

**NO-GO for public launch.** Default-branch metadata still reports `protected:
false`. Detailed protection GET returns HTTP 403 (integration access); rulesets
GET returns HTTP 403 (private-repository plan restriction). Effective required
checks/review/bypass controls are not verified or changed. Recommended controls
and the necessary owner-authorized negative merge test are documented.

Hosting/public HTTPS/renewal, trusted ingress, durable target volumes, independent
backup/key recovery, actual monitoring and human alert receipt, target capacity
and repository protection remain open Phase 8 gates. No public domain, DNS,
production certificate, host, storage service, merge or deployment is created.
The deployment configuration is tested locally only.

Phase 11.3.1 remains **PARTIAL**. Scientific evaluation remains **BLOCKED**.
ESA time, KIN-quality and frame-alignment questions remain unresolved. Historical
availability/creation clocks remain unknown, complete fitting lineage and
statistical independence remain unestablished, and no genuine Swarm-A propagation,
qualified residuals or independent-accuracy claim is generated.

Local verification, publication, exact-commit remote CI, production deployment and
production infrastructure verification are separate milestones. The latter two
remain unperformed even if E4 repository-side checks pass.
