# Phase 1: orbital data and scientific engine

## Acceptance criteria

1. Fetch real, single-object CelesTrak GP JSON through a fixed HTTPS destination,
   with TLS verification, timeouts, bounded response size and no automatic retries.
2. Reject malformed, unsupported and mismatched records without saving snapshots.
3. Preserve exact upstream response bytes, SHA-256, original record, retrieval time,
   orbital epoch, source URL and validation/library versions in append-only history. Persist normalized
   frame/time-system/model defaults and explicit element units separately from
   the unmodified source record.
4. Explicitly migrate Phase 0 databases with a verified pre-upgrade backup; never
   initialize implicitly or overwrite existing database/backup files.
5. Match trusted near-Earth/deep-space SGP4 reference vectors with stated tolerances.
6. Expose read-only, validated APIs for history and calculated TEME state vectors,
   with UTC times, explicit units/frame, provenance and limitations.
7. Verify populated database backup/restoration, API behavior, locked installation,
   tests, lint, formatting and existing frontend regression checks.
8. Record actual live ingestion evidence separately from fixture-driven tests.

## Architecture and data contract

- `ingestion/celestrak.py`: operator command and fixed-origin streaming HTTP fetch.
- `orbits/elements.py`: CelesTrak GP JSON validation (OMM field names).
- `orbits/engine.py`: WGS72 SGP4 propagation in Earth-centered TEME.
- `storage.py`: transactional append-only retrieval snapshots and archive checks.
- `api/orbits.py`: read-only history, original record and propagation routes.
- `migrations/002_snapshots.sql`: schema version 2, history index and immutability
  triggers. Migration 001 is unchanged.

CelesTrak GP JSON defines omitted `CENTER_NAME=EARTH`, `REF_FRAME=TEME`,
`TIME_SYSTEM=UTC`, `MEAN_ELEMENT_THEORY=SGP4` defaults. An epoch without an offset
means UTC under that format, never machine-local time. Explicit contradictory
metadata is rejected. Format reference: https://celestrak.org/NORAD/documentation/gp-data-formats.php.
Only publicly classified (`U`), ephemeris-type 0, elliptical Earth SGP4 elements
are supported. Numeric fields must be finite and in declared ranges; source
numeric strings and booleans are refused. Epochs must be in 1957..2099.

Catalog IDs are supported through **339999**, the installed SGP4 library's
initialization limit. Larger identifiers are rejected explicitly. Mean motion
is constrained to (0,100] rev/day as a broad implementation input bound, not an
assertion that all such orbits are physically valid. Initialization must also
successfully propagate to the epoch. This is structural/model usability
validation, **not observation-based accuracy validation**.

An exact dataset replay (same source URL, catalog ID and raw-response SHA-256)
reuses its existing snapshot without changing the first retrieval timestamp.
A different raw response appends new history; no existing snapshot is overwritten.
Byte changes, including JSON whitespace, count as a different dataset. This is
dataset history, not a complete audit log of every repeated retrieval. A writer
transaction serializes lookup and insertion, including concurrent processes.
Legacy duplicate rows are retained rather than destructively deduplicated. The raw
entity body is limited to 64 KiB, must be application/json, and must contain
exactly one matching record. Compressed bodies, redirects, duplicate JSON keys,
nonfinite values, empty results, errors and rate-limit responses are rejected.
HTTP connect timeout is 5 seconds, per-operation timeout 15 seconds, with a
20-second elapsed budget checked between unbuffered chunks. These bounds do not
constitute a hard real-time deadline. No retries or background polling occur.
Operators should retrieve a given object no more frequently than every two hours
and honor upstream restrictions; there is no public ingestion endpoint or daemon.

