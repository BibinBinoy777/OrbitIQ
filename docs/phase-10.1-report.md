# Phase 10.1 — Scientific evidence integrity and replay reliability

**Local completion: 20 October 2026 UTC.** The focused hardening scope is verified:
**23 acceptance criteria PASS, 0 FAIL, 0 BLOCKED within the local scope**. This does
not close observation-based prediction validation, production infrastructure or
publication/remote-CI gates. Nothing was committed, pushed, published or deployed;
no remote workflow was queried, triggered or rerun.

See [structured actual evidence](phase-10.1-integration-results.json), the
[versioned integrity contract](replay-integrity-contract.md) and
[operator guide](evidence-replay.md). Earlier Phase 10 reports/evidence are unchanged.

## Baseline and inspection

Started on `phase-10-evidence-replay`, HEAD
`d9f85d5d6e28cea90f25965c761422f16705eea8`, with **16 existing modified/new Phase 10
paths**. The tree was not clean. A 237-file SHA-256 baseline, original Git status,
ordinary database hash and full read-only schema/table fingerprint were retained
before implementation. Existing changes were extended deliberately, not reset.

All eight requested reports existed, were checked before reading and inspected:
Phase 10, Phase 9, Phase 9 publication review/status, Phase 8.2 release readiness,
Phase 6, Phase 6.1 and Phase 6.1.1. The publication documents describe different
historical checkpoints: Phase 10's report records the later merge/CI on main.
No historical report was edited to imply new verification or publication.

Fresh baseline commands, before changes:

| Command | Exit | Actual result |
| --- | ---: | --- |
| `UV_CACHE_DIR=/tmp/orbitiq-phase101/uv-cache uv run --locked pytest -q` | 0 | **730 passed**, 14.82 s; existing TestClient deprecation |
| `npm test` in `frontend` | 0 | **307 passed** |

Inspected the report API/model/capture/export, directory bundle and manifest,
source parser/storage/identities, exact payload/resource hashing, dependency/runtime
recording, propagation/transforms/sampling, historical EOP scope, replay projection,
comparison/error handling, database access, immutable collection ledger, reference
fixtures/audits, backend/frontend tests and actual browser/PDF runners.

Existing format was directory bundle 1, report schema/template 1, one/two exact
sources, fixed member names, original response bytes, optional exact terrestrial
resources, locked runtime/backend hashes and per-quantity absolute tolerances.
Source-only, unavailable and failed results were already distinct. Source loading
and replay were read-only. These capabilities and all 55 existing Phase 10 tests
were preserved rather than duplicated or replaced.

## Gaps and focused changes

| Demonstrated gap | Improvement |
| --- | --- |
| Exact numeric reproduction and tolerated numeric differences both returned generic `matched` | Add explicit `numerical_outcome`, exact comparison profile, tolerated-value counts/details and projection hashes; retain primary status compatibility |
| Diagnostics lacked residuals, units and useful missing-input identification | Structured validation stage/code/member/field and affected calculation; signed/absolute/meaningful-relative residuals, unit, tolerance and pass/fail |
| Byte limits did not explicitly bound JSON nesting/nodes/collections; directory enumeration allocated a complete listing | Pre-decoder depth scan, decoded budgets, bounded strings/collections/nodes; stop directory scanning at the first unexpected member |
| Some contradictory result metadata was discovered only after recalculation | Shared scientific preflight checks exact source lineage, request time/frame/units/result shape, execution clocks, required EOP/leap provenance/parameters and software/limitation declarations first |
| Offline behavior was primarily demonstrated by a successful external audit | Scoped verifier policy denies Python socket, SQLite and process operations; attempted forbidden work blocks success even if caught downstream |
| Manifest defaults accepted absent version/kind; identifiers were unrestricted strings | Require explicit supported format/version fields, bounded UUID form and complete supported report fields/versions |
| Existing independent references and replay were tested separately | Reuse the published 6251 reference in a full capture/export/validation/offline-replay/reference-comparison/evidence lifecycle |

No orbital equations, scientific/reference tolerances, normal API clock/resource
policy, ingestion behavior, database schema or dependencies were changed. The
format remains version 1. No signature system, archive-extraction engine, public
upload API, new frontend feature or general observation-validation framework was
introduced.

