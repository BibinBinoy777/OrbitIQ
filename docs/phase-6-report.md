# Phase 6: reliable data collection and historical validation

Implementation and verification: **19 October 2026 (IST)**. Scientific/audit
instants below are explicitly UTC. Changes are local and uncommitted.

## Outcome and acceptance scope

**All 35 requested acceptance criteria PASS within the verified local scope.**
The former genuine historical-pair gap is closed: the preserved original ISS
snapshot and one newly acquired, distinct CelesTrak payload were retrieved and
compared through actual APIs in TEME and ITRS at the same explicit epoch.

The exact published Phase 5 GitHub Actions run and job logs were verified green.
A supplemental branch-protection configuration lookup is **BLOCKED**: GitHub
returned HTTP 403, `Resource not accessible by integration`. Workflow job results
are accessible and verified; branch-protection enforcement is not established.
Phase 6 changes, including new workflow steps, have **not run remotely**. No new
commit, push, deployment, publication, remote modification, workflow dispatch or
rerun was performed. No scheduler was enabled.

See [structured evidence](phase-6-integration-results.json),
[ingestion operations](ingestion-operations.md), and
[backup/recovery runbook](backup-restore-runbook.md).

## Baseline and inspection

- Repository `BibinBinoy777/OrbitIQ`, branch `main`, clean working tree.
- Exact local and published Phase 5 SHA:
  `6c60655402b70306f654c3f9b30f79ff6c7c3e45`.
- Baseline executed suites: **398 backend / 172 frontend tests passed**.
- SQLite application schema **2**, **one genuine ISS snapshot**, ID 1, NORAD
  25544. `PRAGMA integrity_check` was `ok`.
- Original DB file SHA-256 before any mutation:
  `c389d0f1d663957be70a32f846f8e968e70a4f46c37343a5b80ceca5954e5f59`.
- Existing snapshot identity: catalog ID + exact source URL + SHA-256 of raw
  response bytes, serialized writer lookup/insert. Retrieval timestamp is not
  identity. Exact replay reuses the original row and first retrieval. Source
  formatting changes still count as distinct raw datasets under this contract.
- Existing collector: fixed official one-object GP JSON, no redirects/compression,
  64 KiB ceiling, 5-second connect/15-second HTTP operation timeouts, elapsed
  chunk budget, strict parsing/orbital validation and epoch propagation. No ledger,
  persisted request gate or independently recorded insertion time existed.
- Existing migration framework: numbered SQL, writer lock, consistent old-version
  backup, transactional DDL/version update; exclusive no-overwrite init/restore.
- Existing readiness: conservative latest-100 metadata assessment, separate EOP/
  leap policies, no collection side effects. History, direct access and comparison
  were already read-only. Schema stores one satellite per snapshot, not batches.
- Existing CI: backend locked uv install/tests/Ruff; frontend locked npm ci/tests/
  ESLint/Prettier/TypeScript/Vite. Published references are included in the backend
  test suite; standalone numerical audit scripts were not separate CI steps.

Read Phase 1–5 reports and structured evidence, readiness/EOP reports/guides;
inspected source, parser, source configuration, persistence/transactions, migrations,
pagination, comparisons, freshness, error handling, backup and CI. The repository
matched the reported baseline. Eighteen earlier report/plan/evidence artifacts
remain byte-identical. Current operational guides were updated deliberately.

## Implementation

### Controlled collection and audit

`ingestion/collection.py` extends the existing CelesTrak fetch/parser/processing/
storage pipeline. Both the previous CLI and `ingest()` delegate to it. Explicit
`collection collect <catalog>` returns concise inserted/deduplicated JSON and
nonzero safe failures. `collection history` is operator-only, read-only, paginated
and bounded (20 default, 100 maximum plus lookahead). No administrative HTTP
endpoint, new service, broker, cache, dependency or schedule was introduced.

Official GP documentation and usage policy were actually retrieved successfully.
The policy requires stopping on every non-200 response. The implementation:

- Makes at most one HTTP request per invocation, no immediate retries.
- Serializes admission with a database-wide durable two-hour gate, shared across
  catalog IDs and official hostname aliases within the authoritative archive.
