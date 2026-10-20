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

## Phase 8.1 encrypted export and independent recovery preparation

The existing SQLite backup procedure remains authoritative. The new operator CLI
`orbitiq.maintenance.backup_export` first runs that same consistent local rehearsal,
then uses **restic 0.19.1** to encrypt/export the verified backup point and retrieve
that exact restic snapshot into a new target. It checks the retrieved file checksum,
complete schema/table fingerprints, every stored payload and representative APIs.
It never restores onto the source, initializes a repository, deletes retention data
or enables a scheduler. Restic snapshot IDs identify backup objects, not orbital
snapshot IDs.

Install restic from an approved distribution. The Phase 8.1 Linux-amd64 test binary
was fetched from the official `v0.19.1` GitHub release over verified HTTPS and checked
against its published SHA256SUMS:
`f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c`
(compressed `restic_0.19.1_linux_amd64.bz2`). The release signature was not separately
verified. Review publisher provenance/signatures and updates for the production
operator environment; do not blindly execute an unverified download.

Provision an **independent approved destination**, such as a separate SFTP backup
host or HTTPS S3-compatible repository. No such destination or credentials are
configured in this task. Repository-file contents support `sftp:user@host:/path`
or `s3:https://host/bucket/prefix`, without embedded passwords, query credentials,
fragments or insecure HTTP. SFTP needs preverified SSH known-hosts and a restricted
backup account/key; never disable host-key checking. HTTPS storage needs certificate
verification and least-privilege credentials supplied through its supported secure
environment/identity mechanism. Do not reuse an unapproved ambient cloud identity.
The CLI never prints repository values, password contents or subprocess stderr.

Use a protected directory owned by the operator account. Repository and password
files must be absolute, non-symlink, private (0600/0400), owned and nonempty; store
passwords/keys outside both Git and the exported backup point. Separate recovery
credentials from the application host. Losing the restic password loses access to
its encrypted contents. Test credential recovery independently of the primary host.
Initialize the selected repository deliberately only after approval; the export
command refuses a missing/unusable repository and does not invent one.

```sh
export PYTHONPATH=backend
export ORBITIQ_DATABASE_PATH=/absolute/path/to/authoritative/orbitiq.sqlite3
uv run --locked python -m orbitiq.maintenance.backup_export \
  --directory /protected/jobs/new-UTC-job-directory \
  --restic /approved/bin/restic \
  --repository-file /protected/config/restic-repository \
  --password-file /protected/keys/restic-password \
  --status-file /protected/state/latest-backup.json \
  --independent-destination-approved
```

The independence flag is an explicit operator attestation that the selected
external destination has been approved as a separate failure domain. It cannot
verify physical infrastructure from a URL and cannot be combined with local-test
mode. Actual off-machine closure additionally needs remote round-trip evidence,
provisioning/ownership records and recovery from a replacement host. No such
attestation or remote operation was performed here.

Names use a new operator-selected UTC job directory; receipts record UTC completion,
restic snapshot ID, backup checksum, bytes, original schema/table hashes, verified
record count and API statuses. The stable status file atomically reports success
or failure for the monitoring CLI. Unknown status-file formats are preserved and
refused. Keep one export job at a time; no scheduler or fleet coordination is added.
The restore selects only the backed-up point subtree, avoiding restoration of
system ancestor directories/ownership. Source and destination identities, permissions
and restore-user ownership behavior still require target-host testing.

`--allow-local-test` permits an absolute local encrypted-repository path and always
records `off_machine_recovery_verified=false`. The Phase 8.1 genuine two-record
round-trip and encrypted repository check used that mode; **they do not establish
off-machine recovery**. A wrong-password test failed safely, updated a failure
receipt and left the primary archive intact. Unit mocks are not encrypted-storage
or independent-destination evidence.

Retention proposal for owner approval: keep the last two verified points plus
7 daily, 4 weekly and 12 monthly points. Preview against the intended repository:

```sh
restic --repository-file /protected/config/restic-repository \
  --password-file /protected/keys/restic-password forget --dry-run \
  --tag orbitiq-archive-v1 --group-by tags --keep-last 2 \
  --keep-daily 7 --keep-weekly 4 --keep-monthly 12
```

Only a dry-run was tested locally. No `forget` deletion or `prune` is automated.
Review preview results, successful recovery receipts, policy approval and destination
immutability/access controls before authorizing deletion. Failed uploads retain
private staging artifacts and return nonzero; they do not claim success or replace
valid source data. Disk-space, incomplete uploads, lock contention and failed
restorations need an operator response. Preserve failure evidence, retry only after
investigation, and remove only identified job artifacts under approved retention.
Private plaintext staging is not an off-machine backup; protect and expire it
separately. RPO/RTO, independent retention/encryption keys and retrieval from a
replacement host remain launch blockers.