Snapshot validation records `structural_and_epoch_propagation_passed`, validator
`orbitiq-omm-v1`, and the SGP4 library version. Freshness is displayed as recent
(up to 24h after epoch), stale (older), or future epoch. This is a transparent UI
policy, not an accuracy estimate. Retrieval time is distinct from orbital epoch.
The normalized record and element unit map are persisted even when upstream
invariant fields are omitted. Derivative values retain CelesTrak/TLE conventions;
they should not be treated as standalone measured accelerations. No position is
stored as a direct observation.

## Explicit database setup and migration

From the repository root, after locked installation:

```sh
export PYTHONPATH=backend
export ORBITIQ_DATABASE_PATH=/absolute/path/to/orbitiq.sqlite3
# Only if deliberately creating a NEW database; parent directory must exist:
uv run --locked python -m orbitiq.database init
```

A new database gets migrations 001 and 002. For an existing Phase 0/schema-1
database, use a distinct, nonexistent backup path:

```sh
uv run --locked python -m orbitiq.database migrate --backup /absolute/path/to/pre-phase1.sqlite3
uv run --locked python -m orbitiq.database check
```

Migration obtains a writer lock, validates the source, backs it up using SQLite's
online backup API, then applies DDL/version updates in one transaction. A failed
backup prevents migration; a failed migration rolls back and retains the backup.
Re-running on schema 2 is a no-op. Unknown versions are refused. Existing user
records/tables are retained. No startup hook runs these commands.

## Ingestion and read-only API

```sh
# Requires HTTPS egress to celestrak.org; no credentials are required.
uv run --locked python -m orbitiq.ingestion.celestrak 25544 --verify-replay
uv run --locked python -m orbitiq.database verify-archive
```

The command reports an actual snapshot ID only after the transaction commits
or an existing identical dataset is found. `--verify-replay` processes those same
downloaded bytes twice and confirms the same ID without a second HTTP request.
Failures print a sanitized error category and exit nonzero. Proxy failures are
reported separately from an upstream HTTP status, transport timeout, TLS failure
with an identifiable SSL cause, and other network errors. An upstream HTTPS
403 alone does not prove that CelesTrak itself rejected the request; a gateway
can also return it. Error bodies, proxy credentials and cookies are not logged. A snapshot ID is a retrieval event ID,
not a satellite ID. The frontend remains the Phase 0 health view in this phase.

- `GET /api/satellites/25544/snapshots?limit=20`: newest retrieval first;
  optional `before_id` supports keyset pagination; maximum page size 100.
- `GET /api/snapshots/{id}`: source metadata and original JSON record.
- `GET /api/snapshots/{id}/position?at=2026-10-18T00:00:00Z`: calculate using that
  exact snapshot, not an implicit latest record. Choose a time within seven days
  of its epoch. URL-encode a `+` timezone offset if used in a query string.

Calculation times require a timezone and normalize to UTC. Returned position is
in km and velocity in km/s in **TEME**, not Earth-fixed coordinates, latitude,
longitude or altitude. The response identifies WGS72/SGP4, engine version,
calculation time, target time, source snapshot/hash/retrieval and orbital epoch.
Requests beyond ±7 days from epoch are refused as a product safety policy; this
window does not guarantee accuracy. An offset beyond 24h produces a warning.
SGP4 errors or nonfinite output are rejected rather than returned as positions.

No Astropy coordinate transformation is performed in this phase. Ground tracks,
Earth-fixed vectors and a globe require their own frame/time reference tests.
No observation residuals, uncertainty model, anomaly or collision claims exist.

## Backup and recovery

Use the existing README's new-destination backup/restore procedure. Both schema
versions remain supported by those commands. For populated schema 2 archives:

```sh
uv run --locked python -m orbitiq.database backup /absolute/path/to/new-backup.sqlite3
# Switch to a NEW destination; never replace the source database:
export ORBITIQ_DATABASE_PATH=/absolute/path/to/new-restored.sqlite3
uv run --locked python -m orbitiq.database restore /absolute/path/to/new-backup.sqlite3
uv run --locked python -m orbitiq.database verify-archive
```