- Supports only deferred operator retries for network/proxy/timeouts: 2h/4h/8h
  exponential delays plus 0..300s jitter, maximum three consecutive failures.
- Stops eligibility for review after every non-200 HTTP response, TLS, parsing,
  validation or persistence error; 401/403/404 have at least 24h cooldown.
- Honors delta/date `Retry-After` by extending the gate. Explicit operator resume
  cannot bypass cooldown or erase old attempts/failure history.
- Preserves existing time/size/content/provenance validation, TLS trust and raw
  identity/deduplication. No permissive parser or satellite fixture was added to
  the real archive.

A short reservation transaction commits a running audit/gate before HTTP I/O.
The writer lock is released during acquisition/validation. Successful snapshot
insert/replay, separate insertion time, completed success audit and gate release
commit atomically. Snapshot or success-ledger failure rolls back both. One separate
best-effort failure transaction records the categorized stage when storage remains
available. If that also fails, safe operational logging reports the limitation
without recursive retries. A 120-second stranded-attempt lease permits explicit
reconciliation as `interrupted`, retaining unknown outcomes and cooldown.

Start, attempt database insertion, response retrieval, successful validation,
snapshot insertion and completion remain separate. Source epoch and propagation
execution/evaluation retain their existing scientific meanings. Finished attempts
and insertion timestamps are immutable; no audit retention deletion is implemented.
A running/interrupted attempt's unconfirmed acquisition count is not proof that a
provider request did not occur. Full transaction and crash limitations are in the
operator runbook.

### Migration and monitoring

Additive migration `003_ingestion.sql` creates the audit, separate snapshot
insertion records, request gate, partial stage indexes, payload-identity lookup
index and immutability triggers. It never updates/backfills existing snapshot rows.
Fresh explicit initialization applies migrations 001–003; existing schemas 1/2
need explicit pre-backed-up migration. Schema 2 remains browsable but cannot use
controlled collection until upgraded. There is no destructive audit down migration;
failed migrations roll back, and retained backups can be restored separately.

The existing readiness API/dashboard gains `components.ingestion`: actual last
attempt, acquisition, validation and insertion, latest outcome, consecutive
failures, safe category, cooldown/review status and epoch-based freshness. Indexed
single-row queries have explicit SQLite read budgets. Empty history, source
failure, missing/future metadata, successful deduplication and stale elements
remain distinct. Legacy history is never invented. No readiness request probes or
fetches the provider. Snapshot detail/state/history and existing source panels now
show insertion time when recorded; legacy sources stay unknown. This is a metadata
extension to the existing UI, not a redesign.

## Real database preservation and collection

Migration executed at `2026-10-19T07:58:05.835720+00:00`, after creating the
consistent schema-2 backup:

`backups/phase-6-pre-migration-20261019T075805Z.sqlite3`

- Size: **16,384 bytes**.
- Backup SHA-256:
  `3b3d25e49fbfff35165c5cadb7c9c694f8f4e47c095462c553877731fc446550`.
- Snapshot count immediately before/after migration: **1 / 1**.
- Original snapshot row digest before/after migration and after collection:
  `84da784e9e46989fa0a2deb6c10eb0b70c3e968ec5433b4133d9944e53fb84fc`.
- All original columns, raw payload bytes, identity and provenance unchanged.
- Schema now **3**; integrity `ok`, zero foreign-key violations.

The row digest uses sorted-key JSON of every original snapshot column with BLOB
bytes represented as hex. Whole-file byte identity is **not claimed**: migration
changes schema, and collection appends legitimate data.

Exactly **one** actual provider acquisition was invoked during this phase:

```sh
PYTHONPATH=backend uv run --locked python -m orbitiq.ingestion.collection collect 25544 --verify-replay
```

Exit **0**, HTTP **200**, parsed **1**, validation **passed**, committed new
snapshot **2**, audit attempt **1**. Response received, parse, validation, commit,
insertion and replay outcomes are separately captured in the evidence JSON.

