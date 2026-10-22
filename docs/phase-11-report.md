# Phase 11 — Historical change analysis and explainable findings

Local implementation and verification, **20 October 2026 UTC**. Publication,
remote CI, production deployment and production-infrastructure verification are
separate milestones. No commit, push, publication, deployment, remote workflow,
remote configuration, DNS or infrastructure operation was performed.

See [methodology and operator instructions](historical-analysis-methodology.md)
and [structured actual evidence](phase-11-integration-results.json).

## Baseline and historical coverage

Started with a clean tree on `phase-10-evidence-replay`, HEAD
`be3710dae9f21bae817637d7bfdb87509b3f6a34`. The existing Phase 10/10.1 publication
receipt records its earlier CI results; those were not substituted for this
phase's fresh local checks or queried remotely. Baseline tracked-file hashes,
database bytes and complete schema/table fingerprints were saved before edits.
Fresh baseline suites passed **785 backend** and **307 frontend** tests, exit 0.

All requested reports/artifacts exist: Phase 5, 6 (including integration JSON),
6.1, 6.1.1, 9, 10 and 10.1 (including integration JSON). Reviewed their architecture,
scientific limits, verification and preservation evidence alongside current
storage, identity/deduplication, immutable ledger, indexed history/discovery,
comparison, units, freshness/readiness, SGP4/coordinates/EOP, report/export/replay,
frontend routing/restoration and test implementations. Current code and newly
executed checks are authoritative; old reports remain historical checkpoints.

The archive was enumerated using **one record per page through both pages**, then
all sources passed the existing full stored integrity/provenance checks:

| Snapshot | NORAD | Retrieval (UTC) | Element epoch (UTC) | Insertion |
| --- | --- | --- | --- | --- |
| 1 | 25544, ISS | 2026-10-18 17:14:39.983172 | 2026-10-18 11:12:47.040768 | Unknown legacy timestamp |
| 2 | 25544, ISS | 2026-10-19 07:58:23.407349 | 2026-10-18 18:57:18.892800 | 2026-10-19 07:58:23.415000 UTC |

There are **two genuine snapshots, two distinct payloads, one repeated satellite
identity, zero missing/ambiguous catalog identities**. Both sources are suitable
for pairwise element comparison. The table gives the complete archive's verifiable
retrieval extrema. Retrieval span is **53,023.424177 seconds**, element-epoch
separation **27,871.852032 seconds**. These are different clocks, neither an
independent observation time. No observation-based validation data exist here.

Payload SHA-256 values:

- #1: `556827b7dc6cbccd0cbc3e40a9e0a0ed2205ad2d2006a8649e16ee8c0c143d4b`
- #2: `8105d7f3aa846b3c0452a3dd9cbee4a6fe5348ea6d081afbdfc98b86e49fd7cd`

Both retain the recorded official CelesTrak GP URL. No source request or collection
attempt was made. Acquisition, payload validation, distinct insertion and deduplication
remain separate existing operations; their safeguards were not changed to obtain
additional history. Controlled fixtures were confined to isolated test archives.

## Implemented scope

`GET /api/historical-analysis` uses the existing budgeted indexed listing and shared
comparison helpers, rather than another storage/comparison engine. It validates
and rechecks exact sources, analyzes at most 20 records / 19 adjacent pairs /
200 findings per request, and retains fixed-anchor cursors. API and gateway
calculation admission/rate limits include the new route. All operations are
read-only. No migration, ingestion alteration, scientific algorithm/tolerance,
dependency or lockfile change was needed.

**Discovery & history → Historical analysis** offers a stable NORAD selector,
accessible persisted-point timeline, bounded next/previous navigation, actual
source-element inspection, retrieval/epoch/insertion/provenance/validation details,
within-window intervals and missing-data notices, and selection of two valid
sources for the existing comparison view. Snapshot detail navigation reuses the
existing view. Native controls, labelled regions, visible focus, readable text and
scrollable tables support desktop/tablet/mobile layouts. No fictitious points or
connecting trajectory are drawn.

