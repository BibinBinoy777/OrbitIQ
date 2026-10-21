# Phase 11.3.1 — historical input and frame/time qualification

Local work on **21 October 2026**. **PARTIAL implementation; overall scientific
qualification BLOCKED.** The historical Swarm-A GP/TLE is still absent. Ordinary
GPS timestamp conversion is qualified for a strictly bounded subset; full-source
time handling, quality approval and realization alignment remain incomplete.
No actual prediction/reference residual was generated.

Deliverables: [frame/time assessment](phase-11.3.1-frame-and-time-qualification.md),
[prepared historical-input request](phase-11.3.1-historical-input-request.md),
and [structured execution evidence](phase-11.3.1-integration-results.json).

## Baseline and preserved implementation

Branch `phase-10-evidence-replay`, HEAD
`be3710dae9f21bae817637d7bfdb87509b3f6a34`. Began with **45** modified/untracked
Phase 11 paths, all unstaged. Saved a **282-file** baseline, all eight private
Phase 11.3 source/receipt/inspection file hashes, original database SHA and complete
schema/table/integrity fingerprints. Fresh baseline execution passed **915 backend
tests and 344 frontend tests**; earlier reports were not assumed current.

Every requested report was present except the proposed filename
`observation-validation-methodology.md`; the actual guide is
`docs/observation-validation.md`. Inspected the retained source inspector, actual
KIN/VAL ZIP contents and metadata, prior inspection results, Phase 11 validation,
source/ingestion controls, SGP4 input conventions, strict Astropy/EOP/leap pipeline,
Phase 10/10.1 file integrity/replay and regression conventions. No existing source
file or prior report was changed. The original inspector was not silently revised.

The ordinary database is still schema 3 with two genuine ISS GP snapshots, no
Swarm-A GP, one ingestion attempt, one insertion record and one collection gate.
No ordinary initialization, migration, ingestion, reset, restoration or write
occurred. Locked dependencies, scientific tolerances and EOP policies are unchanged.

## Authentic reference audit and historical search

Reused the two genuine ESA ZIPs already present; **no duplicate product downloads**.
Current complete inspection exactly equals the previous captured source inspection:

| Retained product | SHA-256 |
| --- | --- |
| Swarm-A SP3AKIN_2_ 0201 | `a62164ca7940d415d63a81518a974422d7868b285abc2509423bac96bd9048b3` |
| Matching SP3AVAL_2_ 0201 | `e258ea6afb9bc998e406c5d2f7a26369d716d958da7d2961eb273b645adfeca2` |

All ZIP members were read and checked by hash, ZIP CRC, XML size and POSIX header
checksum. Product version 0201, software 44.88, UTC coverage, source filenames,
quality codes, 7,647 P/EP records, GPS time, km positions, IGb08 and absent velocities
were verified again. Original bytes remain private and ignored; no licensed source
coordinate fixture was placed in Git. Checksums alone are not scientific approval.

Swarm-A identity is established by the retained official ILRS mapping
**L47 / NORAD 39452 / ILRS 1306702**, corroborated by CelesTrak SATCAT
**SWARM A / 2013-067B**. It cannot yet be matched to a historical GP because none
was supplied. The reference is an external observation-derived processed orbit,
not raw measured XYZ or physical truth. Independence from an eventual GP fit is
uncertain; full SSN fitting lineage is unavailable.

Searched authorized project/attachment/prior-task data locations using bounded
text/JSON/TLE checks: **692 files** inspected, **11 identity mentions**, **zero
matching GP/TLE candidates**. Five over-2-MiB items were excluded and listed:
three generated maximum-track reports and two cached ESA specification PDFs.
Runtime/dependency/cache copies were excluded; credentials and secret configuration
were not searched. This is a scoped workspace search, not proof that no historical
data exists elsewhere. A read-only archive query separately confirmed zero catalog
39452 records and only two catalog 25544 records.

The earlier Space-Track request/401 error and CelesTrak CAPTCHA/email procedure
were inspected alongside current runtime credential readiness. No suitable identity
or credentials are configured. **No new Space-Track retry, CAPTCHA interaction,
form submission, authentication or email operation occurred.** The retained 401 is
historical evidence from Phase 11.3, not a newly executed request in this phase.
New network work was limited to nine bounded public frame/time documentation
requests, all HTTP 200; no GP or ESA orbit product was acquired.

