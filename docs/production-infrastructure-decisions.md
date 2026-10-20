# Production infrastructure decisions and release gates

Status assessed in Phase 8.2: **NO-GO**. No production provider, account, host,
domain, production archive, independent backup repository or alert receiver has
been established. The managed task workspace is a development environment, not
durable production storage. Its configured `ORBITIQ_DATABASE_PATH` identifies the
existing development archive; it is not evidence of a production database.

Keep the existing container architecture: one private FastAPI worker, a same-origin
static Nginx gateway, and schema-3 SQLite on reliable local POSIX storage. The
operator collector, migration, EOP maintenance, backup and monitor remain separate
CLI operations. No additional hosting or monitoring product is selected here.

## Decisions required from the infrastructure owner

Record actual selections and evidence in a protected operations inventory. Do not
put credentials, repository passwords, private keys or webhook URLs in this file.
Every row below is currently **BLOCKED for production**; an implementation or
local test alone cannot close it.

| Decision | Required input / authorization | Evidence needed to close the gate |
| --- | --- | --- |
| Hosting | Named provider/account, owner, region, supported Linux/CPU architecture, budget and provisioning authorization | Target configuration review, resource limits, host lifecycle and recovery exercise on that target |
| Public origin | Owned domain, DNS authority and approved canonical HTTPS origin | Real DNS resolution, trusted public certificate/hostname, redirects, security headers and same-origin static/API requests |
| TLS lifecycle | Issuance and renewal mechanism, secret storage, renewal owner and expiry alert | Actual certificate chain/expiry checks, successful renewal/reload and negative trust/hostname checks; test CA certificates do not qualify |
| Ingress | Direct TLS overlay or trusted external ingress; firewall and trusted proxy CIDRs | No public API port, no forwarded-IP spoofing, actual shared-NAT/rate-limit and perimeter tests; never trust arbitrary forwarded headers |
| Authoritative storage | Durable volume lifecycle, mount path, POSIX/locking semantics, ownership and capacity | Existing schema-3 archive integrity, non-root read access, writer coordination and volume reattachment on a replacement host |
| Backup independence | Approved SFTP or HTTPS-S3 repository, separate failure domain/account/access controls | Actual encrypted upload, retrieval and separate-target restore; independence attested by owner and supported by provisioning records |
| Backup credentials | Restricted storage identity, verified SSH host key or HTTPS trust, restic password and independently recoverable keys | Recovery from a replacement host without relying on the lost application instance; no host-key/TLS bypass |
| Recovery policy | Backup owner, schedule, approved retention, RPO and RTO | Scheduled job evidence, full restored schema/table/payload fingerprints and API checks, measured recovery time and retention review |
| Monitoring | Approved HTTPS receiver and optional token, signal owner, check schedule and escalation | End-to-end test through intended production delivery mechanism plus confirmed human receipt; persistent cooldown state and monitor-failure detection |
| Host sensors | Selected host/platform facilities for disk, CPU, memory, OOM, restarts, TLS and ingress | Controlled failure/threshold tests and alerts; the application CLI is not a host resource monitor |
| Logs | Protected stdout collection, retention/cost limits, access controls and request-log path | Correlated redacted request events, bounded log signal checks and collection failure detection; no raw query/credential forwarding |
| Ingestion and EOP | Single collector owner, explicit schedule/review policy, approved EOP policy and maintenance owner | Two-hour persisted acquisition gate, non-200 review stop, retry budget, freshness/EOP alerts and validated offline resource replacement |
| Release | Separate authorization to review/commit/push, exact candidate SHA and retained image IDs | All required jobs/steps for that SHA, administrator confirmation of branch/ruleset requirements and matching local recovery/browser evidence |
| Traffic and users | Expected archive size, concurrent users, latency/availability goals and target devices | Representative target-host load/capacity/shared-NAT tests and physical device/assistive-technology checks |

Managed PostgreSQL merits a separate evaluation when multi-host operation,
concurrent writers, failover or managed point-in-time recovery becomes necessary.
No conversion is justified solely by an absent hosting decision. Such a project
must preserve identities, audit records, immutability and provenance and have its
own migration and recovery evidence.

## Configuration contract

The [existing deployment runbook](production-deployment-runbook.md) and
[`production.env.example`](../deploy/production.env.example) remain authoritative.
Use a protected external environment file. `.env` files are not automatically
loaded by Python. `VITE_*` values are public frontend configuration, never secrets.

- `ORBITIQ_RELEASE`: reviewed image tag tied to the exact release SHA and recorded
  API/web image IDs. A local content hash is not a Git commit or remote CI result.
- `ORBITIQ_DATA_DIRECTORY`: existing absolute durable directory containing
  `orbitiq.sqlite3`; missing bind paths must fail, not be silently created.
- `ORBITIQ_ALLOWED_HOSTS`: explicit canonical and probe hosts, including
  `127.0.0.1` for the existing container probe. No wildcards, URLs or ports.
- `ORBITIQ_EOP_POLICY`: explicitly approved `measured_only` or
  `measured_or_predicted`; retain freshness and sampling bounds.
- `ORBITIQ_HTTP_BIND`: loopback behind selected ingress by default. API port 8000
  is never published. One origin serves static files and `/api`; permissive CORS
  is unnecessary.