| Fact | Preserved genuine snapshot 1 | New genuine snapshot 2 |
| --- | --- | --- |
| NORAD | 25544 | 25544 |
| Source epoch UTC | 2026-10-18T11:12:47.040768+00:00 | 2026-10-18T18:57:18.892800+00:00 |
| Independent retrieval UTC | 2026-10-18T17:14:39.983172+00:00 | 2026-10-19T07:58:23.407349+00:00 |
| Separate snapshot insertion UTC | Unknown legacy value | 2026-10-19T07:58:23.415+00:00 |
| Payload SHA-256 | `556827b7dc6cbccd0cbc3e40a9e0a0ed2205ad2d2006a8649e16ee8c0c143d4b` | `8105d7f3aa846b3c0452a3dd9cbee4a6fe5348ea6d081afbdfc98b86e49fd7cd` |

The source for both is the official
`https://celestrak.org/NORAD/elements/gp.php?CATNR=25544&FORMAT=JSON`.
Epochs and validated orbital elements differ, beyond raw formatting. The pair is
**one preserved earlier acquisition plus one new Phase 6 acquisition**; there was
no need to wait/poll for another download or fabricate a second Phase 6 attempt.

Audit 1: start `07:58:22.439562`, SQLite attempt insertion `07:58:22.440`, response
`07:58:23.407349`, validation `07:58:23.413162`, snapshot insertion `07:58:23.415`,
completion `07:58:23.416100`, all on **2026-10-19 UTC**. It records request count 1,
parsed count 1, linked snapshot 2, new insertion true, no failure category. The
original Phase 1 acquisition has no invented retrospective audit row.

Exact-byte replay reused snapshot 2 inside the committed transaction, without a
second HTTP request. No real deduplicated *independent acquisition* is claimed;
that audit outcome is verified in isolated tests. An immediate subsequent local
collection admission was refused by cooldown with no new audit/data rows.
Earliest next permitted request: **19 October 2026, 15:28:23 IST**
(`2026-10-19T09:58:23.407349+00:00`). Consult current state before a later run.

## Genuine comparison evidence

Actual local HTTP calls to history, snapshot 1/2 detail, readiness and comparisons
returned 200. The comparison used **`2026-10-18T18:57:18.892800+00:00`**, the new
source's element epoch, explicitly for both model states.

- Matching: validated NORAD ID 25544; counts shared **1**, added **0**, removed
  **0**, incompatible **0**. Added/removed nonzero edge cases remain isolated
  deterministic tests, not invented real archive changes.
- Element differences: complete, canonical units, signed/wrapped conventions.
- TEME and ITRS states: **complete**, km and km/s, same evaluation time, explicit
  snapshot IDs, hashes, source epochs, retrievals, execution times and assumptions.
- ITRS uses the existing locally installed predicted EOP under
  `measured_or_predicted`, package `0.2026.10.12.1.3.27`; automatic download and
  degraded-result fallback are false. No scientific policy was bypassed.
- Repeating both API comparisons reproduced exactly the element differences,
  state vectors/differences, frame, units, source linkage and resource hashes.
  Calculation execution, freshness evaluation and EOP-table age are wall-clock
  metadata and correctly differ across requests.
- The ITRS position-vector disagreement was **0.27227977490332145 km** at that
  common time. This compares two model fits for **the same satellite**; it is not
  observed separation, accuracy validation, a maneuver, anomaly or collision claim.

No reference fixture or edited provider payload was involved in this pair.

## Backup and separate recovery evidence

The repeatable `orbitiq.maintenance.recovery` command reuses SQLite consistent
backup, restores into an exclusively new target, fingerprints all schema objects/
tables and checks restored application routes. It streams table hashes and never
writes the source. It refuses success if concurrent source changes prevent matching
its recorded backup point. This explicit maintenance scan is not a health request.

Actual command (exit **0**):

```sh
PYTHONPATH=backend uv run --locked python -m orbitiq.maintenance.recovery --directory /workspace/OrbitIQ/backups/phase-6-recovery-20261019T0800Z
```

Backup at `2026-10-19T07:59:05.454518+00:00`, **53,248 bytes**, SHA-256
`644585974d4192d47797b17ff2fc20e660d723f779d2d9362780230d50989c0c`.
Schema **3**, snapshots **2**, attempts **1**, separate insertions **1**, gate
**1**. All source/backup/restored schema and table digests match, including
snapshot payload bytes and the ledger. Integrity and foreign keys pass.

