# Production deployment preparation

This is a provider-neutral, single-host release candidate. No public service was
deployed in Phase 8. Provider/account, region, billing approval, domain, TLS ingress,
durable storage, backup destination, monitoring delivery and operational owners
must be selected and validated before public exposure. See the
[readiness decision](phase-8-readiness-report.md) and [security review](production-security-review.md).

**Current E4 operator entry point:** use the
[release-engineering and approval procedure](engineering-e4-release-readiness.md)
and its [actual verification report](engineering-e4-report.md). Earlier dated
Phase 8 publication statements below describe their original checkpoints. Current
CI includes E1/E2 browser/PDF and E3 isolated installation/recovery, plus E4 image
and artifact identity checks. No production gate is closed by engineering CI.

## Architecture and storage decision

```text
Public HTTPS domain -> trusted TLS ingress -> private loopback Nginx :8080
                                         -> static Vite build / same-origin /api
                                         -> private FastAPI :8000, one worker
Operator collector/maintenance -> authoritative SQLite archive on durable disk
API -> same archive, read-only directory mount
Verified SQLite backups -> separately provisioned protected off-machine storage
```

Use the existing schema-3 SQLite archive for a bounded single-host candidate;
do not introduce a database conversion without measured demand and a migration
project. SQLite needs a reliable local POSIX filesystem, one designated collector,
bounded readers and tested attachment/recovery. Do not use an ephemeral container
layer, cloud task workspace, object-storage mount or unvalidated network filesystem
as the authoritative archive. Keep the current rollback-journal configuration;
WAL plus read-only directory/SHM permissions needs its own live-writer validation.

Managed PostgreSQL is the preferred evaluation for multi-host service, concurrent
writers, failover or managed point-in-time recovery. That requires a provider,
capacity/retention requirements, costs, provenance-preserving data migration,
indexes/immutability checks and a separate recovery rehearsal. It is not implemented.
The two-record local benchmark is insufficient to establish production capacity.

| Event | Candidate behavior / evidence |
| --- | --- |
| API restart | Same mounted archive; tested locally with genuine restored records |
| API container replacement | Image has no archive; same bind mount; tested locally |
| Frontend replacement | Stateless built assets; browser saves remain tied to browser/origin |
| Host/instance replacement | Requires provider-backed disk reattachment or verified off-machine restore; BLOCKED pending provider validation |
| Deployment/rollback | Keep archive outside release directories; drain writers before migrations; no automatic down migration |
| Database outage | Liveness stays separate; minimal readiness returns 503, reads fail safely; recover storage rather than initialize |

No cloud-synchronized saved investigations exist. Preserve browser-local saves and
read-only parameter links. Initial public read-only exploration can retain this
model if product owners accept the visible limitation. Scope managed identity and
user-owned persistent cloud saves separately before promising accounts or sync.
Moving to another origin does not automatically migrate browser storage. The
recipient must have access to the exact archive IDs, epochs, retrievals and hashes.

## Build and configuration

Required: Docker with Compose on the target architecture; locked Python 3.12/uv
0.12.23 and Node 24/npm workflow for operator development/checks. Digest-pinned
base images and both dependency lockfiles are retained. Deliberately review base
image updates and rerun all checks; a pinned old image is not automatically secure.

```sh
docker build --target api -t orbitiq-api:<tested-release-id> .
docker build --target web -t orbitiq-web:<tested-release-id> .
python3 scripts/verify_release_containers.py --release <tested-release-id>
```

The last command explicitly creates a separate empty test archive, starts only
loopback-bound test containers, checks the static page and APIs, verifies unchanged
fixture bytes, then removes its containers and temporary files. It never selects
or initializes the normal archive. No registry push occurs. Record image IDs and
the exact source SHA; Phase 8 working-tree images are not an immutable Git release.

In this managed cloud environment, keep Docker registry credentials unchanged,
use the local socket, and set `BUILDX_CONFIG` to a writable task cache if needed.
For HTTPS build downloads through the session proxy:

```sh
docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt --target api -t orbitiq-api:<tested-release-id> .
docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt --target web -t orbitiq-web:<tested-release-id> .
```

The optional BuildKit secret supplies trusted CAs only during dependency installation;
TLS verification stays on and the bundle is not copied into the images. Compose
builds use `ORBITIQ_BUILD_CA_BUNDLE`. The Docker context is allowlisted and excludes
Git, normal data/backups, environment files, credentials and private keys.

Use `deploy/production.env.example` as a placeholder reference. Keep the real file
outside the checkout with restrictive permissions; do not add its values to logs.