Phase 10.1 intentionally edits six pre-existing files: README, the active replay
guide, `replay.py`, `replay_contract.py`, `services/replay.py` and the replay CLI.
It adds `replay_json.py`, `replay_validation.py`, `replay_isolation.py`,
`test_phase101_integrity.py`, `verify_phase101_golden.py`, the integrity contract,
this report and its JSON evidence. The complete inventory and source identities
are retained in the structured record. Other pre-existing Phase 10 edits remain.

## Integrity, import safety and offline semantics

The [contract](replay-integrity-contract.md) specifies every manifest/scientific
field location, exact hashed bytes, JSON serialization profile, timestamps,
resources, supported modes/frames, comparison projection and limits. Existing
metadata is linked through hashed report/source members rather than duplicated
under competing manifest fields. Payload hashes cover exact bytes; the manifest
hash is returned separately and never embedded into itself.

Checksums establish integrity, not producer authenticity. A separately retained
trusted manifest checksum pins capture bytes; replacing a whole untrusted bundle
can replace its own checksums. No provider signature or signing identity is claimed.

Imports accept only the fixed regular-file directory layout. No ZIP/tar extraction,
code execution, shell command, arbitrary module import, ingestion or maintenance
operation is selected by bundle data. Unknown/executable members, absolute/traversal
member paths, symlinks, FIFOs, missing/mismatched/oversized members and invalid JSON
are refused. Limits include 5–9 fixed members, 128-KiB manifest, 24-MiB payload total,
8-MiB per-file maximum with tighter per-type bounds, manifest/other depths 12/32,
4,096 collection entries, 16,384-character strings and 4,096/200,000 decoded nodes.
Detailed residuals are bounded independently from total difference counts.

`validate` uses the same preflight as `verify` and returns `status="validated"`,
`numerical_outcome="not_performed"`, `replay_started_at=null` before any orbital
calculation. Missing EOP/leap/source members name the original required input and
affected calculation. Invalid frame/unit/time/source/resource metadata cannot
reach recalculation. There is no latest-source lookup or installed-file fallback.

The synchronous verifier's scoped audit policy denies connection/resolution/send,
SQLite connection and process-execution events. Tests force those attempts and
verify refusal; a swallowed denial still cannot yield success. Normal contexts
and another thread's ordinary SQLite use remain unaffected. This is defense in
depth for trusted installed Python/native libraries, not a general hostile-code OS
sandbox. The independent fresh-process audit starts before imports. A separate
golden run also passed under Docker `--network none` with all inputs provisioned.

Historical EOP assessment uses the captured policy clock and exact copied bytes.
Normal API behavior remains current-time and unchanged. Captured/replay resources
are not refreshed; ERFA leap table/expiry and Astropy context restoration retain
the existing regressions. Current scientific-resource readiness is not certified.

## Repeatability, residuals and provenance

Successful state replay distinguishes **exact decoded binary64 reproduction**
(including signed zero and selected exact metadata) from **tolerance agreement**.
It does not require an identical whole-report UUID/clock/JSON spelling or prove
identical native-library binaries. Unsupported/missing inputs remain unverifiable;
source-only results do not claim a state replay.

The unchanged matching-runtime replay bounds are `1e-8 km` position/separation,
`1e-10 km/s` velocity/relative speed, `1e-9 deg` geodetic angles, `1e-8 km` altitude,
other numeric/metadata exact, relative tolerance zero. These are software replay
bounds, not physical prediction uncertainty or new universal portability targets.
No tolerance was weakened. Relative residuals are null for zero references,
angles, unknown units or unrepresentable ratios. Longitude differences use
`remainder(delta,360)`; latitude is not wrapped. Existing element conventions remain.

Each valid replay report retains source references with epoch/retrieval, requested
calculation, package creation, original report generation/calculation times,
historical policy evaluation, replay start and verification completion separately.
No observation timestamp is inferred from any of these clocks.

Fresh CLI captures from the existing genuine ISS archive, with **three independent
fresh-process replays of each package**, produced:

