# Engineering milestone E3 verification report

This is local-first engineering evidence, not a scientific qualification or a
production launch decision. Execution began from clean branch
`engineering-e2-accessibility-performance`, commit
`d8aa10fdbb9f4be13ff8c5f096b93f0bb17e0af4`, verified locally and against the
configured GitHub remote. E3 uses `engineering-e3-reliability-recovery`.

## Review and demonstrated defects

The existing provider adapter, durable collection gate/ledger, snapshot storage,
readiness, migrations, recovery manifests, development instructions and CI were
reviewed before changes. The starting provider/collection/readiness selection
passed **134 tests**. Five new probes then failed against the original code:
initialization and copy exposed the final destination during validation; handled
KeyboardInterrupt left that target behind; operational readiness accepted a
missing collection-gate row.

E3 fixes those defects through validated sibling staging and atomic no-overwrite
publication, cleanup on handled interruptions, and shared gate validation in
maintenance/production startup and operational readiness. A bounded backup
progress callback prevents indefinite SQLite backup retries under contention or
repeated restart. No schema migration or dependency change was required.

A later CLI probe also reproduced an uncaught TypeError for a missing gate.
The collector now returns a safe storage error without making a request or
repairing the gate; the failure-audit path uses the same checked lookup.

The public changes are the database helper, operational readiness, collector gate
lookup, two E3 test
modules, isolated-installation verifier, additions to the existing backend CI
job, README/runbook updates, this report and the
[E3 reliability guide](engineering-e3-reliability-recovery.md). No prior phase or
E1/E2 reports are edited.

## Provider reliability and ingestion recovery

The existing conservative CelesTrak policy is retained: one request per admitted
invocation, a two-hour global per-archive gate, bounded deferred network retries,
HTTP error review, permanent-error cooldown, and extending `Retry-After` handling.
No new live acquisitions, provider integration, scheduler, queue or polling were
introduced. Tests use deterministic HTTPX transports and public reference fixtures.

New probes verify interrupted streams, restart after failure, exact retry
idempotency, whole-response rejection of malformed/empty/multi-record/partially
invalid responses, older-epoch history preservation, and interruption after
snapshot insertion before commit. The latter rolls back snapshot/success state,
retains a `running` admission, reconciles it after its lease without resetting
cooldown, and safely accepts a subsequent permitted retry.

Byte-identical data retains the first snapshot and separate retrieval history.
The existing identity is catalog ID + exact source URL + raw-response digest;
byte differences are not proof of distinct orbital element sets. A new acquisition
can remain stale: freshness is based on epoch, not last HTTP success. Failure does
not erase the last accepted history. Existing tests additionally cover timeout,
proxy/network/TLS failures, 429/5xx/permanent 4xx, retry budgets, concurrency,
failure-audit errors and transactional migration rollback.

## Storage and restoration

All write/corruption/interruption tests use temporary archives. New tests cover
committed, uncheckpointed WAL preservation through backup and restoration;
hidden destination until validation, KeyboardInterrupt cleanup, racing creators,
broken-symlink refusal, backup progress timeout, actual SQLite exclusive-lock
contention, process termination before init/restore publication, restart, and
nonzero CLI failure for missing/corrupt/incomplete backup input. Existing recovery
checks compare full schema/table/row digests, exact payloads, audit history and
restored APIs, with no restore applied to the source.

SQLite hard-link support is required for atomic publication. Uncatchable process
death can leave private staging artifacts; cleanup is an explicit scoped operator
action after workers stop. The 30-second progress budget covers backup callbacks,
not every validation scan/filesystem call. File fsync and atomic visibility do not
prove resilience to host power loss or off-machine disaster. See the
[updated runbook](backup-restore-runbook.md).

