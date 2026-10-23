# E4 release engineering and production-readiness decisions

Assessment date: **23 October 2026 (IST)**. This is repository-side preparation,
not deployment authorization. Production remains **NO-GO**. See the
[execution report](engineering-e4-report.md), historical
[Phase 8 closure](phase-8-closure-report.md), and the current
[infrastructure decision inventory](production-infrastructure-decisions.md).

## ADR E4-001: retain the existing bounded single-host candidate

Decision: retain one private FastAPI worker, same-origin static Nginx/Vite,
explicit schema-3 SQLite on durable local POSIX storage, and separate operator
collection/backup/maintenance/monitor commands. This accepts the architecture for
local release verification only; no host, provider or database is provisioned.

The API mounts the archive read-only, has no published port, and does not collect
from providers during browsing. Keep authoritative storage outside image/release
folders and container layers. One designated collector owns the durable cooldown.
Do not run collectors against restored copies. The application currently has no
server-owned user accounts or persisted report store: report captures/downloads
are generated on request, and saves remain browser/origin-local. There is no need
to add an object store or background queue solely for this milestone.

Evaluate managed PostgreSQL separately when measured concurrent writes,
multi-host/failover or point-in-time recovery requirements justify it. That project
must preserve IDs, provenance, immutability and audit history and verify migrations
and recovery. Kubernetes, distributed locks and managed queues are not justified
by the present workload. Two genuine stored records do not establish capacity.

## Current security assessment

The Phase 8 [security review](production-security-review.md) is dated evidence;
E4 preserves it and assesses the current state here.

- Production startup requires explicit hosts, absolute existing storage and an
  explicit EOP policy. It validates schema 3 without creating/migrating data.
- API reads are anonymous by design, with bounded query/time/sample/page/report
  inputs, body/method/header/URI restrictions, safe error envelopes and bounded
  expensive-request admission. Ordinary reads never perform upstream retrieval.
- Same-origin hosting has no permissive CORS grant. Uvicorn ignores proxy headers;
  Nginx strips user identity/authorization/cookies. Arbitrary forwarded addresses
  cannot select the edge rate bucket. A future load balancer needs reviewed trusted
  CIDRs and spoof/NAT/capacity testing, not blanket forwarded-header trust.
- CSP, nosniff, framing/referrer/permissions headers are edge controls; API error
  headers and request IDs remain application controls. HSTS applies only on actual
  TLS. No public certificate, redirect or renewal is established by a test CA.
- Logs contain generated correlation IDs, route templates, method, status, time,
  latency and size; queries, cookies, credentials and arbitrary request IDs are
  excluded. Raw access logs are disabled. Retention/access/collection remain host
  decisions. Configuration examples contain placeholders; `.env` is not loaded
  automatically, and `VITE_*` values are public, never secret storage.
- Report JSON/HTML/PDF downloads contain approved source evidence and limitations,
  not browser-local private notes. There is no private-document ownership promise.
  **Any configured validation archive is publicly readable through its existing
  bounded APIs.** Never point it at private ESA/reference inputs. Before public
  use, approve every served dataset's disclosure and redistribution conditions.
  The standard Compose configuration does not mount that opt-in archive.
- There is no account authentication/authorization system. Anonymous approved
  archive exploration can be a product decision; operator CLIs require protected
  host/filesystem access. Private investigations, user-owned cloud saves, uploads
  or admin APIs require an explicit identity/ownership/abuse design before exposure.
  The present gateway strips credentials, so future authentication cannot be added
  by assuming existing Authorization/Cookie forwarding works.

### Confirmed dependency finding and coverage

