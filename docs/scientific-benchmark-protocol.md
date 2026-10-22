# Scientific benchmark and independence protocol (proposal version 1)

Status: **protocol defined; concrete dataset and evaluation period not frozen**.
No real-world accuracy result is claimed. This protocol complements the existing
[observation methodology](observation-validation.md) without changing its version-1
contract or the completed scientific engine. The
[source review](phase-11-dataset-source-review.md) explains why existing ISS data
does not close the validation gate.

## Claim and lineage gates

Choose a claim before processing data:

1. **Implementation/reference-case agreement:** published mathematical vectors or
   labelled synthetic residual oracles. This verifies software arithmetic.
2. **Reference-product comparison:** SGP4 states versus a documented processed orbit
   at common epochs. Report discrepancies and reference limitations, including
   uncertain/shared lineage. This does not establish independent physical accuracy.
3. **Independent observation validation:** authenticated validation measurements,
   or explicitly qualified observation-derived states, whose lineage supports the
   specific independence claim against the prediction fit and processing chain.
   A trusted assessment is required; a distinct provider or timestamp is insufficient.

For each proposed benchmark retain a reviewed lineage record containing prediction
snapshot/catalog ID, exact GP raw bytes/hash, retrieval/epoch/insertion knowledge,
producer and fit/model version/interval if known, fitting observation identities
and weights if known, and an explicit unknown list. Reference lineage includes
provider, exact product/revision, sensor/record IDs, raw bytes/hash, retrieval and
processing times, processor/version, upstream observation sets, orbit models,
external GNSS/EOP/clock resources, quality report and licensing/citation evidence.
Link all derived normalized records to original member/line/epoch identities and
record every time/frame/unit transformation with version/resource hashes.

Do not treat a declaration in operator JSON as authentication. Preserve a separate
trusted receipt or archive anchor and who/what performed the lineage assessment,
when, its scope, evidence references and remaining qualifications. File hashes
prove byte identity only. Full GP fitting lineage is presently unavailable.

| Protocol assessment | Required basis | Allowed interpretation |
| --- | --- | --- |
| Independence established | Authenticated sources and sufficient reviewed fit/reference lineage exclude relevant reuse/dependence for the stated claim; shared resources and limitations explicitly assessed | Only the scope established by that review; no general certification of all model outputs |
| Independence uncertain | Sources appear distinct but fitting input identities, authenticity or relevant shared processing cannot be resolved | Descriptive comparison only; independently verified count zero |
| Independence not established | Duplicate/aliased records, known reused fit input or documented dependency invalidating the claim | Exclude duplicate/reused samples as existing rules require; otherwise disclose a reference-product/self-check rather than an independent metric |

After-GP-retrieval measurements are conditional temporal holdout candidates only.
They do not authenticate clocks, rule out shared processing or prove the output
was historically issued. For a future prospective claim, independently anchor the
input/capture *before* the validation epoch and retain the later reference lineage.
Retrospectively generated states remain labelled retrospective.

### Mapping to today's API, interface and JSON

Current `reused_prediction_payload` and duplicate exclusions represent detected
dependencies. `unverified_input_lineage`, `temporal_holdout_candidate_unverified`
and `unverified` remain uncertain, with `eligible=false`. These internal strings
are not a trusted three-state certification system. No API option promotes a
record to established independence. Summaries keep
`independently_verified_count=0` and `independent_error_metrics=null`.

The existing interface shows provenance, per-record `data_kind`, compatibility,
discrepancies and uncertainty limitations; JSON exports retain these exact captured
values. A prediction/CPF/TLE-derived trajectory must not be relabelled measurement
or observation-derived state to bypass the `model_output` rejection. Before adding
a processed reference product, its API/UI/export interpretation must explicitly
identify **reference-product comparison**, original product type and uncertain
independence. The current generic observation view is not a provider-adapter
integration or a certificate that such terminology is already implemented.
No such product was integrated here, so no application contract was changed.

