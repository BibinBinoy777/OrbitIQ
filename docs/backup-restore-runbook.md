# SQLite backup and isolated recovery runbook

Historical payloads and audit records are valuable data. Backups are separate
from Git. An ephemeral task filesystem is not durable production storage.

## Consistent backup

From the repository root, with a locked development installation:

```sh
export PYTHONPATH=backend
export ORBITIQ_DATABASE_PATH=/absolute/path/to/existing/orbitiq.sqlite3
uv run --locked python -m orbitiq.database check
uv run --locked python -m orbitiq.database verify-archive
uv run --locked python -m orbitiq.database backup /absolute/path/to/new-backup.sqlite3
```

Set `UV_CACHE_DIR=/tmp/orbitiq-uv-cache` on read-only-home machines. Parent
folders must exist. The destination must not exist. SQLite's `Connection.backup`
creates a consistent database image, including committed data in journals/WAL;
never substitute a raw `cp` of an active database file. Source/destination schema
and integrity are checked. Schema 3 also checks foreign keys. Source access is
read-only. Partial target creation failures remove only the newly reserved target.
No successful message is emitted for failure.

Retain the artifact checksum, creation UTC time, size, schema version, source
identity and a manifest of table/row hashes at the backup point. Protect the
backup and retain it in a durable location with access controls; neither a Git
commit nor an ignored local directory is a backup service.

## Repeatable verified rehearsal

The operator command automates backup, separate restoration, full streaming table
hashes, schema/index/trigger hashes, archive provenance checks and restored APIs:

```sh
uv run --locked python -m orbitiq.maintenance.recovery --directory /absolute/path/to/new-recovery-directory
```

The directory must **not exist**, and its parent must exist. It creates
`backup.sqlite3`, restores to a distinct `restored.sqlite3`, then checks:

- Schema/migration version, all application tables/indexes/triggers, integrity
  and foreign keys.
- Every table's row count and deterministic row digest, including exact BLOB
  contents, original snapshot identities, payloads, insertion times, attempts
  and the provider gate.
- Full archived source parsing/validation and representative actual history,
  detail and comparison API routes through an in-process FastAPI TestClient;
  requests use the isolated restored path, without mocked responses.
- Source fingerprints before/at/after the backup match. If concurrent collection
  changes the source, verification refuses a success claim: repeat during a
  quiescent collection window. SQLite backup consistency itself does not depend
  on no concurrent writers; equality with a recorded live-source point does.

Success writes `verification.json`, prints structured evidence, exits 0 and removes
**only** the restored target the command created. The verified backup and manifest
remain. `--keep-restored` deliberately retains that target for further read-only
inspection; after inspection, remove only that named target. No restore is applied
to the original. Failure exits nonzero and leaves identifiable diagnostic artifacts;
review them, then use a new directory on the next run. Do not delete unrelated files.

The verifier is an explicit full-archive maintenance operation, not a cheap health
check. It uses the existing locked httpx/FastAPI development environment for API
smoke tests. For a single snapshot the comparison is labelled a self-check; for
empty archives no pair is invented. A successful fixture recovery is separate from
real-archive recovery evidence. Scientific current-time/EOP restrictions still
apply independently of byte-level recovery.

## Restore for operator evaluation

```sh
# A NEW destination, never the original path:
export ORBITIQ_DATABASE_PATH=/absolute/path/to/new-restored.sqlite3
uv run --locked python -m orbitiq.database restore /absolute/path/to/verified-backup.sqlite3
uv run --locked python -m orbitiq.database check
uv run --locked python -m orbitiq.database verify-archive
```

Existing destinations and same source/destination aliases are refused. Keep the
original archive and backup. Validate table/row/payload fingerprints against the
backup manifest, then inspect history/detail and compatible historical comparisons.
No ingestion should run against the restore target. Ordinary reads never collect.
A restored gate may predate requests after the backup point: account for the latest
actual provider activity before authorizing collection from any replacement archive.
Do not run collectors against multiple restored copies.

Changing the application's configured database or restarting production services
is a separate explicit operator decision. Stop writers before a path switch and
verify the intended source. This phase performs no production switch or deployment.
Restoring an older pre-migration schema does not overwrite or downgrade the current
archive; schema 2 is browsable, while schema 3 is required for audited collection.

## Failure and rollback guarantees

Migration holds a writer lock, creates a recoverable old-version backup, then
applies DDL and version updates in one transaction. Failure rolls back partial
DDL/version changes. The repository supports forward migrations, not destructive
removal of completed audit records. Evaluate the retained old-version backup at a
new path if rollback is needed; do not replace the live database blindly.

Tests cover corrupt/missing backup input, existing restore/backup targets,
unchanged source bytes, failed snapshot/audit transactions and migration rollback.
The real Phase 6 run also attempted restoration to the existing original: exclusive
creation refused it, and the complete source fingerprint remained unchanged.

## Actual Phase 6 artifacts

Local, Git-ignored artifacts retained for this execution:

- `backups/phase-6-pre-migration-20261019T075805Z.sqlite3`: schema 2, one original
  genuine ISS snapshot, SQLite consistent pre-upgrade backup.
- `backups/phase-6-recovery-20261019T0800Z/backup.sqlite3`: schema 3, two genuine
  snapshots, one completed ingestion attempt, one recorded snapshot insertion.
- The corresponding `verification.json`: schema/table digests and actual restored
  API results. Its temporary restored database was removed after successful checks.

Checksums, sizes, row preservation and acceptance evidence are recorded in
[Phase 6 evidence](phase-6-integration-results.json). No database, backup, raw
provider body or secret is added to Git. These local recovery drills establish
local SQLite consistency and application readability; they do not establish
cross-region recovery, production RPO/RTO, encryption, off-machine retention,
capacity or managed PostgreSQL readiness. Those remain public-launch work.
