# Controlled EOP maintenance

Resources are installed by the locked **astropy-iers-data** dependency, loaded via
its exported local file paths and cached by the backend process. Maintain this
package lifecycle rather than editing installed files or adding an HTTP refresher.
No ordinary API request acquires resources. No dependency upgrade was applied in
this task; the actual rehearsal used the already locked version twice.

## Operator requirements and trust

Use Python 3.12, the repository's uv workflow, normal verified TLS/proxy trust,
access to official PyPI/package artifacts, and an explicit absolute orbital DB
path. No special user credentials or personal cache are required. `uv` verifies
locked artifact hashes. Only an exact date-style supported astropy-iers-data
version is accepted, never `latest`, ranges, commands or arbitrary URLs.

Use new absolute candidate directories **outside** the active checkout and a
separate protected state directory on durable storage. Parents must already
exist. Candidate environments and receipts are sensitive operational assets:
restrict write permissions, retain them with the source/lock and reference
outputs, and back them up. They contain local paths for operators; the public
API never exposes those paths. Receipts are not signed; this assumes a trusted
operator and filesystem, not hostile writers. Do not run the CLI with greater
privilege than needed. No public administrative API or authentication system is
introduced.

Examples below are a local **rehearsal**, not deployment instructions or a request
to upgrade production. Choose unused paths. `/tmp` is disposable and unsuitable
for retaining real production selections. Run from the repository root:

```sh
export PYTHONPATH=backend
# On read-only-home environments only:
export UV_CACHE_DIR=/tmp/orbitiq-uv-cache
uv run --locked python -m orbitiq.maintenance.eop --help
uv run --locked python -m orbitiq.maintenance.eop prepare \
  --destination /tmp/orbitiq-eop-candidate-a --version 0.2026.10.12.1.3.27
uv run --locked python -m orbitiq.maintenance.eop validate \
  --candidate /tmp/orbitiq-eop-candidate-a
uv run --locked python -m orbitiq.maintenance.eop activate \
  --candidate /tmp/orbitiq-eop-candidate-a --state /tmp/orbitiq-eop-state
uv run --locked python -m orbitiq.maintenance.eop status \
  --state /tmp/orbitiq-eop-state
```

For an intentional future upgrade, choose a reviewed exact supported version and
repeat prepare/validate. Do not change the active lock or environment just because
a newer version exists. If the candidate needs another dependency version, this
CLI rejects it; review that as a separate dependency change.

## Acquisition and provenance

`prepare` exclusively creates the candidate. It copies a whitelist: backend,
scripts, pyproject.toml, uv.lock and .python-version. It excludes Python bytecode
and does not copy the orbital DB, backups, frontend, Git metadata or environment
files. It resolves the one exact package with uv against
`https://pypi.org/simple`, checks that **all other locked package versions are
unchanged**, then runs `uv sync --locked` into a fresh candidate `.venv`.
No active checkout, lock or installed resource is overwritten.

An initial probe must load coherent resources and support current-time operation
under the configured existing scientific policy. Failure leaves an explicit
`acquisition_failed` receipt in the rejected candidate, preserving active files.
Successful `acquisition.json` records UTC start/acquisition times, source index,
requested/installed version, table identity/coverage, EOP and leap SHA-256, lock
SHA-256 and source digest. Cached package artifacts may be reused when their locked
hashes match; successful acquisition does not imply a new dataset version.
Commands use no shell, bounded subprocess timeouts (180 seconds each), 30-second
HTTP timeout and one uv retry. Failed candidates are not retried in place; inspect
and retain their receipts, correct the cause, and use a new destination.

## Validation gate

`validate` rechecks source/lock digests and the installed resource identity,
then requires:

- Parseable bounded EOP/leap files; at least 366 and at most 100,000 EOP rows.
- Finite, unmasked MJD/day, DUT1/seconds and polar-motion/arcseconds columns;
  coherent daily coverage and known B/I/P provenance flags.
- First predicted boundary matching parsed table metadata; coherent leap chronology
  and expiry; strict negative out-of-range UT1 and polar-motion status checks.
- Loading through the actual application context and strict current-time policy,
  plus required historical reference epochs. Prediction/expiry guards are not
  weakened to admit a candidate.
