# Phase 11.3 — independent reference dataset integration

Local work on **21 October 2026**. **PARTIAL: authentic ESA reference and quality
products acquired and inspected; historical GP pairing and numerical benchmark
remain BLOCKED.** No prediction/reference residual or independent accuracy result
was produced. Prediction uncertainty remains unquantified.

The result goes beyond the previous research plan: a bounded offline source
inspector was implemented, tested on synthetic edge cases and exercised against
the actual acquired files in three fresh offline processes. It is deliberately
not advertised as an operational normalized-state adapter. The request requires
qualification of a real pair before building that adapter; the missing GP and
unresolved frame/time gates prevent that qualification.

See [dataset provenance and reproduction](phase-11.3-dataset-provenance.md) and
[machine-readable execution evidence](phase-11.3-integration-results.json).

## Baseline and inspection

Branch `phase-10-evidence-replay`, HEAD
`be3710dae9f21bae817637d7bfdb87509b3f6a34`; began with 40 existing unstaged
modified/new Phase 11 paths. Saved a **277-file** hash manifest, Git state, original
database bytes and complete schema/table/integrity fingerprints before changes.
Fresh baseline checks ran: **874 backend / 344 frontend** tests passed.

All requested reports/evidence files were available except
`docs/observation-validation-methodology.md`; the actual existing guide is
`docs/observation-validation.md`. Inspected the Phase 11 history/extension/follow-up
reports/evidence, Phase 10/10.1 capture/integrity/replay, Phase 6/6.1/6.1.1 scientific
and collection reports, schemas and code. Reviewed exact snapshot validation,
catalog identities and timestamps, single-object CelesTrak ingestion/cooldown,
SGP4/WGS72 initialization, strict EOP/leap transformations, observation contract,
residuals, file evidence, JSON export and regression conventions.

Actual existing scope is unchanged: OMM-field GP JSON, SGP4/WGS72, UTC requests,
TEME and validated ITRS transforms, ±7-day source-epoch bound, microsecond report
timestamps, optional private immutable observation packages. No historical Swarm
GP, raw TLE importer, general SP3 importer, IGb08 alignment, arbitrary time
interpolation or prediction covariance exists. The ordinary archive still contains
two ISS GP snapshots, not Swarm inputs or independent measurements.

## Acquired reference and qualification outcome

One official Swarm-A **SP3AKIN_2_ version 0201** ZIP and the matching **SP3AVAL_2_**
ZIP were actually downloaded, opened, hashed and inspected. Combined compressed
size is **907,347 bytes**. ILRS maps SP3 ID **L47** to NORAD **39452**, corroborated
by the CelesTrak SATCAT. Header contents establish processing software
`L2PS-DUT/44.88`, UTC validity 2013-12-31 23:59:44 through 2014-01-01 23:59:44,
2022 header creation dates, quality/error codes and matching upstream filenames.

The real product is **SP3-d / IGb08 / GPS / km**, with **7,647** position/EP records
and **no velocity records**. This corrects the earlier planning assumption of
SP3-c based on the nominal specification; prior reports remain unchanged as
historical records. Header interval is zero and actual epochs are irregular.
There are **1,806 submicrosecond** and **723 second-60** encodings; counts overlap.
The tool preserves these facts without rounding or treating them as ordinary UTC.
First/last actual epochs, full interval histogram, source/member hashes and code
identities are in the evidence. Source coordinates remain private, outside Git.

The matching nine-page quality PDF was rendered and visually reviewed, with OCR
used only as a nonauthoritative aid. It contains GPS-fit/visibility, comparison and
SLR plots; one page is blank. Its plotted residuals describe the provider's
processing/validation, **not OrbitIQ's SGP4 error**. No universal sample acceptance
or prediction covariance was inferred from quality `000`, product error `0`,
nominal accuracy, EP correlations or those plots.

The reference is an external observation-derived processed estimate. Its producer
and upstream GPS/attitude/spacecraft inputs are documented, and production is
independent of OrbitIQ's code. Independence from an eventual GP fit is **uncertain**;
SSN fitting lineage and relevant shared inputs remain unresolved. It is not raw
XYZ observation truth, a GP input, or a synthetic scientific result.

## Historical pairing blocker and alignment design

CelesTrak's actual historical route is a CAPTCHA-protected email request form.
No form was submitted and no message was sent. One bounded, documented
Space-Track `gp_history` request for Swarm-A around January 2014 returned **401**;
no authorized session/identity is configured. No credentials were requested or
exposed and no access controls were bypassed. Inspected ESA product navigation
did not supply a historical GP. A current TLE or another spacecraft was not used.

There is therefore **no authentic paired GP/TLE**, no GP hash/epoch/availability
cutoff, and no eligible evaluation. A GP epoch alone would not prove its historical
publication. The intended future experiment must remain retrospective unless
historical availability before every evaluation epoch is evidenced.