The prepared request specifies verified catalog **39452**, **2013-12-30 through
2014-01-02**, original **GP JSON**, intended comparison purpose and required source,
epoch, availability, receipt, hash and reuse fields. The user must complete any
provider-required CAPTCHA, login or email submission. The document is ready for
that interaction but has **not been submitted**. No current input, another satellite,
fabricated element set or inferred acquisition time was substituted.

## Implemented qualification functionality

Added `scripts/qualify_swarm_inputs.py` and
`backend/tests/test_phase1131_qualification.py` (**48 new cases**).

The offline tool composes the unchanged source inspector and existing bounded
reads, GP JSON validation, explicit scientific-resource scope and hash/JSON
functions. It does not introduce a new TLE/SP3 framework or propagation engine.
There is no writable API, external fetch, database operation or approval switch.

Actual source-time diagnostics convert **5,118** ordinary, exactly microsecond-
representable GPS timestamps to UTC using Astropy TimeGPS with split seconds and
the retained leap resource. They exclude **1,806 submicrosecond** and **723
second-60** records without rounding or assuming rollover. All 7,647 records are
accounted for. Literal reference tests cover 1980, documented 2000 and historical
2014 instants, exact microseconds/date rollover, 2015/2016 leap boundaries, invalid
metadata, missing/expired resources and unsupported UTC leap-second output.

Converted subset bounds are `2014-01-01T00:02:04.000000Z` through
`2014-01-01T23:57:54.000000Z`. Time status is **QUALIFIED_WITH_LIMITATIONS for that
ordinary subset**, not full-source approval. First/last converted-epoch strict
EOP preflights pass, including ±0.5-second support; this is not an all-epoch frame
validation. Source time, header interval and actual audit clock are separate.
No GP epoch, retrieval, publication or scientific evaluation time was invented.

The optional GP diagnostic reuses the existing one-record parser with hash/size/
target/epoch checks. It rejects missing/empty/truncated/wrong-target/unsupported
records in synthetic tests. Parsing does not authenticate provenance or establish
historical availability: a supplied record remains PARTIAL without those facts.
No authentic GP was available, no new historical importer was validated and no
record was inserted into the archive. Multi-record attachments must be preserved
and reviewed rather than hand-edited to masquerade as an original single record.

## Frame and gate decision

New authoritative IGS documentation establishes **IGb08 aligned to the ITRF2008
datum** and explains its station discontinuity, tie and antenna updates. The
correct IGb08 directory and small station-change table were located and read;
the 110-MB SINEX covariance file was not downloaded. The earlier guessed 404 is
not treated as evidence that frame documentation does not exist.

Installed Astropy provides TEME→ITRS, with no named IGb08 frame or realization
selector in this application's ITRS representation. That does not prove a future
mapping impossible. It means a precision-scoped identity approximation or
realization-aware treatment, reference epochs/parameters, error budget and
independent tests are **not yet qualified**. Station-specific offsets and an
IGS05→IGS08 transformation are not repurposed for satellite states.

**Frame status: BLOCKED.** No new transform, tolerance or identity assumption was
applied. Additional documentation discrepancies remain unresolved: nominal ESA
SP3-c versus actual SP3-d, source nominal interval zero versus the normative
positive interval, and unapproved GPS second-60 encodings. Parsing and ordinary
timestamp conversion do not waive those qualification stops.

The gate records actual source integrity/identity, GP provenance/pairing, time,
frame, quality, documentation and lineage conditions. Output is **BLOCKED**,
`comparison_ready=false`, `adapter_operational=false`, no normalized observations,
zero prediction evaluations and null residuals. Tests intercept propagation and
residual functions and confirm they are never called even with a valid synthetic
GP-format candidate. The underlying Phase 11 workflows remain intact.

No selected reference interval was scientifically accepted from the retained
quality plots/codes. No GP/reference temporal overlap or availability cutoff was
verified. A future selection rule must be declared before discrepancies, e.g. the
earliest bounded set of otherwise qualified exact epochs, with all exclusions.
Unknown availability allows only the retrospective interpretation actually
supported; it cannot establish that OrbitIQ issued a historical forecast.
Prediction uncertainty remains **unquantified** and no independence claim is made.