- Optional TLS overlay: protected `ORBITIQ_TLS_DIRECTORY` with `fullchain.pem`
  and `key.pem`, readable by UID 101, and deliberately selected
  `ORBITIQ_HTTPS_BIND`. It does not issue/renew certificates or install redirects.
- Backups: explicitly approved restic binary, private repository/password files,
  new staging directory and private latest-job receipt. Approved external mode
  additionally needs `--independent-destination-approved`; a URL cannot prove
  infrastructure independence. Local test mode cannot claim off-machine recovery.
- Monitoring: canonical HTTPS base URL, private state/backup receipt/log paths,
  approved webhook file and optional private token file. Delivery requires
  `--deliver`; a test requires `--test-alert`. Never send to a real recipient merely
  because a credential exists in the environment.

There is no selected production storage identity, receiver, provider-specific
configuration or schedule in the repository or current managed environment
bindings. Ambient identity variable names do not authorize unrelated cloud access.

## Operational signals and ownership

| Signal | Existing mechanism | Remaining production integration |
| --- | --- | --- |
| Availability / database | `/api/health`, minimal `/api/ready` and monitor | Independent probe schedule, sustained-failure policy and receiver |
| Latency / unsuccessful requests | Structured `http_request` events; monitor's bounded recent 429/5xx/slow-request signal | Durable log export, representative budgets, ingress errors and complete metrics if required |
| Ingestion / cooldown | Redacted `/api/readiness` ingestion component and operator audit history | Single collector schedule, acquisition/review owner and stuck/failed job escalation |
| Orbital freshness | Epoch-based readiness, separate acquisition time | Approved acceptable-age severity; collection success is not freshness or accuracy |
| EOP / leap readiness | Offline resource policy and readiness components | Expiry/coverage owner, controlled maintenance and worker replacement |
| Backup | Successful/failed export receipt; local-only/stale/missing receipts stay unknown | Independent scheduled export, recovery rehearsal, credential and retention ownership |
| Resource exhaustion | CPU/memory/PID/container limits; bounded application admission | Actual host disk/CPU/memory/OOM/restart sensors, capacity alerts and replacement exercise |
| Alert system | Separate opt-in CLI, safe bounded payload, durable admission/cooldown | Receiver approval, HTTPS delivery and human escalation, scheduling and monitoring of the monitor |

The monitor's exit 0 means a check completed, not that components are healthy.
Inspect JSON findings and delivery state. Failed delivery exits 2 and consumes the
same cooldown; invalid configuration/state exits 1. Do not delete state or wrap
failed jobs in unbounded retries. Predicted EOP can be deliberately degraded under
the selected policy; never weaken scientific gates to silence alerts.

## Exact-release verification after separate publication authorization

No publication is authorized by Phase 8.2. These are future release requirements:

1. Review all tracked and untracked Phase 8/8.1/8.2 files, exclude secrets/data and
   retain the existing archive and prior reports. Obtain publication authorization.
2. After authorized commit/push, record the complete release SHA and image IDs.
   Confirm the remote branch contains it; do not use the older Phase 7 CI result.
3. Inspect Actions runs and every job/step for that exact SHA. The local workflow
   currently expects `backend`, `frontend` and `release-images`. Require backend
   tests, all four scientific audits, migration/recovery checks, Ruff, frontend
   tests/lint/format/type checking/build, image builds, Nginx validation and isolated
   container smoke. Record failed, cancelled, skipped and missing checks explicitly.
4. Have an administrator inspect actual branch protection/rulesets, required
   status contexts and review policy. Current API access returns 403; this proves
   neither that protection exists nor that it is absent. Do not change repository
   visibility or purchase a plan to bypass the limitation without authorization.
5. Browser and encrypted-recovery checks are separate local/manual evidence in
   the current workflow. Match their input hashes and image IDs to the final
   candidate or rerun them if inputs change. Do not call them remote CI jobs.
6. Deployment remains a separate authorization even after publication/CI. On the
   selected target, verify the missing production gates and rehearse replacement,
   recovery and compatible rollback before recommending public launch.

Read-only inspection recipes, after a candidate SHA exists:

```sh
git rev-parse HEAD
git status --porcelain=v1 --untracked-files=all
git ls-remote origin HEAD refs/heads/main
gh api 'repos/BibinBinoy777/OrbitIQ/actions/runs?head_sha=<full-release-sha>&per_page=100'
gh api 'repos/BibinBinoy777/OrbitIQ/actions/runs/<run-id>/jobs?per_page=100'
gh api repos/BibinBinoy777/OrbitIQ/branches/main/protection
gh api repos/BibinBinoy777/OrbitIQ/rulesets
```

Paginate if a response reports more results; do not infer absent jobs from a
truncated page. No workflow dispatch/rerun, commit, push, deployment, DNS edit or
resource provisioning belongs to this read-only verification.

Scientific limits remain those in [intended use](intended-use.md): independent
observation validation is BLOCKED, prediction uncertainty is unquantified, and
published numerical reference agreement is not universal physical prediction
accuracy. No maneuver, anomaly, collision or operational-safety claim is supported.