Before a benchmark can run, obtain authorized historical elements for NORAD 39452
covering the acquired interval, with original bytes and publication/retrieval
provenance. Then resolve IGb08 realization treatment, the source's GPS precision/
second-60 encodings, required EOP/leap resources, quality inclusion and lineage.
The proposed alignment uses **exact supported reference epochs**, propagating the
same recorded GP at each accepted UTC epoch. No nearest-neighbour tolerance or
interpolation is needed or justified yet. If conversion cannot preserve precision
or frame semantics, exclude/block that sample rather than silently round.

A future adapter should emit the existing `observation_derived_state` contract only
after those gates, with an explicit **reference-product comparison** interpretation,
source/member/record hashes, preserved original fields, quality references and
transform/resource metadata. Reuse `analysis.load_snapshot`, existing propagation/
ITRS conversion, residual/statistics and capture/replay. Do not manufacture an
official current-GP URL, historical retrieval time, covariance or source record to
force an imported historical TLE through today's CelesTrak-only storage contract.
Any required historical input adapter must separately preserve its actual source.

Reference-minus-predicted XYZ/norm in one frame is the planned residual convention.
ITRS RAC stays unavailable; there is no usable reference velocity in this file.
Aggregate metrics require sufficient compatible samples and retain exclusions.
No usable pair exists now, so actual comparison count is **0**, and residuals,
aggregate accuracy metrics and confidence intervals are **null**, not zero error.

## Implemented files and safety boundary

- `scripts/inspect_swarm_reference.py`: operator-only offline inspection of the
  demonstrated Swarm-A 0201 / 44.88 / SP3-d layout and matching VAL ZIP. Reuses
  existing bounded no-symlink file reads and SHA/JSON mechanisms. Checks pinned
  source hashes, fixed safe ZIP membership, size/ZIP CRC/POSIX header checksum,
  explicit XML identity/coverage/lineage, supported frame/time declarations, state
  structure/counts, finite numeric fields, EP ranges and chronological diagnostics.
  No filesystem extraction, network/DB calls, normalization, propagation or import.
  Successful inspection still emits `comparison_ready=false`, no normalized
  observations and null residuals. This is a qualification tool, not a complete
  SP3 standard parser, source authentication service or scientific acceptance gate.
- `backend/tests/test_phase113_swarm_inspection.py`: **41** new, clearly synthetic
  format/boundary cases, including wrong target/version/frame/time/fields, missing
  provenance, corrupt/truncated/hash-altered archives, unsafe members/links/DTD,
  size bounds, uncertain quality, exact time diagnostics, deterministic JSON and
  exclusive output. No genuine provider coordinate fixture or network dependency.
- This report, dataset provenance document and structured integration evidence.

All existing source/configuration/tests/reports/locks are unchanged. No backend or
frontend runtime feature, database schema, dependency or public API was added.
Source material and generated inspections remain in an ignored private directory;
data redistribution terms were assessed and not assumed to permit GitHub fixtures.

## Actual verification

Commands used `UV_CACHE_DIR=/tmp/orbitiq-phase113/uv-cache` and, for scripts,
`PYTHONPATH=backend`; npm commands ran in `frontend`. Exact commands, exits, source
hashes, artifacts and actual counts are in the JSON evidence. Raw verification
artifacts remain in `/tmp/orbitiq-phase113`; original source ZIPs/receipts remain in
`data/validation-phase-11.3`.

| Check | Actual result |
| --- | --- |
| `uv run --locked pytest -q --junitxml=/tmp/orbitiq-phase113/backend-final.xml` | **915 passed**, zero failures/errors/skips; original 874 plus 41 new inspector cases |
| `npm test` | **344 passed**, 25 files; no frontend source changed afterward |
| Authentic inspector, three fresh offline processes | All exit 0, **byte-identical** reports; 7,647 source states inspected; zero network/database/process attempts; benchmark explicitly blocked |
| `uv sync --locked`; Ruff check / format check | All exit 0; locks unchanged |
| ESLint / Prettier / TypeScript noEmit / `npm run build` | All exit 0 |
| SGP4 / terrestrial / expanded science / geodesy audits | **40 / 6 / 32** comparisons plus **28** independent geodetic cases and **28** round-trips pass; observation validation still blocked |
| Existing golden evidence lifecycle | **6** published components, **3** exact offline replays pass |
| Existing controlled observation packages | **6** fresh offline replays pass; synthetic arithmetic only, not a Swarm benchmark |
| Existing browser regression matrix | **77 flows**, Chromium/Firefox/WebKit; genuine-history/empty evidence and isolated synthetic package contexts |
| Existing Phase 9 PDF text/pagination checks | **7 PDFs pass**, including all 361 maximum-track rows |
| Preservation / whitespace checks | Original 277 files and complete DB fingerprint unchanged; HEAD/index preserved; `git diff --check` passes |