The initial integrity check matched all **72 private files** to the trusted E2
baseline. The real database remained schema 3 with two existing snapshots. Its
SHA256 was `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
The raw database digest was taken only while SQLite confirmed DELETE journal mode
and a shared read transaction prevented commits. A consistent logical table/schema
fingerprint was also captured. No incomplete process-list inspection was used as
proof of quiescence. The post-test shared-lock digest, logical fingerprint and
all 72 private inputs matched the initial and trusted E2 baselines.
No private data, provider attachments, restricted ESA products, credentials,
local database or generated evidence bundle belongs in the commit.

## Fresh checkout and regression verification

The verifier exports only the reviewed Git index into a new isolated checkout,
records the source tree identity, installs both locked dependency sets into fresh
directories, builds, configures from the tracked example, starts backend/Vite,
checks missing-database behavior, explicit initialization/no-op migration, proxy
communication, synthetic catalog/detail/position flows, provider failure, restart,
deduplication and the existing isolated recovery rehearsal. It retains only
fixture evidence and stops the processes it started. This runs in the existing
CI backend job; no redundant workflow was created.

Local verification is complete. Publication and exact-commit remote CI remain
pending at this pre-publication checkpoint:

| Check                                                              | Actual result                                                                                              |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| Starting provider/collection/readiness baseline                    | 134 passed                                                                                                 |
| Original-defect probes before fixes                                | 5 initial failures + 1 later CLI failure, all expected                                                     |
| Final full backend regression                                      | 1,234 passed; two existing warnings                                                                        |
| New E3 failure/recovery cases included above                       | 26 passed                                                                                                  |
| Explicit migration/backup/restore selection                        | 5 passed, 57 deselected                                                                                    |
| Frontend unit tests                                                | 345 passed, 25 files                                                                                       |
| Frontend lint/format/TypeScript/build                              | Passed; existing large-renderer warning retained                                                           |
| Ruff, Markdown parsing/links/format/whitespace and workflow syntax | Passed; 63 local Markdown targets/anchors verified                                                         |
| Published SGP4 / terrestrial / expanded audits                     | 40 / 6 / 32 passed; zero failures                                                                          |
| Geodetic audit                                                     | 28 component and 28 algebraic round-trip checks passed                                                     |
| Release images and isolated empty-archive API smoke                | Built; four HTTP checks passed, fixture unchanged                                                          |
| E1 browser/PDF and E2 accessibility                                | 77 browser flows, 5 failure cases, 2 expected-failure probes, 7 PDFs; 62 E2 checks and 18 axe scans passed |
| Isolated fresh installation                                        | Passed; actual backend/Vite proxy, failure, restart and recovery                                           |
| Exact-commit remote CI                                             | Pending publication                                                                                        |

The PDF maximum-track check verified all 361 rows. Browser fixture fingerprints
were unchanged. Axe reported zero violations in its 18 scans; incomplete contrast
items remain explicit, so this is not a full accessibility certification. Firefox
covered the WebGL fallback; Chromium and WebKit had native WebGL2 evidence.
Physical-device and assistive-technology sessions were not performed.

Backend warnings are the existing Starlette/httpx TestClient deprecation and an
intentional duplicate ZIP-member warning in a rejection test. Frontend Vitest
retains its existing test-environment advisory. No assertions or functionality
were disabled to make tests pass. Routine checks require no live provider access.

The installation used Python 3.12.14, uv 0.12.23, Node 24.19.0 and npm 11.9.0.
The final isolated source tree was
`dc4664451d7e5abfef6df89c8b1cb6205a36cb17`. It includes the committed-WAL
case and safe collector-gate correction. The complete exported source matched
the reviewed index byte for byte, with fresh dependency installations. The full
backend run was repeated after that correction: 1,234 passed. Subsequent report
updates are documentation only.
The fixture recovery compared every table/schema digest and retained one snapshot,
one insertion timestamp, three audit attempts and the singleton gate. All three
restored API checks returned 200; the one-record comparison was explicitly a
self-check. Fixture processes stopped normally, and only fixture evidence remains
under `/tmp/orbitiq-e3`. Native Windows and macOS execution were not tested.

The local E1/E2 run started before the final collector error-message correction.
Its API/readiness/database and frontend code match the final implementation;
collection is not invoked by browser reads. Final-commit remote CI must rebuild
the image and rerun the complete browser/PDF/E2 set before remote success is claimed.
The final local API image was separately rebuilt and passed release startup/ready
checks; the final collector passed the full backend and isolated install runs.

## Publication and remaining gates

The dedicated branch publication is authorized after final review and applicable
checks. The reviewed file boundary is exactly:

- `.github/workflows/ci.yml`
- `README.md`
- `backend/orbitiq/api/operational.py`
- `backend/orbitiq/database.py`
- `backend/orbitiq/ingestion/collection.py`
- `backend/tests/test_e3_ingestion.py`
- `backend/tests/test_e3_recovery.py`
- `docs/backup-restore-runbook.md`
- `docs/engineering-e3-reliability-recovery.md`
- `docs/engineering-e3-report.md`
- `scripts/verify_fresh_checkout.py`

No commit or push has occurred at this report checkpoint. Exact SHA,
pushed file list, remote CI and final integrity evidence must be recorded after
those operations actually occur.

Phase 11.3.1 remains **PARTIAL**. Scientific evaluation remains **BLOCKED**.
ESA time clarification, KIN-quality qualification and frame alignment remain
unresolved. Historical availability and creation timestamps remain unknown;
complete fitting lineage and statistical independence are not established.
No genuine Swarm-A propagation, qualified residuals or independent-accuracy
claims are produced by E3.

Production hosting/public HTTPS, independently stored backups with demonstrated
off-machine recovery, actual monitoring/alert delivery and repository protection
remain open under the [Phase 8 gates](phase-8-closure-checklist.md).
The default branch still reports `protected: false`. GitHub ruleset inspection
returned HTTP 403 with a private-repository plan restriction. Required-check
enforcement is not verified; no protection settings were changed. No merge,
production deployment, DNS or infrastructure/protection change occurred.
