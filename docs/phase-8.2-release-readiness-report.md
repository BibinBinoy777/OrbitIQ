# Phase 8.2 production infrastructure and release verification

Assessment: **20 October 2026 (IST)**. **Public launch recommendation: NO-GO.**
Locally testable work is complete: fresh regressions and a genuine-data deployment
rehearsal passed. Production hosting, public HTTPS, independent recovery,
operational monitoring/alerts and exact-release CI/protection remain unverified.
No production target or staging target is configured; no deployment occurred.

Acceptance: **12 PASS, 0 FAIL, 4 BLOCKED**. Criteria 3/5/7 explicitly allow missing
infrastructure decisions/dependencies to be documented; those documentation
alternatives passed. They do **not** mean the corresponding external capability
exists. Actual production gates remain BLOCKED regardless of the acceptance count.

## Checkpoint and blocker inspection

Started on `main`, HEAD `ec1f9f832e5f2a488169d43083d83e24e1eac25e`: published Phase 7. No commit contains
Phase 8 or 8.1. The 35 pre-existing uncommitted files were preserved. This phase
adds four documentation/evidence files and intentionally changes two existing
local draft files; 39 files remain uncommitted across all three readiness phases.
A local manifest in the [evidence](phase-8.2-integration-results.json) identifies
inputs; it is explicitly not a release commit or remote CI result.

Checked every requested report/runbook existed before reading. The actual Phase
8.1 table has five blocked criteria: **3 hosting/HTTPS, 4 off-machine architecture,
7 monitoring, 8 real alert delivery, 9 exact-release CI**. Reassessed the seven
broader Phase 8 launch groups as well: hosting, durability, operations, release,
traffic, compatibility and stronger scientific accuracy claims.

Repository deployment files are provider-neutral examples. The only ready managed
runtime binding is `ORBITIQ_DATABASE_PATH` for the existing development archive;
there are no configured secrets, outbound identities or provider capabilities.
Ambient identity variable names were not used as authorization. No provider,
account, domain, production database, independent repository, receiver or owner
was invented or contacted. Read-only Git access and required GitHub APIs were
checked with existing platform authentication.

## Infrastructure preparation and focused reliability fix

Added the [infrastructure decision checklist](production-infrastructure-decisions.md):
provider/account/region/budget, domain/DNS/TLS renewal, ingress/firewall/client trust,
durable volume lifecycle, independent storage/keys/retention/RPO/RTO, monitoring
receiver/owners/schedules/logs/host sensors and release authorizations. Each gate
specifies actual evidence required. It retains SQLite for the bounded single-host
candidate and evaluates managed PostgreSQL only for a separate justified project.

Added a [repeatable local release rehearsal](production-release-rehearsal.md) covering
configuration, exclusive recovery, source identity, probes, restart/replacement,
compatible rollback, TLS, browsers, backup, monitoring, failures and cleanup.
The existing deployment runbook retains its original bytes as a prefix.

**Fixed a real readiness gap in `deploy/compose.yaml`:** the gateway now probes its
actual same-origin `/api/ready` using BusyBox wget with a finite timeout and proxying
disabled only for that loopback request. Previously Compose could finish `--wait`
while the gateway restarted because it had no health check. With the fix, an
unreadable owned test TLS mount makes `--wait` fail (exit 1); correcting only its
traversal permission makes startup/probe pass. An intentionally unusable proxy
also cannot redirect the loopback probe. Health checking does not automatically
restart unhealthy containers or prove public HTTPS/scientific readiness.

Existing image build inputs and locks match verified Phase 8.1 content. Reused the
recorded local image IDs; no expensive rebuild was necessary. The Compose change
is runtime orchestration excluded by the Docker build-context allowlist and was
freshly exercised. No dependency, orbital algorithm, API, scientific policy,
ingestion behavior, frontend logic, reference fixture or lockfile changed.

## Actual fresh command results

All commands executed in this phase. Exact arrays, working directories, timestamps,
stdout/stderr, negative-case expectations and helper sources are in the evidence.
`UV_CACHE_DIR=/tmp/orbitiq-uv-cache`; scientific/operator Python uses
`PYTHONPATH=backend`. npm/tsc run in `frontend`.