| Setting | Required semantics |
| --- | --- |
| `ORBITIQ_RELEASE` | Tested immutable release identifier; retain corresponding image digests |
| `ORBITIQ_DATA_DIRECTORY` | Existing provisioned absolute durable directory containing `orbitiq.sqlite3`; Compose refuses to create missing bind paths |
| `ORBITIQ_ALLOWED_HOSTS` | Explicit bare DNS/IPv4 probe hosts, comma separated; no URLs, ports or wildcards; include `127.0.0.1` for the supplied health check |
| `ORBITIQ_EOP_POLICY` | Explicit `measured_only` or `measured_or_predicted`; choose scientifically, never relax to mask errors |
| `ORBITIQ_HTTP_BIND` | Default `127.0.0.1:8080`; keep private behind the selected trusted TLS ingress |
| `ORBITIQ_BUILD_CA_BUNDLE` | Trusted CA bundle for optional build-time secret mount |

Compose sets `ORBITIQ_ENVIRONMENT=production`, `/data/orbitiq.sqlite3`, 24h/72h
freshness thresholds and 361 samples/86400 seconds. The application rejects invalid
hosts, paths, EOP, sampling and freshness settings. Production startup validates
the existing database read-only and requires schema 3. Startup never initializes,
migrates, collects or downloads EOP. A full startup integrity check can take longer
on a large archive; measure it before choosing startup-probe grace periods.

Provision directory traversal and read permission for API UID/GID 10001, ideally
directory 0750/file 0640 with a deliberately managed read group; protect the parent
and backups. Verify actual container UID access before starting. The API must not
own collection credentials or a writable archive mount. Nginx runs as UID 101.
API and gateway have read-only roots, dropped capabilities, PID/memory/CPU limits
and temporary `/tmp` mounts. API has no published port or outbound Internet network.

## Release, ingress and probes

Only after a separately authorized deployment, use the tested Compose file with
protected configuration, for example:

```sh
docker compose --env-file /protected/path/production.env -f deploy/compose.yaml config --quiet
docker compose --env-file /protected/path/production.env -f deploy/compose.yaml up -d --no-build --pull never --wait
```

These are operator deployment instructions, not commands executed against a public
host in Phase 8. Preload the reviewed images by an approved registry/transfer process;
do not rebuild floating dependencies on the production host. Keep old images available.

The selected ingress must provide HTTPS certificates/renewal, HTTP-to-HTTPS redirect,
appropriate HSTS after HTTPS validation, trusted client addressing, connection/body
limits, traffic budgets, request timeouts and DDoS protection. Do not expose :8000.
The supplied Nginx template is plain HTTP on private :8080; no HTTPS/DNS/certificate
or public firewall claim follows from local testing.

Nginx limits ordinary API reads to 30 requests/s with burst 60, calculations to
1 request/s with burst 6, and connections to 16 per source IP. Rejections return
429 with Retry-After. The app admits at most four simultaneous calculation paths
per one worker, returning 503/Retry-After at capacity; Uvicorn limits concurrent
connections/tasks to 32. Bodyless read-only API requests, 4096-byte request URI,
16-KiB aggregate application headers and existing scientific time/sample/query
bounds apply. Proxy connect/read/send timeouts are 3/30/10 seconds; they are not
a hard cancellation deadline for Python work. Keep one worker or reassess global
admission limits. Do not claim fleet-wide limits from a per-process counter.

Behind an upstream load balancer, Nginx sees the balancer's IP until a **verified
provider-specific trusted-CIDR real-IP configuration** is installed and spoofing
tested. Otherwise the rate bucket is shared across users. Never trust arbitrary
X-Forwarded-For. The API ignores proxy identity headers; the gateway strips them,
authorization and cookies because this public API has no authentication contract.
Review these choices before introducing authenticated endpoints. Rate/burst and
memory/CPU defaults need representative production load and shared-NAT testing.

| Probe | Meaning / action |
| --- | --- |
| `/api/health` | Liveness, no storage/science claim; restart on sustained process failure |
| `/api/ready` | Minimal schema-3 bounded database reads, 200/503; no internal path/details; route traffic only when ready |
| `/api/readiness` | Existing redacted informational scientific/ingestion assessment; HTTP 200 may report degraded/unavailable/unknown; inspect its JSON |

Do not restart repeatedly because data age is stale or EOP predictions are disallowed.
Those require an operator/scientific-resource decision, not a liveness workaround.

## Collection, resources and monitoring

Run one designated, separately managed operator collector against the authoritative
archive, using the locked environment and [collection runbook](ingestion-operations.md).
No automatic scheduler was enabled. A future scheduler must respect the persisted
two-hour global gate, deferred backoff, three-failure budget and every non-200 review
stop; do not wrap it in an unbounded restart/retry loop. Never collect from test or
restore copies. Store successful/failed job outcomes and notify the assigned owner.
When the provider is unavailable, continue eligible reads of existing validated
records with their actual age; do not bypass EOP/leap or source-validation failures.

