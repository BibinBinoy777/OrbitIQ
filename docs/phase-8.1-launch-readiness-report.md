# Phase 8.1 launch-readiness report

**Recommendation: NO-GO for public launch.** Local blocker-remediation work is
implemented and verified, but real hosting, independent recovery, production
monitoring/delivery and exact-release CI/protection still lack required evidence.
The acceptance table records **12 PASS, 0 FAIL, 5 BLOCKED**. This is an evidence
index, not a readiness score; passing local tests cannot substitute for those gates.

## Initial state and blocker review

Started on `main`, HEAD `ec1f9f832e5f2a488169d43083d83e24e1eac25e`, the published
Phase 7 commit. All Phase 8 preparation was still modified/untracked locally; no
commit contains Phase 8 or this Phase 8.1 candidate. Preserved both tracked and
untracked files, verified requested reports/runbooks existed before reading, and
established a new baseline: **609 backend tests, 275 frontend tests and build passed**.

Phase 8 criterion **20 — Deployment and rollback instructions are complete** was
BLOCKED. Its seven launch-gate groups were hosting, durability, operations, release
verification, traffic, compatibility and stronger scientific-accuracy claims.
The old summary of one blocked criterion did not mean only one substantive gap.
No approved production provider/domain, independent backup destination or real
alert recipient is configured. Ambient identity-variable names do not establish
approval for a destination; no unapproved cloud identity or credential was used.

## Implemented changes and verified scope

**TLS preparation:** defined the Linux/Docker single-host candidate and added an
optional TLS overlay with TLS 1.2/1.3, shared static/API routes, security headers
and HTTPS-only staging HSTS. Private keys/certificates remain operator-provisioned;
no issuance, DNS or deployment occurred. Six actual loopback checks passed: trusted
CA/hostname, forced TLS 1.2, forced TLS 1.3, rejection of untrusted CA, rejection of
wrong hostname and no HSTS on HTTP. No certificate-verification bypass was used.
The local dependency probe now avoids inherited proxies only for its own loopback
address. Public-domain HTTPS, redirect, renewal and ingress trust remain BLOCKED.

**Encrypted recovery:** an explicit operator CLI reuses the existing consistent
SQLite backup/rehearsal, exports through established restic encryption, retrieves
its exact backup-point subtree into a new private target, then verifies file SHA,
full schema/table hashes, every source payload and representative APIs. Repository
and password files are private and explicitly selected. It does not initialize
repositories, delete retention data, change the primary archive or enable scheduling.
Stable operator receipts report success/failure without raw credentials/transport
errors. Local mode cannot claim independent/off-machine recovery.

The genuine two-record archive passed encrypted local export/retrieval with
**schema 3**, both original identities/hashes and the audit ledger preserved.
Backup size **53,248 bytes**, SHA-256:
`644585974d4192d47797b17ff2fc20e660d723f779d2d9362780230d50989c0c`.
Retrieved listing, snapshot #2, snapshot #1 and two-source comparison each returned
200. A full restic repository read/check found no errors (two encrypted backup
snapshots, four packs; these are backup objects, not new orbital acquisitions).
Wrong-password export exited **1 as expected**, reported failure safely and did
not overwrite the source. Retention was previewed only; no forget/prune deletion.

The restic 0.19.1 Linux-amd64 binary matched the official compressed release
SHA256SUMS `f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c`
over verified HTTPS. Its publisher signature was not separately verified. The
repository is on this machine: **off-machine recovery remains NOT VERIFIED**.
An approved independent destination, credentials/key recovery, ownership and
replacement-host rehearsal are still required.

**Monitoring:** implemented a separately invoked CLI using existing liveness,
minimal dependency/scientific readiness, optional bounded request logs and backup
receipts. Alerts contain only known component/status/time/incident metadata.
Delivery is opt-in; admission is locked/atomically persisted before sending, and
failed deliveries consume the same global cooldown. Corrupt/unsupported state is
preserved, redirects refused and arbitrary response/log/credential content is not
forwarded. The CLI does not run inside or crash the API. No scheduler/service was
activated and no real recipient was contacted.

