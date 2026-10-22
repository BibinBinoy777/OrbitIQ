# Historical change analysis, version 1

Open **Discovery & history → Historical analysis**, enter a stable NORAD catalog
identifier, and analyze the existing archive. This tool reads persisted records.
It does not ingest, initialize storage, run SGP4, transform coordinates, maintain
EOP resources, or create replay packages. Orbital calculations stay in the backend.

## Bounded history and clocks

`GET /api/historical-analysis?catalog_id=25544&limit=20` returns
`kind=orbitiq_historical_analysis`, `schema_version=1`, `rule_set_version=1`.
Catalogs are bounded to 1–339999; page sizes to 1–20; optional `before_id` and
`anchor_id` to positive JavaScript-safe integers. Invalid inputs return safe 422
errors. Storage and source errors use the existing API error boundary.

The service uses the existing indexed, query-only, budgeted snapshot listing.
It validates at most 20 exact sources, makes at most 19 adjacent comparisons, and
emits at most 200 findings. It rechecks validated source identities before return.
Missing archives are never created. API and gateway calculation limits cover this
route. No schema migration, additional dependency, collector, or persistence layer
was introduced.

Pages seek by descending insertion ID under a fixed upper anchor. Insertion IDs
are **not** chronological timestamps. The client renders one page, retains at
most 100 previous cursors, and never automatically traverses the full archive.
Next/previous pages preserve the anchor; refresh starts a new one. Counts are
anchored stored metadata counts (existing 1000-record count budget), not provider
population counts or a claim that every counted source passed provenance checks.

Within a page, unique valid retrieval times sort the timeline ascending. Missing
or equal times cause an explicitly labelled ID-only order. Comparison candidates
are adjacent in that displayed window; individually orderable candidates are
oriented by retrieval time. No claim of global adjacency is made for partial or
ambiguous windows. Comparisons do not bridge page boundaries automatically; use
the existing comparison view with the desired exact IDs for that case.

Each point retains its persisted ID, NORAD identifier, payload SHA-256, source URL,
validation provenance, retrieval timestamp, element epoch, separate insertion
metadata and actual validated normalized elements. An unusable persisted row
remains a point with no calculated values. Invalid/missing times are not inferred.
Epoch, retrieval and insertion time are different clocks. Legacy insertion time
can be unknown. These mean-element sets contain no independent observation time.
`generated_at` is the common analysis/rule evaluation clock; the null methodology
`calculation_at` denotes no requested **propagated orbital state**. Element
subtraction is evaluated when the report is generated. Capture recipes separately
specify any requested historical orbital calculation time.

Coverage reports inspected and provenance-validated counts, distinct payload
count, complete/partial scope, and extrema of valid source retrievals in this
window. They do not infer earlier/uninspected history. Fixture archives are for
controlled tests and must never be counted as genuine application history.

## Element differences and interpretation

The existing comparison service now exposes reusable source-validation and
already-validated-source comparison helpers. Both old and new views use its
`element_differences` calculation and the authoritative `ELEMENT_UNITS` mapping:

| Field | Unit | Formula |
| --- | --- | --- |
| `INCLINATION` | deg | later value minus earlier value, linear; no angular wrap |
| `ECCENTRICITY` | dimensionless | later value minus earlier value |
| `MEAN_MOTION` | rev/day | later value minus earlier value |

Finite compatible values must pass existing source hash, raw/normalized fields,
units, catalog, epoch, retrieval and provenance validation. Missing values are not
zero. No percentage, trend slope, statistical significance, anomaly classifier,
interpolation, extrapolation or forecast is produced. Existing cyclic RAAN,
argument-of-pericenter and anomaly conventions are unchanged in direct comparison;
those fields are not added to this phase's three-field change summaries.

Directional changes require reliable unequal retrievals, matching validated
identity, distinct payload hashes, nonreversed element epochs, and no future
retrieval relative to the evaluation clock. Missing/equal/conflicting/future
chronology or invalid sources yield unavailable results and explanatory findings.
Same-epoch distinct solutions can be subtracted, without claiming time evolution.

Zero or one suitable record cannot support historical change. Two support a
pairwise comparison only. Three or more display differences across the available
samples, without claiming a reliable long-term trend. Connecting lines are not
needed: the timeline uses separate semantic list items, without fictitious points.
Sampling intervals describe selected archived records only. A large interval is
not evidence of a provider outage or a missed scheduled collection.

Different published solutions may reflect estimation, source updates, epoch,
physical motion, data quality or other effects; these inputs do not identify the
cause. They do not independently establish a maneuver, anomaly, collision risk,
position accuracy, uncertainty estimate or operational safety.

## Deterministic finding contract

Every finding has schema/rule version 1, a `history.<rule>` identifier, deterministic
content-derived `finding_id`, category, recorded status, title, templated
explanation, catalog ID, exact source references, inputs, units/conditions where
applicable, result/calculation reference, assumptions, limitations, evidence
availability and reproduction status. Severity and confidence are null. There is
no LLM or probabilistic classification. The report includes every rule's condition
and category semantics.