GitHub advisory [GHSA-6q48-6c7w-9gw2](https://github.com/advisories/GHSA-6q48-6c7w-9gw2)
classifies the vulnerable certifi CA bundle as **critical**. The starting lockfile
selected `2026.7.22`; the published first patched version is `2026.10.19`.
E4 updates only that transitive package in `uv.lock`, with new distribution hashes.
Rebuild API images; retaining an old image retains its old trust store. No actual
interception or compromise of OrbitIQ traffic is asserted.

The existing audit strategy is retained: isolated pip-audit 2.9.0 over fully pinned
uv-exported requirements, plus npm's locked-tree audit. CI now runs both and keeps
their reports. Python uses strict coverage/refusal; npm fails at high/critical
severity and records all reported levels. Advisory lookup errors fail their step;
they are not a zero-vulnerability result. Audits use live advisory services, not
live orbital providers. UV's lock/hash checks remain the installation authority;
export without hashes is used only for name/version advisory lookup, not install.

Known-advisory matches are not a complete security guarantee. No comprehensive
OS/base-image vulnerability scanner, publisher-signature verification, penetration
test, denial-of-service capacity study or physical-device audit is claimed. Before
public release, review current final images and advisories, dataset disclosure,
perimeter abuse protection, target capacity and operator privileges. Old E3 images
with the vulnerable bundle are not an approved production rollback target.

## Exact-source release verification

The existing three-job workflow remains authoritative:

| Job              | Blocking work                                                                                                                                                   |
| ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `backend`        | Locked install, Python advisory audit, full tests/scientific audits, migrations/recovery, Ruff, E3 isolated installation/restart/failure/recovery               |
| `frontend`       | Locked install, npm audit, tests, ESLint/Prettier, TypeScript/build, retained frontend artifact                                                                 |
| `release-images` | Requires both jobs above; labelled images, exact frontend/image comparison, gateway/TLS/outage/replacement tests, E1/E2/PDF, final image/source/artifact record |

No redundant workflow is added. Failed/cancelled prerequisites skip image
verification; skipped/missing/failed/cancelled checks cannot authorize a release.
Always-uploaded partial diagnostics are not a successful release record.

From a **clean committed** checkout, with Python 3.12, uv 0.12.23, Node 24/npm 11,
Docker/Compose, OpenSSL and Poppler available:

```sh
uv sync --locked
(cd frontend && npm ci && npm test && npm run lint && npm run format:check && npm run build)
export ORBITIQ_RELEASE="$(git rev-parse HEAD)"
export ORBITIQ_SOURCE_TREE="$(git rev-parse HEAD^{tree})"
# A new evidence directory, not an existing data/recovery directory:
export ORBITIQ_RELEASE_EVIDENCE="$(mktemp -d /tmp/orbitiq-release-XXXXXXXX)"
docker build --build-arg ORBITIQ_SOURCE_REVISION="$ORBITIQ_RELEASE" --build-arg ORBITIQ_SOURCE_TREE="$ORBITIQ_SOURCE_TREE" --target api -t "orbitiq-api:$ORBITIQ_RELEASE" .
docker build --build-arg ORBITIQ_SOURCE_REVISION="$ORBITIQ_RELEASE" --build-arg ORBITIQ_SOURCE_TREE="$ORBITIQ_SOURCE_TREE" --target web -t "orbitiq-web:$ORBITIQ_RELEASE" .
python3 scripts/verify_release_evidence.py capture --release "$ORBITIQ_RELEASE" --frontend frontend/dist --output "$ORBITIQ_RELEASE_EVIDENCE/capture.json"
python3 scripts/verify_release_containers.py --release "$ORBITIQ_RELEASE" --tls --output "$ORBITIQ_RELEASE_EVIDENCE/proxy.json"
docker build -f deploy/Dockerfile.browser -t orbitiq-browser:e1 .
python3 scripts/run_browser_regressions.py --release "$ORBITIQ_RELEASE" --engineering-e2 --output "$ORBITIQ_RELEASE_EVIDENCE/browser"
python3 scripts/verify_release_evidence.py seal --capture "$ORBITIQ_RELEASE_EVIDENCE/capture.json" --frontend frontend/dist --directory "$ORBITIQ_RELEASE_EVIDENCE" --output "$ORBITIQ_RELEASE_EVIDENCE/verified-release.json"
python3 scripts/verify_release_evidence.py verify-files --record "$ORBITIQ_RELEASE_EVIDENCE/verified-release.json" --directory "$ORBITIQ_RELEASE_EVIDENCE" --frontend frontend/dist
```

Use the [existing development](../README.md#development),
[deployment configuration](production-deployment-runbook.md),
[backup/restore](backup-restore-runbook.md) and
[monitoring](monitoring-and-alerting.md) runbooks for their complete contracts.
On read-only-home machines use writable `UV_CACHE_DIR`, `npm_config_cache` and
`BUILDX_CONFIG`. Managed proxy builds also need the documented
`--secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt`; never disable TLS.
The API/web image defaults remain buildable for development, but unrecorded image
labels cannot pass a release capture.

Local implementation testing can explicitly pass `capture --candidate-index`
after reviewing/staging all changes. It records the current base revision plus
the index tree, labels itself `reviewed-index`, and always sets
`release_candidate=false`. It is not proof that an unpublished tree is a Git
release. CI uses only clean committed mode. Untracked or unstaged changes refuse
both modes; documentation changes after capture also invalidate sealing.

The capture records full source-file hashes (including locks and build/proxy
configuration), Git revision/tree, local API/web image IDs and platform, and every
frontend file digest. The image web root must exactly match the frontend artifact
from the successful frontend job. Stock gateway HTML is removed so extra files
cannot silently enter that equality. OCI labels are checked against the source.

After tests, sealing refuses changed source, retagged images or changed frontend
files and requires successful proxy/TLS, all three browser engines, E2 accessibility,
expected-failure probes and seven PDF checks. PDFs and paired captured JSON now
have hashes recorded by the PDF validator; sealing refuses changes after that
validation. The final record hashes the capture and test/PDF evidence. `verify-files`
can recheck downloaded evidence and an optional frontend artifact without Docker.
It verifies file integrity, **not deployment approval or image availability**.

These records are unsigned trusted-CI evidence, not independent cryptographic
build attestations. OCI labels alone are self-asserted metadata. A compromised
builder or someone able to replace both records and hashes is outside this check.
Image IDs are local content identities, not registry manifest digests. This
pipeline compares identity before/after tests; it is not an adversarially isolated
builder. Branch review/protection, trusted artifact access and deliberate approval
remain necessary. CI retains metadata/diagnostics for seven days, not application
image archives or production history. No registry push, release object or deploy
is performed. Before actual deployment, retain the **same tested image bytes** in
an owner-approved artifact store and verify transfer integrity/platform. Rebuilding
later requires a new complete verification; the old record cannot bless new IDs.

## Repository protection and final approval

The current branch API reports `main` unprotected. Detailed protection returns
HTTP 403 (integration access); rulesets return HTTP 403 (private-repository plan
restriction). Effective required-check/review/bypass behavior is not verified.
No settings, plan or repository visibility are changed by E4.

Before launch, an authorized administrator should select supported controls:
PR-only default-branch updates, an assigned independent reviewer, stale-approval
dismissal after changes, successful `backend`, `frontend` and `release-images`
checks from the intended Actions workflow, up-to-date/merge-queue verification,
resolved review conversations and blocked force/deletion/direct bypass. Define an
audited emergency process; do not invent an unavailable reviewer or silently use
admin bypass. Require the final merged/release SHA's own verification, not only a
PR merge-ref or earlier branch commit. Capture Settings/API evidence and perform
an approved negative merge test proving a failed/missing check blocks merging.
These remote changes/tests require separate authorization.

A future release reviewer must confirm:

1. Exact candidate SHA is published at the intended repository/ref; source tree,
   locks, OCI labels and retained image IDs match the verification record.
2. All expected checks and steps completed successfully for that SHA. Inspect run
   event/head SHA, test/advisory reports, artifacts/digests and failures/skips.
3. Current vulnerability/disclosure review and the public anonymous-data contract
   are acceptable; no private datasets, credentials or environment files are served.
4. Durable storage ownership/capacity and single collector coordination are verified.
   Before any schema change stop writers/drain traffic, create a verified backup
   and check migration/current-schema compatibility using isolated copies.
5. Production HTTPS/domain/renewal/ingress, independent backup/key recovery,
   monitoring/alert delivery, operators, target load and repository protections
   have their own current closure evidence.
6. The owner explicitly authorizes deployment of those retained artifacts and
   protected configuration. No successful local record supplies that approval.
7. After the future deployment, verify actual HTTPS/headers/health/readiness,
   approved source/report workflows, storage, logs and alert delivery and record
   the outcome. Stop/recover on failure without silently initializing storage.

## Recovery and rollback

No E4 migration exists. Schema-3 initialization is explicit and no-overwrite;
schema-1/2 upgrade uses the existing writer-locked transactional migration and
new pre-upgrade backup. Production startup and restore never replace the archive.
Temporary-database suites and the E3 isolated rehearsal cover WAL inclusion,
interruption, corruption, row/audit fingerprints and restored APIs. Do not raw-copy
or hash a changing SQLite file; use engine snapshots or the established verified
DELETE-mode shared read transaction for a preservation checksum.

Local release smoke additionally replaces its API container against the same
new read-only empty archive and checks liveness/readiness and unchanged bytes.
This tests same-release replacement, not host-loss durability or a different
approved-release rollback. No suitable prior patched production release is selected;
rollback to a different approved release remains a target rehearsal requirement.

For a future rollback, retain the prior approved image IDs, protected configuration
and compatible schema contract before deployment. Stop writers/drain traffic;
verify current schema and backup first; select the retained image IDs without a
floating rebuild; recheck health, source IDs and read workflows. Do not reverse
schema changes by deleting audit/history or restore over the live archive. If
current data is incompatible, restore a verified backup to a **new** path, compare
all schema/table/payload/audit fingerprints and APIs, and separately authorize a
mount/path switch while retaining the original. Account for provider activity
since the backup before resuming collection. An application rollback is not a
schema downgrade or data recovery guarantee.

Off-machine storage, encryption/key recovery, approved retention, schedules,
RPO/RTO and independent replacement-host recovery remain unverified. The monitor's
existing 48-hour receipt threshold is not an approved product RPO. Owners must set
loss/recovery objectives from collection cadence and historical-record value and
measure an actual independent recovery. Local archives and Git are not substitutes.

## Operations and remaining external gates

| Signal                   | Repository mechanism                                                                       | Required production closure                                                                                    |
| ------------------------ | ------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| Process/startup/shutdown | Liveness and Uvicorn lifecycle diagnostics                                                 | Protected host logs, restart/escalation policy and collection-failure detection                                |
| Mandatory database       | Minimal readiness 200/503 and safe production startup validation                           | Durable volume lifecycle, permissions, disk monitoring and replacement recovery                                |
| HTTP failures/latency    | Redacted route/request-ID/status/duration/size events; monitor's bounded recent log checks | Retention, route-specific error/latency budgets, 429/shared-NAT capacity and owner alerts                      |
| Provider attempts        | Operator audit, failed/deferred/review states; no live availability probe on reads         | One collector owner/schedule and stuck/failure/review escalation respecting provider policy                    |
| Orbital freshness        | Epoch age, separate acquisition/validation/insertion clocks                                | Owner-approved stale-age severity; success does not imply fresh or accurate elements                           |
| Report/export failures   | Request route/status/latency and browser error states                                      | Selected client-failure and server-failure collection, abuse budgets and escalation                            |
| Scientific resources     | EOP/leap components and stated qualification status                                        | Resource maintenance owner; never weaken science to silence an alert                                           |
| Backups/monitor jobs     | Safe receipts, explicit check/delivery outcome and durable cooldown state                  | Independent backup, approved receiver, human receipt, persistent schedules/state and monitoring of the monitor |
| Host/edge resources      | Container limits, request limits and local TLS template                                    | Disk/CPU/memory/OOM/restart/TLS-expiry/firewall/renewal sensors on the actual target                           |

`/api/health` stays up for an optional provider failure; `/api/ready` fails for
missing mandatory storage. `/api/readiness` can return HTTP 200 with degraded or
unknown components: inspect JSON. Do not restart repeatedly for stale elements or
known scientific blocking. Monitor exit 0 means a check completed, not all healthy.
No production monitor receiver, delivery integration or scheduler is configured.
Loopback test certificates and receiver tests do not verify actual public trust,
renewal or human alert receipt. RPO/RTO, retention, cost, capacity and on-call are
owner decisions, not invented defaults.

Phase 8 launch gates remain open. Phase 11.3.1 remains **PARTIAL** and scientific
evaluation **BLOCKED**. ESA time, KIN-quality and frame-alignment questions remain
unresolved. Historical availability/creation times are unknown, complete fitting
lineage and statistical independence are not established, and no genuine Swarm-A
residual or independent-accuracy claim is produced by E4.