Six actual loopback integration cases passed: observation without delivery,
labelled test delivery against genuine archive readiness, repeat suppression,
controlled receiver HTTP-503 failure (CLI exit **2**, expected), failure suppression,
and API outage plus an actual failed-backup receipt. Three test payloads reached
the controlled receiver, each explicitly `test=true`; none was a production incident.
Current acquisition time came from the real readiness response, distinct from
source epoch freshness. Local encrypted recovery correctly stayed `unknown` for
production backup readiness. **Real production alert delivery remains BLOCKED**.

**Browser compatibility:** resolved the earlier runtime blocker with a pinned
official Playwright environment plus matching Python packages. Seven actual-API
critical workflows passed per engine: **Firefox 153.0, WebKit 26.5 and Chromium
151.0.7922.34**. They cover startup/discovery, exact snapshot inspection, keyboard
save/reopen/reload/sharing, selected track sample, A/B common-time ITRS comparison,
readiness, read-only recipient reconstruction, reduced motion and missing-source
errors. Tests used existing genuine ISS sources and their actual backend services;
no canvas/API mocking, fixture insertion or source acquisition occurred.
Firefox exercised the actual usable 2D graphics fallback; WebKit/Chromium rendered
software WebGL2. Mobile viewports did not overflow. This is not physical-device,
GPU, Apple Safari or assistive-technology certification.

**Scientific transparency:** added an always-visible exploration/uncertainty notice
and [intended-use statement](intended-use.md). Observation-based prediction validation
remains BLOCKED, uncertainty unquantified, and historical element differences do
not establish a maneuver/anomaly. No orbital algorithm, tolerance, source identity,
collection cooldown/deduplication, EOP rule or geodetic correction was weakened.

## Actual regression and configuration results

All commands used the actual project setup, with `UV_CACHE_DIR=/tmp/orbitiq-uv-cache`;
scientific scripts also used `PYTHONPATH=backend`. npm/tsc ran in `frontend`.
Complete command arrays, output, statuses and integration distinctions are in
[structured evidence](phase-8.1-integration-results.json).

| Command / check | Actual result | Exit |
| --- | --- | --- |
| `uv run --locked pytest -q` | **634 passed**, 25 added to the 609-test baseline | 0 |
| `npm test` | **275 passed**, 20 files | 0 |
| `scripts/verify_scientific_references.py --output /tmp/orbitiq-phase81/verify_scientific_references.json` via locked project Python | 40 passed, 0 failed | 0 |
| `scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-phase81/verify_earth_fixed_references.json` | 6 passed, 0 failed | 0 |
| `scripts/verify_phase61_science.py --output /tmp/orbitiq-phase81/verify_phase61_science.json` | 32 numerical comparisons passed; observation validation BLOCKED | 0 |
| `scripts/verify_phase611_geodesy.py --output /tmp/orbitiq-phase81/verify_phase611_geodesy.json` | 28 independent-reference component cases + 28 separate round-trips | 0 |
| `uv run --locked ruff check .` / `uv run --locked ruff format --check .` | Passed; latest format check 92 files | 0 / 0 |
| `npm run lint` / `npm run format:check` | Passed | 0 / 0 |
| `npx --no-install tsc --noEmit` / `npm run build` | Passed; existing renderer chunk warning retained | 0 / 0 |
| API/web image builds and TLS Compose configuration/startup | Passed against separate genuine restored copy | 0 |
| `python scripts/verify_release_containers.py --release phase81-local` | Explicit empty isolated archive/static/health/ready/list smoke; fixture unchanged and removed | 0 |
| `python scripts/verify_browser_critical.py ... --engine firefox/webkit/chromium` in supported runtime | Seven actual-API cases per engine | 0 each |
| Encrypted export and retrieval / restic full repository check / retention dry-run | Passed, local-only scope | 0 each |
| Wrong-password backup / controlled alert receiver failure | Safe refusals and correct failure receipts/cooldown | 1 / 2 expected |
| Verified loopback TLS trust/protocol checks | Positive checks 0; untrusted/wrong-host negative curl checks 60 as expected | expected |

