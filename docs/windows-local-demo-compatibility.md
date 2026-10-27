# Windows local demo compatibility — 26 October 2026

**Authorized publication checkpoint — 27 October 2026:** the owner authorized
committing and pushing the reviewed nine-file Windows compatibility patch to
`publication/windows-compatibility-2026-10-27`, then checking its exact-commit CI.
The reported native Windows17 pass and four matching source backups are recorded
in the publication addendum below. Earlier local/pending statements remain dated
checkpoints. New remote CI is **PENDING**, not a reported pass. No merge or
production deployment is authorized.

**Final review — 26 October 2026:** the owner reports **17 native Windows tests
passed, 0 failed, 0 skipped in 7.09 seconds**. See the
[final-review addendum](#final-compatibility-review--26-october-2026).
The new Windows CI job has not run; Windows browser workflows remain unverified.
Earlier pending-retry/test statements describe their original checkpoints.

The owner reported native Windows initialization failing at
`os.fsync(completed.fileno())` with `OSError: [Errno 9] Bad file descriptor`.
The source baseline was published commit
`c904082f55df8ad133eefffceb5cca73da7287ff`. Python 3.12.14 and locked Python and
frontend dependencies had installed successfully. The Windows retry of this fix
is **PENDING**; the checks below ran in the Linux cloud workspace.

## Changes and safety scope

- `backend/orbitiq/database.py` reopens only its own completed temporary file in
  **`r+b`** before flushing. Windows requires a writable descriptor. This mode
  preserves existing bytes and does not create or truncate the staging file.
  Validation, mandatory flush, exclusive hard-link publication and cleanup remain
  intact. Flush failure prevents publication; existing destinations remain refused.
- `scripts/seed_browser_fixtures.py` adds explicit **`--catalog-only`**, requiring
  **`--local-owner`**. It creates just the two labelled synthetic catalog-6251
  snapshots in a fresh directory, then marks the archive read-only. The receipt
  states `validation_fixture_created: false` and supplies no validation run ID.
  This mode does not call position calculation, observation validation, protected
  evidence-bundle creation or ownership changes. Those bundles use POSIX file
  operations and are unnecessary for the intended local browser demo.
- The existing full-fixture/default container mode and secure evidence-bundle
  implementation are unchanged. No fallback weakens their filesystem protections.
  The new mode is a snapshot-only demo, not observation-validation evidence.

Keep the failed Windows demo directory intact. Inspect/retry only using a new,
explicit directory; do not silently reseed, delete or repair an existing archive.
No real database, research input or scientific policy is changed by this fix.

## Local verification actually executed

```bash
/workspace/OrbitIQ/.venv/bin/python -m pytest -q \
  backend/tests/test_database_publication.py \
  backend/tests/test_local_catalog_seed.py \
  backend/tests/test_owner_acceptance_seed.py \
  backend/tests/test_foundation.py \
  backend/tests/test_e3_recovery.py \
  backend/tests/test_phase6_collection.py \
  --junitxml=/tmp/orbitiq-windows-local-demo-fix-20261026/targeted-tests.xml
```

**94 passed in 9.93 seconds.** One existing Starlette/httpx deprecation warning
was reported. Targeted Ruff lint, formatting and whitespace checks passed.
The writable-flush regression first failed against the original code with the
same `Errno 9`, using a zero-length write to enforce Windows' descriptor-access
requirement on Linux without changing data. It now passes through initialization,
backup and restore. Other tests cover flush-failure cleanup, preservation,
publication races, recovery, and rejection of catalog-only container use.

The default/full seeder tests still pass. Their existing explicitly synthetic
arithmetic fixtures are not acquired observations or scientific qualification.
No genuine historical GP propagation, real spacecraft transformation, real ERP
interpolation or scientific residual calculation was performed.

An actual fresh catalog-only CLI run produced exactly two synthetic snapshots and
no observation bundle. An in-process API smoke check returned **200** for
`/api/health`, `/api/ready` and `/api/snapshots`; its demo DB bytes stayed unchanged.
The local repair utility was checked against LF and CRLF source copies, repeat
application, and unexpected source edits. It applies only two source-file changes,
checks original/result hashes, retains source backups and refuses unknown contents.
These are local utility checks, not native Windows runtime verification.

## PowerShell retry after applying the reviewed fix

From the existing checkout root, choose a new directory, such as:

```powershell
Set-Location "D:\OrbitIQ-local-review"
$demoPath = "D:\OrbitIQ-demo\owner-review-windows-1"

if (Test-Path $demoPath) {
    throw "Preserve the existing directory and choose a new target."
}

uv run --locked python -c "from pathlib import Path; import sys; Path(sys.argv[1]).mkdir(parents=True, exist_ok=False)" "$demoPath"
```

Only after successful directory creation:

```powershell
$env:PYTHONPATH = "backend"
uv run --locked python scripts\seed_browser_fixtures.py --directory "$demoPath" --local-owner --catalog-only
```

Require a successful exit and `synthetic_only: true`, catalog 6251, IDs 1/2,
`validation_fixture_created: false`, and the exact new archive path. Do not run
initialization again against an existing directory. Configure only that archive
when launching the backend; keep `ORBITIQ_VALIDATION_ARCHIVE` unset. Use the
existing loopback-only backend/Vite instructions, with ports checked first.

## Verification and publication boundary

The previous exact-commit CI results belong to **c904082**, before this source fix.
No new full application suite, frontend/browser/PDF suite or remote CI was run for
this fix. Native Windows setup remains awaiting the owner's actual retry.
The fix, two regression-test files and this report remain **local and unpublished**.
Research inputs/hashes, original database, earlier reports, comparison protocols,
retrospective-admission policy and active EOP policy are preserved. Phase 11.3.1
remains **PARTIAL**, scientific study **BLOCKED — NO-GO**, production readiness
**NO-GO**. No commit, push, deployment or external data upload occurred.

Task-local receipts and the guarded repair utility are under
`/tmp/orbitiq-windows-local-demo-fix-20261026/`; temporary files are not durable
backups or scientific evidence.

## Windows regression-prevention follow-up — 26 October 2026

**Latest status:** the owner reports successful catalog-only seeding and backend
startup. The pre-follow-up pending retry statements above describe their original
checkpoint. Native automated Windows tests and the new Windows CI job remain
**NOT RUN / PENDING**; this task ran only the focused Linux checks.

The owner's reported demo is
`D:\OrbitIQ-demo\owner-review-windows-2\archive.sqlite3`, receipt
`synthetic_only: true`, `validation_fixture_created: false`, catalog **6251**, IDs
**1/2**. Backend startup is reported as `Application startup complete` and
`Uvicorn running on http://127.0.0.1:8000`. These details came from the owner's
instructions, not an original successful startup transcript or independent `D:`
inspection. Initial initialization failure and captured installation/HEAD evidence
are preserved separately. Frontend/browser and endpoint results remain unverified.

The five-file patch was reviewed against **c904082**. Its production/helper code
is unchanged in this follow-up. Focused tests add success-cleanup coverage and an
actual seeder subprocess check with strict receipt, database identity/read-only,
no-overwrite and untouched synthetic-sentinel assertions. The sentinel represents
no real operator data. Existing publication/race/foundation tests are reused.

The existing workflow adds `windows-compatibility` with Windows/PowerShell,
locked uv **0.12.23** and Python **3.12**. It runs the two compatibility files,
foundation tests and only the existing validation-before-publication/publication-
race E3 cases, then uploads JUnit XML only. The release job requires this native
Windows job; existing Linux/frontend/release steps are unchanged.

The exact selection passed **17 tests in 5.06 seconds in Linux**. The earlier
94 Linux passes remain prior evidence. Targeted Ruff, workflow YAML/duplicate-key/
job/dependency invariants, documentation and preservation checks passed. No native
Windows execution was available; no broad suites or remote CI were run. The new
job and all related changes remain local and unpublished.

For an owner-run native check **after these local test/workflow changes are
available in the existing Windows checkout**, run from its root:

```powershell
uv run --locked pytest -q backend/tests/test_database_publication.py backend/tests/test_local_catalog_seed.py backend/tests/test_foundation.py backend/tests/test_e3_recovery.py::test_destination_not_visible_until_validation_completes backend/tests/test_e3_recovery.py::test_publication_race_preserves_other_creators_file
```

The tests create only disposable temporary synthetic files, without requiring
another demo seed or stopping the existing local servers. A command listing here
is not evidence that it ran. Preserve the current Windows checkout and demo DB;
do not reset/reclone to acquire unpublished changes.

See the [V1 closure](v1-local-release-closure.md#windows-compatibility-and-ci-preparation--26-october-2026)
and [owner checklist](v1-user-acceptance-checklist.md#windows-compatibility-follow-up--26-october-2026).
All four decisions and the scientific/production boundaries remain unchanged.

## Final compatibility review — 26 October 2026

The owner reports the documented focused command completed on native Windows:
**17 passed, 0 failed, 0 skipped in 7.09 seconds**. This is
**OWNER_REPORTED_NATIVE_WINDOWS_PASS**, not an assistant-executed Windows run.
No raw terminal log, JUnit file, exact run time or current Windows source hashes
were provided. The earlier **94 Linux passes in 9.93 seconds** and **17 Linux
passes in 5.06 seconds** remain separate historical runs. The owner's successful
synthetic seeding/backend startup remains owner-reported; it establishes no
Windows browser, frontend connection or manual-checklist result. The prepared
`windows-compatibility` job remains **NOT RUN — LOCAL_UNPUBLISHED**.

The complete nine-file cloud patch was reviewed against published **c904082**,
including the three new files omitted by ordinary tracked-file diffs. The
database fix changes only the completed staging-file open mode to non-truncating
`r+b`, retaining validation, flush, atomic no-overwrite `os.link` publication and
`finally` cleanup. The two new test files invoke actual database functions and
both in-process and subprocess seeder entry points; no production implementation
is duplicated. Existing race/validation tests remain selected. No production or
test code changed during this final review, so application tests were not rerun.

Catalog-only mode requires explicit `--local-owner`, creates labelled synthetic
records only, refuses a nonempty target, and exits before position/bundle creation
or `chown`. New files retain ordinary process-user ownership/inherited ACLs;
Windows owner/ACL inspection was not available. The read-only flag is not an ACL
security boundary. The receipt and database checks cover synthetic identity,
IDs, hash, no validation run ID and preservation of a separate synthetic sentinel.

Strict duplicate-key YAML parsing and focused job/dependency checks passed:
Windows runner, PowerShell, Python 3.12, locked dependencies, JUnit-only upload,
read-only permissions and the required Windows-to-release dependency are correct.
There is no `continue-on-error`; PowerShell propagates the pytest exit code and
the release job cannot run successfully after a failed prerequisite. Artifact
upload uses `always()` without clearing test failure. This is static validation;
`actionlint` and actual GitHub execution remain unperformed.

All nine cloud files use LF; existing-file diffs are localized, with no whole-file
line-ending rewrite. The owner reports a clean `git diff --check` with LF-to-CRLF
warnings. Those warnings alone are not whitespace failures; actual Windows
line-ending configuration, new-file hashes and complete status still require a
local inspection. No Git line-ending settings or attributes were changed.

Only the four existing tracking documents were updated to record this evidence.
Cloud preservation checks cover the real database, research inputs/manifests,
protocols, scientific policies and known synthetic demos. The owner's Windows
demo and C: source-backup directory are inaccessible from this cloud workspace:
their current hashes, backup size and completeness remain **UNVERIFIED**. The
updater saves only overwritten existing text files, not a database/research backup;
files already matching the update and newly created files need no preimage copy.
Backup completeness must be assessed against that actual scope, not nine files.
No backup was deleted.

Code/workflow review found no blocking implementation defect. Final Windows
publication sign-off remains conditional on checking the actual working tree and
backup contents locally. All changes remain unpublished; no remote CI, scientific
comparison or deployment was performed. Scientific study stays **BLOCKED — NO-GO**,
production readiness **NO-GO**, Phase 11.3.1 **PARTIAL**, IGS clarification pending.

## Authorized Windows publication checkpoint — 27 October 2026

The owner supplied Windows `git status --short --untracked-files=all`, showing
exactly the six modified and three new reviewed paths, all unstaged, and
`git diff --check` exit **0**. LF-to-CRLF warnings were recorded without a
whitespace failure. These are owner-supplied console results, not direct access
to the Windows filesystem. Native focused tests remain separately recorded as
**17 passed, 0 failed, 0 skipped in 7.09 seconds**, owner-reported; the prior
Linux94 and Linux17 receipts are preserved, not rerun or relabelled.

The updater backup inventory reports **four files / 237,292 bytes**: the previous
workflow and three V1 tracking files. Both raw SHA-256/size and LF-normalized hashes
match the published pre-update contents (the raw files are CRLF). This is consistent
with two already-fixed source files being skipped and three new files having no
preimages. The backup was retained. It is a source/documentation backup, not a
research database backup, off-machine recovery demonstration or a direct C: audit.
Current Windows research/demo hashes and ACLs were not supplied.

Owner screenshots show backend-connected status, both synthetic catalog-6251
snapshots, source-detail display, save confirmation, report-ready status, a
portable JSON download opened in an editor and the matching import preview.
Final import, refresh/reopen persistence and Windows PDF/download-content checks
are not established by these screenshots. No original owner checkbox was marked
passed on this basis.

The owner explicitly authorized committing and pushing exactly the reviewed
nine-file patch on `publication/windows-compatibility-2026-10-27`, followed by
CI verification for the exact commit. Source/tests/workflow remain unchanged by
this documentation checkpoint. New CI must verify **backend**, **frontend**,
**windows-compatibility** and **release-images**. The committed snapshot cannot
contain its own future SHA or CI result; those must be read back and reported
separately. Earlier pending/blocked statements remain historical evidence.

Scientific study stays **BLOCKED — NO-GO**, Phase 11.3.1 **PARTIAL**, IGS
clarification **PENDING**, production readiness **NO-GO**, E4 **OPEN**. Owner
acceptance and scoped local engineering decisions remain unchanged. No real
historical scientific comparison, merge, deployment or private-data upload is
authorized by publication.

## CI runtime correction — 27 October 2026

Initial published commit `d3c12b8d310ebf26ce95447282ecc36b69101750` ran workflow
**40454175340**. Backend (**1,593** tests), frontend (**427**) and native Windows
(**17**) jobs passed. `release-images` failed before browser/PDF execution: the
runner's Python **3.14** rejected the ephemeral synthetic CA for a missing key-usage
extension. That failed run is retained; it is not a release or browser pass.

The release harness had inherited a rolling runner interpreter. OrbitIQ's
`.python-version`, `pyproject.toml` and documented release procedure specify
Python **3.12**. The existing workflow now explicitly selects `.python-version`
for the release job. No SSL verification flag, trust/hostname assertion, API
check, browser flow or scientific calculation was disabled or changed. Python
3.14 support and synthetic-CA qualification under its stricter default are not
claimed. CI for the corrective commit remains **PENDING** at this checkpoint;
all four jobs must be verified for that new exact SHA. Total publication scope
remains the same nine paths. Scientific and production **NO-GO** decisions remain.