- The **full backend pytest suite** in the candidate environment.
- The existing independent numerical audit scripts: **40 SGP4 cases and 6
  terrestrial/time/geodesy cases**, with explicit expected totals and zero failures.

Successful validation writes an immutable operation receipt and atomic
`validation.json`; failed validation invalidates any earlier latest success.
Activation rejects changed source/lock/resource identity or missing/failed matching
validation. The reference outputs remain with the candidate.

Passing these tests demonstrates the stated implementation/reference agreement,
not observational accuracy, independent certification of all IERS entries or
future validity. A new release may legitimately need review if its historical
values change beyond existing justified tolerances. Investigate such failures;
do not widen tolerances or remove cases to accept it.

## Selection, process handoff and rollback

`activate` means **validated environment selection**, not a deployed-worker update.
It records the candidate's Python/backend paths and matching provenance in an
atomic `active.json`, preserves `previous.json` and immutable before/after audit
records, then re-probes the new selection with strict current-time checks. An
exclusive operation lock serializes selection changes. Activation verification or
bookkeeping failure restores the previous selection and previous history. The
candidate/previous installed files themselves are never replaced or deleted.

The running app keeps its existing Python process and cached resources. An
operator must separately authorize and perform its process restart using the
selected absolute Python and backend paths, with existing explicit DB
configuration, then validate actual HTTP responses. For a **local** smoke check,
read the `python`/`backend` fields from `status` and use those exact paths, e.g.:

```sh
export ORBITIQ_DATABASE_PATH=/absolute/existing/orbitiq.sqlite3
export ORBITIQ_EOP_VERIFICATION_FILE=/tmp/orbitiq-eop-state/active.json
/tmp/orbitiq-eop-candidate-a/.venv/bin/python -m uvicorn orbitiq.main:app \
  --app-dir /tmp/orbitiq-eop-candidate-a/backend --host 127.0.0.1 --port 8042
```

Do not launch root `uv run` expecting it to use the selected environment: it can
sync the root lock instead. Verify liveness and `/api/readiness` on the newly
started process, matching version/hashes and requested epochs, then existing
calculation/track checks. Changing the receipt alone never switches resources.
Receipt matching does not prove all workers use the new environment.

To rehearse rollback, prepare and validate candidate B into another new directory,
activate B with the same state, then:

```sh
uv run --locked python -m orbitiq.maintenance.eop rollback \
  --state /tmp/orbitiq-eop-state
uv run --locked python -m orbitiq.maintenance.eop status \
  --state /tmp/orbitiq-eop-state
```

Rollback verifies and atomically selects the retained previous environment;
post-switch failure restores the current selector. It is idempotent selection
of the recorded previous value, not a toggle. Restore the appropriate worker
process separately and validate actual readiness again. Identity/structural checks
for the **previous** resource do not require that its current-time predictions
are still fresh: otherwise maintenance could become impossible when the old
resource ages. Returning to that resource does not assert current readiness or
relax any calculation guard. A new candidate and its post-selection check still
must pass current-time policy.

The actual local rehearsal acquired A/B at the existing pin, validated both,
selected A then B, rolled back to A, verified the receipt and exercised the selected
API in TestClient without restarting the running server. Fault tests additionally
simulate acquisition, metadata/unit/coverage, reference, activation verification,
atomic replacement and bookkeeping failures. See the [report](pre-phase-5-readiness-report.md)
and [evidence](pre-phase-5-integration-results.json).

## Failure recovery and limits

On failure, inspect the bounded receipts, preserve the previous resource and
investigate. CLI output deliberately omits raw subprocess/registry errors that
might contain credentials; trusted operators can reproduce the failed candidate
command in its isolated directory with normal secure logging. Do not remove a
stale operation lock until verifying that no maintenance operation is running.
Never edit an acquired/validated source tree in place; acquire a new candidate.

Atomic rename and fsync protect individual files, but multi-file state is not a
power-loss transaction and this task does not prove host-loss or distributed
worker recovery. After interruption, inspect immutable before/after history and
actual worker identity before selecting a verified retained environment. Rehearsal
and injected faults prove process-level behavior, not production disaster recovery.
Plan durable releases, monitoring, backup retention, multi-worker handoff and
recovery drills before public launch. Files under `/tmp` must not become the
production persistence strategy. This CLI never migrates, restores or writes the
orbital database; its existing non-destructive backup/restore procedure is separate.
