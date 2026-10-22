# Observation validation and prediction discrepancies (extension version 1)

Historical change analysis compares published element sets. This extension compares
an explicitly supplied position record with a propagated state at the same epoch.
These quantities and their evidentiary strength remain separate. There are currently
**zero supplied/configured independent observations**. The two genuine ISS GP
snapshots are propagation inputs, not measurements or independent ground truth.

The existing SGP4/WGS72 engine and Astropy TEME/ITRS transformation are reused.
No external observation source, downloader, collector or automatic ingestion was
added. No observation is populated into the ordinary archive. Mathematics and
integration tests use labelled isolated reference-derived/synthetic fixtures.

## Supported input and interpretation

An operator supplies a UTF-8 JSON file with exactly `kind`, `schema_version` and
`observations` fields. Kind is `orbitiq_observation_input`, integer version is 1,
and the observation array contains **1–10** records. Empty available history is
reported by the read-only API; it is not populated by a demonstration dataset.
Input is bounded to **64 KiB**, uses the existing depth/node/collection/string
budgets, and rejects duplicate JSON keys and nonfinite numbers. Invalid individual
records remain in the captured evidence with explicit exclusion status.

The [generated observation-record schema](observation-record.schema.json) describes
valid record structure. The schema describes supported normalized input; it is
not a provider-specific scientific data adapter. Each record requires:

- Stable observation ID, target NORAD ID, source ID and underlying source-record
  reference. Source organization, retrieval time and upstream payload hash may be
  unknown and remain null.
- Explicit observation timestamp with timezone, declared time scale, frame, origin,
  position unit, measurement type, data kind, three finite components and quality.
- Optional provider/operator-referenced axis standard deviations with explicit
  units and nonnegative values. They are preserved and normalized for inspection.

Only `geocentric_cartesian_position`, Earth-center origin, **UTC**, **TEME or ITRS**,
and **km or m** are supported for residuals. Input components have magnitude at
most `1e9` in their declared unit; residual components/norm have a `1e12 km`
numeric guard. No raw range, angular measurement, geodetic coordinate, GCRS state,
orbital element or unknown-unit record is directly subtracted. Unsupported fields,
covariance formats or required transformations produce explicit unavailable/invalid
results. They are not silently reinterpreted. Original input bytes/records survive.

Quality `rejected`, model-output/unknown data kind, inconsistent retrieval ordering,
future observation, target mismatch or incompatible definitions fail compatibility.
Quality `unknown` is retained without implying verified measurement quality.
Retrieval metadata may be missing; its absence is visible, not invented. Unknown
source authenticity remains a limitation for every record.

For compatible inputs the prediction is evaluated at the observation's exact UTC
epoch. ITRS converts the **prediction** with the existing strict EOP/leap policy;
the recorded observation retains its declared frame. Metres convert to km with
factor `0.001`. Source epoch, source retrieval, observation time, observation
retrieval, prediction generation and run evaluation are separately recorded.

Every prediction retains the exact source ID/catalog/epoch/retrieval/raw-payload
hash, requested time/frame, calculation generation time, SGP4/WGS72/model versions,
source freshness warnings, and applicable EOP/leap hashes/versions/flags. A negative
interval from source retrieval to observation is not a forecast horizon. Results
are always labelled **retrospective propagation from archived input**, never an
assertion that OrbitIQ issued a forecast before the observation occurred.

## Independence and authenticity

There is deliberately **no automatic `independence_verified` route**. The current
CelesTrak GP archive does not identify all observations used in its fit, and the
new file input is operator-normalized, not an authenticated provider feed.

- Repeated observation IDs or repeated `(source_id, source_record_reference)`
  identities exclude **all** ambiguous copies in a run.
- A declared payload hash plus the same underlying record reference also detects
  aliases across source IDs. One provider payload may legitimately contain multiple
  different observation records; payload equality alone is not a duplicate rule.
- An observation declaring the same payload as the prediction input is flagged
  `reused_prediction_payload` and excluded from independent comparison.
- An observation after archived source retrieval is a
  `temporal_holdout_candidate_unverified`, conditional on truthful clocks and
  provenance. This is not authentication or independently established lineage.