| Case | Outcome on every repeat | Numeric values per replay |
| --- | --- | ---: |
| Snapshot | `not_applicable_source_only` | 0 |
| TEME position | `exact_output_reproduction` | 9 |
| Three-point ITRS track | `exact_output_reproduction` | 93 |
| Common-time ITRS A/B comparison | `exact_output_reproduction` | 100 |
| Maximum 361-point ITRS track | `exact_output_reproduction` | 11,191 |

All 15 runs had stable projection hashes, unchanged package members and **zero
network/database/process attempts** in the scoped policy. The independent import-
time audit also recorded zero network/database attempts. No provider acquisition
occurred. Seven disposable-copy diagnostic cases additionally recorded missing
inputs, tolerated/failed numeric changes, incompatible units and an unexecuted
unexpected Python member. Their deliberately altered expectations are labelled
test data, not observations. Zero/wrap/signed-zero examples are separately labelled
synthetic comparator tests.

Five original Phase 10 bundles still match their separately recorded manifest and
member hashes. Their old backend hashes intentionally produce `runtime_incompatible`
under Phase 10.1. Format 1 remains recognized; faithful replay requires their exact
trusted code/runtime. No old manifest, source or resource was edited to bypass this
requirement. This compatibility boundary is documented, not silently relaxed.

## Published golden-reference lifecycle

`verify_phase101_golden.py` reuses the unmodified existing `vallado-leo.json`
reference, NORAD **6251**, epoch **2006-06-25T19:46:43.980096Z**, offset zero.
Inputs derive from Vallado et al. AIAA 2006-6753, `SGP4-VER.TLE`/`tcppver.out`,
distributed with pinned python-sgp4 **2.27**. The upstream output hash is checked:

`687bf28dbe52df86e8e60ab5cb4a08d1aa3dbcaf4e63b1f7ab95f044fbe3833b`

The outer audit kit records literal published expectations, TLE/OMM, source/fixture
hashes, WGS72, Earth-centered TEME, UTC nominal-day convention, km/km/s, requested
epoch, expected/actual component values and residuals. EOP/leap resources are
explicitly not applicable to this TEME case. The inner bundle captures OrbitIQ's
own computational baseline, which is not labelled independent scientific truth.

Lifecycle: isolated fixture archive → capture → detached fixed-directory export →
validation-only result → three fresh-process offline replays → six independent
published-component comparisons → evidence report. **All six components pass**
the existing published-reference `1e-5 km` / `1e-8 km/s` tolerances, relative zero.
Maximum component residuals are approximately `8.279e-7 km` and `7.057e-10 km/s`.
The broader published tolerances allow reference precision/datetime representation;
they are distinct from matching-runtime replay tolerances. Three host and three
OS-network-isolated replays reproduced their captured numerical projection exactly.

The test archive's URL/retrieval metadata and serialized response are explicitly
fixture-adapter scaffolding, not a provider download. Only the object-name label is
changed; published orbital elements/expected vectors are preserved. Fixture records
never enter the ordinary archive. These are numerical references, not independently
observed satellite positions or universal model validation.

## Final executed checks

Root Python commands used `UV_CACHE_DIR=/tmp/orbitiq-phase101/uv-cache` for uv and
`PYTHONPATH=backend` for operator/science scripts. npm commands ran in `frontend`.
Exact command strings, exit statuses, JUnit groups, versions, output hashes and
supporting harness sources are in the JSON artifact.

