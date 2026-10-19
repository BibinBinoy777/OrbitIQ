# Ingestion operations (Phase 6)

Collection is an explicit operator action. Normal API reads, search, history,
readiness, position calculations and the globe do not contact CelesTrak. There is
no public collection endpoint, daemon, activated schedule, or automatic retry loop.

## Prerequisites and migration

From the repository root, install the locked environment and export configuration:

```sh
uv sync --locked
export PYTHONPATH=backend
export ORBITIQ_DATABASE_PATH=/absolute/path/to/existing/orbitiq.sqlite3
# Optional; the default is this same official endpoint:
export ORBITIQ_CELESTRAK_URL=https://celestrak.org/NORAD/elements/gp.php
```

On read-only-home machines, set `UV_CACHE_DIR=/tmp/orbitiq-uv-cache` first.
`.env` files are not loaded automatically. Never put credentials in `VITE_*`.
No source credentials are needed. TLS verification and inherited proxy/CA trust
remain enabled. Only official HTTPS CelesTrak GP endpoints, no credentials/query/
fragment/nonstandard ports, are accepted. The operator supplies one catalog ID
(1..339999); the query is always `CATNR=<id>&FORMAT=JSON`, not an entire catalog.

Existing schema 1/2 archives need an explicit, consistent pre-upgrade backup:

```sh
uv run --locked python -m orbitiq.database migrate --backup /absolute/path/to/new-pre-schema3-backup.sqlite3
uv run --locked python -m orbitiq.database check
uv run --locked python -m orbitiq.database verify-archive
```

The backup destination must not exist; parent directories must exist. Migration
uses a writer lock and transactional DDL/version changes. Existing snapshot rows,
raw bytes, identities, first retrievals, triggers and user tables are preserved.
Schema 3 adds `ingestion_attempts`, `snapshot_insertions`, `collection_gate`, and
indexes. New databases explicitly created with `database init` include schema 3.
Do not initialize an existing archive. Existing schema 2 supports read-only
browsing; controlled collection refuses it until migration. Schema 1 still needs
the snapshot migration. Repeating migration at schema 3 is a no-op.

Migration rollback on failure is transactional. There is no destructive down
migration that drops valuable audit history. Recovery to a prior schema uses the
retained backup restored into a separate path; see the recovery runbook. Old
rows' insertion times and old collection attempts are **not backfilled**.

## Collect one satellite

```sh
uv run --locked python -m orbitiq.ingestion.collection collect 25544 --verify-replay
uv run --locked python -m orbitiq.ingestion.collection history --limit 20
# Cursor is the previous page's next_before_id:
uv run --locked python -m orbitiq.ingestion.collection history --limit 20 --before-id 20
```

The old `python -m orbitiq.ingestion.celestrak 25544 --verify-replay` command and
`ingest()` function delegate to this collector. Existing fetch/parser/
`process_dataset()`/snapshot persistence conventions are retained. Internal
exact-byte processing/replay performs no HTTP request; it is not an independent
acquisition and does not manufacture a second audit attempt.

A successful collection emits JSON, exit 0: `attempt_id`, `snapshot_id`, outcome
`inserted` or `deduplicated`, response/parse/validation/persistence flags, checksum,
retrieval/completion times, replay result and `next_allowed_at`. Failure/refusal
exits nonzero with a safe category/message; raw upstream bodies, headers, internal
exceptions, credentials and configuration dumps are never printed. A failed
admission/configuration check is not an upstream acquisition attempt and does not
append a misleading attempt row.

`--verify-replay` processes the *same downloaded bytes* twice inside the success
transaction. It makes exactly one HTTP request. Matching catalog ID, exact source
URL and raw-response SHA-256 reuse the first snapshot. Its original retrieval and
insertion timestamps remain unchanged. A byte difference, including whitespace,
remains a different dataset under the established identity contract. A scientific
historical investigation must additionally inspect source epochs/element changes;
a hash difference alone is not a maneuver or accuracy measurement.

## Provider policy, cooldown and retry budget

Official sources inspected on 19 October 2026:

- <https://celestrak.org/usage-policy.php>
- <https://celestrak.org/NORAD/documentation/gp-data-formats.php>

GP updates are every two hours; download only needed data once per update. The
policy says machine clients must stop and report **every non-200 HTTP response**
for human investigation, including server errors. Accordingly:

- Every admitted invocation makes **at most one** HTTP request. No internal
  transport retries, automatic redirects, background loops or sleeping for hours.
- A committed, database-wide gate enforces at least **7,200 seconds** between
  acquisitions, including different catalog IDs and official hostname aliases.
  Successful completion extends the gate through response retrieval + two hours.
- Network/proxy/timeouts get **deferred**, explicitly invoked retries: first
  failure +2h, second +4h, third +8h, each with 0..300 seconds system-random jitter.
  The budget is exhausted after three consecutive failures. Successful collection
  clears the failure count; an operator review does not erase historical failures.