The full suite includes ingestion/deduplication, migration/failure rollback,
backup/restore, production configuration and saved/share tests. No skipped or
expected-failure result was counted as a pass. Frozen GeographicLib references
were reused; the C++ reference executable was not rebuilt. The existing
Starlette/httpx deprecation and >500-kB renderer warning remain visible.

## CI and publication evidence

Read-only GitHub inspection still shows successful backend/frontend jobs for
Phase 7 SHA `ec1f9f832e5f2a488169d43083d83e24e1eac25e`,
[run 39293109185](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39293109185).
It does not verify this working tree. No commit contains the current Phase 8/8.1
changes, so **exact-release remote CI is BLOCKED**. Protection/ruleset APIs still
return HTTP 403; administrator verification is necessary. The artifact includes a
local content manifest/hash explicitly distinguished from a Git commit.

After future authorized review/commit/push, record the actual release SHA, inspect
all required jobs and individual steps for that SHA, record skipped/cancelled/missing
checks, and confirm branch/review rules. Current CI covers unit/scientific/build/
migration/image startup commands; critical browser and encrypted-recovery drills
are separate local artifacts, not automatic remote jobs. No commit, push, remote
modification, workflow dispatch or rerun occurred here.

## Findings investigated

The official browser image initially lacked its Python Playwright package; a
matching pinned runtime resolved it. Initial full-tree restic retrieval failed on
unmapped ownership of a `/tmp` ancestor. That failure was retained and reported;
restoration now selects only the exact backup-point subtree and verifies contents,
without ignoring tool errors. New-file formatting issues were fixed. The phase did
not relabel a mock/local service as an externally verified capability.

## Preservation and external requirements

Normal database SHA-256 before/after:
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Complete fingerprints match, including schema 3, two snapshots, one attempt, one
insertion and one gate row, all payloads/indexes/triggers and integrity/foreign keys.
All completed phase reports, including Phase 8, are unchanged. Existing runbooks
append new procedures/evidence. Scientific/storage/ingestion sources and dependency
locks are unchanged. Private keys/passwords/repos/raw database copies are outside
Git. Normal data were not reset, initialized, migrated or silently rewritten.

Still required: approved hosting/account/domain/DNS/TLS/renewal and ingress; durable
volume replacement proof; independent backup destination and separately recoverable
keys/retention/RPO/RTO; production monitoring receiver, on-call and schedules; actual
release publication authorization, exact-SHA CI and protection evidence; representative
target-host traffic/shared-NAT and physical device/assistive-technology verification.
Public operational readiness remains NO-GO until those gates have actual evidence.
Stronger scientific-accuracy claims additionally remain blocked by the absence of
independent observations and quantified uncertainty. The approximately 1.317 cm
reference-residual explanation and Phase 6.1.1 correction remain unchanged.