- Earlier/equal observation time leaves `unverified_input_lineage`: reuse in fitting
  cannot be excluded. Different IDs, providers or database rows do not prove
  independence.

Compatible unverified samples can yield **descriptive discrepancies**, but the
independently verified count remains zero and independent-error metrics remain
null. No checkbox, source-name heuristic or forged hash can promote them to
verified independence. Hashes verify retained bytes, not provider authenticity.
An upstream payload hash is a declaration unless the original upstream bytes and
an appropriate adapter/verification process are supplied in future approved work.

Genuine independent validation therefore remains blocked by both missing data and
the need for reviewed source lineage/authenticity evidence. Supplying an arbitrary
JSON file is not sufficient to close that scientific gate.

## Residuals and statistics

Residual convention is **observed minus predicted**. Both values must describe the
same target, UTC epoch, coordinate frame and normalized unit.

For position vectors `o` and `p`, `d_i = o_i - p_i`; position discrepancy is
`sqrt(d_x² + d_y² + d_z²)` in km, evaluated with `hypot`.

Optional TEME radial/transverse/normal components use
`R=r/|r|`, `C=(r×v)/|r×v|`, `A=C×R`, then dot the residual with each unit axis.
"Along track" means transverse and is not generally the velocity direction.
Zero/ill-conditioned angular momentum (`|r×v| <= 1e-12 |r||v|`) makes RAC
unavailable. No rotating-frame RAC basis is substituted for ITRS. XYZ discrepancy
can remain available when RAC is not supported.

At least **two compatible samples in the same frame** are required for aggregate
statistics. There is no aggregation between TEME/ITRS or across separate runs.
For scalar component residuals `e_j`, with `N` compatible samples:

| Metric | Formula / interpretation |
| --- | --- |
| Bias | `sum(e_j)/N` |
| MAE | `sum(abs(e_j))/N` |
| RMSE | `sqrt(sum(e_j²)/N)` |
| Maximum absolute | `max(abs(e_j))` |
| Median absolute | median of `abs(e_j)` |
| Population dispersion | `sqrt(sum((e_j - bias)²)/N)` for this finite sample set |

The vector position-norm summary separately reports mean norm, RMS norm, maximum
norm and median norm. RMS norm uses denominator **N**, not `3N`. No norm bias is
labelled a signed position bias. All statistics are unweighted descriptive values,
not estimates for an independent/IID population. One sample still permits an
individual residual but aggregate values are null; zero samples never imply zero
error. Every invalid/duplicate/incompatible/failed sample and its reason remains
in the report. No outlier rejection, fit, interpolation or extrapolation is used.
Available observation epochs, intervals and retrieval-relative horizons are retained;
there is no assumed observation cadence to infer missing measurements or outages.

Observation axis sigmas are preserved and normalized without assuming diagonal
joint covariance. GP prediction covariance is absent. Consequently joint
uncertainty, significance tests, confidence intervals, standardized residuals and
weighted statistics are **unavailable**, not zero. Covariance-aware validation
requires an additional scientifically justified method and actual inputs.

## Evidence packages, persistence and local authorization

The existing SQLite schema stays at 3. No migration is necessary: this extension
creates opt-in immutable **file evidence packages**, following the existing replay
bundle approach. It does not add another scientific snapshot database or writable
HTTP API. A run is a new private directory named by 32 lowercase hexadecimal
characters, containing `observations.json`, `report.json`, `manifest.json` and
up to ten `prediction-0` … `prediction-9` directories.

Original observation input bytes are retained exactly. The manifest hashes both
input and authoritative report and pins each nested prediction manifest. Existing
fixed-member bounds, regular-file/no-symlink checks and hash checks are reused.
Nested packages retain the Phase 10/10.1 format unchanged. TEME uses the existing
position report; ITRS uses an exact source self-comparison to capture the supported
transformation. That self-comparison is a propagation self-check, not a second
observation or independent evidence.

The wrapper records every source, state, input, residual, metric and finding.
Read inspection verifies source/value lineage, recomputes inexpensive arithmetic
from preserved inputs, and checks file hashes; it does not trigger ingestion or
orbital replay. Saved report inspection does not require the original runtime's
backend hash to match. **Numerical propagation replay does**, and uses the existing
strict verifier and exact captured EOP/leap bytes without resource substitution.

