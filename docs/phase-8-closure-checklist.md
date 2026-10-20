# Phase 8 closure checklist

**20 October 2026 (IST): NO-GO for public launch.** Local preparation is verified;
production readiness is incomplete. This checklist distinguishes local evidence
from the resources, decisions and authorizations needed to close the remaining
gates. See the [closure report](phase-8-closure-report.md) and
[actual evidence](phase-8-closure-evidence.json) for all 21 acceptance criteria.

## Completed locally

- [x] Inspect current files, prior reports and actual acceptance tables; preserve
  all 39 pre-existing uncommitted files and the authoritative archive.
- [x] Confirm `main` HEAD and published remote are still Phase 7
  `ec1f9f832e5f2a488169d43083d83e24e1eac25e`; identify the newer work as uncommitted.
- [x] Check all 198 Phase 8.2 candidate input hashes against current files and all
  five retained API/web/browser/rollback image IDs against their original evidence.
- [x] Run fresh backend **634 passed** and frontend **275 passed**, scientific
  audits, lint/format, TypeScript and production build. Existing warnings remain.
- [x] Create a fresh consistent backup and separate restore of the genuine
  two-snapshot schema-3 archive; verify full schema/table/payload fingerprints,
  ingestion audit records, integrity/foreign keys and restored APIs.
- [x] Start the existing production-mode images against another new read-only
  restored copy; pass all **17** current container/API checks, including both
  health probes, discovery/details/comparison, readiness, denied admin operations,
  unknown Host, same-origin boundary and unchanged runtime bytes.
- [x] Run observe-only monitoring against those real local services. Correctly
  report aging data, stale ingestion, predicted EOP and unknown production backup;
  send no notification. HTTP 200 readiness is not treated as scientific health.
- [x] Revalidate recent encrypted backup, retention preview, wrong-password,
  TLS, cooldown/receiver, browser and replacement/rollback evidence for unchanged
  inputs. These remain **dated Phase 8.2 results**, not new Phase 8.3 executions.
- [x] Review input limits, read-only history, operator boundaries, security headers,
  safe exceptions/logs, rate/admission limits, private mounts and locked dependencies.
- [x] Retain the existing provider-neutral architecture and runbooks; no new
  provider, database conversion, scheduler, auth system or application feature.
- [x] Preserve every previous report, all application/scientific/test/fixture/lock
  files and database bytes; remove owned test containers/networks and close the
  owned loopback endpoint.

## Production gates requiring external resources or authorization

Unchecked items are **not complete**, regardless of existing configuration files
or local passing tests. Do not deploy, provision, send real alerts, change remote
settings or publish merely by following this checklist.

| Gate | Current status | Required input / action | Closure evidence |
| --- | --- | --- | --- |
| Hosting and public HTTPS | BLOCKED | Owner-selected provider/account/region/budget, host, domain/DNS authority, deployment authorization, TLS issuance/renewal and ingress/firewall/client trust | Actual intended public endpoint, trusted certificate/hostname, redirect/headers, same-origin assets/API, correct allowed hosts and no public admin operations; certificate renewal/reload verified |
| Durable primary archive | BLOCKED | Approved persistent POSIX volume, lifecycle, UID/GID access, capacity and replacement-host procedure | Existing archive survives container and host/volume replacement; full fingerprints and API reads; task `/tmp` and workspace are not production storage |
| Independent backup and recovery | BLOCKED | Approved independent SFTP or HTTPS-S3 repository/failure domain, restricted storage identity, separately recoverable encryption keys, retention/RPO/RTO and recovery owner | Real encrypted upload/retrieval, exact-point separate restore, schema/index/audit/payload/integrity/API verification and recovery from a replacement host without depending on the lost instance |
| Production monitoring and delivery | BLOCKED | Approved receiver/token, operator/on-call ownership, escalation, durable state/log export, check/backup schedules and host resource sensors | Real intended delivery acceptance and confirmed human receipt; duplicate/failure cooldown, outage/recovery, failed backup/restore and monitoring-system failure tests; disk/CPU/memory/OOM/restart/TLS coverage |
| Exact release commit and CI | BLOCKED | Separate review/commit/push authorization; reviewed candidate containing all current changes | Full published SHA and images, successful backend/frontend/release-images jobs and required individual steps for that SHA; no skipped/failed/cancelled/missing required checks |
| Required repository safeguards | FAIL as reported by branch metadata | Administrator review and separately authorized remediation of required status/review settings; appropriate account/plan decision if needed | Fresh branch read reports `protected=false`, protection disabled and checks off/empty. Detailed APIs return 403. Require administrator evidence of effective intended rules; no visibility/plan/settings changes were made |
| Target-host traffic and ingress | BLOCKED | Representative data/users, latency/availability budgets and trusted proxy CIDRs | Target-host load/capacity, shared-NAT, spoofed forwarding, rate-limit and failure/recovery evidence; a two-record local archive cannot establish throughput |
| Device and accessibility scope | NOT VERIFIED | Target device/browser/GPU and assistive-technology test access | Physical device and screen-reader checks. Linux WebKit is not Apple Safari certification; Firefox previously exercised the actual 2D fallback |