## Actual verification

uv used `UV_CACHE_DIR=/tmp/orbitiq-phase1131/uv-cache`; script commands used
`PYTHONPATH=backend`; frontend commands ran in `frontend`. Structured evidence
records exact commands, exits, source/runtime identities and actual results.

| Check | Actual result |
| --- | --- |
| Fresh baseline `uv run --locked pytest -q` | **915 passed** |
| Final `uv run --locked pytest -q --junitxml=/tmp/orbitiq-phase1131/backend-final-state.xml` | **963 passed**, zero failures/errors/skips, including **48 new cases** |
| `npm test` | **344 passed**, 25 files; frontend unchanged afterward |
| `uv sync --locked`; Ruff lint / format | All exit 0; locks preserved |
| ESLint / Prettier / TypeScript noEmit / production frontend build | All exit 0 |
| Existing SGP4 / terrestrial / expanded science audits | **40 / 6 / 32** checks pass; observation accuracy remains blocked |
| Existing geodesy audit | **28** independent mathematical cases plus **28** separate round-trips pass |
| Existing golden evidence lifecycle | **6** published components and **3** exact offline replays pass |
| Existing controlled observation packages | **6** fresh offline replays pass; synthetic/reference tests, not ESA accuracy results |
| Actual qualification, three fresh offline processes | All audit commands exit 0 with BLOCKED decisions; invariant source/time/frame/gate projection matches exactly; zero network/database/process attempts |
| Relevant browsers | **77 flows** across Chromium/Firefox/WebKit, using genuine-history and separate synthetic-package contexts |
| Existing application PDF checks | **7 PDFs pass**, including all 361 maximum-track rows; distinct from the retained nine-page ESA quality PDF |
| Final preservation / whitespace | All 282 original files and eight private Phase 11.3 files unchanged; DB bytes/full fingerprint, HEAD/index preserved; diff check passes |

Initial new tests passed **47/47**. After an offline audit assertion showed that
full reports differed in live EOP table-age metadata, the tool was improved to
record one explicit audit clock shared by endpoint checks, and one regression
test was added. The entire final 963-test suite reran after that change. No
scientific tolerance, propagation convention or EOP policy was weakened.

The final three offline reports intentionally retain different audit clocks and
derived live resource ages. Only those explicitly named fields are omitted from
the exact invariant projection. Full JSON reports are **not byte-identical** and
no numerical propagation replay is claimed for these diagnostics. Failed initial
assertion evidence and initial outputs were preserved alongside final runs.

Known warnings remain: Starlette/httpx deprecation, the existing deliberate
duplicate-ZIP test warning, and the globe bundle-size advisory. Initial development
format/lint issues were corrected. Local health probes can fail during container
startup; final browser results and exact attempts are recorded. Owned verification
containers/network were removed; no host ports, release publication or production
deployment were performed.

## Acceptance criteria

**15 PASS / 3 PARTIAL / 4 BLOCKED / 0 FAIL.** Documentation of a blocker does
not turn the blocked scientific condition into a pass.