The manifest is written last. Interrupted packages lack a seal and remain explicit
unavailable evidence rather than successful runs. Exclusive directory/file creation
refuses existing destinations, including concurrent captures using the same run ID.
Repeated GET/export returns the captured result. Separate captures are separate
runs; no cross-run statistical deduplication or aggregation is claimed.

Creation/verification is a local operator CLI using filesystem permissions. Packages
are created mode 0700 with files mode 0600. The optional
`ORBITIQ_VALIDATION_ARCHIVE` is an explicit existing absolute directory containing
only operator-approved packages that may be served to this application. It is not
selected by HTTP parameters. Keep it unset for ordinary development with no
observations. Do not mount private evidence into a public deployment without an
appropriate access policy. No user-account authorization system or public upload
service is claimed by this extension. Source paths/credentials are not echoed by
API failures. A read-only runtime mount is sufficient for inspection.

Example operator workflow (placeholders are not observation data):

```sh
# Existing archive and genuine operator-reviewed observation input required.
# Create the dedicated output parent explicitly; the CLI reserves a NEW run leaf.
export ORBITIQ_DATABASE_PATH=/absolute/path/to/existing.sqlite3
PYTHONPATH=backend uv run --locked python -m orbitiq.maintenance.observation_validation capture \
  --snapshot <exact-existing-source-id> \
  --observations /absolute/path/reviewed-observations.json \
  --directory /absolute/path/validation-evidence/<new-32-lowercase-hex-run-id>

# Retain the returned manifest checksum separately from the package.
PYTHONPATH=backend uv run --locked python -m orbitiq.maintenance.observation_validation verify \
  --directory /absolute/path/validation-evidence/<same-run-id> \
  --expected-manifest-sha256 <trusted-capture-checksum>

# Opt in to serving captured evidence through the existing local API.
export ORBITIQ_VALIDATION_ARCHIVE=/absolute/path/validation-evidence
```

`reproduced` means the captured compatible arithmetic and its prediction replays
succeeded; it does not establish observation authenticity or scientific accuracy.
`validated_no_compatible_samples` means no numerical sample succeeded; it is not a
prediction-error pass. A required compatible prediction returning unavailable
blocks reproduction. Individual unavailable captures never count as matched.

Back up entire immutable run directories, including all nested resources. Copy to
an exclusively new destination with `shutil.copytree` (no existing-directory merge),
retain the original run-ID leaf name, and verify against the separately retained
manifest hash. Restore to a **new parent**, never over an existing run or database.
Select that parent explicitly only after verification. Preserve the matching
trusted source checkout/runtime for later propagation replay. Task-local copies
are not independent/off-machine recovery or production backup verification.

## Read-only UI and API

- `GET /api/observation-validations`: configured/empty/unavailable listing. At most
  100 fixed-name run directories; other entries or over-limit roots are refused.
- `GET /api/observation-validations/{run_id}`: bounded validated saved report.
  Invalid IDs return 422; absent configuration returns 404 for detail, while the
  listing explains the empty dependency; unsafe/incomplete evidence returns safe
  503 errors. Only GET exists. Runtime workload and gateway calculation admission
  apply to detail requests; no endpoint initiates a capture, replay or acquisition.

Open **Discovery & history → Observation validation**. With no evidence there are
no fictitious selection controls/results. Captured runs expose prediction source,
observation detail, compatibility, discrepancy samples, same-frame metrics,
unknown independence, missing uncertainty, findings and limitations. Sample tables
are the error timeline; they do not imply a populated historical trend.

JSON export uses the existing Phase 9 `reportJson` serializer on the captured
canonical result. It does not recompute scientific results in the frontend. This
report has a separate `orbitiq_observation_validation_report` version-1 kind;
Phase 9's strict report schema and printable formats remain unchanged. Exported
JSON preserves references/hashes and limitations but is not itself the entire
nested replay package. Finding schema/rule version 1 uses deterministic templates
with content-derived SHA-256 IDs, null severity/confidence and exact observation,
prediction, compatibility, residual and evidence references.
