# Phase 11 follow-up — independent dataset and scientific benchmark review

Local review on **20 October 2026 UTC**, branch `phase-10-evidence-replay`, HEAD
`be3710dae9f21bae817637d7bfdb87509b3f6a34`. Started with 36 unstaged modified/new
paths from the completed Phase 11 and extension work. No commit, push, merge,
workflow dispatch, deployment, DNS or production-infrastructure change occurred.

**The data/provenance investigation and benchmark design are complete locally.
Genuine independent accuracy validation remains incomplete.** No compatible,
authenticated independent reference paired with the two archived ISS inputs was
established. No real-data accuracy benchmark ran and no prediction-error numbers
are reported. Passing software tests do not close that scientific gap.

This task adds only this report, the
[dataset source review](phase-11-dataset-source-review.md),
[independence/benchmark protocol](scientific-benchmark-protocol.md), and
[structured evidence](phase-11-followup-integration-results.json). No application,
test, schema, dependency, configuration or existing documentation file was changed.
No adapter was justified before obtaining a reviewed, paired dataset. The original
Phase 11 and extension reports retain their historical acceptance records.

## Individual review of outstanding extension criteria

The prior extension reports **9 PASS / 3 PARTIAL / 1 BLOCKED**. These four gaps
remain; the follow-up does not retroactively promote them.

| Extension criterion | Already implemented | Missing evidence | Data/code requirement and next action |
| --- | --- | --- | --- |
| AC-02 observation provenance — BLOCKED | Bounded normalized contract; original operator input, source/record identifiers and declared hashes retained; no fabricated measurements | Genuine compatible source bytes, authenticated acquisition/record provenance, target/time/frame/quality and applicable retention terms | Data first, then a narrow reviewed source adapter and original→normalized map. Acquire a real matched dataset; arbitrary JSON is insufficient. |
| AC-04 independence handling — PARTIAL | Duplicate/alias and known payload reuse exclusions; unknown fit lineage and conditional temporal holdout remain unverified; independent metrics null | Authentic fitting/reference lineage and a trusted claim-scoped assessment, including shared GNSS/EOP/processing inputs | Data plus future review-record integration if independence can be established. Use the new three-case protocol; retain uncertain status where SSN fit details are inaccessible. |
| AC-07 uncertainty — PARTIAL | Optional reference axis sigmas retained/normalized; missing prediction covariance explicit; no unsupported weighting/significance | Prediction covariance or a justified calibrated uncertainty model, reference covariance/meaning/correlations and an appropriate joint method | Scientific inputs and separately justified code. Keep prediction uncertainty unquantified. A nominal product accuracy statement is not per-axis covariance. |
| AC-10 evidence export — PARTIAL | Captured canonical JSON and nested replay references; exports verified in three engines | A genuine evaluated reference/independent run with traceable inputs; independent accuracy additionally needs established independence | Real data and interpretation review first. Reuse capture/export; explicitly label a processed reference-product comparison before integrating that source. |

Original Phase 11's broader genuine three-or-more-snapshot historical verification
also remains constrained by its two-record archive. It was not closed by producing
additional mathematical fixtures or by researching reference products.

## Findings and selection decision

- CelesTrak GP is the correct SGP4 mean-element input, not independent position truth.
- NASA/JPL Horizons' actual ISS metadata explicitly says **TLE-based**. SSCWeb's
  actual ISS provenance also identifies TLE input. An authoritative host does not
  make these trajectories independently observed positions.
- NASA CDDIS/IGS products offer processed GNSS reference orbits with documented
  SP3 conventions. They require different target inputs, identity/time/frame review,
  access arrangements and source-specific quality/lineage; no current ISS pair exists.
- ILRS CRD contains genuine range-related observations, which the current
  Cartesian-position comparison does not model. CPF contains predictions.
- Previously known NASA ISS OEM URLs returned 404. They provide no current
  dataset evidence. HTTP-200 placeholder/not-found pages and IGS 503 responses
  were identified rather than counted as documentation success.
- ESA Swarm kinematic POD is the best documented LEO *candidate for a separate
  reference-product comparison*. Its specification identifies GPS time, ITRF,
  center-of-mass km positions, GPS/IGS/IERS/CODE upstream inputs, quality reports
  and final-product latency. Directory listings confirm historical product names;
  they do not prove a selected file's quality, uncertainty or download success.