| Command/check | Exit | Actual final result |
| --- | ---: | --- |
| `uv sync --locked` | 0 | Existing locked environment checked |
| `uv run --locked pytest -q --junitxml=/tmp/orbitiq-phase101/backend-final.xml` | 0 | **785 passed**, 22.41 s; **0 failures/errors/skips** |
| New `test_phase101_integrity.py` within full suite | 0 | **55 passed** |
| Preserved Phase 10 replay tests within full suite | 0 | **55 passed** |
| Ingestion reliability / collection groups within full suite | 0 | **29 / 62 passed**, respectively; other ingestion/science/API regressions also included |
| `npm test` | 0 | **307 passed**; no frontend implementation change required new tests |
| `uv run --locked ruff check .` / `ruff format --check .` | 0 / 0 | Passed |
| `npm run lint` / `npm run format:check` | 0 / 0 | Passed |
| `./node_modules/.bin/tsc --noEmit` / `npm run build` | 0 / 0 | Passed |
| `python scripts/verify_scientific_references.py --output /tmp/orbitiq-phase101/sgp4-final.json` | 0 | **40 passed, 0 failed** |
| `python scripts/verify_earth_fixed_references.py --output /tmp/orbitiq-phase101/terrestrial-final.json` | 0 | **6 passed, 0 failed** |
| `python scripts/verify_phase61_science.py --output /tmp/orbitiq-phase101/science61-final.json` | 0 | **32 comparisons passed**; observation validation still blocked |
| `python scripts/verify_phase611_geodesy.py --output /tmp/orbitiq-phase101/geodesy-final.json` | 0 | **28 independent cases + 28 separate round-trips passed** |
| `python scripts/verify_phase101_golden.py --directory /tmp/orbitiq-phase101/golden-final` | 0 | Six published components and three exact offline replays passed |
| Golden lifecycle in Docker `--network none` | 0 | Six components and three exact offline replays passed |
| Genuine-archive capture/repeat harness | 0 | Five packages, 15 fresh offline replays; original archive unchanged |
| Existing report browser runner | 0 | **14 cases**, Chromium 6 / Firefox 4 / WebKit 4 |
| Existing critical browser runner | 0 | **21 cases**, seven per engine |
| `python scripts/verify_report_pdf.py --directory /tmp/orbitiq-phase101/browser-final/exports --output /tmp/orbitiq-phase101/pdf-final.json` | 0 | **Seven PDFs passed**, including all 361 maximum-track rows and page counters |
| Preservation / `git diff --check` | 0 / 0 | Original data, earlier reports, locks and staging preserved; whitespace passed |

Browsers: Chromium **151.0.7922.34**, Firefox **153.0**, WebKit **26.5**. Actual
APIs/canvas were used; zero page errors/CSP violations and standalone HTML offline
checks passed. Existing test images were reused on an owned internal Docker
network, with a byte-matched read-only current backend copy and a separately
restored, unchanged genuine database. All 13 files in the current production
frontend build exactly match the retained web image used for the checks. Containers
and the owned network were removed. No application was publicly exposed.

Initial browser rehearsal failed with 502 because non-root runtime access could
not traverse the private workspace source permissions; an isolated import reproduced
the failure. Only temporary copied-file permissions were corrected. Initial
OS-isolated golden capture also could not read the retained Phase 9 image's
root-owned lockfile. The final audit supplied an exact, read-only matching lockfile,
code, scripts and fixtures. An attempted helper write inside an already sealed
read-only inputs directory was refused; the final lock copy used its separate owned
path. Evidence assembly initially expected the browser request counter as an array;
the reader was corrected to preserve the emitted integer counter. No source
permissions, application assertions, tolerances or security policy
were relaxed. These failed harness attempts are retained as failed evidence.

This is a provisioned verification environment, not a newly built release image.
A future packaged CLI image must provide its matching lockfile readably; it must
not infer readiness from this overlay audit. Native Firefox/WebKit PDF output,
physical printers/devices, screen readers and cross-platform bitwise reproducibility
remain outside the checks. Existing TestClient deprecation and Vite globe-chunk
size warning remain visible. No warning was suppressed.

## Historical data and Git preservation

Ordinary database before/after SHA-256:

`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`

Complete schema/table fingerprints match: schema 3, two genuine ISS snapshots,
one ingestion attempt, one insertion record and one gate. Raw source bytes,
identities, audit records and parameters are unchanged. There was no normal-database
initialization, migration, reset, restore target switch, snapshot insertion or
upstream ingestion. Test-only archives and a separate consistent browser copy are
clearly separated.

All **47 historical phase-document files**, including the original Phase 10 report,
plan and verification JSON, retain their initial hashes. Existing tests, scientific
algorithms/fixtures/audit scripts, tolerances, storage/ingestion code, migrations and
both lockfiles retain their hashes. Six active Phase 10 files were intentionally
extended; all other pre-existing file hashes match. HEAD, branch and staged content
remain as at entry. Remotes were not modified; no commit, push or remote workflow
operation occurred. New/modified work remains local and reviewable.

## Requested acceptance criteria