## Proposed small benchmark: paired Swarm kinematic orbit comparison

Candidate identifier `swarm-kinematic-reference-v1` is a **protocol identifier**,
not an executed run, accepted dataset or result. Choose one verified Swarm spacecraft,
one final `SP3xKIN_2_` product/quality report and one genuinely archived matching GP
snapshot. Freeze its NORAD/mission/SP3-ID mapping, dates, product baseline and hashes
only after review. Do not mix spacecraft or use the ISS archive as its predictor.
Reduced-dynamic `SP3xCOM_2_` would be a separately identified study sharing inputs.

Final POD's documented 21-day latency requires historical GP provenance or
prospective GP capture followed by later POD release. A current GP input cannot
be propagated arbitrarily far backward to match a newly published final product.
Neither this protocol nor a future adapter may weaken the ±7-day rule.

### Inclusion and transformation rules

- Use the unchanged SGP4/WGS72 implementation and locked runtime. Record the
  exact initial snapshot and all run/environment/resource identities. For a
  prospective prediction claim, require an independently anchored source capture
  before every evaluation epoch; otherwise call it retrospective propagation.
- Inspect original SP3-c header/comments, product identity, center-of-mass
  convention, time system, frame realization, quality report and processing baseline.
  No filename/default alone supplies missing scientific metadata.
- Use only original, valid, nonpredicted position records for the selected target
  at exact provider epochs, inside the unchanged propagation/resource limits.
  Initial bounded capture: at most ten records, chosen deterministically as the
  earliest ten in the predeclared eligible interval, not by discrepancy magnitude.
  Record total candidates in that interval, selected records and exclusions.
  This small sample describes those epochs; it is not representative global accuracy.
- Convert GPS-calendar epochs using a documented, tested GPS/TAI/UTC relation and
  retained leap-second resource, never by relabelling or assuming a constant modern
  UTC offset across the archive. Preserve the original timestamp and precision.
  Epochs not exactly representable by the current microsecond contract must be
  excluded until a separate precision change is justified; do not silently round.
- Verify the terrestrial realization's relationship to ITRS for the claimed error
  scale. Record the alignment method/parameters and any approximation uncertainty.
  If it is unjustified or required resources are unavailable, block the comparison.
  Propagate at each exact UTC epoch and use existing strict TEME→ITRS; never
  subtract TEME from ITRF, ICRF/J2000 or an unspecified Earth-fixed frame.
- SP3 positions are km; if an approved source supplies m, use exactly `0.001`.
  Preserve units and original values. Satellite center of mass must match the
  calculated Earth-centered position interpretation; antenna/reflector offsets
  cannot be silently ignored. Reference velocities are unnecessary for this first
  position-only study. Do not mistake dm/s velocity fields for km/s.
- Exclude missing/sentinel/nonfinite position fields, duplicate identity/alias,
  rejected/unsupported quality, predicted segments, mismatched target/epoch/frame,
  incomplete required provenance and failed propagation. Keep a reason for each.
  An unknown sigma is not a zero position or zero uncertainty. No interpolation,
  extrapolation, orbit fitting, residual-based clipping or hidden gap filling.

Full source/product/quality bytes and legal retention rights must be settled
before a small fixture is checked into Git. A normalized ten-record excerpt alone
cannot establish original product provenance; preserve upstream bytes in an
explicit evidence location or immutable accessible archive with trusted hashes.
Provider ZIP handling, if needed later, must be bounded and reject unsafe paths,
links, duplicates and decompression excess. No archive extraction code is added now.

### Residuals, coverage, uncertainty and valid evaluation

Residual sign is **reference minus predicted**, agreeing with existing
observed-minus-predicted arithmetic for a correctly classified observation-derived
state. Compute common-frame XYZ and Euclidean norm in km. Existing ITRS comparisons
do not provide an inertial RAC basis; leave RAC unavailable. At least two usable
records in the same frame are needed for aggregate component bias/MAE/RMSE,
maximum/median absolute discrepancy and population dispersion (denominator N).
Report norm mean/RMS/max/median separately, RMS denominator N. No confidence,
IID/population claim or extrapolated error-growth trend follows from these values.