Inclination (`deg`), eccentricity (`dimensionless`) and mean motion (`rev/day`)
reuse the existing linear second-minus-first calculation. Earlier/later refers to
known unequal retrieval times; reversed epochs, missing/equal/future retrievals,
repeated payloads or invalid/incompatible sources cannot produce directional
changes. No percentages, fits, prediction, anomaly classifier or LLM were added.

The version-1 deterministic rule set covers record counts, partial scope,
incomplete metadata, source validation, existing freshness, unreliable chronology,
wide sampling/epoch intervals, unavailable comparison and each calculated element
difference. Every finding records its condition/inputs, exact source IDs/hashes/
clocks, rule/version, category, explanation, assumptions, limitations and available
calculation evidence. Severity/confidence are null. Categories describe evidence
quality rather than physical danger. All rules and boundary semantics are defined
in the methodology; defaults reuse the existing 24/72-hour freshness policy.

Historical JSON export preserves the captured result and limitations without
recalculation. Available pairs expose exact Phase 9/10-compatible capture
definitions, clearly labelled **not captured**. They do not invent a manifest hash,
package URL or successful replay. No Phase 9 or Phase 10/10.1 format was extended.
The historical-report kind has its own explicit version. Underlying comparison
replay and deterministic finding recomputation are separately described.

## Actual genuine-source result and replay