No dataset was selected for ingestion. The archive has only ISS GP, no Swarm GP,
and no independent observations. A specific paired Swarm product/quality report,
mission/SP3/NORAD mapping, original bytes, processing baseline, current applicable
reuse conditions and lineage decision are still required. The documented **21-day
final POD latency** exceeds the ±7-day propagation limit for a GP fetched only at
reference release. Obtain authentic historical GP or capture prospectively and
wait; never forge earlier retrieval metadata or widen scientific bounds to force
a benchmark. Documentation research did not create a data-use agreement, register
accounts, or redistribute provider orbit products.

The protocol defines exact-epoch reference-minus-predicted residuals, unweighted
same-frame descriptive statistics, exclusions/coverage, preserved evidence and
fresh-process replay. It forbids GPS→UTC relabelling, frame guessing, interpolation,
residual-driven sample selection and confidence without covariance. Its candidate
run period, exact inputs and actual numerical results remain **unavailable**.
The nominal Swarm 10-cm 3D specification is not assigned as reference axis sigmas
or OrbitIQ uncertainty. Prediction uncertainty remains **not quantified**.

## Actual verification

Checks below reran in this task against unchanged application/test bytes. The
273-file starting manifest and full original database schema/table fingerprints
were saved before research or edits. Scientific scripts used `PYTHONPATH=backend`;
uv used `UV_CACHE_DIR=/tmp/orbitiq-phase11-followup/uv-cache`. Exact command records,
source/log hashes and results are in the structured evidence; task-local raw logs
and browser/PDF artifacts are under `/tmp/orbitiq-phase11-followup`.

| Check | Actual result |
| --- | --- |
| `uv run --locked pytest -q --junitxml=/tmp/orbitiq-phase11-followup/backend.xml` | **874 passed**, zero failures/errors/skips, including all 46 extension cases |
| `npm test` in `frontend` | **344 passed**, 25 files, including 14 extension cases |
| `uv sync --locked`; Ruff lint / format check | All exit 0; locks unchanged |
| ESLint / Prettier / `tsc --noEmit` | All exit 0 |
| `npm run build` | Exit 0; TS/Vite production build succeeds |
| Existing SGP4 published reference audit | **40** comparisons pass |
| Existing terrestrial reference audit | **6** cases pass |
| Existing expanded science audit | **32** comparisons pass; observation validation still BLOCKED |
| Existing geodesy audit | **28** independent mathematical cases plus **28** separate round-trips pass |
| Existing golden evidence lifecycle | **6** published vector components and **3** exact offline replays pass |
| Genuine archive history audit | Complete two-record pagination, deterministic repeat and **3** exact detached comparison replays; zero acquisitions; original database preserved |
| Existing controlled observation packages | **6** fresh-process offline wrapper replays (three TEME, three ITRS); no network/database/process attempts; labelled synthetic arithmetic, not accuracy evidence |
| Actual browsers | **77 flows**: 24 history, 21 critical investigations, 14 Phase 9 reports, 6 genuine-empty and 12 controlled synthetic observation flows; Chromium/Firefox/WebKit |
| `python scripts/verify_report_pdf.py --directory /tmp/orbitiq-phase11-followup/browser/reports --output /tmp/orbitiq-phase11-followup/pdf.json` | **7 PDFs pass**, including all 361 maximum-track rows |
| Final whitespace / preservation checks | Exit 0; every starting file unchanged, original DB/schema/rows preserved, index empty and HEAD unchanged |

The requested normalized-record coverage already exists in
`backend/tests/test_observation_validation.py`: supported capture, missing/invalid
fields and provenance references, duplicate IDs/source aliases, bad units/frame/
measurement/target/time, unavailable uncertainty, insufficient samples, GP payload
reuse and uncertain temporal lineage, literal residual/statistics/RAC oracles,
capture/replay/tampering and read-only API. Frontend tests and actual browser
downloads verify the captured JSON. Full history/export/replay regressions passed.
No provider parser was added, so no synthetic parser tests were invented to stand
in for missing real-data ingestion. Provider-specific records, conversion edge
cases and benchmark reproducibility tests are explicitly deferred with the dataset
gate in the new protocol.