- Every non-200 HTTP response stops unattended eligibility pending review. Parsing,
  orbital validation, TLS and persistence errors also require review. 401/403/404
  impose at least a 24-hour cooldown. 429 and 50x receive at least the normal
  backoff and also require review.
- Valid `Retry-After` delta seconds or HTTP dates extend (never shorten) the
  earliest next time. An unrepresentably huge numeric delay blocks through the
  maximum representable UTC time; investigate it rather than retrying early.
- `history` and readiness show safe metadata. Check `next_allowed_at`, investigate
  the category/source condition, and only then explicitly resume:

```sh
# Only AFTER the reported cooldown and human review:
uv run --locked python -m orbitiq.ingestion.collection collect 25544 --resume-after-review
```

This option permits an operator to resume a stopped budget; it **cannot bypass
cooldown**. No automatic operator review or automatic retry is implied.

Timeouts remain 5 seconds connect / 15 seconds per HTTP operation. An elapsed
20-second budget is checked between raw chunks; a blocked read may additionally
consume its finite read timeout. It is not a hard real-time 20-second deadline.
Responses must be HTTP 200, uncompressed JSON, <=64 KiB, exactly one matching
record, with unique keys, finite supported fields and successful epoch SGP4
propagation. HTML/error pages and incomplete/malformed/invalid records fail.

The gate coordinates processes **sharing this one SQLite archive**, not independent
copies, machines or other applications sharing an IP. Run one designated collector
against the authoritative archive. Do not collect from restore targets or create a
new archive to circumvent a cooldown. Legacy archives have no failed-request
history; before first adoption, operators must account for recent requests made by
older software. The collector also respects the newest stored legacy retrieval's
two-hour interval. It cannot reconstruct undocumented pre-ledger provider calls.

## Audit and transaction guarantees

1. Validate configuration and existing schema, then atomically reserve the gate
   and create a `running` attempt. No network call occurs without admission.
2. Release the writer lock during HTTP acquisition and validation.
3. Atomically insert/deduplicate the snapshot, record a separate SQLite-generated
   insertion timestamp for a new row, complete the success audit and release the
   active gate. A failed commit cannot report a successful snapshot.
4. On failure, roll back snapshot/success changes, then make **one** best-effort
   failure transaction. If storage is unavailable, log only stage/category,
   attempt ID where known, and whether the audit write succeeded; return failure.
   No recursive logging/persistence retry occurs.

The audit distinguishes start, database insertion, response retrieval, successful
validation and completion. Provider epoch belongs to the immutable snapshot;
propagation evaluation/execution belong to the calculation response. The attempt
stores sanitized source identity, catalog ID/query SHA-256, HTTP status when
available, completed acquisition-call count (0/1), payload checksum where received,
parsed count, validation status, linked snapshot and inserted/deduplicated result.
A crash can leave `running` with unconfirmed request count/outcome: **0 is not proof
that no request reached the provider**. The conservative gate remains effective.

An active job blocks duplicates. After 120 seconds an explicit later invocation
can mark a stranded job `interrupted`, retaining unknown acquisition outcomes and
all cooldown restrictions. A normal request is bounded below this lease. Treat a
stranded job as an operational issue; do not run overlapping collectors or alter
clocks/state to force admission. Completed attempts and insertion timestamps have
immutability triggers; there is no retention deletion.

Audit history is operator CLI only: read-only, ID cursor, default 20/max 100,
100+1 lookahead, 250ms busy/50,000 VM/250ms work budget. It excludes raw payloads,
URLs, paths, arbitrary exception text and headers. There is no administrative HTTP
history endpoint. Readiness exposes only coarse, redacted operational facts.

## Monitoring

`GET /api/readiness` and its existing dashboard now include `ingestion`:
last attempt/start/completion, successful acquisition/validation, latest recorded
snapshot insertion, latest result, exact consecutive failures, last safe category,
next allowed time and whether operator review is required. Indexed single-row
lookups replace ledger scans. This is not a live provider availability probe.

No history is degraded/explicit; schema 2 reports migration required; malformed,
missing or future required timestamps are unknown. A failed latest attempt with
older stored data is degraded and does not remove those records. Successful
collection can coexist with stale/unknown orbital data. Freshness still uses the
source epoch (24h fresh / 72h aging defaults), never a deduplicated collector run.
Large archives retain the earlier conservative bounded orbital assessment.

The Phase 6 evidence records one new genuine ISS acquisition plus the preserved
Phase 1 snapshot, not two new Phase 6 downloads. The next permitted collection
from that run is `2026-10-19T09:58:23.407349+00:00` (19 October, 15:28:23 IST).
This is the earliest gate time, not a guarantee that CelesTrak will provide a new
payload or that the source remains available then. Read the current persisted gate
before any later operation. No production scheduler was enabled.
