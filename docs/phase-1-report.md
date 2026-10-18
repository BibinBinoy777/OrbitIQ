# Phase 1 implementation and connectivity resolution report

## Outcome

**Phase 1 acceptance criteria PASS.** A real request to the unchanged CelesTrak
GP endpoint succeeded, one real ISS record was validated and persisted, and exact
dataset replay added zero rows. All existing 74 backend tests remain in place;
the current suite passes 103 backend tests plus 6 frontend tests. No Phase 2 work
was performed. No commit, push, application deployment or publication occurred.

## Failure classification and supporting evidence

The historical failure is classified as **confirmed outbound proxy connection
rejection**, based on the recorded `httpx.ProxyError: 403 Forbidden` while
establishing the HTTPS tunnel. That is distinct from an HTTP 403 returned after a
successful tunnel/TLS handshake. The historical proxy response headers/body and
provider policy decision were not retained; the exact internal denial reason is
therefore **unresolved**, not assumed to be a hostname, User-Agent, destination
ban, DNS, TLS or application bug. Earlier reports that implied a specific stale
policy cause were hypotheses, not established root causes.

On this investigation the runtime reports the existing `celestrak.org` allowlist
rule **enforced**, with current observations and configuration revision 2. Its
startup policy snapshot now also lists the domain. The same source URL, query
parameters, headers and inherited proxy/CA settings worked without alteration:

| Request-path stage | Actual evidence |
| --- | --- |
| OrbitIQ source configuration | HTTPS `/NORAD/elements/gp.php`, CATNR=25544, FORMAT=JSON |
| HTTPX route | Inherited HTTPS proxy enabled; no proxy bypass |
| Proxy tunnel | CONNECT response **HTTP 200**, safe Server header `envoy` |
| TLS | `proxy.start_tls.started` followed by `proxy.start_tls.complete`; verification enabled |
| Upstream HTTPS response | **HTTP 200**, Content-Type `application/json; charset=UTF-8`, Content-Length 419, Server `envoy` |
| Body | 419 actual bytes, parseable JSON, one orbital element record |

The Server header identifies an intermediary; it does not independently identify
CelesTrak's origin server. The request was made to the configured CelesTrak HTTPS
endpoint using the managed trust path. No claim of independently measured orbit
accuracy follows from this request. Local destination DNS lookup returned
`gaierror`, but proxied HTTPS succeeded, so local destination DNS was not blocking
this route. No DNS, TLS, source hostname, User-Agent or routing workaround was
justified or applied. Credentials, cookies, authorization headers, proxy URL
userinfo and internal addresses were omitted from diagnostics. There is no old
403 body to inspect retroactively; no body text was invented. The successful raw
JSON body is retained in the snapshot.

**Resolution:** the configured outbound route is now operational. No additional
network rules or credentials were added, and no access control or verification
was bypassed. A specific provider-internal explanation of the old rejection would
require provider logs; it is not required to claim the directly verified current
successful request.

## Real live ingestion evidence

Live retrieval was verified at **2026-10-18 22:44:39 IST**.
Scientific timestamps below retain explicit UTC as required by the data contract.
Exactly one external data request was made in this investigation; replay did not
make another HTTP request.

| Field | Actual result |
| --- | --- |
| Endpoint | `https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=JSON` |
| HTTP status | 200 |
| Received / validated / newly persisted records | **1 / 1 / 1** |
| Satellite | ISS (ZARYA), NORAD catalog 25544 |
| Snapshot ID | 1 |
| Orbital epoch (UTC) | `2026-10-18T11:12:47.040768+00:00` |
| Retrieval time (UTC) | `2026-10-18T17:14:39.983172+00:00` |
| SHA-256 of exact upstream body | `556827b7dc6cbccd0cbc3e40a9e0a0ed2205ad2d2006a8649e16ee8c0c143d4b` |
| Validation | `structural_and_epoch_propagation_passed` |
| Stored convention | Earth-centered TEME, UTC, SGP4; explicit element units |
| Replay snapshot ID / new rows | **1 / 0** |
| Final database snapshot count | 1 |

The diagnostic HTTPX request first captured exact live response bytes and their
real retrieval time. After offline changes passed, those same captured bytes
were passed through `DownloadedDataset`, `parse_response` and `process_dataset`.
The persisted bytes, source URL, timestamp and hash match that live capture.
This was genuine live-source ingestion followed by an **offline replay of the
same real dataset**, not a mocked HTTP response presented as live connectivity.
The production CLI's new `--verify-replay` mode is tested offline to use one
request and two processing passes; no extra CLI retrieval was made merely to
repeat the already successful external request.

