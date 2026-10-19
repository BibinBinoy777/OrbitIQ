# Phase 7 — Saved investigations and shareable links

Phase 7 meets its 24 acceptance criteria for local implementation and verification.
This does not establish public-launch readiness or observational prediction accuracy.
Work resumed from the existing checkpoint; no Phase 7 feature was recreated or discarded.
Verified branch `main`, HEAD `9d413f093677c572443633e225b2e052de1bc2df`.

## Implementation and architecture

The application has no authentication/account service. Saves therefore use bounded,
versioned browser storage, with validation, exact read-back, stale-edit detection
and same-origin Web Locks where supported. No backend storage service, account
system, endpoint, migration, dependency or lockfile change was introduced.

Integrated saving/sharing with existing discovery details, exact snapshots, TEME
positions, ground tracks with selected timeline sample, and A/B comparisons in
TEME or ITRS. The local list supports open, rename, supported parameter editing,
confirmed deletion and share copying. Existing explorer/discovery contexts remain
mounted across navigation; hidden playback pauses. React-generated heading IDs
keep retained and reconstructed view labels independent.

Version-1 records contain a UUID, title/notes, creation/modification timestamps and
mode-specific inputs. Source references bind snapshot/catalog ID, element epoch,
first retrieval and response hash. The local envelope and each record/state are
validated with strict fields and size/count/text/time/frame bounds. Unknown versions
or corrupt local data are preserved and writes refused. Read-back confirms the
current browser value, not permanent disk retention. There is no cloud sync,
cross-device saved list or server ownership claim.

Versioned parameter-only fragment links reconstruct exact source selections via
existing listing/detail validation, followed by existing scientific services.
Missing/mismatched source metadata or unavailable payloads fail explicitly;
there is no newest-source fallback. Links exclude title, private notes, local UUID,
orbital payloads, calculated vectors, secrets and policy overrides. Shared input
controls are read-only, with an explicit editable-copy action that does not import
or mutate the sender's save. Clipboard feedback reflects actual completion or
an actionable manual-copy fallback. Deleting a local save does not revoke a link.

The [usage and schema guide](saved-investigations.md) specifies every field,
URL parameter, bound, timestamp distinction, fixed units/conventions, persistence
boundary, recovery option and navigation behavior. [Structured evidence](phase-7-integration-results.json)
contains actual command outputs, timestamps, browser runner sources, test origins,
source provenance, preservation hashes and all acceptance decisions.

## Actual automated verification

Baseline before implementation: **582 backend tests**, **180 frontend tests**,
both exit 0. Final: **589 backend tests**, **275 frontend tests across 20 files**,
all passed; 7 backend and 95 frontend tests added. The 68 model/storage tests are
included in the frontend total. No expected failure or skip is counted as a pass.

Commands ran from the repository root, except npm/tsc commands from `frontend`.
Python commands used `UV_CACHE_DIR=/tmp/orbitiq-phase61-uv-cache`; scientific scripts
also used `PYTHONPATH=backend`. Audit outputs went to `/tmp/orbitiq-phase7/`, so no
prior phase artifact was overwritten. Commands, durations and output appear in JSON.