No test or browser flow failed in this run. Six initial local health probes returned
exit 1 while containers started, then readiness succeeded; all verification commands
completed successfully. Source discovery's 404/503 and semantic not-found responses
are actual unresolved/rejected sources, not successful retrieval claims. Existing
Starlette/httpx deprecation and 558.60-kB globe-chunk warnings remain. Chromium
151.0.7922.34, Firefox 153.0 and WebKit 26.5 had no recorded page errors/CSP violations.
WebKit native printing, physical printers, full accessibility certification and
universal cross-host bitwise reproducibility are outside these checks.

Browser runs used isolated local containers with exact current backend/dist copies
and no published ports. Genuine-history/empty-observation tests and synthetic
fixture-package tests used separate read-only archives. Local retained images were
verification runtimes, not newly built or published production release images.
Owned containers and the internal network were removed afterward.

## Preservation and milestones

Original SQLite SHA-256 remains
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Schema 3, both genuine snapshots, one ingestion attempt, one insertion record and
one collection gate, including indexes/triggers, are unchanged. No ordinary
initialization, migration, restoration, collection or write occurred. All 273
starting files, including existing reports/artifacts and uncommitted code, retain
their hashes. The new four documentation/evidence paths are unstaged.

| Milestone | Status |
| --- | --- |
| Local review, protocol and regression verification | Verified as above; data benchmark blocked |
| Publication of Phase 11 / extension / follow-up | Not committed or pushed; pre-existing work remains local |
| Remote CI for this work | Not run; no exact published commit exists |
| Production deployment | Not performed |
| Production infrastructure verification | Not established here; Phase 8 hosting/domain/public HTTPS, off-machine recovery, actual monitoring/alert delivery, publication/CI and branch protection/required checks remain separate gates |

## Follow-up acceptance

**9 PASS / 1 PARTIAL / 2 BLOCKED / 0 NOT STARTED.** This task's criteria are
distinct from the original Phase 11 and extension criteria.

| Criterion | Status | Evidence / remaining dependency |
| --- | --- | --- |
| AC-01 outstanding criteria individually reviewed | PASS | Four-row audit above, with implementation/data/code/next-action distinctions |
| AC-02 compatible source identified or lack documented | PASS | Authoritative source review documents no accepted independent pair for available ISS inputs, plus a conditional Swarm reference-product candidate; not a proof that no source exists anywhere |
| AC-03 provenance and licensing/access assessed | PASS | Actual documentation/metadata/listing receipts and source-specific missing lineage, login and onward-distribution constraints; no blanket license or data accessibility claim |
| AC-04 independence protocol documented | PASS | Established/uncertain/not-established cases, trusted evidence requirements and current API/UI/export mapping |
| AC-05 compatibility requirements documented | PASS | Actual engine/data contract and target/center/frame/time/unit/precision/quality gates |
| AC-06 reproducible benchmark protocol defined | PARTIAL | Reproducible conditional procedure exists; no frozen matched dataset, period, mapping, product lineage or executable source adapter |
| AC-07 real-data ingestion/validation for selected source | BLOCKED | No accepted paired dataset; no provider adapter implemented. Accessible documentation/listings do not satisfy source/fit/compatibility gates |
| AC-08 benchmark results traceable to inputs | BLOCKED | No genuine real-data benchmark executed and no accuracy result to trace; software/reference/replay evidence remains separately traceable |
| AC-09 uncertainty assessed or explicitly unquantified | PASS | Prediction uncertainty unquantified; product nominal accuracy not coerced into covariance; extension AC-07 remains PARTIAL |
| AC-10 results and scientific limits documented | PASS | No real-world error metrics; source exclusions, reference-product distinction and precise missing evidence recorded |
| AC-11 existing Phase 11 intact | PASS | Starting file hashes, database fingerprints, history/observation/browser regressions unchanged |
| AC-12 applicable checks/build pass | PASS | Actual full suites, science, replay, three engines, PDFs, lint/format/TS/build evidence above |

Recommended next task: **freeze one paired Swarm kinematic reference-product
dataset** with authentic historical GP (or plan prospective capture and wait for
final POD), exact target mapping, quality/processing metadata and applicable data
terms. Review that finite dataset and lineage, then implement only the narrow
SP3-c/time/frame adapter and explicit reference-product reporting that it requires.
Keep independence uncertain unless stronger evidence becomes available. A successful
processed-product comparison can provide useful evidence while the independent
physical accuracy and prediction-uncertainty gates remain open.