The full captured response and safe trace evidence are retained locally at:
`/workspace/OrbitIQ/data/phase1-live-evidence-20261018T172038280954Z.json`. This file is ignored by Git along with the application database.

## Existing database safety and recovery

Before any modification the existing configured database was opened read-only:
schema 2, zero snapshots, integrity valid. Its original SHA-256 was
`d896988b134e9fffbb875d86b6cfa23f88a5eb0aeb490d81a20e674fbb8d7f88`.
No initialization, reset, deletion, recreation or migration of that database was
performed. Its fingerprint remained unchanged throughout offline code/tests.
A new pre-ingestion backup preserved that original state before the one intended
snapshot insertion. No existing row was overwritten.

- Current database: `/workspace/OrbitIQ/data/orbitiq.sqlite3`.
- New pre-ingestion backup: `/workspace/OrbitIQ/backups/pre-live-ingestion-20261018T171942735203Z.sqlite3`.
- New populated backup: `/workspace/OrbitIQ/backups/phase1-real-snapshot-20261018T172038280954Z.sqlite3`.
- Recovery validation used a newly created **temporary destination**. It did not
  restore over or modify the existing database. The restored snapshot, raw bytes,
  original/normalized records, units, timestamps and hash equalled the source.
- A deliberately mocked HTTP 403 against that temporary recovery copy left its
  file hash and real stored record unchanged. This failure check was **offline**.
- Fresh API processes returned HTTP 200 for health, history, detail and calculated
  position through Vite, first using the original database and then after restart
  against the recovery copy. Calculated vectors matched across recovery.
- The original database's file hash and snapshot stayed unchanged during all
  recovery/API checks. Final SQLite `integrity_check`: **ok**; schema **2**;
  `verify_archive`: **1** valid snapshot. No schema migration was needed.

These are local persistence/recovery checks. Managed PostgreSQL, independent
production backup storage and actual public-deployment recovery remain future
launch gates; a cloud-task filesystem is not production durable storage.

## Smallest justified code changes

- Source URL is configurable using optional `ORBITIQ_CELESTRAK_URL`; the default
  remains unchanged. Only the official GP path on `celestrak.org` or
  `www.celestrak.org`, HTTPS port 443, without credentials/query/fragment is
  accepted. No arbitrary fetch URL or new dependency was introduced.
- Extracted bounded download and dataset processing so exact captured bytes can
  be validated/replayed without repeating network requests. Existing parsing,
  epoch normalization, provenance and scientific engine were retained.
- HTTP errors now distinguish proxy, upstream HTTP status, timeout, identifiable
  TLS causes and other network failures without exposing bodies or credentials.
  An upstream HTTP status is not automatically attributed to the origin server.
- Idempotency uses catalog ID + exact source URL + raw-response SHA-256 under a
  `BEGIN IMMEDIATE` transaction. Concurrent application writers cannot race the
  lookup/insert. An identical dataset reuses its first snapshot and timestamp;
  changed bytes append immutable history. Existing duplicates are not deleted.
- `--verify-replay` confirms the same snapshot ID using one download. Reporting
  says the snapshot is ready rather than claiming a duplicate was newly saved.
- No migrations, lockfile changes, dependency additions, scientific-engine
  changes or frontend source changes were required. Existing tests and
  assertions were not removed or weakened.

## Current executed checks

| Check | Result |
| --- | --- |
| Backend full pytest suite | **103 passed**, baseline 74 retained + 29 new cases |
| Published SGP4 references within full suite | **24 passed**, unchanged fixed-vector assertions |
| New ingestion reliability suite | **29 passed**, offline fixtures/mocked HTTP only |
| Missing required fields, empty/malformed responses, epochs | PASS in offline suites |
| HTTP 403 / 429 / 5xx, connection failures, connect/read timeout, TLS classification | PASS in offline suites |
| Exact duplicate and concurrent duplicate processing | PASS; one snapshot |
| Post-insert transaction failure | PASS; rollback preserves existing history |
| Timestamp/source/epoch preservation | PASS, offline and actual persisted live record |
| Frontend tests | **6 passed**, baseline retained |
| Ruff lint and formatting | PASS |
| Frontend ESLint and Prettier checks | PASS |
| TypeScript and Vite production build | PASS |
| Genuine external request | **HTTP 200**, one record received/validated/persisted |
| Actual HTTP API through Vite, original and recovery copy | PASS |
| Original SQLite integrity and archive verification | **ok**, one snapshot |
| Current clean source: locked sync, backend tests, lint/format | PASS; excludes real data, caches and local secret files |
| GitHub CI, public deployment, real-browser accessibility audit | **NOT RUN**; no commit/push/deployment authorized |