| Command | Actual result | Exit |
| --- | --- | --- |
| `uv run --locked pytest -q` | 589 passed; existing Starlette/httpx deprecation warning | 0 |
| `npm test` | 275 passed, 20 files | 0 |
| `npm test -- src/saved-investigation.test.ts src/investigation-storage.test.ts` | 68 passed; subset of full frontend total | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_scientific_references.py --output /tmp/orbitiq-phase7/verify_scientific_references.json` | 40 passed, 0 failed | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-phase7/verify_earth_fixed_references.json` | 6 passed, 0 failed | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_phase61_science.py --output /tmp/orbitiq-phase7/verify_phase61_science.json` | 32 numerical comparisons passed, 0 failed; observation validation BLOCKED | 0 |
| `PYTHONPATH=backend uv run --locked python scripts/verify_phase611_geodesy.py --output /tmp/orbitiq-phase7/verify_phase611_geodesy.json` | 28/28 independent-reference component cases and 28 separate algebraic round-trips | 0 |
| `uv run --locked ruff check .` | Passed | 0 |
| `uv run --locked ruff format --check .` | 76 files already formatted | 0 |
| `npm run lint` | Passed | 0 |
| `npm run format:check` | Passed after formatting one added test file | 0 |
| `npx --no-install tsc --noEmit` | Passed | 0 |
| `npm run build` | Passed; existing >500-kB renderer-chunk warning, 558.60 kB minified | 0 |

The seven new backend tests verify fixed-ID reconstruction and full archive
preservation, missing-source behavior, POST/PUT/PATCH/DELETE refusal and strict
resource failure without synthetic coordinates. They use isolated reference-only
archives. Frontend tests cover strict schema/URL parsing, corrupt/unavailable/full
storage, read-back failure, count limits, duplicate IDs, stale edits/deletes,
clipboard success/restriction, UI lifecycle, source/time mismatch, cancellation,
read-only reconstruction, selected-sample bounds and retained-view accessibility.
Existing migration, recovery, globe, timeline, discovery and scientific suites pass.
The geodesy audit uses the unchanged frozen GeographicLib reference fixture; the
C++ reference executable was not rebuilt or rerun in Phase 7.

## Genuine-data browser integration

Local Uvicorn on 8066 and Vite on 5196 used the existing configured database;
no ingestion was performed. Chromium **154.0.8037.57**, actual API and software
WebGL2, no mocked API/canvas. The nine-flow browser suite passed before and after
the heading-ID correction. The final run recorded **438 GET requests**, all to the
same local origin, zero page errors and no ingestion/admin operations.
Additional actual position, WebGL and strict-EOP browser checks exited 0.

Existing genuine CelesTrak ISS GP records (not direct observations):

| Source | Epoch UTC | First retrieval UTC | SHA-256 |
| --- | --- | --- | --- |
| #1 / NORAD 25544 | 2026-10-18T11:12:47.040768Z | 2026-10-18T17:14:39.983172Z | `556827b7dc6cbccd0cbc3e40a9e0a0ed2205ad2d2006a8649e16ee8c0c143d4b` |
| #2 / NORAD 25544 | 2026-10-18T18:57:18.892800Z | 2026-10-19T07:58:23.407349Z | `8105d7f3aa846b3c0452a3dd9cbee4a6fe5348ea6d081afbdfc98b86e49fd7cd` |

Verified discovery detail save using keyboard Enter, confirmed local persistence,
real clipboard read-back, navigation context retention, three-point track save at
sample 1, reopen, refresh into read-only link mode, explicit editable copy and
fresh recipient reconstruction. Comparison restored exact sources #1/#2 at
`2026-10-18T18:57:18.892800Z` in ITRS, then a local rename/frame edit reopened as
TEME. Cancelled/confirmed local deletion left the snapshot and shared link usable.
An actual browser-process close/relaunch preserved the same two local saves.

The additional TEME-position workflow calculated from #1 at the same common time,
saved/reopened/reloaded it and restored the link in a fresh mobile browser context.
Its exact source/time/frame matched, notes stayed out of the link, shared controls
were disabled, and recipient storage remained empty. Fixture values were not used
as real orbital data in any of these browser workflows.

Desktop 1440×1000, tablet 820×1180 and mobile 390×844 checks found no horizontal
overflow. Visible track canvases had non-lost WebGL2 contexts at all three widths.
Saved-list and mobile/globe screenshots were inspected. Native labelled controls,
keyboard save and independently associated retained-view headings were checked;
this is not a full assistive-technology or WCAG conformance audit.

Missing #99999, wrong catalog, changed hash, unsupported version and oversized URL
produced explicit errors without substitution. Invalid version/oversize caused no
snapshot requests. With a separate local backend restart under
`ORBITIQ_EOP_POLICY=measured_only`, the actual archived track request returned
**422 `eop_prediction_disallowed`**, displayed “Policy requires measured
Earth-orientation data”, and exposed no track samples. No resource bypass was added.
Both owned development servers were stopped after verification.

## Investigation of failures

One added test file initially failed Prettier; formatting and the complete frontend
checks subsequently passed. Final accessibility review found duplicate static
heading IDs when original/restored views coexisted; `useId`, a new regression test,
and repeated real browser workflows resolved this. Initial browser runner failures
were exact-label lookup and incorrect expected strict-EOP wording/status; assertions
were corrected to the established contract, without changing product policy.
An initial backend fixture omitted UTC and was correctly rejected; its isolated
input was corrected. An initial preservation command used global Python without
sgp4; repeating with locked project Python succeeded. These superseded outcomes
are disclosed in the JSON; no failed check is represented as a pass.

## Preservation and execution boundaries

Main database SHA-256 before and after:
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Full fingerprints match: schema 3, two snapshots, one ingestion-attempt row,
one insertion-ledger row and one collection-gate row, including original payloads,
triggers and schema. Integrity and foreign-key checks are OK. No initialization,
reset, migration or normal-archive fixture insertion occurred.

All pre-existing reports, including Phase 6, 6.1 and 6.1.1, retain their hashes.
All backend production/scientific code, numerical fixtures, audit scripts,
dependency declarations, lockfiles and CI workflow remain unchanged. HEAD,
branch, remotes and staging remain unchanged. No commit, push, deployment,
publication, remote workflow dispatch or rerun was performed. No cloud environment
configuration change was needed; existing locked installation/startup commands remain valid.

## Acceptance criteria

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Existing architecture and persistence capabilities inspected | PASS | Existing React navigation, read-only API, schema-3 archive, CLI-only ingestion and absence of auth inspected; baseline recorded. |
| 2 | Versioned investigation schema documented and validated | PASS | saved-investigations.md; strict version-1 model, local envelope and URL validators; 68 model/storage tests. |
| 3 | Saved investigations preserve exact snapshot and satellite context | PASS | Both source references bind snapshot/catalog/epoch/retrieval/hash; resolver and genuine archive checks reject differences. |
| 4 | Users can save and reopen supported investigations | PASS | Real browser snapshot, position, track/sample and A/B comparison save/open workflows passed. |
| 5 | Persistence guarantees match the implemented storage mechanism | PASS | Validated browser-local writes with exact read-back; reload and actual browser-process restart passed; retention limits disclosed. |
| 6 | Shareable links reconstruct the intended investigation | PASS | Actual application fragment route reconstructs all four modes against genuine archive records. |
| 7 | Links contain only bounded, necessary state | PASS | 2048-character URL, known unique mode-specific keys; excludes title/notes/local identity/payloads/numerical results. |
| 8 | Missing historical records are disclosed without silent substitution | PASS | Real browser missing snapshot, wrong catalog and changed hash fail explicitly; exact-ID resolver never searches latest. |
| 9 | Shared investigations are read-only | PASS | Shared definition controls disabled and local mutation controls absent; temporary camera/timeline navigation and explicit editable copy only. |
| 10 | Authentication and authorization follow the existing architecture | PASS | No auth exists; no improvised identity system or anonymous permanent server storage API introduced. |
| 11 | Unsupported claims of cross-device or cloud persistence are avoided | PASS | UI and guide identify browser/origin-local saves and parameter links; recipients import no local records automatically. |
| 12 | URL state and persisted investigation records are validated | PASS | Strict schema, size/text/identifier/time/frame/count validation, corrupt-store preservation, duplicate/irrelevant-key rejection tested. |
| 13 | Evaluation time, coordinate frame, units, and provenance are preserved where relevant | PASS | UTC microseconds and exact source metadata retained; TEME/ITRS and existing fixed km/km/s, WGS84 conventions displayed; actual selected sample/common time restored. |
| 14 | Existing propagation and transformation services are reused | PASS | Existing position, ground-track and comparison APIs/components reused; no production backend or scientific algorithm changed. |
| 15 | The application distinguishes restored inputs from guaranteed historical numerical output | PASS | Restored-view notice explicitly describes current-resource recomputation and no stored or guaranteed original numerical outputs. |
| 16 | Local saves and shareable links are clearly distinguished | PASS | Visible browser-local/non-sync labels, read-only link banner, manual clipboard fallback and no auto-import. |
| 17 | Responsive and accessible interactions work | PASS | Chromium desktop/tablet/mobile workflows, keyboard Enter save, labelled native controls and unique retained-view heading IDs checked; scope is not a full accessibility audit. |
| 18 | Existing snapshots and ingestion audit records remain intact | PASS | Database bytes and full schema/table fingerprints match baseline; all pre-existing reports unchanged. |
| 19 | Applicable security and migration tests pass | PASS | Seven new restoration/read-only backend tests passed in full suite; existing migration/recovery tests passed. No migration or capability-token service applicable. |
| 20 | New backend and frontend tests pass | PASS | 7 new backend and 95 additional frontend tests passed; full totals 589 backend and 275 frontend. |
| 21 | Existing scientific regression checks pass | PASS | 40 SGP4, 6 terrestrial, 32 expanded comparisons, 28 geodetic components and 28 separate round-trips passed with unchanged fixtures/thresholds. |
| 22 | Lint, formatting, TypeScript, and production build checks pass | PASS | Final Ruff check/format, ESLint, Prettier, tsc and Vite production build exit 0; warning retained. |
| 23 | No unresolved regression is hidden | PASS | Resolved formatting/a11y issues and harness corrections disclosed; no unresolved defect found in executed scope; limits and warnings remain visible. |
| 24 | Documentation accurately records the implementation and its limitations | PASS | Schema/usage guide, this phase report and command-derived structured evidence distinguish real archive workflows from fixtures and numerical references. |

## Changed files

- `README.md`
- `backend/tests/test_phase7_restoration.py`
- `docs/phase-7-integration-results.json`
- `docs/phase-7-report.md`
- `docs/saved-investigations.md`
- `frontend/src/App.tsx`
- `frontend/src/GroundTrack.tsx`
- `frontend/src/InvestigationActions.tsx`
- `frontend/src/InvestigationRestoration.test.tsx`
- `frontend/src/Investigations.tsx`
- `frontend/src/RestoredInvestigation.tsx`
- `frontend/src/SavedInvestigations.test.tsx`
- `frontend/src/SavedInvestigations.tsx`
- `frontend/src/ScientificExplorer.tsx`
- `frontend/src/investigation-storage.test.ts`
- `frontend/src/investigation-storage.ts`
- `frontend/src/restore-investigation.test.ts`
- `frontend/src/restore-investigation.ts`
- `frontend/src/saved-investigation.test.ts`
- `frontend/src/saved-investigation.ts`
- `frontend/src/style.css`
- `frontend/src/test-fixtures/saved-investigations.ts`

## Remaining limitations

- Independent observation-based prediction validation remains BLOCKED: zero independent observations used. Orbital prediction uncertainty remains unquantified; regression agreement is not universal real-world accuracy.
- Persistence is browser-profile/origin local and plaintext. Clearing storage, eviction, private browsing or profile loss can remove saves; no cloud synchronization, account ownership, application export/import or retention guarantee.
- Parameter links require the exact underlying archive records to remain accessible and match hashes/times. The genuine local SQLite archive is ignored by Git and is not distributed by a fresh source checkout.
- Sharing has no token secrecy, expiry or revocation. Deleting a local record does not revoke links. Anyone with parameters and archive access can reconstruct them.
- Original calculated outputs and EOP versions are not stored. Recomputations use current resources and strict backend limits; original byte-identical results are not guaranteed.
- Camera/zoom and playback state are not serialized; selected aligned track sample and sampling parameters are restored. Shared camera/timeline navigation is temporary.
- Web Locks serialize cooperating same-origin tabs where available; fallback browsers have no cross-tab atomicity guarantee.
- Chromium with software WebGL2 was tested at three viewport sizes; no Safari/Firefox, physical mobile GPU, formal screen-reader/conformance audit, public deployment or remote CI result is claimed.
- Existing Vite renderer chunk exceeds 500 kB (558.60 kB minified); existing Starlette/httpx test-client deprecation warning remains. No dependencies changed.
- No new authenticated/public-hosting protection is provided. Production hosting, persistent archive deployment and public launch controls remain separate work.

All 24 Phase 7 implementation criteria pass within this verified local scope.
Observation-based prediction validation remains **BLOCKED**, and orbital prediction
uncertainty remains unquantified. No universal real-world prediction accuracy is claimed.