Record candidate/selected/usable/excluded counts, exact epochs, source epoch offsets,
retrieval-relative intervals, oldest/newest usable epoch and sampling gaps. Compare
against a documented provider cadence only when its applicability is known; missing
measurements and operational outages cannot be inferred from a ten-point excerpt.
Different frames, products, initial conditions or runs are not pooled silently.

Prediction uncertainty remains **not quantified**. A nominal 10-cm product
specification does not define per-axis sigmas and cannot be assigned as covariance.
Preserve genuine uncertainty metadata and its definition, frame, epoch, dimensions,
confidence/scale convention and correlations where available; unsupported forms
stay separate, not coerced into the current axis-sigma field. No weighting,
standardized residuals, significance test, confidence interval or model-superiority
claim is allowed with the present inputs. A future joint-covariance method would
need covariance transport, prediction/reference cross-correlation and a reviewed
statistical interpretation; this proposal does not implement or validate one.

A valid *reference-product evaluation* requires the frozen input/reference manifest,
reviewed compatibility/quality, at least one traceable residual and exact replay;
aggregate reporting needs at least two compatible samples. A valid *independent
accuracy evaluation* additionally needs established independence for its scoped
claim. Zero compatible samples is blocked/unavailable, never zero error or success.
No pass threshold in kilometres is invented before scientific requirements and
reference limitations are agreed. Successful replay is reproducibility, not accuracy.

## Evidence and reproduction requirements

For each accepted dataset create a new, exclusively reserved run location. Retain
original payloads and hashes, retrieval receipts without credentials, source terms
and citations, product quality/processing metadata, target mapping, lineage decision,
normalization code/version and original→normalized record map. Retain prediction
definitions, runtime/lock/backend hashes, EOP/leap bytes and every exclusion.
Do not overwrite an existing database, evidence directory or prior report.

After a narrow adapter and explicit reference-product labelling have been reviewed,
reuse the existing capture/verification CLI documented in
[observation-validation.md](observation-validation.md). The operator supplies a
reviewed normalized file and exact existing snapshot ID; the CLI does not download
or authenticate a provider. Retain its trusted top-manifest SHA separately. Verify
three times in fresh, matching-runtime processes with network/database access
denied; compare captured values/metrics and require each needed prediction replay.
Export the captured report, compare JSON values/provenance to the run and verify
the UI does not recompute scientific numbers. Failed/unavailable records stay visible.

The final scientific report must contain dataset/run identity and period; raw
source/provenance and rights; initial conditions/model; candidate/usable/excluded
counts/reasons; reviewed independence; frame/time/unit transformations; residual
method and actual metrics; uncertainty; cadence/coverage; scientific limits;
exact reproduction commands and checks. Unavailable sections are explicit nulls
with reasons. Publish no numeric results until a real evaluation actually runs.

## Required adapter tests when the dataset gate opens

Existing observation/history tests already cover arithmetic oracles, invalid and
missing normalized fields, duplicate/reused inputs, unsupported units/frame/type,
future epochs, absent uncertainty, sparse samples, replay/tamper rejection and
JSON export. They do not test a provider parser that does not exist.

A future source-specific adapter additionally requires retained genuine licensed
records and invalid derivatives, header/time/frame/target mismatch, date-dependent
GPS→UTC conversion (including historical offsets and precision refusal), SP3
sentinels/flags, source/quality lineage conflicts, deterministic sample selection,
original-byte/record mapping and repeated end-to-end benchmark reproduction.
Expected residuals must come from separately checked reference examples, not from
OrbitIQ output renamed as ground truth. Synthetic examples remain labelled
mathematical tests. Run existing backend/frontend, scientific, browser, formatting,
lint/type/build and preservation checks after that code change.