| AC | Status | Evidence / limitation |
| --- | --- | --- |
| 1 implementation/reports inspected | PASS | Actual baseline/code/reports/private sources inspected; missing filename resolved |
| 2 authentic ESA files verified | PASS | Complete pinned ZIP/member inspection matches previous result, source bytes unchanged |
| 3 product/spacecraft/quality/provenance documented | PASS | Actual headers, identity mapping and limits of quality plots/codes retained |
| 4 authorized historical-source search | PASS | Bounded local scan and archive query; retained source/access configuration reviewed, no denied-source retries |
| 5 genuine GP/TLE acquired/validated | BLOCKED | No authentic local candidate; provider interaction/access still required |
| 6 spacecraft identity matching | PARTIAL | ESA L47→39452 verified, but no historical GP to match |
| 7 temporal overlap/pair suitability | BLOCKED | No GP epoch/provenance/availability or accepted quality interval |
| 8 lineage/independence limits | PASS | External processed reference and unknown GP fitting dependencies disclosed |
| 9 actual GPS timestamp conventions | PARTIAL | GPS metadata and ordinary semantics verified; full-source precision/second-60 ambiguities excluded, not approved |
| 10 required conversions tested | PARTIAL | Literal/library/resource tests and 5,118 ordinary conversions; 2,529 source times remain unsupported |
| 11 reference frames/realizations identified | PASS | Actual IGb08, official ITRF2008 datum relationship and installed TEME/ITRS definitions checked; this is not alignment approval |
| 12 TEME→reference realization qualification | BLOCKED | No precision-specific approved mapping/error treatment to IGb08 |
| 13 EOP/leap requirements preserved | PASS | Explicit pinned resources, endpoint checks and missing/expired/failure rejection tests; no fallback or policy change |
| 14 invalid-residual gate | PASS | Computed blocked conditions; propagation/residual sentinels prove no calls |
| 15 actual-source adapter requirements | PASS | Explicit format/time/frame/units/provenance/quality/output requirements with unresolved gates |
| 16 qualified operational adapter | BLOCKED | No qualified pair; diagnostic composition only, no state importer or propagation adapter |
| 17 no fabricated residuals/results | PASS | Zero ESA prediction evaluations, empty normalized output, null residuals/accuracy |
| 18 existing data/evidence preserved | PASS | All starting source/report/DB/private-file hashes and full DB fingerprint retained |
| 19 scientific regressions | PASS | Full final suites, original numerical references/geodesy/replay rerun |
| 20 new tests where implemented | PASS | 48 final cases; actual retained-source and fresh offline diagnostics |
| 21 quality/build/browser checks | PASS | Final lint/format/TS/build, three engines and seven PDF checks |
| 22 remaining limitations/actions | PASS | Separate time/frame qualification and precise unsubmitted human request |

## Final boundaries and next action

No genuine historical GP/TLE was acquired; no GP/reference identity or temporal
pair was verified. Ordinary subset GPS conversion is qualified with limitations;
the entire source is not. Frame/realization alignment is BLOCKED. An operational
adapter and numerical residual calculation are **not justified by current evidence**.

Next action: the user obtains the original historical payload through the supported
human/account route described in the request document. In parallel, resolve the
provider format/time discrepancies, quality inclusion and a precision-specific
IGb08 treatment. Preserve source availability as unknown when it cannot be proved
and label any later permissible comparison retrospective. Do not lower scientific
bounds or repurpose another object's data to force a result.

Original DB SHA-256 remains
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
All earlier reports and immutable evidence were preserved. **No commit, push,
publication, deployment, remote CI dispatch/rerun, repository-remote change or
production-infrastructure operation was performed.** Local qualification checks,
GitHub publication, exact-commit CI, production deployment and Phase 8 infrastructure
verification remain separate milestones. Phase 8 hosting/domain/HTTPS, off-machine
recovery, real monitoring/alert delivery and branch-protection gates are not closed.


## Subsequent scientific qualification checkpoint — 21 October 2026

The earlier report above is preserved as its original execution checkpoint.
Historical GP is now present as a separate, hash-preserved CSV with three Swarm-A
records passing static checks; the original JSON still fails strict decoding.
The current [scientific pairing assessment](phase-11.3.1-scientific-pairing-report.md)
supersedes the historical absence/acceptance statements for current status and
records all 22 criteria, exact GP timing offsets and remaining prerequisites.
The [CSV intake checkpoint](phase-11.3.1-csv-intake-report.md) remains unchanged.

New redundant-header checks identify a 120-second disagreement between GPS
week/seconds-of-week and the first calendar epoch, plus a 37.12-ns MJD-fraction
discrepancy. Existing 5,118 ordinary calendar conversions / 2,529 exclusions are
preserved as conditional diagnostics; all 5,118 ordinary-epoch EOP preflights pass.
The exact KIN specification confirms VAL applicability to KIN as well as COM,
but KIN epoch-quality acceptance and IGb08 alignment remain unqualified.

Overall Phase 11.3.1 remains PARTIAL; scientific pairing and operational evaluation
remain BLOCKED. No genuine Swarm propagation, coordinate-state transformation,
real residual, publication, remote CI or deployment was performed. The
[clarification checklist](phase-11.3.1-scientific-clarification-request.md) was
prepared for manual review and was not sent.