Restored `/api/snapshots`, `/api/snapshots/1`, `/api/snapshots/2` and actual
non-self `/api/comparisons` returned **200**, shared 1. Full archive verification
parsed/validated both genuine records. These use actual in-process FastAPI routes
with a restored-path dependency override, not fabricated API responses. Primary
comparison evidence additionally uses real HTTP and Chromium through Vite.

The temporary restored database was removed after success; the consistent backup
and verification manifest remain Git-ignored. A real attempt to restore that backup
onto the existing original raised `FileExistsError`, with the complete source
fingerprint unchanged. Corrupt input, existing target, migration rollback and
storage/audit failures were also exercised in isolated tests. No original data
was used as a failure-injection target.

## Exact Phase 5 CI evidence

Published SHA: `6c60655402b70306f654c3f9b30f79ff6c7c3e45`.
Run **39211182705**, `completed`, **success**:
<https://github.com/BibinBinoy777/OrbitIQ/actions/runs/39211182705>.
Both job metadata and logs were fetched with read-only HTTPS operations:

| Job | ID | Actual result |
| --- | --- | --- |
| backend | 117924701294 | success; locked uv setup, **398 tests passed**, Ruff lint/format success |
| frontend | 117924700864 | success; npm ci, **172 tests passed**, lint/format and TypeScript/Vite build success |

Every normal step in each job completed successfully for this exact SHA; no merge
SHA or unrelated latest-green run was substituted. Log result excerpts and log
checksums are in the structured evidence. Published scientific reference tests are
inside the full backend suite; standalone audit scripts had no separate job step.
Migration verification was not a separately named Phase 5 step.

Local workflow changes add explicit 40-case SGP4 and 6-case terrestrial audits and
a migration/restore test selection (**5 passed, 57 deselected locally**). Those
steps have not run remotely because no Phase 6 commit/push/dispatch is authorized.
The required-status-checks/branch-protection API returned **403**; its enforcement
configuration is **BLOCKED/unknown**, not inferred from a successful run. The
accessible workflow-defined backend/frontend jobs are both verified successful.

## Verification results and resolved failures

| Executed command/check | Actual result |
| --- | --- |
| Baseline `uv run --locked pytest -q` | 398 passed |
| Baseline frontend `npm test` | 172 passed |
| Final `uv sync --locked` | PASS, existing locked environment checked |
| Final `uv run --locked pytest -q` | **460 passed**, 1 known TestClient/HTTPX deprecation |
| New Phase 6 backend cases within full suite | **62 passed** |
| `uv run --locked ruff check .` | PASS |
| `uv run --locked ruff format --check .` | PASS, 68 Python files formatted |
| Migration/recovery selection from the new test file | 5 passed, 57 deselected |
| `PYTHONPATH=backend uv run --locked python scripts/verify_scientific_references.py --output /tmp/orbitiq-phase6/sgp4.json` | **40 passed, 0 failed** |
| `PYTHONPATH=backend uv run --locked python scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-phase6/earth-fixed.json` | **6 passed, 0 failed** |
| Final frontend `npm test` | **180 passed**, 15 files, 8 additional cases |
| Frontend `npm run lint` / `npm run format:check` | PASS / PASS |
| Frontend `npm run build` | PASS, TypeScript noEmit and Vite |
| Real DB `database check` / `verify-archive` | PASS / 2 genuine snapshots verified |
| Real controlled collection / replay | PASS, new snapshot 2, one HTTP request |
| Genuine same-time TEME / ITRS API comparisons | PASS / PASS, repeated stable numerical results |
| Actual separate recovery / existing-original refusal | PASS / PASS |
| Real Chromium/Vite/backend at three viewports | PASS, details below |
| Dependency/lock comparison and `git diff --check` | PASS, dependencies/locks unchanged |
| Isolated source-only `uv sync --locked` + full pytest | PASS, fresh environment, 460 tests passed |
| Isolated source-only frontend `npm ci` + `npm run build` | PASS, locked installation and TypeScript/Vite build |

Final source-only installation/reproduction results are recorded separately in the
machine-readable evidence. No database or previous virtual environment is copied
into that isolated source directory.