`verify-archive` checks database integrity/schema, response hashes, correspondence
between original response and record, and catalog/epoch metadata. Tests additionally
compare complete restored records and raw bytes. This is accidental-corruption
detection, not tamper-proof storage: a database administrator can drop triggers or
rewrite hashes. Keep production backups in separate durable storage and test
actual recovery there before launch. This task's temporary fixture databases are
not real historical satellite archives or a production durability demonstration.

## Reference science and checks

Fixture provenance, source hashes, reference cases, units and tolerances are in
`backend/tests/fixtures/README.md`. Run `uv run --locked pytest` from the root.
The CI workflow already runs this suite along with Ruff and frontend checks;
GitHub execution still requires an authorized commit/push and is not claimed.
Live ingestion is deliberately not part of deterministic CI tests. See
`phase-1-report.md` for executed results and any remaining blocker.

## Source configuration and connectivity diagnosis

`ORBITIQ_CELESTRAK_URL` is an optional exported environment variable, defaulting to
`https://celestrak.org/NORAD/elements/gp.php`. Only that official GP path on
`celestrak.org` or `www.celestrak.org`, HTTPS port 443, without credentials, query
or fragment, is accepted. The client adds `CATNR` and `FORMAT=JSON`. These checks
prevent accidental insecure or unrelated sources; this is not a generic URL-fetch
service. `.env` files still are not loaded automatically. No source URL, query,
User-Agent or proxy bypass was needed to restore this environment's access.

The historical failure was an outbound proxy connection rejection (`ProxyError`
403), not evidence of a CelesTrak HTTP rejection. Its old response headers/body
and internal provider decision were not retained, so the exact old policy reason
cannot be established retroactively. The current runtime reports the existing
`celestrak.org` rule **enforced**, and a real trace now shows CONNECT 200, TLS
completion, then upstream HTTP 200 with a valid GP record. Local destination DNS
resolution failed in the worker; proxied HTTPS nevertheless succeeded, so that
local DNS result was not blocking this route. No DNS or TLS configuration was
changed, and no verification or access control was bypassed.

If blocked again, inspect `environment_status` and the safe request trace:
CONNECT failure precedes the destination HTTPS request; a status after TLS is
an upstream response and needs separate origin/gateway investigation. Preserve
inherited proxy routing and CA trust. Record safe status/header names and a
bounded redacted body only when actually available; do not dump environment
values, authentication headers, cookies or full proxy URLs. Stop consistent
retries. The supported configuration is restricted HTTPS egress to the selected
official hostname; apply it through environment settings, not proxy bypasses.
An unenforced/unknown observation needs runtime diagnosis. Do not keep adding a
duplicate rule that already exists. Live acceptance remains unmet until a real
request succeeds.

## Offline and live verification

Offline regression commands (mocked HTTP; no internet required):

```sh
uv run --locked pytest backend/tests/test_phase1.py backend/tests/test_ingestion_reliability.py
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

The reliability suite covers concurrent duplicate processing, rollback after an
injected post-insert failure, required-field rejection, HTTP 403/429/5xx,
connection/timeouts, distinguishable TLS errors and secret-safe messages. It
uses temporary databases and explicit fixtures, not real observations.

For a live integration run, select the existing database and export PYTHONPATH
as above, then run the ingestion command with `--verify-replay`, followed by
`verify-archive`. Do not run `init` on the existing database. Inspect the snapshot
API's source URL/hash, retrieval timestamp, orbital epoch, normalized conventions
and units. Make an API position request with a timezone-aware time within the
supported epoch window. Test backup/recovery into a separate new path, preserving
the source. Keep failure injection in temporary copies. A successful fixture
suite is never a substitute for this real request.

The completed live run downloaded exactly one ISS record and replayed the captured
response without another download. The evidence includes the actual response
hash/status, persisted metadata, API checks, and a recovery check using a new
copy. See `phase-1-report.md` for the exact results and limitations. Do not fetch
the same object repeatedly to verify idempotency; use the same downloaded bytes.