EOP/leap files are locked offline package resources. Use the
[controlled maintenance runbook](eop-maintenance.md), separate validated candidate
environment, deliberate selection and worker restart. Keep source hashes, expiry
and verification receipts. Ordinary browsing cannot collect or maintain resources.

Ship stdout logs to a selected protected log service with retention and cost limits.
Application request records contain UTC time, generated request ID, route template,
method, status, latency and response size. Edge records correlate the backend
request ID and omit client IPs, paths, queries, referrers, cookies and authorization.
Raw Uvicorn access logging is disabled. Configure safe retention and operator access.
No monitoring vendor or alert delivery channel is configured or tested yet.

Before launch, assign owners and alert routes for sustained 5xx/readiness failure,
latency/capacity/429 changes, disk capacity, failed or stuck collection, review/cooldown
state, oldest acceptable element age, EOP/leap expiry/unknown status, failed backups,
missing recent verified backup and failed restore rehearsals. Use `/api/readiness`
and private CLI evidence; do not publish raw internal logs or a new admin endpoint.

## Backup, migrations and recovery

Follow the existing [backup/restore runbook](backup-restore-runbook.md). Use SQLite
online backup, exclusive new destinations and manifest/payload verification. Copy
verified backups to protected encrypted off-machine storage, test retrieval and
restore on the selected infrastructure, and record checksums and elapsed recovery
time. Proposed backup-after-insertion plus scheduled checks is not an enabled
schedule. RPO, RTO, retention, encryption keys and recovery owner remain unapproved
launch decisions; a local successful rehearsal does not establish them.

Before an upgrade, stop the collector and drain API traffic. Retain the current
image/configuration and a verified pre-upgrade backup. Existing migration CLI:

```sh
export PYTHONPATH=backend
export ORBITIQ_DATABASE_PATH=/absolute/path/to/authoritative/orbitiq.sqlite3
uv run --locked python -m orbitiq.database migrate --backup /absolute/path/to/new-pre-upgrade.sqlite3
uv run --locked python -m orbitiq.database check
uv run --locked python -m orbitiq.database verify-archive
```

Migration is explicit, writer-locked and transactional, with a prior backup;
schema 3 is a no-op. Existing schema-1/2 upgrade and failed-DDL rollback tests pass.
No Phase 8 migration is needed. Never run `init` against an existing archive.
Never down-migrate by dropping audit records.

For failure: stop writers, preserve failed image/config and logs by request ID,
check dependency status, storage permissions/free space and recent maintenance.
Rollback to the retained tested image only if it supports the current schema.
If data recovery is needed, restore to a new path, compare full table/schema/payload
fingerprints, verify exact IDs and APIs, and then explicitly switch the mount during
maintenance. Retain the original and account for provider calls after the backup
before re-enabling collection; an old gate cannot authorize an early retry.

Post-release checks must include HTTPS/redirect/headers, actual same-origin health,
readiness JSON, exact known-source detail/calculation/share reconstruction, static
assets/WebGL fallback, rate-limit behavior, archive fingerprints, backup retrieval,
logging/alert delivery and rollback. Local evidence covers a restored two-record
archive, isolated fixture CI smoke, restart and replacement on one host only.

Independent observation-based prediction validation remains **BLOCKED**, uncertainty
is unquantified, and the approximately 1.317 cm numerical-reference residual
explanation and Phase 6.1.1 precision correction remain unchanged. Ground tracks,
element differences and reference agreement do not establish guaranteed future
positions, maneuvers or collision risk.

## Phase 8.1 optional TLS target and operator checks

The defined candidate target is a Linux host with Docker/Compose, a separately
provisioned durable POSIX archive and an independently approved backup destination.
No provider, public hostname, DNS records, account/billing approval or production
certificate has been selected. This target is a preparation choice, not an existing
host. The exact external inputs still required are: provider/account/region and
owner approval; durable volume lifecycle/reattachment; domain and DNS authority;
certificate issuance/renewal ownership; ingress trusted-client configuration and
traffic budget; independent backup/key recovery; monitoring receiver and on-call;
and publication authorization plus exact-release CI/protection evidence.

`deploy/compose.tls.yaml` optionally adds Nginx TLS on container port 8443 while
keeping the existing HTTP listener bound to loopback by default. It reuses the same
static/API routes, security headers and limits, with TLS 1.2/1.3 and no session
tickets. It requires `ORBITIQ_TLS_DIRECTORY` containing `fullchain.pem` and `key.pem`
readable by Nginx UID 101. Provision restrictive file/directory permissions through
the selected secret-management/host mechanism; no key is included in source or an
image. Do not use generated test keys for a public release.