Tests cover real-format reference-derived parsing, malformed/empty/invalid payloads,
HTTP/network/timeouts, one-call admission/cooldown/backoff/Retry-After/budget limits,
operator review, concurrent admission, interrupted jobs, stage recording and safe
errors, exact replay/distinct insertion, atomic rollback, immutable audit, bounded
history/status queries and indexes, invalid/missing time metadata, recent/stale/
deduplicated/failure states, schema-2 migration/rollback, recovery and unchanged
source failures. Fixture tests are explicitly labelled and use temporary archives.
Ordinary API browsing/readiness tripwires prove no collection call path.

Development failures were investigated and resolved: the new readiness component
initially needed adding to its API response model; fixture setup needed selecting
the actual reference-array record; older tests asserting all insertion times were
null needed the intentional schema-3 contract; a timestamp assertion needed
instant comparison across millisecond/microsecond ISO formatting. The first live
reproducibility harness included changing wall-clock EOP-age metadata, and the first
browser harness attempted a button in the existing collapsed TEME details panel.
The harness now excludes only wall-clock assessment fields and explicitly opens
that panel. Scientific assertions/tolerances were not weakened. A formatting check
flagged one new frontend test; it was formatted and the check/build rerun passed.
No final test failure is concealed.

Actual Chromium **154.0.8037.57**, real WebGL 2/SwiftShader, no mocked responses or
canvas: **1440×1000**, **820×1180**, **390×844**. Each flow checked five readiness
sections with actual acquisition/cooldown times, read-only historical readiness
refresh, genuine ISS search, A1/B2 ITRS comparison/real canvas, explicit old-source
handoff and TEME calculation, and return retaining the comparison. Zero JavaScript
page errors, zero external browser requests, no horizontal overflow. Mobile
readiness screenshots were visually inspected. This is not a full browser/GPU/
screen-reader or production-capacity certification.

The existing TestClient/HTTPX and npm `whatwg-encoding` deprecations, and ~558.60 kB lazy Three renderer warning
remain visible; dependencies were not upgraded or warnings suppressed to hide them.

## Every requested acceptance criterion

| # | Criterion | Status and evidence |
| --- | --- | --- |
| 1 | Existing ingestion/dedup inspected | PASS — baseline source and replay contract |
| 2 | Established ingestion pipeline reused | PASS — existing fetch/parser/process/storage, old CLI delegates |
| 3 | Bounded timeouts/retries | PASS — one call, finite HTTP budgets, three deferred failures; tests |
| 4 | Provider restrictions respected | PASS — official policy retrieved, two-hour gate, every HTTP error stops for review |
| 5 | Invalid/incomplete payload rejected | PASS — malformed/empty/invalid/content/size/status tests |
| 6 | Duplicate payload remains deduplicated | PASS — actual exact-byte replay and isolated repeated acquisition tests |
| 7 | Clear collection outcomes | PASS — actual success JSON/exit 0, safe nonzero failures/refusals |
| 8 | Distinct genuine payload persisted | PASS — genuine snapshot 2, distinct hash/epoch/elements |
| 9 | Non-destructive ledger migration | PASS — real 2→3 upgrade, pre-backup, preserved row digest |
| 10 | Separate start/completion/insertion times | PASS — actual attempt 1 and snapshot 2 timestamps |
| 11 | Correct success/failure/validation/dedup audit | PASS — actual success, isolated failure/dedup/rollback tests |
| 12 | Safe failure records | PASS — body/header/internal-error redaction tests; fixed categories |
| 13 | Actual ingestion freshness metadata | PASS — actual readiness HTTP/UI and persisted audit |
| 14 | Identical download cannot refresh old epoch | PASS — preserved first retrieval/epoch and dedup freshness tests |
| 15 | Bounded history/status queries | PASS — ID cursor/max 100, indexed single-row monitoring, VM/time budgets |
| 16 | Two independent genuine snapshots | PASS — preserved Phase 1 acquisition + one new permitted acquisition |
| 17 | Both retrieved through application interfaces | PASS — actual history/detail HTTP 200 and restored routes |
| 18 | Real persisted-source comparison | PASS — actual non-self A1/B2 comparison in TEME and ITRS |
| 19 | Verifiable provenance/times/assumptions | PASS — payload hashes, source URLs, epochs, same-time frames/units |
| 20 | Fixtures not counted as genuine | PASS — separate temporary reference tests; only genuine ISS data in real archive |
| 21 | Dedup/EOP policies preserved | PASS — replay idempotence, existing strict science regressions, labelled predicted EOP |
| 22 | Consistent original backup | PASS — pre-migration SQLite backup, size/hash recorded |
| 23 | Separate restoration | PASS — new isolated restore path, original never target of successful restore |
| 24 | Backup-point identities/payloads match | PASS — complete table/row/BLOB and schema digests |
| 25 | Integrity/restored application verified | PASS — full archive 2, FK/integrity ok, restored history/detail/comparison 200 |
| 26 | Failed restore cannot overwrite original | PASS — actual existing-original refusal and unchanged fingerprint |
| 27 | Exact Phase 5 SHA identified | PASS — local and remote main `6c606554…` |
| 28 | Actual CI run inspected | PASS — run 39211182705, metadata and actual logs |
| 29 | Jobs classified by actual conclusions | PASS — backend/frontend success for exact SHA |
| 30 | Missing CI evidence not assumed successful | PASS — branch protection BLOCKED by 403; Phase 6 remote CI explicitly not run |
| 31 | Applicable local regressions executed | PASS — 460 backend/180 frontend, 40/6 audits, quality/build/browser checks |
| 32 | No hidden unresolved regression | PASS — resolved failures and remaining warnings disclosed |
| 33 | Evidence-backed report | PASS — this report |
| 34 | Structured verification artifact | PASS — phase-6-integration-results.json with actual results |
| 35 | Limitations/follow-up documented | PASS — operational and recovery runbooks, scope below |