The backend still emits the known Starlette TestClient deprecation warning; it
was not suppressed. New coverage is deterministic and makes no external requests.
Offline tests use temporary databases and explicitly labelled verification
fixtures. Fixture success is separate from the genuine live request above.

## Files inspected and modified

Inspected repository status/structure, Phase 0 and prior Phase 1 reports,
README/configuration, HTTP client/proxy metadata, ingestion/storage modules,
schema migrations 001/002, orbital validation/engine, API routes, dependency
manifests/lockfiles, and existing tests. Secret values and credential files were
not dumped.

Modified:

- `backend/orbitiq/ingestion/celestrak.py`: configuration, download/processing
  separation, categorized safe errors and verified replay mode.
- `backend/orbitiq/storage.py`: serialized transactional idempotency.
- `.env.example`: optional source URL documentation.
- `README.md`, `docs/phase-1.md`, `docs/phase-1-report.md`: current commands,
  diagnostics, data contract and actual evidence.

Added: `backend/tests/test_ingestion_reliability.py` (29 offline cases).
Existing `backend/tests/test_phase1.py`, foundation tests, migrations, dependency
manifests and lockfiles were preserved. Live database, backups and evidence are
ignored local outputs and contain no added credentials.

## Acceptance criteria

| Criterion | Status | Evidence |
| --- | --- | --- |
| Connectivity failure identified/addressed | **PASS** | Historical outbound proxy rejection classified; current enforced route returns CONNECT/TLS/HTTP success; provider-internal old reason remains unknown |
| Real configured-source request succeeds | **PASS** | Actual HTTP 200, exact raw response retained |
| Returned records parsed and validated | **PASS** | 1 real ISS record accepted without alteration |
| Provenance and orbital epochs preserved | **PASS** | Exact body/hash, original source/retrieval time, UTC epoch, units and validation retained |
| Safe idempotent database ingestion | **PASS** | Replay reused snapshot 1 and inserted 0 rows; concurrent replay tested |
| Failure handling and rollback | **PASS** | Mocked transport/status failures and injected post-insert rollback verified |
| Existing regressions | **PASS** | Original 74 backend and 6 frontend tests pass |
| New ingestion tests | **PASS** | 29 additional offline cases pass |
| Documentation reflects verified implementation | **PASS** | Current guide, report, config example and README updated |
| Existing database remains intact | **PASS** | Preserved schema/database; one deliberate append, no overwrites; final integrity ok |

No Phase 1 criterion remains FAIL or BLOCKED. The historical provider-internal
reason is not known; that limitation is explicitly separate from the now verified
operational connectivity and ingestion outcome.

## Remaining limitations and exact next action

No further external action is required to accept Phase 1. Preserve the ignored
local database and its backups; do not run init or restore over it. Start normal
development using the configured database and documented commands. A new live
retrieval should be intentional and honor source limits; use downloaded-byte
replay to test idempotency without another request. Do not proceed to Phase 2,
commit, push, deploy or publish without authorization.

Positions remain **calculated WGS72 SGP4 TEME vectors**, not direct observations
or Earth-fixed coordinates. The independent published reference tests measure
implementation agreement, not satellite prediction accuracy. No Astropy frame
transformation, uncertainty model, anomaly/collision claim or public-launch
readiness is implied. Exact-byte/source deduplication preserves the first
retrieval timestamp; later identical checks are not a full retrieval-event log.

Reusable `start_skill` guidance was saved as a draft, preserving existing startup
requirements and adding source/replay/error guidance. No network rule, secret or
install-script change was needed. Saving did not apply or publish it. To activate
that optional instruction update, review/save it in environment settings and
publish the **environment configuration** when authorized; no application or
environment publication was performed here. No fresh cloud snapshot restoration
is claimed.
