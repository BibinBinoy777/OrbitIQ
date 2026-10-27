# OrbitIQ V1 — owner acceptance

**Authorized publication checkpoint — 27 October 2026:** the owner authorized
committing and pushing the reviewed nine-file Windows compatibility patch to
`publication/windows-compatibility-2026-10-27`, then checking its exact-commit CI.
The reported native Windows17 pass and four matching source backups are recorded
in the publication addendum below. Earlier local/pending statements remain dated
checkpoints. New remote CI is **PENDING**, not a reported pass. No merge or
production deployment is authorized.

**Windows final review — 26 October 2026:** the owner reports **17 native Windows
tests passed in 7.09 seconds**, with zero failures/skips. See the
[final-review addendum](#windows-final-review--26-october-2026).
Windows browser workflows remain unverified and the new CI job has not run.
Earlier dated checkpoints and acceptance remain preserved.

**Publication review — 26 October 2026:** the owner authorized publishing this
verified documentation on `publication/v1-verified-docs-2026-10-26`. Earlier
"local/unpublished" statements describe their dated verification checkpoints.
The publication commit and its remote CI must be verified separately; no new CI
success is asserted by this pre-publication snapshot. Scientific validation and
production readiness remain **NO-GO**; no deployment is authorized.

**Status: ACCEPTED_FOR_INTENDED_LOCAL_USE.** Owner acceptance date:
**2026-10-25 (Asia/Calcutta)**. No precise acceptance time was supplied or recorded.
Target decision: **31 October 2026, Asia/Calcutta**.

The owner explicitly confirmed in this conversation:

> Yes, I am satisfied with this version of OrbitIQ for its intended local use.

Acceptance covers **the current OrbitIQ version for its intended local use**.
It does not establish individual technical checklist outcomes, browser/OS/device
observations or acceptance of outstanding engineering limitations. All six items
below remain unchecked because no item-specific results were supplied.

Local engineering is **GO_FOR_INTENDED_LOCAL_USE**, based on exact-current-helper
CI at `8160bcb972c5c1486b2b138008b0cd4d5bd633c4` and the narrowly targeted helper
checks. The authorized CI run passed all three engines and all seven PDFs,
including the offline PDF; local managed-browser restrictions remain unchanged.
This does not mark any of the six manual-review items below passed or establish
physical-device, screen-reader or printer certification. Public hosting, HTTPS,
off-machine backups, real alert delivery and release-control enforcement remain
open. Scientific validation and production readiness remain **NO-GO**, with IGS
frame/EOP clarification pending. See the
[latest helper-integration decision](v1-local-release-closure.md#final-helper-integration-decision--25-october-2026)
for evidence and scope. This status update is local documentation, not a new CI run.

See the [owner execution guide](#owner-execution-guide) for numbered steps,
expected outcomes and an evidence/defect record. No manual result is filled in.

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

## Owner execution guide

**Instructions, not completed observations.** Retain the exact six criteria above.
Record substeps as `PASS`, `FAIL`, `BLOCKED` or `NOT_RUN`; leave an item unchecked
while its required observations are incomplete. Overall acceptance supplies none
of those individual results.

**Setup:** use [Safe local launch](#safe-local-launch) on the intended computer,
with Python 3.12, uv 0.12.23, Node 24 and npm 11. Examples use Bash (an existing
approved WSL/Bash setup on Windows); use the appropriate installed-shell syntax.
After `uv sync --locked`, activate that checkout's environment with
`source .venv/bin/activate` in Bash. `/workspace` paths apply only to this cloud
workspace. Choose an ordinary review browser profile, not private/incognito mode.

Keep the same profile, exact origin **`http://127.0.0.1:5173`** and fixture across
restarts. `localhost`, another port or profile has separate browser saves. If Vite
cannot bind 5173, resolve/select one consistent address first. Never clear site data
to test persistence. For review across reboots, initially choose a new persistent
absolute fixture directory and substitute it consistently; `/tmp` is not a backup.

Use only **E1 SYNTHETIC UI FIXTURE - NOT OBSERVED HISTORY**, catalog **6251**, IDs
**1 and 2**. An unexpected source/count means stop and record setup differences.
The core path uses snapshot metadata/element history; no blocked research comparison
is needed. Optional calculated views must stay within this synthetic fixture and
its displayed epochs. Do not collect, configure an observation archive, select
private G05/G30/Swarm inputs, reseed existing storage or alter scientific policy.

Record the actual review date/timezone, implementation identity, observer's local
identifier, OS/device, browser/version/profile, screen size/zoom, application origin,
explicit synthetic DB path and fixture receipt/source IDs/epochs/hashes. Record
assistive technology or `NOT_RUN`. Keep sanitized screenshots, exports and logs
locally; omit credentials, personal paths and private notes before sharing excerpts.
Each item below needs an observed outcome plus an evidence path, not an automated
pass or download-request notification alone.

### 1. Startup and primary workflows

**State:** locked setup, explicit synthetic archive and both local servers running.

1. Open the app and `http://127.0.0.1:5173/api/health`, `/api/ready`, `/api/snapshots`
   through the same address. Check health `status: ok`, readiness `status: ready`
   and the two synthetic catalog-6251 records.
2. Choose **Discovery & history**, enter **6251** in **Name, NORAD ID or international
   identifier**, choose **Search stored records → Inspect snapshot #1**, and inspect
   its name, ID, epoch, retrieval and hash.
3. Open **Scientific-data readiness**, read actual statuses, then return to the
   explorer. Inspect the globe or explanatory fallback. Use Tab/Shift+Tab and
   Enter/Space to reach navigation and source controls on the intended device.

**Expected:** source identity stays explicit, text is readable, controls have visible
focus and globe/fallback is understandable. Old synthetic epochs can be stale;
backend connectivity does not establish scientific readiness or require green cards.
**Pass evidence:** endpoint outcomes, source/readiness screenshot and actual keyboard/
globe observations. **On failure/block:** URL/control, message/status, loading or
fallback behavior and retry outcome; do not initialize another DB or bypass policy.

### 2. Investigations and history

**State:** item 1's source open; ordinary review profile/storage and origin retained.

1. In the snapshot’s **Keep this investigation** controls, enter **V1 owner review** as
   **Investigation title**, add a harmless synthetic **Private local notes (optional)**
   value, then **Save in this browser**. Wait for confirmation. In **Saved
   investigations**, record the card's title, note and source parameters, then
   **Open V1 owner review**.
2. Close the tab/browser and stop only the review servers with Ctrl+C. Restart the
   identical commands/address and archive. In the same profile choose **Saved
   investigations → Refresh local saves**, compare the card, then reopen it. Do not
   clear site data or reseed.
3. Use the card's **Copy share link** and open it in another local tab. If clipboard
   permission is denied, use **Select link for manual copying** and the displayed URL.
4. Under **Discovery & history → Historical analysis**, set **Historical satellite
   NORAD ID** to **6251**, then **Analyze archived history**. Inspect both source
   points and limitations. Repeat with **6252** for an empty stored-history case.
5. Keep the valid share link. In one copied URL change `snapshot=1` to
   `snapshot=999999`; in another alter one hex character of `sha` without changing
   its length. Observe missing/mismatched-source refusal, then return to the valid
   link. Change only copied URLs, never an archive or saved record. Item 3 covers import.

**Expected:** saved title/note/inputs survive restart; reopening verifies the exact
epoch/retrieval/hash. Calculations, if requested, are recomputed, not frozen old
outputs. Missing/mismatched sources get no silent replacement. Empty local history
is not proof of absence from orbit. A share link transfers parameters, not the saved
list, source archive, title or notes; deleting a local save does not revoke it.
**Pass evidence:** before/after card fields, restored identity and actual history/
error/share observations. **On failure/block:** profile/origin, differing field, exact
message and reproducible steps; preserve saves and record clipboard restrictions.

### 3. Report/export

**State:** saved synthetic source available; local downloads/printing permitted or
restrictions can be recorded.

1. Choose **Export portable bundle for V1 owner review**. Leave **Include private
   local notes for V1 owner review** off and inspect the JSON's omitted/empty note.
   For recovery of the harmless synthetic note, explicitly enable that option and
   export a second file; record which file includes it. Never include private notes.
2. Preserve the original profile/save. In a separate ordinary test profile at the
   same address choose **Saved investigations → Portable investigation file** and
   select the bundle. Inspect **Preview portable investigation → Confirm local
   import**, compare title/parameters/expected notes, then reopen the exact source.
   Cancel a collision or explicitly import a separate copy; never overwrite silently.
   Reimporting an identical record should not add a duplicate.
3. Back in the original card choose **Generate investigation report** once. From that
   capture use **Download JSON evidence**, **Download printable HTML**, then **Open
   printable report → Print report / Save as PDF**. Inspect the actual files.
4. Compare the same capture's report ID/time, source IDs/hashes, epochs, retrievals,
   seven sections and limitations. Inspect page breaks/counters and Escape/dialog
   focus. If permitted, open/print the downloaded HTML offline; a managed `file:`
   refusal is **BLOCKED**, not an owner pass. Do not bypass it.

| State/file           | Preserves                                                                                                 | Does not provide                                                                                     |
| -------------------- | --------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Browser save         | Local title, note and reconstruction inputs in that profile/origin.                                       | Durable backup, cloud sync or frozen calculations.                                                   |
| Portable JSON        | Title/inputs; notes only by opt-in; local import supports bundles up to 16 KiB.                           | Orbital records/results, authenticity or confidentiality; matching source archive remains necessary. |
| Report JSON/HTML/PDF | Captured evidence, clocks, sources, requested results and limitations; browser-only title/notes excluded. | A portable restore file, database backup or independent scientific accuracy.                         |
| Share link           | Reconstruction parameters for accessible source records.                                                  | Source-data transfer, browser-list transfer or revocable cloud sharing.                              |

**Expected:** files exist, are readable and agree within one capture. Regenerating a
report later can change its ID/time; PDF appearance can vary. Notes follow the
recorded portable opt-in and remain excluded from reports.
**Pass evidence:** sanitized files/sizes or hashes, report/source identities, inspected
fields, import/reopen result and representative print pages. Record offline results
separately. **On failure/block:** export/capture ID, exact step and permission/message;
never use report JSON as a portable restore or assume a requested download completed.

### 4. Errors and recovery

**State:** saved investigation and portable file intact; explicit synthetic DB only.

1. Stop only the API with Ctrl+C, leaving the frontend open. Reopen the saved
   investigation or request source detail; record the service error.
2. Restart the identical API command and choose **Retry reconstruction / recompute**
   (or **Retry source detail**). Confirm the same inputs and two fixture records.
3. Read the [backup/restore runbook](backup-restore-runbook.md); identify the source,
   new backup and different new restore target. Portable JSON does not contain the DB.
   If actually rehearsing, use the command below with the explicit synthetic source
   and a nonexistent destination. Inspect its actual `verification.json`; a runbook
   review alone must be recorded **reviewed; recovery NOT_RUN**.

```bash
env ORBITIQ_DATABASE_PATH=/tmp/orbitiq-owner-review/archive.sqlite3 \
  PYTHONPATH=backend python -m orbitiq.maintenance.recovery \
  --directory /tmp/orbitiq-owner-recovery
```

Substitute the actual synthetic path if different. If the destination exists, choose
a new one; do not delete another folder or overwrite an archive. A local synthetic
rehearsal is not off-machine real-data protection; temporary files are not backups.
**Expected:** understandable failure, explicit retry, preserved inputs and no restore
over an existing target. **Pass evidence:** failure/recovery messages and source fields;
actual recovery receipt only if executed. **On failure/block:** stopped server,
restart command/path, error, repeatability and diagnostic receipt; preserve evidence.

### 5. Limits and accessibility

**State:** synthetic source/history/save/report views ready; device, zoom and any
assistive technology recorded.

1. With keyboard only traverse navigation, search, inspect, save/reopen, portable file
   selection and report/dialog controls. Use Tab/Shift+Tab, Enter/Space, Escape and
   native arrow keys as appropriate. Record unreachable controls or lost focus.
2. Inspect normal/increased zoom on the intended screen: readable text, labels,
   visible focus, logical order, understandable errors and no lost essential controls.
   If a screen reader is used, record its actual headings/labels/status/dialog output;
   otherwise record **NOT_RUN**. Automated axe/viewport tests are not human evidence.
3. Read source-age, provenance and report limitations: calculated positions are not
   observations; old synthetic data is not fresh; uncertainty/independence remain
   explicit. No qualified real residual, maneuver/anomaly/collision claim follows.

**Expected:** representative actions work without a mouse and limitations/fallbacks
are understandable. **Pass evidence:** actual keys/focus, zoom/screen and safe excerpts;
screen-reader observations only if performed. **On failure/block:** exact control,
sequence, expected/actual announcement or overflow, and impact on task completion.

### 6. Deployment/data expectations

**State:** loopback services and synthetic storage; four separate decisions retained.

1. Compare those statuses with the [latest closure decision](v1-local-release-closure.md#final-helper-integration-decision--25-october-2026).
   Record intended local scope; overall owner acceptance need not be supplied again.
2. Using the export table, record where permitted review files will be kept locally.
   Browser saves and `/tmp` are not independent backups. Do not upload private data.
3. Record hosting/HTTPS, durable storage, off-machine recovery, real alerts and
   branch/required-check controls as open production work; no configuration here.
4. Record scientific NO-GO and pending IGS frame/EOP clarification; software tests
   and local acceptance do not qualify the research comparison.

**Expected:** intended-local-use acceptance/engineering GO stay separate from
scientific/production NO-GO. **Pass evidence:** owner's actual scope/retention/open-gate
understanding. **On failure/ambiguity:** quote the confusing screen/doc and practical
misunderstanding; never record an untested infrastructure control as successful.

## Reproducible defect record

**Blank template, not a reported defect.** Fill only after an actual observation,
reproducible failure or concrete implementation finding. Keep evidence sanitized/local.

```text
Issue ID / short description: <assign only when observed>
Actual date/timezone; review ID/observer: <actual>
Implementation; browser/version/profile; OS/device; origin/zoom: <actual>
State/prerequisites: <view, synthetic source IDs, saved state>
Reproduction:
1. <exact action>
2. <next action, input or key sequence>
3. <where the discrepancy appears>
Expected result: <existing criterion/documented behavior>
Actual result: <observed, not inferred>
Severity and practical impact: <blocking local work | major | minor | cosmetic; why>
Exact error / sanitized log, screenshot or file reference: <safe excerpt/path>
Repeatable: <attempts/outcomes or UNKNOWN>
Recovery/workaround tried: <actual; no policy bypass or overwrite>
Proposed fix: <supported cause or NOT YET DETERMINED>
Focused regression test: <affected behavior or NOT YET DETERMINED>
Post-fix command/result: <actual or NOT_RUN>
```

Prioritize observed data loss, silent source substitution or inaccessible essential
controls. Distinguish environment/policy blocks and expected stale-data warnings
from product defects. Stop potential data-loss reproductions and preserve evidence.
Fix only a supported cause, then run focused affected checks. The blank template
creates no issue and all six original items still await owner observations.

See [closure and separate decisions](v1-local-release-closure.md) and
[recorded verification evidence](v1-local-release-evidence.json).

## Owner checklist acceptance — 26 October 2026

The owner explicitly confirmed in this conversation:

> i accept `user-acceptance-checklist.md`.

This refers to this existing `docs/v1-user-acceptance-checklist.md` and records
acceptance of the checklist for the current OrbitIQ version's **intended local
use**. Acceptance date: **2026-10-26 (Asia/Calcutta)**; no precise time was supplied.
It supplements the original local-use acceptance dated 2026-10-25, which remains
preserved above.

**Owner checklist acceptance: ACCEPTED_FOR_INTENDED_LOCAL_USE.** No individual
workflow results, browser/OS/device details, recovery observations or limitation
waiver accompanied this confirmation. The six manual criteria remain unchecked
and their observations remain unreported. The execution guide remains available
for recording any later observations; acceptance alone is not technical pass evidence.

Local engineering remains **GO_FOR_INTENDED_LOCAL_USE** on its existing evidence.
Scientific validation remains **BLOCKED — NO-GO**, with IGS clarification pending;
production readiness remains **NO-GO** and E4 **OPEN**. Public hosting/HTTPS,
independent backup/recovery, actual alert delivery and release-control enforcement
remain unverified. Local managed-browser restrictions and unreported human-device/
screen-reader outcomes remain documented; earlier authorized automated browser/PDF
results are retained, not rerun by this acceptance update.

This is a local, unpublished documentation update. It authorizes no scientific
comparison, publication, deployment or infrastructure change. See the
[closure addendum](v1-local-release-closure.md#owner-checklist-acceptance--26-october-2026)
and [evidence ledger](v1-local-release-evidence.json).

## Agent-executed local checks — 26 October 2026

At the owner's request, the assistant executed the available local checks using
only the existing explicitly synthetic catalog-6251 archive, snapshots 1 and 2.
These are **agent-executed observations**, separate from the owner's acceptance
and from owner-device or assistive-technology observations. The six original
checkboxes remain unchanged; the following table records the new evidence.

| Checklist area                      | Agent-executed result                                                                                                                               | Remaining scope                                                                                           |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Startup and navigation              | PASS within local automated scope: health/readiness, discovery, actual globe and keyboard workflows                                                 | Owner's intended physical device not tested                                                               |
| Investigations and history          | PASS within local automated scope: save/share, exact-source reopen, history, portable round trips and persistence across browser/service restarts   | Owner's ordinary browser/profile not tested                                                               |
| Reports and exports                 | PARTIAL: JSON/HTML capture assertions and six PDF content/pagination checks passed                                                                  | Standalone offline HTML/seventh PDF blocked by administrator policy; physical printer not tested          |
| Errors and recovery                 | PASS within local synthetic scope: actual backend stop, error, explicit retry, unchanged saves; separate backup/restore and existing-target refusal | Off-machine/production recovery not tested                                                                |
| Accessibility and scientific limits | PARTIAL: 23 checks passed; zero axe violations across six views; responsive layouts at 320, 390, 768 and 1440 pixels                                | Some contrast checks remain incomplete; screen reader, physical device and actual browser zoom not tested |
| Deployment and data expectations    | PARTIAL: documentation/disclosure boundaries reviewed and retained                                                                                  | Owner understanding and production controls cannot be established by this automated run                   |

See the [execution report](v1-local-release-closure.md#agent-executed-local-checklist-verification--26-october-2026)
and [structured evidence](v1-local-release-evidence.json), section
`agent_assisted_review_20261026`, for commands, receipts, limitations and the corrected
test-driver attempt. No blanket manual-checklist pass is claimed. Owner acceptance
and local engineering retain their local-use decisions; scientific validation and
production readiness remain **NO-GO**. This update is local and unpublished.

## Windows compatibility follow-up — 26 October 2026

**Evidence class: OWNER_REPORTED local Windows progress; native automated tests
and new CI execution remain PENDING.** The owner supplied these details in the
follow-up instructions; the assistant has no access to `D:` from the Linux cloud
workspace and did not capture the reported Windows startup/receipt directly.

- Checkout: `D:\OrbitIQ-local-review`, branch
  `publication/v1-verified-docs-2026-10-26`, HEAD
  `c904082f55df8ad133eefffceb5cca73da7287ff` with the local compatibility fix.
- Python 3.12 and locked Python/frontend dependency installation succeeded. The
  earlier captured console transcript independently supports installation and HEAD.
- The owner reports successful `--local-owner --catalog-only` setup, receipt
  `synthetic_only: true`, `validation_fixture_created: false`, catalog **6251**,
  snapshot IDs **1/2**, at
  `D:\OrbitIQ-demo\owner-review-windows-2\archive.sqlite3`.
- Backend startup is owner-reported as `Application startup complete` and
  `Uvicorn running on http://127.0.0.1:8000`. No actual endpoint response, database
  hash, frontend connection result or item-specific browser observation accompanies
  that report. The initial `Errno 9` failure remains a failure in the chronology.

The new `windows-compatibility` job in the existing workflow is prepared to run
**17 focused checks** on `windows-latest`: publication/cleanup/no-overwrite,
backup/restore, and the actual catalog-only CLI receipt and unchanged-source
checks. Those **17 passed in Linux**; the previous **94 Linux passes** remain prior
evidence. Neither result is labelled Windows or remote CI. The workflow is local
and unpublished; no job has run for these additions.

All six original owner checkbox criteria stay unchecked; existing owner acceptance
is retained. Local engineering stays **GO_FOR_INTENDED_LOCAL_USE** within its
recorded scope, with this new compatibility work awaiting native/CI verification.
Scientific study stays **BLOCKED — NO-GO**, Phase 11.3.1 **PARTIAL**, IGS clarification
pending; production readiness **NO-GO**, E4 **OPEN**, public hosting/domain deferred.
See the [compatibility report](windows-local-demo-compatibility.md#windows-regression-prevention-follow-up--26-october-2026)
and [closure addendum](v1-local-release-closure.md#windows-compatibility-and-ci-preparation--26-october-2026).

## Windows final review — 26 October 2026

The owner reports the documented focused command completed on native Windows:
**17 passed, 0 failed, 0 skipped in 7.09 seconds**. This is owner-reported native
execution, separate from the prior **94 Linux passes in 9.93 seconds** and
**17 Linux passes in 5.06 seconds**. No raw Windows test log or JUnit file was
inspected. Owner-reported catalog seeding and backend startup remain separate from
unverified Windows browser workflows, frontend connection and endpoint responses.
No new human-device, accessibility or manual-workflow observation is inferred.

All six original checklist items stay unchecked. Owner acceptance remains
**ACCEPTED_FOR_INTENDED_LOCAL_USE**, local engineering **GO_FOR_INTENDED_LOCAL_USE**
within its existing scope. The new Windows CI job remains **NOT RUN**, and this
patch remains local/unpublished. The Windows working tree, demo hashes and C:
backup size/completeness have not been independently inspected from the cloud.
See the [compatibility review](windows-local-demo-compatibility.md#final-compatibility-review--26-october-2026)
and [closure](v1-local-release-closure.md#windows-final-review-and-owner-test-result--26-october-2026).
Scientific study stays **BLOCKED — NO-GO**, production readiness **NO-GO**,
Phase 11.3.1 **PARTIAL**, IGS clarification pending, E4 **OPEN**.

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