Detailed inputs and provider-neutral settings remain in
[infrastructure decisions](production-infrastructure-decisions.md) and the
[deployment runbook](production-deployment-runbook.md). The recommended bounded
candidate keeps same-origin static Nginx, a private non-root FastAPI worker and
explicit schema-3 SQLite on durable storage. Evaluate managed PostgreSQL separately
if multi-host/failover requirements justify a migration project.

## After separate release and infrastructure authorization

- [ ] Review all current tracked/untracked files and exclude secrets, data and
  private test artifacts. Authorize commit/push separately; no such action occurred
  during Phase 8.3. Record the actual complete release SHA, not a content manifest.
- [ ] Inspect the remote branch and Actions runs for that exact SHA. Require
  `backend`, `frontend` and `release-images` and each scientific/migration/lint/
  formatting/type/build/image startup step. Paginate responses as necessary.
- [ ] Match browser/recovery evidence and image IDs to the final sources, or rerun
  when inputs change. These are not automatically remote CI jobs in the current
  workflow. The successful Phase 7 run is not verification of the current candidate.
- [ ] Have an administrator verify effective required-status and review rules,
  correct the reported disabled protection through an authorized change, and retain
  evidence. A 403 does not grant permission to alter visibility or purchase a plan.
- [ ] Provision only the approved target, persistent storage and canonical HTTPS
  origin under separate deployment authorization. Complete public trust/renewal,
  disk reattachment, trusted-ingress and representative traffic checks.
- [ ] Configure approved independent backup credentials and separately recoverable
  keys through secure operator configuration. Never paste credentials into chat,
  Git or `VITE_*`. Rehearse host-loss recovery and approve retention before deletion.
- [ ] Configure the approved alert route and owner; test the actual delivery and
  human escalation. Retain private monitor state and configure monitoring of the
  monitor. Do not delete cooldown state or create unbounded retries.
- [ ] Assign the single collector and EOP maintenance owners. Preserve the persisted
  two-hour gate, every non-200 human review stop, retry budget, validated offline
  resources and their strict coverage/prediction rules. Never collect from restores.
- [ ] Execute the [release/recovery rehearsal](production-release-rehearsal.md) on
  the selected infrastructure. Keep the archive outside releases, use explicit
  pre-migration backups, restore to a new path and verify a schema-compatible image
  rollback. Local rollback does not prove production disaster recovery.
- [ ] Reassess all acceptance criteria using actual external evidence and approve
  a launch decision. Passing local tests or publishing source alone is insufficient.

## Scientific disclosure retained

- [x] Calculated positions remain distinct from observations; epochs, frames,
  units, source hashes and policy labels remain authoritative.
- [x] Independent observation-based prediction validation remains **BLOCKED**;
  orbital prediction uncertainty remains **unquantified**.
- [x] Numerical reference agreement is not universal physical accuracy; element
  differences alone do not establish a maneuver/anomaly or collision risk.
- [x] The visible application notice and [intended-use statement](intended-use.md)
  remain unchanged. These limits restrict claims; the present NO-GO decision follows
  from infrastructure and release safeguards, not a claim of failed numerical tests.

No external production blocker was resolved in Phase 8.3. Local preparation and
the closure review are complete; **Phase 8 production readiness remains incomplete**.