Initial development checks found formatting issues and an incorrect ZIP-CRC
assumption for the XML checksum. Native `cksum` verified the actual POSIX header
checksums; the inspector was corrected and final checks rerun. Checksums and
scientific tolerances were not weakened. All new tests passed on their first run;
the full final suite also passed. Existing Starlette/httpx deprecation and globe
chunk-size warnings remain; the intentional duplicate-ZIP fixture emits a warning.
Browser startup health probes may fail before readiness; final flows must pass,
and their actual attempt records are retained. Local verification containers are
not newly built/published release images or a production deployment.

## Acceptance status

**12 PASS / 5 PARTIAL / 6 BLOCKED / 0 FAIL.** Completion of software inspection
does not close the absent scientific benchmark.

| AC | Status | Evidence / limitation |
| --- | --- | --- |
| 1 repository/validation inspected | PASS | Baseline, actual code/reports/archive audited; missing filename resolved explicitly |
| 2 official documentation reviewed | PASS | Actual ESA spec/terms, SP3-d and identity documentation read |
| 3 specific product/format identified | PASS | Acquired KIN/VAL 0201, 44.88 headers; SP3-d rather than assumed SP3-c |
| 4 processing lineage assessed | PARTIAL | Actual upstream filenames/producer and general methodology known; GP fitting/shared lineage unresolved |
| 5 applicable access requirements satisfied | PARTIAL | ESA public acquisition succeeded; historical GP authorization/human delivery remains unavailable |
| 6 authentic reference acquired | PASS | Two actual ZIPs, member parsing/visual inspection, hashes and receipts |
| 7 actual historical GP verified | BLOCKED | Space-Track 401; CelesTrak CAPTCHA/email; no source bytes or cutoff |
| 8 payload identities/hashes | PARTIAL | Complete acquired reference/quality identities; no GP identity/hash |
| 9 temporal/frame/unit compatibility | BLOCKED | Units/frame/time known, but no pair, approved IGb08 alignment or exact epoch conversion policy |
| 10 independence/limitations documented | PASS | External processed reference; fit independence uncertain, never truth certification |
| 11 narrow benchmark adapter | BLOCKED | Pair unsuitable/unqualified; only offline source inspector implemented |
| 12 dataset parsing rejection | PARTIAL | Demonstrated source layout inspected/rejected safely; no qualified normalized-state adapter |
| 13 justified alignment | BLOCKED | No GP evaluation or approved conversion; no tolerance/interpolation invented |
| 14 look-ahead protection/retrospective label | PARTIAL | No forecast claim or evaluation permitted; actual historical cutoff cannot yet be checked |
| 15 reproducible residuals | BLOCKED | No real GP/reference comparison; existing residual implementation preserved |
| 16 sample-bounded statistics | PASS | Zero comparisons; metrics null, no general accuracy estimate |
| 17 uncertainty bounded | PASS | EP/reference information separate; prediction uncertainty unquantified |
| 18 benchmark replay integration | BLOCKED | No numerical benchmark to capture; exact offline inspection and existing replay regressions are separate successes |
| 19 existing data/evidence preserved | PASS | All starting files and DB bytes/schema/rows unchanged |
| 20 existing scientific regressions | PASS | Full suites, science/reference/golden/replay audits rerun |
| 21 new tests where implemented | PASS | 41 inspector cases, actual acquired-file inspection and exact offline repetition; no adapter-validation claim |
| 22 quality/build/browser checks | PASS | Actual lint/format/TS/build and three-engine matrix |
| 23 factual final reporting | PASS | Reference acquired, pair absent, inspector real-file tested, residual absent clearly separated |

## Preservation, milestones and next action

Original DB SHA-256 remains
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Schema 3, two genuine ISS snapshots, one ingestion attempt, one insertion record,
one gate, all indexes/triggers and integrity/foreign keys are preserved. No ordinary
DB initialization, migration, collection, restore or write occurred. No old report
or evidence package was overwritten; no numerical tolerance or resource policy changed.

**Local:** source inspection/tool/regressions verified; scientific pair/benchmark
blocked. **Published:** no new commit or push. **Remote CI:** not triggered or
verified for this work. **Production deployed:** no. **Production infrastructure
verified:** no; Phase 8 hosting/domain/public HTTPS, independent off-machine recovery,
real monitoring/alert delivery and branch-protection/required-check gates remain open.

Next action: obtain an authorized historical Swarm-A GP/TLE payload around
2013-12-31/2014-01-01 with its actual source/availability evidence, using the
provider's supported human/account route. Then review IGb08 alignment, GPS epoch
policy and quality inclusion before implementing the state adapter and running
an explicitly scoped reference-product comparison. Do not send credentials into
source files or replace missing inputs with invented observations.
