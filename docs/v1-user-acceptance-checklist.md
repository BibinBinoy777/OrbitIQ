# OrbitIQ V1 — owner acceptance

**Status: ACCEPTED_FOR_INTENDED_LOCAL_USE.** Owner acceptance date:
**2026-10-25 (Asia/Calcutta)**. No precise acceptance time was supplied or recorded.
Target decision: **31 October 2026, Asia/Calcutta**.

The owner explicitly confirmed in this conversation:

> Yes, I am satisfied with this version of OrbitIQ for its intended local use.

Acceptance covers **the current OrbitIQ version for its intended local use**.
It does not establish individual technical checklist outcomes, browser/OS/device
observations or acceptance of outstanding engineering limitations. All six items
below remain unchecked because no item-specific results were supplied.

Local engineering retains **CONDITIONAL GO**. The seventh offline PDF remains
blocked by the recorded browser administrator restriction, and full
Chromium/Firefox/WebKit coverage remains incomplete. Public hosting, HTTPS,
off-machine backups, real alert delivery and release-control enforcement remain
unverified. Scientific validation and production readiness remain **NO-GO**;
the IGS frame/EOP clarification remains pending. See the
[owner-acceptance addendum](v1-local-release-closure.md#owner-acceptance-addendum--25-october-2026)
for the separate completion decisions.

## Safe local launch

Use the documented [locked development setup](../README.md) in a checkout with
Python dependencies installed and frontend `npm ci` completed. The local fixture
mode below always uses the bundled public-reference-derived synthetic test input;
it does not accept a research-file override. Pick a new absolute directory. For
example, in a project-root terminal with the Python environment activated:

```bash
mkdir -m 700 /tmp/orbitiq-owner-review
PYTHONPATH=backend python scripts/seed_browser_fixtures.py \
  --directory /tmp/orbitiq-owner-review --local-owner
```

Creation refuses a symlink, relative target or nonempty directory; do not delete
an existing directory to make this command pass. Choose a new path instead.
The receipt must say `synthetic_only: true`, catalog **6251**, and name exactly
`/tmp/orbitiq-owner-review/archive.sqlite3`. It contains two explicitly synthetic
snapshots, IDs 1 and 2. The database is read-only; do not point collection or
migration commands at it. Local mode retains current-user ownership; the existing
container seed behavior remains unchanged.

Start the API from the project root, explicitly selecting that archive:

```bash
env -u ORBITIQ_VALIDATION_ARCHIVE \
  ORBITIQ_ENVIRONMENT=development \
  ORBITIQ_DATABASE_PATH=/tmp/orbitiq-owner-review/archive.sqlite3 \
  ORBITIQ_ALLOWED_HOSTS=127.0.0.1,localhost \
  PYTHONPATH=backend python -m uvicorn orbitiq.main:app \
  --app-dir backend --host 127.0.0.1 --port 8000
```

In a second terminal, from `frontend/`:

```bash
ORBITIQ_BACKEND_URL=http://127.0.0.1:8000 npm run dev
```

Open `http://127.0.0.1:5173`. Check `/api/ready` is ready and `/api/snapshots`
shows exactly two catalog-6251 records named **E1 SYNTHETIC UI FIXTURE - NOT
OBSERVED HISTORY**. Search that catalog, inspect IDs 1 and 2, use their displayed
element epochs, then save/reopen/share and export JSON/HTML/PDF. The observation
archive is deliberately not configured; no real observations or research data
are being accepted through this setup.

For safe failure/recovery, stop only this API with Ctrl+C, reload the UI and check
the actionable error, then restart the identical command and retry. Confirm both
fixture records remain. Finish by stopping the two development servers. Public
interfaces or port forwarding are not configured by these commands. Review the
[backup/recovery runbook](backup-restore-runbook.md) separately; restore only to
a new target, never over an existing archive.

Prepared workspace archive: `/tmp/orbitiq-v1-owner/acceptance/archive.sqlite3`.
Its receipt is `/tmp/orbitiq-v1-owner/acceptance-receipt.json`. A loopback API smoke
check verified health/readiness and the two synthetic records, then stopped the
service and verified the DB hash unchanged. That smoke check was preparation;
owner acceptance is recorded separately above. For that prepared archive substitute
its exact path in the API command; use a matching installed frontend checkout. On a fresh owner machine,
create the separate archive using the commands above.

In this workspace, activate the existing Python environment with
`source /workspace/OrbitIQ/.venv/bin/activate`, then use the API command from
`/workspace/OrbitIQ-e82` with the prepared archive path. The installed, hash-matched
frontend is `/tmp/orbitiq-v1-closure/fresh-checkout/checkout/frontend`; run the
frontend command there. These temporary workspace paths are not portable backups
or a substitute for the locked fresh-machine setup.

## Six-item owner review

Use a separate, explicitly synthetic acceptance archive. Preserve the real database
and research inputs. Record browser/OS/device, date, outcome and any reproducible
failure; do not put credentials or private research in screenshots or reports.

- [ ] **Startup and primary workflows:** start using the documented explicit DB
      configuration; health/readiness make sense; stored-catalog discovery and globe/
      fallback navigation work. Check keyboard use and an actual intended device.
- [ ] **Investigations and history:** select exact fixture sources, navigate
      history, save/reopen/share and import/export an investigation. Confirm empty,
      stale, missing-source and mismatched-source states are understandable.
- [ ] **Report/export:** inspect downloaded JSON, printable HTML and PDFs for
      correct source IDs/hashes, timestamps, sections, limitations and readable page
      breaks. The offline HTML and seventh offline PDF need an authorized browser
      permitting that workflow; a managed-policy block is not a pass.
- [ ] **Errors and recovery:** observe a safe failure and explicit retry; restart
      preserves fixture history. Review the documented backup/restore procedure and
      confirm restoration uses a new target rather than overwriting an archive.
- [ ] **Limits and accessibility:** calculated positions are not observations;
      uncertainty/validation limits and scientific NO-GO are understood. Review focus,
      labels, readability and screen-reader behavior; automated viewport/axe checks
      do not establish human or physical-device acceptance.
- [ ] **Deployment/data expectations:** confirm the intended local V1 scope.
      Public hosting, HTTPS, independent backup, real alert delivery and release
      controls remain separate open gates. Private data stays local unless a specific
      destination is approved. Scientific comparison is not enabled by acceptance.

The owner's scope acceptance is recorded above. Individual checklist outcomes,
including browser/OS/device observations, were not supplied and remain unverified.
Acceptance does not mark any item passed or formally waive the outstanding
engineering gates. Neither the deadline nor an automated pass supplies that proof.

See [closure and separate decisions](v1-local-release-closure.md) and
[recorded verification evidence](v1-local-release-evidence.json).