The complete genuine ISS history produces one compatible pair (#1 → #2):

| Field | Snapshot 1 | Snapshot 2 | Difference | Unit |
| --- | ---: | ---: | ---: | --- |
| Inclination | 51.6327 | 51.6325 | approximately −0.0002 | deg |
| Eccentricity | 0.0006784 | 0.00067643 | approximately −0.00000197 | dimensionless |
| Mean motion | 15.48923373 | 15.48929442 | approximately +0.00006069 | rev/day |

Full binary64 values are retained in the JSON evidence. At the recorded evaluation
time both epochs were `aging` under the existing policy. Findings also disclose
the unknown legacy insertion time and the two-record limitation. Neither the
14.7-hour sampling interval nor the 7.7-hour epoch separation exceeds the configured
72-hour flags; the actual intervals remain visible. Absence of a flag is not
proof of complete physical history or source accuracy.

The generated report reproduced identically at the same source/window/policy/
evaluation inputs. A new exact-reference comparison was captured at the second
source epoch in TEME. Its three element differences exactly match the historical
report. **Three independent fresh-process offline replays reproduced all 56
checked numeric values exactly**, with zero network/database attempts and stable
projection hashes. Manifest anchor:

`739facf6cc84590864101f0fbadfecc994bc7d192325248a720c9cc6cdb3dee3`

This verifies the underlying numerical comparison, not the physical interpretation
or replay of a new finding schema. The finding rules were reproduced separately.
The published Vallado golden lifecycle also passed six reference components and
three exact offline replays under the final backend. Exact backend/runtime matching
remains required; old bundles must use their original trusted checkout. Original
prior-task temporary bundle directories were unavailable in this session, so their
member hashes were not newly reverified. Their tracked reports and format contracts
remain unchanged.

## Executed verification

Python commands use `UV_CACHE_DIR=/tmp/orbitiq-phase11/uv-cache` where uv is invoked;
scientific/operator scripts use `PYTHONPATH=backend`. npm commands run in `frontend`.
Exact commands, outputs/counts, hashes, browser cases and preservation results are
recorded in the integration artifact.

| Check | Exit | Actual result |
| --- | ---: | --- |
| `uv sync --locked` | 0 | Existing 31-package resolution / 29-package environment checked |
| `uv run --locked pytest -q --junitxml=/tmp/orbitiq-phase11/backend-verified.xml` | 0 | **828 passed**, including **43 new Phase 11** tests and preserved Phase 10/10.1 tests |
| `npm test` | 0 | **330 passed**, including **23 new history/client** tests |
| `uv run --locked ruff check .` / `ruff format --check .` | 0 / 0 | Pass |
| `npm run lint` / `npm run format:check` / `tsc --noEmit` | 0 / 0 / 0 | Pass |
| `npm run build` | 0 | TypeScript and Vite production build pass |
| `verify_scientific_references.py` | 0 | **40** published SGP4 comparisons pass |
| `verify_earth_fixed_references.py` | 0 | **6** terrestrial reference cases pass |
| `verify_phase61_science.py` | 0 | **32** numerical comparisons pass; observation validation remains blocked |
| `verify_phase611_geodesy.py` | 0 | **28** independent cases and **28** separate round-trips pass |
| `verify_phase101_golden.py` | 0 | **6** reference components / **3** exact offline replays pass |
| `verify_historical_analysis.py` | 0 | Two genuine sources, complete pagination, deterministic report, three exact comparison replays; DB preserved |
| Three-engine history and existing critical browser matrix | 0 | **24 history flows + 21 existing critical flows**, Chromium / Firefox / WebKit; final backend/frontend copies byte-match current source/build |
| `git diff --check` / preservation | 0 / 0 | Whitespace passes; original database, ledger, locks and earlier phase documents unchanged |

New tests cover empty/one/two/multiple isolated histories, pagination beyond the
first page and stable anchors, no extra point creation, scalar formulas/units,
invalid hashes/units/metadata, equal/reversed/future chronology, duplicate
payloads, freshness and interval boundaries, deterministic explanations, source
replacement refusal, replay linkage, query/workload bounds, read-only/no-network
behavior, stale-response cancellation, export without recalculation, safe error/
retry/empty states and client rejection of altered contracts including microsecond
source-time differences. Fixtures are explicitly marked as test-only.

Initial new tests exposed incorrect fixture epoch/time assumptions and overly broad
DOM selectors; those test inputs/selectors were corrected. Browser setup initially
sent a loopback health probe to the inherited external proxy; the explicit local
probe was corrected. A comparison selector was corrected to its actual row-header
label. WebKit screenshot CSS injection reproduced an existing documented tool/CSP
limitation; screenshot capture is omitted for that engine while real DOM layout,
keyboard, downloads and scientific checks remain enabled. CSP was not weakened.
A temporary browser copy made before the final frontend build completed was
identified by differing asset hashes and excluded from final-state verification.
Failed attempts remain recorded, rather than counted as passing final checks.

Known existing warnings: TestClient's Starlette/httpx deprecation and Vite's
558.60-kB globe chunk. No warnings/tolerances were suppressed. A full assistive-
technology/WCAG audit, physical-device/GPU checks and WebKit screenshot tooling
remain outside the local browser evidence.

## Preservation, changed files and acceptance

The ordinary schema-3 SQLite file retains byte SHA-256:

`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`

Full fingerprints preserve two snapshots, one ingestion attempt, one insertion
record and one collection gate, plus all schema objects, triggers and constraints.
No ordinary initialization, migration, restore, collection or write occurred.
Browser services use a separate consistent read-only copy on an owned internal
Docker network with no published ports. Retained test runtimes load exact current
backend/frontend copies; this is not a fresh release-image build or production
deployment. Chromium 151.0.7922.34, Firefox 153.0 and WebKit 26.5 passed; all final
page-error/CSP lists are empty. Desktop/tablet/mobile overflow and keyboard checks
ran in all three engines, with screenshots in Chromium/Firefox only. Owned
containers/network were removed after verification. All earlier phase
reports, structured artifacts, scientific algorithms/fixtures, ingestion/storage
code, migrations and dependency manifests/locks retain their baseline hashes.

Existing files changed intentionally: backend composition, request admission and
two comparison helper extractions; gateway route classification; the investigation
view, shared styles and README navigation. New files: history API/service/test, frontend historical
view/decoder/test/isolated fixtures, two local verification scripts, methodology,
this report and the structured evidence artifact. No unrelated existing work was
reset or included. Secret-pattern review found no private keys, credentials or
production secrets in the new work. All modifications remain local and unstaged.

**22 criteria PASS, 0 FAIL, 1 BLOCKED**. The blocked criterion conservatively
tracks three-or-more-sample **genuine-history** verification; controlled multi-point
implementation tests pass. Available genuine pairwise behavior is verified.

| # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Existing architecture and phase reports inspected | PASS | Current source plus nine requested report/artifact paths inspected. |
| 2 | Genuine historical coverage established | PASS | Complete two-page archive audit; both payloads validated and identified. |
| 3 | Historical timeline implemented using actual archived snapshots | PASS | All three engines displayed the two exact genuine source IDs/hashes. |
| 4 | Snapshot pagination and chronology correct where supported | PASS | Actual next/previous anchored pages; equal/reversed/future cases in isolated tests. |
| 5 | Missing history and incomplete metadata disclosed | PASS | Actual legacy insertion null and two-record limitation in UI/export; invalid-row tests. |
| 6 | Pairwise orbital changes computed correctly | PASS | Three real field differences equal existing comparison and detached replay calculation. |
| 7 | Inclination, eccentricity and mean-motion conventions documented | PASS | Authoritative units, scalar formulas, no inclination wrap/percentages. |
| 8 | Pairwise changes not misrepresented as long-term trends | PASS | Actual report/UI explicitly limited to two records and no trend statistic. |
| 9 | Trend summaries bounded by actual historical evidence | BLOCKED | Pairwise limitation verified; three-plus-sample real-history verification blocked by only two genuine records. Controlled multi-point implementation tests pass; no trend or prediction is claimed. |
| 10 | Deterministic quality rules implemented/versioned | PASS | Ten version-1 rule identifiers and explicit category semantics, tested triggers. |
| 11 | Every finding has reproducible explanation | PASS | Same recorded inputs/clock yield identical entire report, findings and IDs. |
| 12 | Every finding references actual supporting data/calculations | PASS | Exact ID/hash/epoch/retrieval, structured inputs and element calculation refs in actual exported findings. |
| 13 | Evidence links/replay references preserved where available | PASS | Uncaptured compatible recipes explicit; actual operator-captured pair replayed separately; prior contracts/reports preserved. |
| 14 | Historical reports accurately represent coverage | PASS | Captured JSON in three engines preserves two validated records, provenance and limitations. |
| 15 | Ingestion/deduplication safeguards intact | PASS | Original ingestion/storage/migrations unchanged; full ingestion/collection regressions and dedup tests pass. |
| 16 | No fabricated snapshots or trend data used | PASS | No acquisition, ordinary write or interpolated point; synthetic data confined to labelled fixtures. |
| 17 | Original records and audit logs preserved | PASS | Exact ordinary DB bytes and complete fingerprints identical before/after. |
| 18 | Scientific readiness/EOP policies remain enforced | PASS | Original science/readiness/resources code and strict policy unchanged; regression/reference checks pass. |
| 19 | New backend/frontend tests pass | PASS | 43 new backend plus 23 new frontend cases; full 828/330 suites pass. |
| 20 | Existing scientific regressions pass | PASS | 40 SGP4, 6 terrestrial, 32 expanded, 28 independent geodetic and 28 round-trip checks. |
| 21 | Lint/format/TypeScript/production build pass | PASS | Recorded exit-0 commands plus final-state exact-byte browser inputs. |
| 22 | Limitations/incomplete coverage documented | PASS | Methodology/report/UI/export explicitly separate data gaps, clocks, physical interpretation and production gates. |
| 23 | Phase report and structured artifact produced | PASS | This machine artifact and Phase 11 report retain actual test/genuine-data evidence. |


## Remaining boundaries and recommendation

Only two genuine ISS records support the real-history demonstration. Three-or-more
sample behavior passes controlled implementation tests, but broader genuine-history
verification is **BLOCKED by coverage**. No reliable long-term trend, forecast,
physical-event attribution or confidence level has been established. Independent
observation validation remains blocked and prediction uncertainty unquantified.

Continue controlled Phase 6 collection over time when separately desired, retain
its audit/deduplication/cooldown protections, and revisit multi-satellite and
multi-sample histories when genuine inputs exist. Do not force collection to fill
a chart. No additional external service or public deployment is required for local
pairwise investigation.

Phase 8 public hosting/domain/HTTPS, independent off-machine recovery, production
monitoring/actual alert delivery and branch protection/required-check enforcement
remain independent unverified production gates. Phase 11 remote CI has not run.
No production-readiness or deployment claim is made.