| Command / check | Actual result | Exit |
| --- | --- | --- |
| `uv run --locked pytest -q` | **634 passed**, one existing deprecation warning | 0 |
| `npm test` | **275 passed**, 20 files | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_scientific_references.py --output /tmp/orbitiq-phase82/verify_scientific_references.json` | 40 passed, 0 failed | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-phase82/verify_earth_fixed_references.json` | 6 passed, 0 failed | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_phase61_science.py --output /tmp/orbitiq-phase82/verify_phase61_science.json` | 32 numerical comparisons passed; observation validation BLOCKED | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_phase611_geodesy.py --output /tmp/orbitiq-phase82/verify_phase611_geodesy.json` | 28 independent-reference component cases plus 28 separate round-trips | 0 |
| `uv run --locked ruff check .` / `uv run --locked ruff format --check .` | Passed; 93 Python files formatted | 0 / 0 |
| `npm run lint` / `npm run format:check` | Passed | 0 / 0 |
| `npx --no-install tsc --noEmit` / `npm run build` | Passed; existing lazy renderer chunk warning | 0 / 0 |
| `python scripts/verify_release_containers.py --release phase81-local` | Separate explicit empty schema-3 fixture smoke, unchanged and cleaned up | 0 |
| `python /tmp/orbitiq-phase82/recovery_checks.py` | Genuine consistent backup, encrypted round-trip, full restic check, retention preview, wrong-password refusal and separate local recovery | 0 |
| `python /tmp/orbitiq-phase82/rehearsal.py` | 15 local cases: configuration, genuine APIs/science/controls, restart/replacement, compatible rollback, candidate return and logs | 0 |
| `python /tmp/orbitiq-phase82/gateway_health_checks.py` | Broken TLS mount blocks readiness; recovery and loopback proxy isolation pass | 0 |
| `python /tmp/orbitiq-phase82/tls_checks.py` | Six actual local trust/protocol/HSTS cases | 0 |
| `python /tmp/orbitiq-phase82/check_monitor.py` | Six actual local monitoring/receiver/failure/cooldown/outage cases | 0 |
| `python /tmp/orbitiq-phase82/run_browsers.py` | Seven actual-API workflows per Firefox, WebKit and Chromium | 0 |

The complete backend suite includes ingestion/deduplication/cooldowns, migration
and failure rollback, backup/restore, saved-source identity and production
configuration regressions. No skipped/expected-failure count was represented as a
pass. Full suites ran before the Compose-only fix; no application/test/lock inputs
changed afterward. Current Compose configuration received fresh positive/negative
integration checks. Frozen GeographicLib reference fixtures were used; no C++
reference executable was rebuilt. Existing dependency advisory results were not
relabelled as new scans. No target-host capacity or physical accuracy test is claimed.

## Genuine archive recovery and local deployment rehearsal