| Rule | Trigger / facts | Category |
| --- | --- | --- |
| `coverage` | Always; suitable record count and window completeness | Incomplete data below three records; otherwise informational |
| `partial_window` | Earlier insertion window selected or more records remain | Incomplete data |
| `metadata` | Metadata issues or unknown legacy insertion timestamp | Incomplete data |
| `validation` | Existing full integrity/provenance checks or identity matching unavailable | Validation failure |
| `freshness` | Existing `classify` result is not fresh | Stale source data for stale; incomplete data for unknown/future epoch; informational for aging |
| `chronology` | Missing/equal retrieval, epoch reversal, repeated payload, future retrieval or unusable source | Comparison unavailable |
| `interval` | Absolute retrieval interval **>** configured stale-hours duration | Incomplete data; sampling flag only |
| `epoch_interval` | Absolute epoch separation **>** configured stale-hours duration | Informational |
| `comparison` | Existing comparison/chronology policy cannot support subtraction | Comparison unavailable |
| `element_change` | One per successfully calculated supported field | Informational |

Freshness uses the same `FreshnessPolicy` as readiness: defaults fresh through 24
hours, aging through 72 hours, stale above 72 hours, all based on **element epoch**.
Retrieval age stays separate. Invalid/future retrieval is unknown; a future epoch
has the existing future-epoch status when retrieval is already past. Configuration
must satisfy `0 < fresh < stale <= 168h`. The two interval rules reuse that
configured duration as an explicit conservative sampling/epoch separation flag;
they do not redefine freshness, impose a collection cadence or quantify accuracy.

For identical validated sources, window metadata, policy, evaluation time and
software/rule version, explanations, findings and report IDs are identical.
`history-finding-sha256:` hashes compact sorted-key JSON of the finding before its
ID is inserted. `history-report-sha256:` uses the same encoding over the complete
report before its ID is inserted (`allow_nan=False`, default ASCII escaping,
UTF-8). These are content identifiers, not signatures or provider authentication.
The evaluation clock is an internal reproducibility input, not a user-selectable
API means to bypass current freshness/readiness policy.

## Export and existing evidence/replay

**Export historical analysis JSON** downloads the already captured result, without
another request or calculation. It includes coverage limitations, exact source
identities, inputs, differences, all findings and rule semantics. It uses a distinct
version-1 historical-analysis kind and does not alter Phase 9's report schema or
Phase 10/10.1's fixed bundle format. No new PDF renderer or dependency was added.

Each available comparison contains a version-1 definition accepted by the existing
Phase 9 report generator and Phase 10 operator CLI. The UI can download that
capture definition. `capture_recipe_available_not_captured` means **no package
exists yet**; manifest hash and package URL remain null. Findings with no suitable
comparison carry unavailable/no replay evidence, rather than a fictitious link.
Use the existing comparison view for its report/export actions and state analysis.

For an operator who explicitly wants a new package, retain the downloaded definition
and run the existing CLI against the same configured archive and a new absolute
destination (never use an existing bundle directory):

```sh
PYTHONPATH=backend uv run --locked python -m orbitiq.maintenance.replay capture \
  --definition /absolute/path/comparison-definition.json \
  --directory /absolute/path/new-comparison-bundle
PYTHONPATH=backend uv run --locked python -m orbitiq.maintenance.replay verify \
  --directory /absolute/path/new-comparison-bundle \
  --expected-manifest-sha256 <separately-retained-capture-checksum>
```

Recipes request TEME at the later source epoch only when both source epochs are
within the existing seven-day propagation window; otherwise `at=null` permits
source/element inspection only. A recipe is not a claim that capture/SGP4 will
succeed. Existing exact-source checks can refuse changed/missing records.

Phase 10 verifies underlying comparison calculations, **not this new finding
schema or scientific interpretation**. Findings are reproduced separately using
the recorded rule inputs and evaluation clock. In this phase's actual audit, the
genuine pair's three field differences were checked against a newly captured
Phase 9 comparison and that exact package replayed in three fresh offline processes.
Replay retained its strict source/runtime/hash/resource constraints. No format,
scientific tolerance, EOP rule or ordinary API clock override was weakened.
Older bundles still require their original matching trusted backend checkout;
adding backend files changes the exact runtime identity. Preserve their bytes.

Re-run the bounded local genuine-archive audit without collection:

```sh
PYTHONPATH=backend uv run --locked python scripts/verify_historical_analysis.py \
  --database /absolute/path/existing-archive.sqlite3 --catalog 25544 \
  --directory /absolute/path/new-audit-directory
```

That operator audit pages up to 1000 archive records (fails explicitly at its
budget), validates actual sources, checks deterministic report reproduction,
captures available comparisons, runs detached offline replays and verifies database
preservation. It does not silently initialize or acquire anything. API analysis
retains its smaller per-request bounds. Broader genuine-history verification
requires controlled collection over time using the existing Phase 6 workflow;
repeated acquisitions must never be used to force a populated chart.