## Changed files and dependency impact

New: `ingestion/collection.py`, `maintenance/recovery.py`,
`migrations/003_ingestion.sql`, `services/ingestion_status.py`,
`tests/test_phase6_collection.py`, the two runbooks, this report and its JSON.
Modified: existing database/storage/collector, readiness API/schema/services,
analysis/investigation metadata, earlier tests for intentional new contracts,
readiness/source frontend contracts/panels/tests/fixture, current README/guides
and CI workflow. The full exact file list is in the JSON artifact.

No dependency declaration or lockfile changed. Existing SGP4, Astropy coordinate
calculations, scientific tolerances, gravity model, EOP/leap source selection and
policy remain unchanged. Earlier phase reports/plans/evidence remain unchanged.

## Remaining limitations and follow-up

- Branch-protection required-check metadata is BLOCKED by integration permissions;
  an authorized repository administrator must inspect enforcement separately.
  Verified successful workflow jobs do not establish branch protection.
- Phase 6 remote CI has not run. After a separately authorized commit/push, inspect
  that exact new SHA and its new audit/migration steps; no remote action is taken
  in this phase. The working tree remains available for review.
- Only two genuine snapshots of one satellite and one audited new acquisition
  exist. There is no catalog batch, multi-satellite observation set, physical
  maneuver determination, uncertainty covariance or observed accuracy validation.
- Cooldown coordinates one authoritative SQLite database. Independent copies/IP
  consumers and pre-ledger failed requests need operator coordination. It is not a
  distributed provider-rate-limit service. No production schedule is active.
- Current-time data will age; collect only after permitted gates and source review.
  Preserve source epoch/retrieval/insertion distinctions. Legacy insertion/attempt
  history remains unknown; bounded orbital-readiness limitations remain explicit.
- Local consistent backup/recovery does not prove durable off-machine storage,
  cross-region recovery, production RPO/RTO, persistent cloud volumes, managed
  PostgreSQL behavior, monitoring delivery or public traffic capacity.
- Public launch still requires durable storage/retention, monitored expiry and
  failure recovery, authentication/authorization for protected operations,
  rate/abuse/concurrency controls, security/accessibility review and deployment
  verification. No application was deployed or made publicly accessible here.

No unauthorized commit, push, deployment, publication, remote modification,
workflow trigger or workflow rerun was performed. Only local verification servers
were started and they were stopped after checks.