| # | Criterion | Status | Actual evidence |
| --- | --- | --- | --- |
| 1 | Existing Phase 10/reports inspected | PASS | All eight requested reports exist/read; implementations and fixtures audited |
| 2 | Baseline recorded | PASS | Branch/HEAD/status, 237-file baseline, DB fingerprints, fresh 730/307 suites |
| 3 | Existing integrity audited | PASS | Preserved fixed-file/hash/source/runtime/resource checks and original 55 tests |
| 4 | Versioned manifest documented | PASS | Format/schema 1 contract and field locations; strict version/type tests |
| 5 | Defined hashing generated/checked | PASS | Stable JSON/raw-byte/hash tests and actual captures; no self-reference |
| 6 | Changes detected | PASS | Existing/new tamper tests and disposable-copy diagnostics; trusted anchor check |
| 7 | Malformed/incomplete/unsupported rejected | PASS | JSON/version/member/source/resource cases execute and block |
| 8 | Safe bounded import | PASS | Depth/node/count/byte limits; symlink/FIFO/traversal/archive/executable tests; denied process attempts |
| 9 | Scientific inputs identified | PASS | Source/request/clock/frame/unit and exact EOP/leap preflight, lineage tests |
| 10 | No silent network replacement | PASS | Core scoped denial, forced-attempt tests, fresh-process audits and OS-network-none golden lifecycle |
| 11 | Missing sources/resources explicit | PASS | Fixed original member, affected calculation, no replay; existing exact-source capture/API refusal tests |
| 12 | Exact and tolerant outcomes separate | PASS | Actual exact runs, deliberate tolerated/out-of-tolerance copies, source-only/unverifiable states |
| 13 | Residuals/units/tolerances useful | PASS | Absolute/signed/relative details; zero, tiny/wrapped longitude, signed-zero and nonfinite tests |
| 14 | Repeatability verified | PASS | 15 genuine package repeats plus golden repeats; stable projection/member/source hashes |
| 15 | Offline golden lifecycle | PASS | Published 6251 fixture pipeline; three host and three OS-isolated exact replays |
| 16 | Reference provenance documented | PASS | Upstream/fixture hashes, literal inputs/expectations, UTC/WGS72/TEME/units/tolerances and limits |
| 17 | Original data/ledger preserved | PASS | Exact ordinary DB hash and complete fingerprints; bundle/legacy member hashes unchanged |
| 18 | Scientific regressions pass | PASS | 40/6/32 audits and 28 independent geodetic cases + 28 round-trips; full suite |
| 19 | Added/relevant tests pass | PASS | 55 new backend tests and all existing 307 frontend tests; no frontend change requiring new tests |
| 20 | Quality/build/browser checks | PASS | Ruff/ESLint/Prettier/TS/build, 14 export + 21 critical cases and seven PDFs |
| 21 | Compatibility preserved/documented | PASS | Directory version 1 retained; five original packages intact and explicitly blocked for different backend identities |
| 22 | Scientific limitations explicit | PASS | Contract/result/report retain observation validation blocked and uncertainty unquantified |
| 23 | Report/structured evidence produced | PASS | This report and actual reference/replay/diagnostic/command/preservation evidence in linked JSON |

## Remaining limits and recommendation

**Phase 10.1 can conclude locally. Phase 11 development can begin under a separately
defined scope.** No Phase 11 functionality was implemented here. Preserve these
checks and review the local changes before any separately authorized publication;
Phase 10/10.1 remote CI remains unverified and no remote workflow was run here.

Independent observation-based satellite prediction validation remains **blocked**;
orbital prediction uncertainty remains **unquantified**. Matching software output
and published numerical vectors do not establish physical prediction accuracy,
maneuvers, anomalies, collision risk or operational safety. Matching versions are
not a guarantee of native-library binary identity or universal cross-host exactness.
Task-local evidence needs separate durable retention; it is not off-machine recovery.

Phase 8 public hosting/domain/HTTPS, independent backups/off-machine recovery,
production monitoring/actual alert delivery, and branch-protection/required-check
enforcement remain separate unverified infrastructure gates. Earlier protection/CI
facts are historical report evidence and were not re-queried in this task. There
was no domain/DNS/infrastructure change or production-readiness declaration.
