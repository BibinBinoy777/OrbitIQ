# E3 reliability and recovery

E3 is an engineering milestone, based on E2 commit
`d8aa10fdbb9f4be13ff8c5f096b93f0bb17e0af4`. Acceptance requires safe bounded
provider failures, truthful freshness, preserved transactional history, verified
separate restoration, a reproducible isolated installation, and healthy E1/E2
regressions. It does not qualify private reference data or authorize production.
See the [execution report](engineering-e3-report.md).

## Install and run locally

Use Python 3.12, uv 0.12.23, Node 24 and npm 11. Follow the
[installation, environment and development commands](../README.md#requirements-and-installation).
Both `uv sync --locked` and `npm ci` must succeed. Export the values described in
`.env.example`; `.env` is not loaded automatically. Choose an **absolute new**
database path, create its parent directory deliberately, and run:

```sh
export PYTHONPATH=backend
export ORBITIQ_DATABASE_PATH=/absolute/path/to/new-orbitiq.sqlite3
uv run --locked python -m orbitiq.database init
uv run --locked python -m orbitiq.database check
uv run --locked uvicorn orbitiq.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

In another shell run `npm run dev` from `frontend`. Vite listens on loopback port
5173 and proxies `/api` to port 8000. Set `ORBITIQ_BACKEND_URL` before starting
Vite to use another backend port. Existing schema-1/2 databases require explicit
[migration with a new backup](ingestion-operations.md#prerequisites-and-migration),
not `init`. Schema 3 requires no E3 migration.

`/api/health` reports process liveness independently of storage or providers.
`/api/ready` reports whether required schema-3 structures and the singleton
collection gate are available; it does not scan all rows or qualify science.
`/api/readiness` reports bounded stored-data freshness, ingestion outcomes and
local scientific-resource status. HTTP 200 from that diagnostic endpoint does
not mean its components are healthy.

## Provider and freshness contract

The [existing operator collection policy](ingestion-operations.md) is unchanged:
one request per admitted invocation, a shared two-hour SQLite gate, bounded
operator-invoked network retries, and human review for non-200 HTTP responses.
`Retry-After` can extend the gate. There is no background scheduler or job queue.
Tests use deterministic HTTPX transports; installation verification never contacts
CelesTrak or ESA.

Exactly one matching valid JSON record is required. Empty, truncated, multi-record
(including mixed known/new or partially invalid), duplicate-key and unsupported
responses are rejected as a whole. Partial acceptance is not this adapter's
contract. An already accepted byte-identical response reuses its original snapshot
and appends an acquisition audit. Byte differences can create distinct snapshots
without proving distinct orbital element sets. Older valid epochs append history
and never rewrite prior records; insertion IDs are not epoch ordering.

| Timestamp                   | Meaning                                                                                                     |
| --------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Orbital epoch               | Element reference instant; the existing 24h/72h presentation policy measures age from this instant.         |
| Snapshot retrieval          | First successful retrieval of the immutable archived payload.                                               |
| Last successful acquisition | Most recent audited complete response, including deduplicated acquisitions; not the same as a new snapshot. |
| Calculation time            | Execution/evaluation metadata in calculation responses; not a new provider observation.                     |
| Playback time               | User-selected evaluation instant; moving the timeline never refreshes data.                                 |

A new HTTP success can still mean stale elements. Failed refreshes leave stored
records available with their source, age and separate failure indicators.
Freshness is not an accuracy guarantee and does not change scientific eligibility.
See [readiness semantics](scientific-data-readiness.md).

Snapshot insertion, insertion timestamp, success audit and gate release share one
transaction. Exceptions roll back that transaction. An uncatchable interruption
may retain a `running` admission; later invocation reconciles it after the 120s
lease, retaining cooldown and failure accounting. Never edit clocks or gates to
bypass policy. The smoke test's fixed clocks exist only in its disposable fixture.

## Storage failure diagnosis

- A missing/unconfigured database is not created by startup. Check the absolute
  path and explicit initialization/migration commands. Production startup refuses
  missing, incompatible or invalid storage; development liveness can remain up.
- A missing collection gate is an integrity failure. Readiness returns 503 and
  maintenance validation refuses it. Collection returns a safe storage error
  without a provider request or an automatic gate repair. Do not insert a replacement gate blindly:
  reconstructing a gate could lose provider cooldown history. Inspect and recover
  into a new target using a verified backup.
- A locked archive can refuse admission or maintenance. Stop conflicting writers,
  inspect the safe operation/category diagnostics, then retry the explicit command.
  SQLite connection/browsing busy timeouts remain in effect. Backup additionally
  has a 30s progress-callback budget, 128-page steps and 50ms busy retry sleeps.
  This budget covers SQLite's backup stage, including restart under write churn;
  initial/final integrity scans, individual filesystem calls and OS scheduling
  are not a strict 30s wall-clock guarantee for the entire maintenance command.
- Initialization, backup and restore build a private mode-0600 sibling staging
  file, validate and close it, fsync its contents, then atomically hard-link to a
  new destination. Existing files, symlinks and racing creators are never replaced.
  Filesystems must support same-directory hard links; unsupported publication
  fails safely. No rename-overwrite fallback exists.
- Handled failures, including KeyboardInterrupt, remove the operation's staging
  file. Uncatchable process death can leave `.DESTINATION.orbitiq-*.tmp` and SQLite
  staging journals. The final target is absent if death precedes publication; if
  publication completed, it contains a validated image. Stop the relevant workers,
  inspect only that operation's named artifacts, and use a new target on retry.
  Do not delete arbitrary database files or apply broad wildcard cleanup.
- Fsync of file contents and atomic linking do not establish a host power-loss,
  filesystem or off-machine disaster-recovery guarantee. Production durability
  and independently stored recovery remain open.

Use the [backup/restore runbook](backup-restore-runbook.md) for consistent engine
backups, full row/schema manifests and isolated restored API checks. Never raw-copy
or hash a changing SQLite file. Recovery tests use temporary databases exclusively.

## Reproduce verification

```sh
uv run --locked pytest
uv run --locked pytest -q backend/tests/test_e3_ingestion.py backend/tests/test_e3_recovery.py
uv run --locked ruff check .
uv run --locked ruff format --check .
# In frontend: npm test; npm run lint; npm run format:check; npm run build
```

To verify a reviewed checkout (including deliberately staged changes), from the
repository root:

```sh
python3 scripts/verify_fresh_checkout.py --output /tmp/orbitiq-e3-new-checkout
```

The output must not exist. The script exports **only the Git index**, identifies
its tree hash, creates new `.venv` and `node_modules` directories, installs with
both lockfiles, builds the frontend, and configures from the tracked example.
Unstaged edits and untracked files are intentionally absent; inspect `git diff`
and `git diff --cached` to know which candidate is being verified. In CI the
index is the exact checked-out commit. The script retains fixture-only logs and
a summary, so failures return nonzero with actionable stage logs.

It starts the backend with missing storage and confirms liveness/503 readiness
without file creation; explicitly initializes schema 3; refuses repeat init;
checks no-op migration; starts Vite and verifies its real same-origin API proxy;
loads public **Vallado 6251 test data (NOT LIVE DATA)** using a mocked transport;
checks history/detail/TEME routes; injects network failure; restarts the backend;
retries after a fixture-clock cooldown and verifies deduplication; then runs the
existing full backup/restore rehearsal against that fixture. It stops its service
process groups. It never copies private archives, credentials, attachments or
untracked setup files. Native Windows execution is not verified.

The existing CI backend job runs this same isolated installation after its normal
checks. Existing frontend and release-image jobs retain E1 browser/PDF, E2
accessibility and deliberate expected-failure probes. CI uploads only smoke logs,
summary and fixture recovery manifest, not dependencies, databases or private data.
Local E1/E2 execution still uses the documented
[existing container runner](engineering-e1-browser-pdf-ci.md).

## Boundaries

Phase 11.3.1 remains **PARTIAL**; scientific evaluation remains **BLOCKED**.
ESA time, KIN-quality and frame-alignment clarification remain unresolved.
Historical availability, full fitting lineage and statistical independence are
not established. E3 produces no genuine Swarm-A propagation or qualified residuals.

Public HTTPS/hosting, independently stored backups and demonstrated off-machine
recovery, real monitoring/alert delivery, release-specific CI and repository
protection remain separate [production gates](phase-8-closure-checklist.md).
No production deployment, merge, domain or protection change is authorized by E3.