The source archive was read-only throughout. Fresh SQLite consistent backup and
restic encrypted retrieval use new separate targets, schema 3, two genuine ISS
snapshots (#1/#2, NORAD 25544), one attempt, one insertion and one gate. Full schema/
table digests, all payloads, source identities and restored APIs match.

Backup size **53,248 bytes**, SHA-256
`644585974d4192d47797b17ff2fc20e660d723f779d2d9362780230d50989c0c`.
A full encrypted repository `check --read-data` passed; retention was dry-run only.
Wrong-password export safely exited **1 as expected** with a failed receipt.
Restic 0.19.1 was reused from the previously official-checksum-verified release;
compressed checksum and equality of the executable to decompressed bytes were
rechecked. Its publisher signature was not separately verified. Every repository,
staging copy and key is on this machine: **off-machine recovery is BLOCKED**.
No approved independent destination or credential binding is configured, so no
remote backup operation occurred.

Actual production-mode containers served static assets, liveness, minimal dependency
readiness, discovery, both fixed source details and historical common-time ITRS
comparison from the restored copy. Schema-3 migration on a separate copy was an
explicit byte-preserving no-op. Public mutation returned 405; unknown Host returned
400. A strict measured-only EOP calculation returned **422
`eop_prediction_disallowed`** without fallback coordinates. Actual readiness retained
degraded data-age/ingestion/EOP findings rather than forcing healthy status.

Restart, API replacement with a new container ID, switch to retained schema-compatible
`phase8-local` images, and return to `phase81-local` passed. Exact source fields
and raw payload checksums were separately compared with authoritative read-only
rows after replacement/rollback; the runtime archive fingerprint stayed unchanged.
This is same-host image rollback and persistence, not zero downtime, production
release rollback, disk reattachment or replacement-host recovery.

## TLS, monitoring and browsers

Six fresh loopback TLS cases passed: trusted local CA/hostname, TLS 1.2, TLS 1.3,
rejection of untrusted CA, rejection of wrong hostname, and no HSTS over HTTP.
Certificate failures exited **60 as expected**; verification was never disabled.
HTTPS HSTS is the existing one-hour staging policy. Keys/test CA remain private
outside Git. No production endpoint, public certificate/redirect or renewal was tested.

Six monitoring cases passed: observation without opt-in sends nothing, actual local
test delivery, repeat suppression, receiver 503 failure (CLI **2 expected**), failed
delivery suppression, and API outage with a real failed-backup receipt. Three
labelled test payloads reached the controlled receiver, one deliberately answered
503. All had `test=true`, the bounded schema and no secrets/raw logs. The ordinary
local encrypted-backup receipt correctly yields unknown production recovery.
The current readiness reports degraded orbital-data/ingestion/EOP states; source
retrieval is not replaced with calculation/check time. **No production receiver
or human escalation was verified.** Scheduling, persistent forwarding and host
resource sensors remain owner/provider dependencies.

Fresh browser results: **Firefox 153.0, WebKit 26.5, Chromium 151.0.7922.34**, seven
actual-API cases each, no page errors/CSP violations. Flows cover discovery,
keyboard save/open/reload/share, exact backend track sample, two-source common-time
ITRS comparison, readiness, mobile read-only recipient/reduced motion and missing
source refusal. Firefox exercised actual 2D fallback; WebKit/Chromium software
WebGL2. No source ingestion, API/canvas mocks or fixture insertions occurred.
No physical GPU/device, Apple Safari or assistive-technology certification follows.

## Exact release and GitHub evidence

Read-only `git ls-remote` and Actions API inspection still identify only published
Phase 7 `ec1f9f832e5f2a488169d43083d83e24e1eac25e`. Its successful
[run 39293109185](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39293109185)
has successful backend/frontend jobs and no skipped/cancelled/failed recorded steps.
It does not contain Phase 8/8.1 or this work. The new candidate has **no commit SHA**;
therefore exact-release CI is **BLOCKED**, not passed or implicitly skipped.

The local workflow expects `backend`, `frontend` and `release-images`, including
expanded scientific/geodesy audits and image startup. Browser/encrypted-recovery
checks remain separate local/manual evidence. Protection API: **403 Resource not
accessible by integration**. Rulesets API: **403 plan/visibility restriction**.
An administrator must verify actual status/review rules; none were assumed enabled
or disabled and no repository visibility/plan change was made. The decision checklist
records future authorized publication, exact-SHA job/step and protection checks.
No remote workflow was triggered/rerun and no remote files were modified.

## Investigated failures and preservation

Initial test-only TLS traversal failure is retained; only that new mount was
corrected, and the new gateway gate was tested against the same negative condition.
Two temporary harness assertions were corrected: an unallowed default TestClient
Host, and comparing dynamic freshness timestamps instead of immutable source fields.
Neither application hosts, source validation nor freshness policy was relaxed.
An inspection assumed Compose would serialize false `create_host_path`; corrected
inspection checks the explicit source setting and normalized representation.
Initial failures are separate evidence, not successful runs.

Authoritative database SHA-256 before/after:
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Full schema/table/payload/index/trigger/integrity/foreign-key fingerprints match.
All completed reports, including Phase 8/8.1 evidence, and application/scientific/
collection/storage/migration code, tests, fixtures and lockfiles retain their hashes.
Existing deployment guidance remains an unchanged prefix. Private repositories,
keys, passwords and database copies are outside Git. Owned containers/networks
were removed and local HTTP/TLS endpoints closed. No normal database initialization,
reset, migration, data switch, live collection or EOP download occurred.

## Acceptance criteria

| # | Criterion | Status | Evidence / scope |
| --- | --- | --- | --- |
| 1 | All existing production blockers have been inspected. | PASS | Read all requested reports/runbooks and actual Phase 8.1 blocked criteria 3, 4, 7, 8 and 9; reviewed all seven broader launch-gate groups. |
| 2 | Current repository state and release candidate are identified. | PASS | main remains at published Phase 7 ec1f9f832e5f2a488169d43083d83e24e1eac25e. No commit contains Phase 8/8.1/8.2; current local source identity is a content manifest, not a release SHA. |
| 3 | Hosting configuration is verified or the missing provider decisions are documented. | PASS | Documentation alternative only: existing container routing/storage/probe/TLS contract tested locally; precise provider/account/domain/volume/ingress decisions are inventoried. Production hosting remains BLOCKED. |
| 4 | Actual public HTTPS is verified or explicitly BLOCKED. | BLOCKED | No approved production endpoint, domain, DNS authority, public certificate or renewal mechanism. Six loopback TLS cases are not public HTTPS evidence. |
| 5 | Independent backup destination is configured or its absence is documented. | PASS | Documentation alternative only: no approved independent destination or credentials are bound. Required failure domain, storage identity, encryption-key recovery, retention, RPO/RTO and replacement-host evidence are specified; capability remains BLOCKED. |
| 6 | Off-machine restore succeeds where the destination is available. | BLOCKED | Destination is unavailable. Fresh real encrypted local round-trip and separate database recovery pass; remote_roundtrip_verified=false and off_machine_recovery_verified=false. |
| 7 | Production monitoring is configured or its missing dependencies are documented. | PASS | Documentation alternative only: receiver/token, scheduling, owner/escalation, durable state/log forwarding and host resource sensors remain missing. Existing CLI/log/readiness integration tested locally; operational production monitoring remains BLOCKED. |
| 8 | Actual monitoring-alert delivery is verified where possible. | BLOCKED | No approved production receiver exists. Controlled loopback acceptance/503/cooldown/outage cases pass, all payloads explicitly test=true; production delivery and human escalation remain unverified. |
| 9 | CI evidence corresponds to the exact release SHA. | BLOCKED | No current release commit exists or is published. Read-only Actions evidence covers Phase 7 only, not the Phase 8+ working tree. |
| 10 | Missing remote CI or branch-protection evidence is reported honestly. | PASS | Exact-release CI blocked. Protection and rulesets APIs returned 403; administrator verification required. No required checks, review rules or visibility changes are assumed. |
| 11 | Existing scientific controls are preserved. | PASS | All scientific/ingestion/storage/migration code, tests, fixtures, locks and tolerances unchanged. Fresh reference audits and full regressions pass; actual strict measured-only EOP request refuses with 422 eop_prediction_disallowed. |
| 12 | Existing database records remain intact. | PASS | Authoritative file SHA and full schema/table fingerprints match baseline: schema 3, two snapshots and one each attempt/insertion/gate; restored runtime copy also unchanged. |
| 13 | Applicable regression tests pass or failures are precisely explained. | PASS | Fresh 634 backend/275 frontend, four numerical audit commands, lint/format/TypeScript/build, three browser engines, local TLS/recovery/monitoring/configuration checks pass. Initial harness failures and corrections are retained separately. |
| 14 | Deployment and recovery procedures are reproducible. | PASS | Local scope: new rehearsal runbook plus existing locked images/commands, exclusive backup/restore, gateway failure/recovery, restart/replacement/compatible image rollback and cleanup exercised. Provider-specific host-loss/release operations remain blocked. |
| 15 | Every external dependency and required authorization is identified. | PASS | Infrastructure decision matrix specifies provider/account/budget/domain/DNS/TLS/storage/backup identities/receiver/owners/schedules/traffic and publication/deployment permissions with closure evidence. No credentials or external recipient guessed. |
| 16 | A reasoned final GO/NO-GO decision is produced. | PASS | NO-GO: real hosting/HTTPS, independent host-loss recovery, operational monitoring/alerts, exact-release CI/protection and representative target-host traffic still lack evidence. Stronger scientific accuracy claims remain prohibited. |

## Remaining actions and decision

Before any public launch, an authorized owner must select/provision the host,
durable volume, domain/DNS/TLS/renewal and trusted ingress; approve an independent
backup destination and separately recoverable keys; execute real off-machine and
replacement-host recovery; configure persistent monitoring/log/resource sensors,
job ownership/schedules and real delivery/human escalation; authorize publication
and verify exact-release CI plus actual required protections; and validate target
traffic/shared-NAT behavior. Physical device/assistive-technology checks remain
unperformed. See the infrastructure decision matrix for inputs and closure evidence.

Independent observation-based prediction validation remains **BLOCKED**, orbital
prediction uncertainty **unquantified**. Numerical reference agreement is not
universal physical prediction accuracy or evidence of maneuvers/collision safety.
The existing public scientific notice and intended-use limits remain unchanged.

**NO-GO** follows from missing external evidence, not an arbitrary pass score.
Phase 8.2 has completed its locally authorized work and documented the blocked
external gates. **No commit, push, deployment, publication, remote workflow action,
remote change, paid infrastructure or unapproved credential use occurred.**

Changed in this phase:

- `deploy/compose.yaml`
- `docs/production-deployment-runbook.md`
- `docs/production-infrastructure-decisions.md`
- `docs/production-release-rehearsal.md`
- `docs/phase-8.2-release-readiness-report.md`
- `docs/phase-8.2-integration-results.json`
