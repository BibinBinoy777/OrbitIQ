# Phase 8 production-readiness report

**Public deployment recommendation: NO-GO.** Production preparation is implemented
and locally verified. The acceptance review has **23 PASS, 0 FAIL, 1 BLOCKED**;
provider-specific deployment/recovery completion is blocked. No public host,
production durability, monitoring service or accuracy certification is claimed.

## Baseline and architecture findings

Started from clean `main` at published Phase 7 commit
`ec1f9f832e5f2a488169d43083d83e24e1eac25e`. Inspected prior Phase 4/5/6/6.1/6.1.1/7
reports/evidence, services, archive schema/migrations, collection policy, EOP
maintenance, URL/local-storage model, tests, CI and environment. All prior docs
remain unchanged. Baseline executed: **589 backend**, **275 frontend** tests and
production build passed. No production deployment/container configuration existed.

No accounts/authentication or server-owned saved investigations exist. The schema-3
SQLite archive contains two genuine ISS snapshots (#1/#2, NORAD 25544), one audited
collection attempt, one insertion-ledger row and one collection-gate row. Collection
and maintenance are CLI-only, bounded and operator-controlled. Existing scientific
readiness already distinguishes database, data age, collection, EOP and leap status.

Prepared a provider-neutral single-host candidate: production static files in
unprivileged Nginx, same-origin `/api` to a private non-root FastAPI worker, and a
read-only mount of an operator-provisioned durable archive. The collector remains
separate. Managed PostgreSQL is evaluated for multi-host/failover requirements;
no speculative conversion, Kubernetes, queue, account system or scheduler was added.
See the [deployment/runbook](production-deployment-runbook.md) and
[focused security review](production-security-review.md).

## Changes implemented

Production startup requires explicit valid hosts, absolute database configuration,
EOP policy and bounded freshness/sampling settings, validates the existing schema-3
archive read-only, and refuses invalid storage without creating or migrating it.
Development liveness retains its database-independent behavior. New `/api/ready`
returns only `ready` or `unavailable` with 200/503 for bounded database reads;
`/api/readiness` remains the separate scientific/ingestion assessment.

Added production bodyless/read-only method and URI/header limits, TrustedHost
validation, four simultaneous calculation admissions per worker and safe generic
pre-response errors. Structured API logs include generated request IDs, UTC,
route templates, status, latency and bytes, omitting input values and sensitive
headers. Production disables raw URL access logs and interactive API docs.

Added digest-pinned multi-stage API/web images, allowlisted build context, locked
installs, optional transient trusted CA mounts, private/read-only non-root Compose
services with CPU/memory/PID limits, and a same-origin gateway. Gateway controls
include CSP/security headers, timeouts, rate/connection limits, redacted correlated
logs and gzip. No application dependency or lockfile changed. The template requires
real TLS ingress and trusted-client configuration; plain local HTTP is not HTTPS.

Added 20 production boundary tests and a reusable isolated release-container smoke
runner. Local CI configuration now explicitly includes expanded/geodetic audits,
frontend artifact output, image builds, Nginx config validation and fixture startup
verification. No remote workflow was modified, triggered or rerun.

## Actual command results

Commands ran at repository root except npm/tsc in `frontend`. Python used
`UV_CACHE_DIR=/tmp/orbitiq-uv-cache`; scientific scripts used `PYTHONPATH=backend`.
Full commands, outputs, timestamps and additional local runner sources are in
[structured evidence](phase-8-integration-results.json). No interrupted command is
counted as a pass. The final backend rerun followed the UTC log-field addition.

| Command | Actual result | Exit |
| --- | --- | --- |
| `uv run --locked pytest -q` | **609 passed**, existing deprecation warning | 0 |
| `npm test` | **275 passed**, 20 files | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_scientific_references.py --output /tmp/orbitiq-phase8/verify_scientific_references.json` | 40 passed, 0 failed | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-phase8/verify_earth_fixed_references.json` | 6 passed, 0 failed | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_phase61_science.py --output /tmp/orbitiq-phase8/verify_phase61_science.json` | 32 numerical comparisons passed; observation validation BLOCKED | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_phase611_geodesy.py --output /tmp/orbitiq-phase8/verify_phase611_geodesy.json` | 28 independent-reference component cases + 28 separate round-trips | 0 |
| `uv run --locked ruff check .` / `uv run --locked ruff format --check .` | Passed; 83 Python files formatted | 0 / 0 |
| `npm run lint` / `npm run format:check` | Passed | 0 / 0 |
| `npx --no-install tsc --noEmit` / `npm run build` | Passed; existing renderer chunk warning | 0 / 0 |
| `npm audit --json` | Zero advisory matches in locked tree | 0 |
| isolated `pip-audit==2.9.0` against project environment | 29 installed packages, zero known matches | 0 |
| `docker build --target api ...` / `docker build --target web ...` | Both final images built with lockfiles, pinned bases and TLS verification | 0 / 0 |
| `python scripts/verify_release_containers.py --release phase8-local` | Separate explicit empty schema-3 fixture, static/health/ready/list reads passed, bytes unchanged, containers removed | 0 |
| `docker compose ... config --quiet` / actual gateway `nginx -t` | Passed | 0 / 0 |
| `PYTHONPATH=backend uv run --locked python -m orbitiq.maintenance.recovery --directory /tmp/orbitiq-phase8/recovery --keep-restored` | Genuine two-record backup/restore and restored API checks passed | 0 |

The full suites include existing ingestion/deduplication/cooldown, schema-1/2
migration/failure rollback, backup/restore, saved/share validation and geodetic
precision regressions. Scientific algorithms, fixtures and thresholds remain
unchanged. The geodesy script used the existing frozen GeographicLib references;
no C++ reference executable was rebuilt or rerun. Package advisory checks are
dated service lookups; no comprehensive base-OS/image scan is claimed.

## Genuine recovery, persistence and security evidence

The local recovery rehearsal used the normal archive only as a read-only source.
A separate restored copy served the container/browser tests, with exact original
IDs, epochs, retrievals and payload hashes. Backup size **53,248 bytes**, SHA-256
`644585974d4192d47797b17ff2fc20e660d723f779d2d9362780230d50989c0c`.
Full schema/table fingerprints, source parsing, both details, listing and two-source
comparison on the restored archive passed. This proves local SQLite recovery,
not off-machine retention or host-loss recovery.

Actual non-root container startup, read-only archive open refusal, safe boundary
errors and correlated log redaction passed. A 24-request cheap invalid-ID comparison
burst produced **17 HTTP 429** and **7 validation HTTP 422** responses; rate rejects
carried Retry-After and CSP. No scientific result or provider request was invented.

API restart briefly returned 502 while the process recovered, then 200; exact
source identities remained unchanged. Container replacement used a new container
ID and retained both genuine records. This single-host candidate has maintenance
interruptions; no zero-downtime or instance-loss guarantee is implied. Actual
`measured_only` container evaluation of genuine snapshot #1 returned **422
`eop_prediction_disallowed`**, with no fallback coordinates.

## Browser, performance and compatibility

Chromium **154.0.8037.57**, actual production static gateway/API, no mocked canvas
or API: all **nine prior saved-investigation flows passed**, including keyboard
save/clipboard read-back, refresh/restart, read-only recipients, exact comparison
and missing/invalid source cases. The bundled production run made **108 same-origin
GET requests**, zero external requests, page errors or CSP violations.

Four additional cases passed: mobile reduced-motion/keyboard timeline and camera,
actual WebGL context loss/restoration retaining numerical track data, simulated
absence of WebGL with a usable 2D fallback, and fresh mobile reconstruction under
150-ms latency / 200,000-byte/s download throttling. The throttled check completed
in **2.935 seconds** locally; this is one scenario, not a service-level guarantee.
Desktop 1440×1000, tablet 820×1180 and mobile 390×844 had no horizontal overflow.
The mobile screenshot and focus state were inspected. Software WebGL2 is not
physical GPU, device or screen-reader validation.

The initial built JS measured **287,164 decoded bytes / 104,450 actual gzip transfer
bytes** through Nginx. The existing lazy Three.js renderer is **558.60 kB minified**
and still emits Vite's >500-kB warning. Twenty bounded listing requests over the
restored two-record archive had median **2.471 ms**, p95 **2.987 ms**, maximum
**3.810 ms**, maximum decoded response **2,867 bytes** on this local setup.
These figures do not establish large-archive capacity, peak memory or public latency.
No broad rendering refactor was justified by this evidence.

Firefox was downloaded but its headless Playwright context/page setup did not
complete; owned attempts were terminated and the result is **BLOCKED**. WebKit
launch is **BLOCKED** by missing libgtk-4, libgraphene, libharfbuzz-icu, libmanette,
libhyphen and libGLESv2. No Firefox/Safari compatibility pass is claimed. Repeat on
a host with supported browser dependencies and real target devices/assistive technology.

## GitHub Actions evidence

Read-only API inspection confirmed published Phase 7 SHA
`ec1f9f832e5f2a488169d43083d83e24e1eac25e` passed both backend and frontend jobs:
[run 39293109185](https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39293109185).
This does not cover the new Phase 8 working tree. New workflow syntax and equivalent
local commands passed, but **Phase 8 remote CI is NOT RUN**. Branch-protection lookup
returned 403 “Resource not accessible by integration”; rulesets lookup returned 403
with a plan/visibility restriction. Administrator review is needed; protection is
not assumed enabled or disabled.

## Investigation of local failures

Initial build/audit tools tried caches in the read-only home; explicit temporary
cache/tool directories resolved them without changing credentials. Actual Compose
startup caught a split/unquoted tmpfs option list and non-root logging/source
traversal permissions; corrected configuration/images passed startup. The new
restored test directory also required UID traversal permission; only that new test
copy was adjusted, then the unhealthy test container was recreated. Ruff layout
issues were formatted. Firefox/WebKit limitations remain explicitly blocked.
No failed startup or compatibility attempt is represented as a successful check.

## Preservation and boundaries

Normal database SHA-256 before/after:
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Schema/table fingerprints match, including both snapshots, attempt/insertion/gate
rows, original payloads, constraints/indexes/triggers and integrity/foreign keys.
All pre-existing documentation and scientific/ingestion/storage/migration source,
fixtures and dependency locks retain their hashes. No normal archive initialization,
reset, migration or live collection occurred; explicit test fixture creation is
separate. Local test containers/networks were removed; the loopback endpoint closed.

HEAD/branch/remotes/staging remain unchanged. **No commit, push, deployment,
publication or remote workflow action was performed in Phase 8.** No cloud
configuration, DNS, billing, hosting provider or alert destination was fabricated.

## Acceptance criteria

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Existing architecture and current project state inspected | PASS | Clean main at published Phase 7 ec1f9f8; architecture, prior documentation and reproducible baseline inspected. |
| 2 | Production deployment architecture documented | PASS | Single-host static gateway/private API/read-only durable archive candidate, collector/resource/backup responsibilities and provider blockers documented. |
| 3 | Persistent-storage behaviour and limitations documented | PASS | Host bind mount decouples archive from images; local restart/replacement proven; host replacement/off-machine durability explicitly unverified. |
| 4 | Existing database, snapshots, and ingestion audit records preserved | PASS | Original file byte hash and full schema/table/row digests unchanged; runtime restored copy matches original content. |
| 5 | Migrations have a safe, tested execution strategy | PASS | Existing explicit writer-locked pre-backed-up transactional schema 1/2 upgrades and failure rollback tests pass; no new migration introduced. |
| 6 | Backup and restoration procedures are verified | PASS | Actual genuine two-record archive backed up/restored separately, full fingerprints/payload validation and restored APIs passed; off-machine recovery remains blocked. |
| 7 | Saved-investigation persistence guarantees are stated accurately | PASS | Local browser/origin storage, parameter links, no numerical-output retention or cloud synchronization; full tests and real production-route browser checks pass. |
| 8 | Authentication and authorization requirements are evaluated | PASS | No auth exists; anonymous public read-only browsing can retain local saves; operator host access and future managed identity/cloud persistence scoped separately. |
| 9 | Public API validation and resource limits are assessed and strengthened where necessary | PASS | Startup/host/URI/header/body controls, per-worker calculation admission, edge rate/connection limits and existing scientific bounds tested. |
| 10 | Secrets management and production configuration are documented | PASS | Placeholder-only config, private external environment file, allowlisted image context and safe required-setting checks; no cloud secrets fabricated. |
| 11 | CORS and other relevant security controls are reviewed | PASS | Same-origin architecture, absent permissive CORS, trusted hosts, CSP/headers, redacted logs/errors and read-only mounts tested. |
| 12 | Ingestion policies and deduplication remain intact | PASS | Existing mocked-ingestion/dedup/cooldown/retry/transaction regressions pass; ingestion source and ledger unchanged; no live provider call. |
| 13 | Scientific readiness and EOP restrictions are preserved | PASS | Existing science/readiness code unchanged; all reference audits pass and actual genuine-source strict EOP container call returns 422 with no coordinates. |
| 14 | Operational monitoring and incident procedures are documented | PASS | Minimal dependency probe, structured request logs and runbooks implemented; alert routes, delivery and on-call ownership explicitly remain unconfigured. |
| 15 | GitHub Actions checks are inspected for the exact relevant commit where access permits | PASS | Remote Phase 7 run 39293109185 and both successful jobs cover exact ec1f9f832e5f2a488169d43083d83e24e1eac25e; local Phase 8 has no remote run. |
| 16 | Missing CI or branch-protection evidence is explicitly documented | PASS | 403 protection/ruleset responses preserved; new local workflow unexecuted remotely; admin verification steps documented. |
| 17 | Production build and applicable regression suites pass | PASS | 609 backend, 275 frontend, 40/6/32 numerical audits and 28+28 geodesy, lint/format/tsc/build, both local image builds and CI fixture smoke pass. |
| 18 | Performance and accessibility checks are performed where possible | PASS | Actual Chromium production UI at three widths, keyboard, reduced motion, WebGL loss/recovery/unavailable simulation, CSP and throttled-mobile loading checked; representative local listing timings only. |
| 19 | Environment-dependent and physical-device tests are accurately classified | PASS | Firefox runner could not complete; WebKit missing runtime libraries; physical GPU/device/Safari/screen reader and target-host tests not claimed. |
| 20 | Deployment and rollback instructions are complete | BLOCKED | Provider-neutral tested artifact/runbook exists, but provider-specific TLS/DNS/ingress trust, durable attachment/off-machine restore and rollout/recovery instructions cannot be finalized or verified without selected infrastructure and owners. |
| 21 | Scientific limitations are accurately disclosed | PASS | Observation validation BLOCKED, uncertainty unquantified; no universal accuracy/maneuver claim; approximately 1.317 cm residual explanation and geodetic correction preserved. |
| 22 | No existing user data are lost or silently rewritten | PASS | Normal archive bytes/all tables and every pre-existing docs file match baseline; browser-local storage implementation unchanged; tests use owned separate profiles/archives. |
| 23 | No unverified deployment or production capability is claimed | PASS | Only local containers and restored copies tested; no provider, durable production, TLS, alert delivery or public deployment claim. |
| 24 | A complete readiness report and structured evidence artifact are produced | PASS | This report, JSON, deployment runbook and focused security review contain actual outcomes and explicit NO-GO decision. |

## Remaining production blockers

- **HOSTING — BLOCKED:** No provider/account/region/billing authority, approved production domain, HTTPS/renewal/HSTS ingress or firewall has been selected/provisioned/validated.
- **DURABILITY — BLOCKED:** Local SQLite recovery and same-host restart/replacement passed; provider disk reattachment, host loss, encrypted off-machine backup retrieval, retention and RPO/RTO have not been established.
- **OPERATIONS — BLOCKED:** No monitoring/log delivery service, alert recipients/on-call owner, backup schedule or approved collector scheduler is configured and tested.
- **RELEASE_GATES — BLOCKED:** Local Phase 8 changes have no published exact SHA or remote CI result. Branch protection/rulesets cannot be verified with available integration permissions. No publication was authorized.
- **TRAFFIC — BLOCKED:** Trusted real-IP CIDRs and representative traffic/shared-NAT/capacity budgets depend on selected ingress and hosting; local two-record timings cannot establish production throughput.
- **COMPATIBILITY — BLOCKED:** Firefox context setup did not complete; WebKit cannot launch without listed libraries; real Safari/devices/GPU and screen-reader validation are not complete.
- **SCIENTIFIC_ACCURACY — BLOCKED:** Independent observation validation remains blocked; uncertainty is unquantified. Numerical regression success supports only its stated reference scope; stronger accuracy claims remain prohibited.

## Changed files

- `.dockerignore`
- `.env.example`
- `.github/workflows/ci.yml`
- `Dockerfile`
- `README.md`
- `backend/orbitiq/api/boundary.py`
- `backend/orbitiq/api/operational.py`
- `backend/orbitiq/main.py`
- `backend/orbitiq/runtime.py`
- `backend/tests/test_production.py`
- `deploy/api-proxy.conf`
- `deploy/compose.yaml`
- `deploy/logging.json`
- `deploy/nginx.conf`
- `deploy/production.env.example`
- `deploy/security-headers.conf`
- `docs/phase-8-integration-results.json`
- `docs/phase-8-readiness-report.md`
- `docs/production-deployment-runbook.md`
- `docs/production-security-review.md`
- `scripts/verify_release_containers.py`

Complete the provider-specific operational gates and verify the exact authorized
release in staging before reconsidering public deployment. Keep observation-based
validation **BLOCKED**, prediction uncertainty unquantified, and the original
approximately 1.317 cm residual explanation and Phase 6.1.1 precision correction
visible and unchanged. No universal prediction accuracy or physical anomaly claim
follows from these local readiness checks.