```sh
docker compose --env-file /protected/path/production.env \
  -f deploy/compose.yaml -f deploy/compose.tls.yaml config --quiet
# After separate deployment authorization only:
docker compose --env-file /protected/path/production.env \
  -f deploy/compose.yaml -f deploy/compose.tls.yaml up -d --no-build --pull never --wait
```

`ORBITIQ_HTTPS_BIND` defaults to `127.0.0.1:8443`. A public bind, DNS, firewall,
port-80 redirect policy and real certificate chain/renewal require deliberate
provider-specific setup. Never publish the private API or assume HTTP-to-HTTPS
redirects exist merely because TLS is enabled. The initial HTTPS-only HSTS header
uses a one-hour staging period; choose a longer policy only after real-domain
HTTPS/renewal validation. HTTP responses do not assert HSTS. Probes explicitly
bypass proxies only for their own loopback address, so an inherited proxy cannot
silently redirect the local dependency probe.

Phase 8.1 tested the overlay on loopback with an ephemeral CA and hostname-valid
certificate, verifying TLS 1.2/1.3 and HTTPS readiness, HSTS, rejection of an untrusted
CA and rejection of a wrong hostname. Certificate verification was never disabled.
This is **not public-domain HTTPS evidence**. Confirm actual HTTPS, redirect/headers,
certificate expiry/renewal and host/volume replacement before closing hosting.

Use the [encrypted backup procedure](backup-restore-runbook.md) and
[monitoring/alert runbook](monitoring-and-alerting.md). No backup/monitor schedule,
production receiver, external storage credentials or provider resource was activated.
The [intended-use statement](intended-use.md) applies to every release and remains
visible in the application.

### Browser verification and exact-release CI follow-up

The isolated `deploy/Dockerfile.browser` pins the official Playwright runtime and
matching Python packages; it is a test image, not an application release image.
Build with the session CA secret when required, retaining TLS verification. The
critical runner uses a local approved two-source test archive and makes only GETs:

```sh
python scripts/verify_browser_critical.py --base-url http://127.0.0.1:8080 \
  --engine firefox --catalog 25544 --first 1 --second 2 --output /private/firefox.json
```

Repeat with `webkit` and `chromium`. IDs must describe records actually available
in the selected isolated archive; fixture-based runs must be labelled as fixtures.
Do not ingest merely to satisfy this test. The Docker browser can share the network
namespace of the owned local web test container to reach its loopback listener;
this needs no host networking or production access. Firefox/WebKit critical flows
now pass in that supported runtime. Firefox used the actual 2D fallback when WebGL2
was unavailable; WebKit/Chromium rendered software WebGL2. No physical-device,
physical-GPU, Apple Safari or screen-reader certification is implied.

At the Phase 8.1 checkpoint, the published commit was Phase 7 `ec1f9f8`; those
Phase 8/8.1 changes were still local. For every new **authorized** publication,
record the actual full
release SHA, locate Actions runs for that exact SHA, and inspect every backend,
frontend and release-images job/step. Require tests, all scientific audits,
migration/recovery checks, lint/format, TypeScript/build and image startup checks;
record skips/cancellations/missing jobs. E1/E2 browser/PDF and E3 local-fixture
recovery now run in CI; encrypted off-machine recovery remains a separate target
requirement. All artifacts must match the selected source/images. Confirm
required-status/review rules with a repository
administrator; existing integration access returns 403 for protection/rulesets.
Do not substitute the successful Phase 7 run for current-release verification.


## Phase 8.2 infrastructure decisions and repeatable rehearsal

The [infrastructure decision checklist](production-infrastructure-decisions.md)
records the still-missing provider/domain/storage/receiver/ownership inputs and
exact-release CI/protection requirements. No provider was guessed or provisioned.
The [local release rehearsal](production-release-rehearsal.md) describes isolated
recovery, production-mode probes, replacement, compatible image rollback, TLS,
browser, backup and monitoring verification without using the normal archive as
a restore target. See the [Phase 8.2 report](phase-8.2-release-readiness-report.md)
for current results and the continuing NO-GO decision.

Both API and gateway now have loopback dependency health checks. Gateway readiness
uses its actual same-origin `/api/ready` route with BusyBox wget and proxying
disabled only for that loopback request. Compose `up --wait` therefore checks the
gateway as well as the API. Previously a restarting gateway could escape the
intended readiness gate because no web health check existed. Retain explicit
HTTP/TLS functional checks: container health does not verify public TLS, renewal,
scientific readiness, capacity or persistence. Health checks alone do not restart
an unhealthy process; configure and verify the selected production policy.