## Acceptance criteria

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | The existing Phase 8 report and exact blocked criterion were inspected | PASS | Criterion 20 was BLOCKED, with seven distinct additional launch-gate groups; all reassessed below. |
| 2 | The current release candidate and Git state were identified | PASS | main HEAD ec1f9f8 remains published Phase 7; all Phase 8/8.1 changes are local/uncommitted; baseline includes tracked and untracked work. |
| 3 | Hosting and HTTPS requirements were resolved or the exact external blocker was documented | BLOCKED | Linux/Docker target and local verified TLS overlay prepared; no approved provider/account/domain/DNS/public certificate/renewal/ingress/durable host exists. |
| 4 | Off-machine backup architecture was implemented or its missing prerequisites were precisely documented | BLOCKED | Restic encrypted export/retrieval is implemented and locally verified, but no approved independent external destination, credentials/key recovery or replacement-host test exists. |
| 5 | Backup integrity verification is implemented | PASS | Real encrypted repository full-data check, exact retrieved file SHA, complete schema/table digests, payload validation and API reads succeeded. |
| 6 | Recovery into a separate database is verified where the environment permits it | PASS | Existing genuine two-record archive restored through restic into a separate private target; schema 3, ledger, source identities and APIs verified. Scope is local. |
| 7 | Monitoring and alert requirements are implemented or their production prerequisites are documented | BLOCKED | Operator CLI, private receipts/log signals, safe opt-in payloads and persistent cooldown implemented; production receiver, state/log delivery, owner/schedule/escalation remain absent. |
| 8 | Actual alert delivery is tested where a real destination is available | BLOCKED | Controlled loopback TCP test receiver exercised acceptance/failure/suppression; no real production destination or human delivery confirmation available. |
| 9 | CI evidence matches the exact tested commit | BLOCKED | Remote success covers only published Phase 7 ec1f9f8; no commit contains the current Phase 8/8.1 candidate. Exact-release CI requires authorized publication; protection APIs return 403. |
| 10 | Current local changes are not misrepresented as remotely verified | PASS | Local command/image/browser evidence is separate from the Phase 7 remote run; future publication/verification steps documented. |
| 11 | Firefox and WebKit tests run successfully or their precise blockers are documented | PASS | Seven actual-API workflows per Firefox 153.0, WebKit 26.5 and Chromium 151.0.7922.34 pass in pinned supported runtime. Firefox used tested 2D fallback; physical devices/Safari not certified. |
| 12 | Relevant security issues are addressed | PASS | TLS hostname/trust tests, exact-point restore, protected operator files/state, no raw secret/error forwarding, body/URL bounds and delivery failure cooldown verified; no public admin API added. |
| 13 | Existing scientific policies and limitations are preserved | PASS | Scientific code/tolerances/collection logic unchanged, all audits pass; app and intended-use document disclose calculated positions, blocked observation validation and unquantified uncertainty. |
| 14 | Existing database contents and prior reports remain intact | PASS | Normal archive file/table fingerprints and all completed phase reports, including Phase 8, match baseline; runbooks append new evidence. |
| 15 | All applicable local regression suites pass or deviations are explained | PASS | 634 backend, 275 frontend, all original/expanded/geodesy audits, lint/format/TypeScript/build, release-container smoke, encrypted recovery, TLS and browser checks passed within recorded scope. |
| 16 | Deployment, monitoring, backup, and recovery runbooks are updated | PASS | Conditional TLS/hosting steps, protected restic workflow/retention preview, monitoring/delivery/cooldown and exact-release CI follow-up documented without claiming external verification. |
| 17 | The final GO/NO-GO decision is based on evidence rather than an arbitrary score | PASS | NO-GO because public hosting, independent recovery, production monitoring/delivery and exact-release CI/protection lack evidence; passing local checks cannot close these gates. |

## Phase 8.1 changed files

- `.dockerignore`
- `Dockerfile`
- `README.md`
- `backend/orbitiq/maintenance/backup_export.py`
- `backend/orbitiq/maintenance/monitor.py`
- `backend/tests/test_phase81_operations.py`
- `deploy/Dockerfile.browser`
- `deploy/compose.tls.yaml`
- `deploy/compose.yaml`
- `deploy/nginx-tls.conf`
- `deploy/nginx.conf`
- `deploy/production.env.example`
- `deploy/security-headers.conf`
- `deploy/server-routes.conf`
- `docs/backup-restore-runbook.md`
- `docs/intended-use.md`
- `docs/monitoring-and-alerting.md`
- `docs/phase-8.1-integration-results.json`
- `docs/phase-8.1-launch-readiness-report.md`
- `docs/production-deployment-runbook.md`
- `docs/production-security-review.md`
- `frontend/src/App.tsx`
- `scripts/verify_browser_critical.py`

Runbooks: [deployment](production-deployment-runbook.md), [encrypted backup/recovery](backup-restore-runbook.md), [monitoring/alerting](monitoring-and-alerting.md).

**No commit, push, deployment, publication, paid-resource creation or remote workflow
action was performed. Owned local test containers and endpoints were removed.**
