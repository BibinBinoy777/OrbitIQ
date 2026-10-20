# Scientific evidence integrity and replay contract

Phase 10.1 hardens the existing Phase 10 directory bundle. The format remains
`kind="orbitiq_replay_bundle"`, `schema_version=1`; no migration or archive format
has been introduced. These two required fields identify **directory evidence
format 1**. The embedded report's schema and template versions must both be 1.
Missing/boolean/unknown versions are rejected, rather than defaulted on import.
The source contract is defined by `replay_contract.py`, `reporting.py` and the
additional scientific preflight. There is no public package upload endpoint.

## What is guaranteed within the supported scope

Validation checks bounded package structure, exact member bytes, the matching
trusted installed software/backend source, exact archived source linkage, request
parameters and original result metadata before orbital replay. Replay uses the
existing SGP4/WGS72 and Astropy/WGS84 calculations with explicitly captured local
resources and historical policy clock. It never substitutes a newer source or
resource. The original report and source bytes remain unchanged.

Integrity means consistency with the manifest's recorded bytes. Authenticity means
association with a trusted producer. SHA-256 does not supply the latter. Without a
separately trusted manifest digest, a complete forged bundle can replace its own
hashes. Supplying `--expected-manifest-sha256` pins externally trusted capture bytes;
it is not a signing identity, independent timestamp, provider signature, satellite
observation or accuracy certificate. No signing/key-management system was added.

## Manifest and scientific inputs

The manifest indexes the following information through hashed members. Scientific
metadata already present in the report/source files is not duplicated under a
second competing representation:

| Information | Recorded and checked location |
| --- | --- |
| Evidence identity and format | Required manifest `capture_id`, `kind`, `schema_version`; UUID format checked |
| Creation and historical assessment clocks | Manifest `captured_at`, `policy_evaluated_at`; timezone-aware ISO timestamps normalized to UTC |
| Exact member bytes | Manifest `files`: SHA-256 and byte count for each fixed member |
| Snapshot, NORAD, source SHA, epoch, retrieval | Report definition and `sources[].reference`, cross-checked against `source-N.json` and exact response bytes |
| Insertion timestamp | Source metadata/report; null and legacy status retained when not recorded |
| Request time, frame, units and calculation parameters | Report definition/calculation and saved settings; result lineage/frame/units/shape validated before replay |
| Runtime | Manifest exact Python patch/implementation and sgp4, Astropy, pyerfa, NumPy, astropy-iers-data versions, backend source hashes, lock hash; embedded `uv.lock` also checked |
| Git and host | Manifest `source_revision`: observed HEAD/dirty/OS/machine or null where unavailable; descriptive, not a replacement for source hashes |
| EOP/leap identities | Exact applicable files in `manifest.files`; parsed metadata and every recorded result's EOP hashes/version/policy/quality/parameters checked before replay |
| Expected numerical outputs | Captured report calculation; numerical projection described below |
| Comparison method | Fixed manifest tolerances, enforced by the verifier; result names its exact-comparison profile and records residuals |
| Scientific limitations | Full report retained; verifier requires blocked independent observation validation and unquantified uncertainty, and repeats those limits in its result |

Only TEME positions are supported by position-mode definitions. Ground tracks use
ITRS; common-time comparisons support TEME or ITRS. Snapshot-only and comparison
without a common-time state request do not claim orbital-state replay. Each source
contains one archived satellite record. Timezone-free OMM epochs have the existing
CelesTrak-defined UTC meaning; API/manifest/request timestamps require explicit zones.

EOP/leap files are required for terrestrial calculations and absent for source-only
or TEME calculations. The verifier reports `resources.status="not_applicable"`
with null metadata in the latter case. Missing required members produce a safe
`missing_input` result naming the fixed original member and affected calculation,
without searching the ordinary database or installed resource directories.

A partial original report remains unavailable; it cannot be upgraded to successful
replay by a fallback. Contradictory complete/unavailable metadata is rejected.

## Hash and serialization rules

Each member SHA-256 covers **all exact file bytes**. Raw response hashes cover the
stored uncompressed response body, not parsed/reformatted JSON. Whitespace or JSON
key-order changes therefore change a raw/file digest even if parsed values agree.

OrbitIQ's emitted JSON profile 1 is UTF-8, sorted object keys, two-space indentation,
ASCII escaping (`ensure_ascii=True`), finite numbers only, and one terminal LF.
Array order is retained. Python 3.12's JSON integer/binary64 spelling is used; no
Unicode normalization or cross-language canonicalization standard is claimed.
Tests pin the emitted representation, including escaped Unicode and signed zero.
Readers accept otherwise valid JSON formatting under the same integrity rules;
normalizing an imported file is never a way to ignore its recorded hash.

The separately returned manifest digest covers its exact serialized bytes. The
manifest contains hashes of payload members, **not a hash of itself**. A later
verification result is written outside the bundle and is not retroactively added
to the manifest. There is no circular hash. Configuration identity retains the
existing Phase 9 compact sorted ASCII JSON/UTC-normalized definition algorithm;
it is distinct from the pretty-printed evidence profile and provider-payload hash.

## Bounded and non-executable import

Import is read-only validation of fixed-name regular files, not extraction. ZIP,
tar and arbitrary executable members are unsupported. Root/file symlinks,
traversal/absolute member paths, unexpected members, FIFOs and directories in place
of members fail closed. Files are opened relative to a directory descriptor with
`O_NOFOLLOW`; parsing uses previously bounded, hash-verified bytes. EOP parsing
reopens only private temporary copies of those verified bytes.

| Limit | Bound |
| --- | --- |
| Member count | Fixed layout, 5–9 including manifest; directory scan stops at first unexpected member |
| Manifest | 128 KiB, depth 12, 4,096 decoded nodes including object keys |
| All payload members | 24 MiB total declared bytes, checked before reading payloads; actual sizes/hashes must match |
| Each payload member | At most 8 MiB; tighter per-type limits below |
| Source response | 64 KiB |
| Source metadata / leap file | 128 KiB each |
| Lock | 2 MiB |
| Other JSON | Depth 32, 200,000 decoded nodes including keys |
| JSON array/object | 4,096 entries |
| JSON string/key | 16,384 Unicode characters |
| Difference detail | At most 20 failed and 20 tolerated differences; separate total counts |

Nesting is scanned outside quoted strings before JSON decoding. Duplicate keys,
nonfinite constants/exponents, excessive collection/string/node budgets and invalid
UTF-8/JSON are refused. Allocation/work is also bounded by file byte limits; this
is not an unlimited streaming JSON parser. No member is executed, imported as a
module, passed to a shell or installed as a dependency. Version/package names used
for introspection are fixed trusted constants. Verification cannot run ingestion,
EOP maintenance or database commands from package contents.

## Validation and offline execution

Use the existing operator entry point to request a validation-only report:

```sh
PYTHONPATH=backend uv run --locked python -m orbitiq.maintenance.replay validate \
  --directory /absolute/path/to/bundle \
  --expected-manifest-sha256 SEPARATELY_TRUSTED_DIGEST
```

`status="validated"` means preflight passed; `replay_started_at=null` and
`numerical_outcome="not_performed"` make the boundary explicit. Exit is zero;
invalid/unavailable validation exits 3. `verify` performs that same preflight then
calculates. Its nested `validation` result identifies the stage, checks and pass or
failure. Known failures identify a safe code, original fixed member and/or field.
Diagnostics do not echo arbitrary filenames, source bodies, exception paths or keys.

The trusted synchronous verifier activates a scoped Python audit policy rejecting
socket connection/resolution/send events, SQLite connections and process execution.
Attempt counts are reported and any attempted forbidden operation blocks success,
even if a downstream caller catches the exception. The policy is inactive outside
the calling context; it does not disable normal application networking. No replay
work is delegated to new threads. Inputs cannot choose an alternate code path,
module, subprocess, network source or maintenance operation.

This policy is defense in depth, **not an OS sandbox for hostile Python/native
extensions**. Libraries and installed code are trusted requirements. The existing
fresh-process audit starts before imports and independently checks database/network
attempts. Phase 10.1 also runs the golden lifecycle with Docker `--network none`.
That proves the tested offline reference lifecycle in OS network isolation, not
universal sandboxing of future extensions. Dependencies must be installed before
offline use; `uv sync`/an absent environment may require network provisioning.

Historical EOP evaluation uses the saved clock, not current time. Local temporary
resource scope restores ERFA leap state/expiry and Astropy contexts after success
or failure. Current API requests retain their normal live-clock/resource policy.
Replay neither refreshes resources nor certifies their present-day readiness.

## Comparison outcomes and diagnostics

Primary statuses `matched`, `verified_source_only`, `mismatch`, `unavailable` and
`blocked` remain compatible. Successful state replay **also requires reading
`numerical_outcome`**, which separates:

| Numerical outcome | Meaning |
| --- | --- |
| `exact_output_reproduction` | Every decoded binary64 numerical value (including signed zero) and all selected metadata match exactly |
| `tolerance_agreement` | At least one selected numeric representation differs, but all residuals meet the fixed per-quantity tolerances and metadata match |
| `mismatch` | A selected numeric residual or metadata comparison fails |
| `unverifiable` | Required inputs/runtime/resources/calculation unavailable or invalid |
| `not_performed` | Validation only; no replay executed |
| `not_applicable_source_only` | Sources/elements verified, without an orbital-state numerical pass |

Exactness is defined over the **decoded scientific projection**, not identical
whole-report JSON, UUIDs, execution clocks, browser rendering or library binaries.
Integers representing numbers are compared as binary64 where the result projection
uses numerical quantities. UTC state timestamps are normalized. JSON formatting
is an integrity concern, not numerical exactness. The result records both expected
and actual projection hashes using the emitted JSON profile; these can additionally
identify representation differences not claimed by the numerical profile.

The projection includes model/frame/units/time/source lineage, TEME/ITRS vectors,
all track states, geodetic coordinates, element differences, common-time state
subtraction and EOP metadata. Track sample identity/count/time is checked. Visual
segments, browsing/chronology summaries, prose, execution clocks and freshness
presentation are retained under file hashes rather than regenerated. Resource and
policy metadata are validated before replay. Incompatible frames, units, times or
source IDs never proceed to orbital calculation.

Unchanged Phase 10 absolute tolerances: position/ground position/separation
`1e-8 km`, velocity/relative speed `1e-10 km/s`, geodetic angles `1e-9 deg`,
altitude `1e-8 km`, other numbers/metadata exact; relative tolerance zero. These
are the existing matching-runtime replay contract, tighter than the existing
published SGP4 fixture's precision allowance. No global replacement tolerance was
invented or weakened. Selected local runs reproduce exactly; broad cross-platform
bitwise portability has not been certified. Numerical libraries, processors and
compiler builds can differ despite matching package version strings; discrepancies
must be reported under this contract, not hidden by relaxing it.

For each nonidentical numeric value, diagnostics give field, expected/actual,
signed/absolute difference, unit, absolute/relative tolerance and pass/fail.
Relative differences are null for zero references, angular quantities, unknown
units or unrepresentable ratios. Longitude uses `remainder(actual-expected,360)`
to handle the wrap boundary without losing tiny differences by adding 180.
Latitude is not wrapped. Element differences retain their established signed/wrapped
conventions and exact metadata/units. Nonfinite/unrepresentable residuals are null
with failure, never plausible zeros.

Replay output preserves source epoch and retrieval separately from the requested
evaluation time, package creation, original report generation, recorded original
calculation times, historical policy evaluation, replay start and verification
completion. None of these is substituted for an observation timestamp.

## Golden reference and compatibility

`scripts/verify_phase101_golden.py --directory /new/absolute/path` exercises:
new isolated reference archive → capture → detached fixed-directory export →
validation-only result → three fresh-process offline replays → published-vector
comparison → evidence report. It never opens the ordinary configured database.
The outer audit kit retains `evidence.json` with the independent reference; the
inner exported replay bundle retains its own captured computational baseline.

The reused reference is Vallado AIAA 2006-6753, `tcppver.out`, catalog 6251,
offset zero, distributed with pinned python-sgp4 2.27. The existing fixture and
upstream output hashes, TLE/OMM, epoch, UTC convention, WGS72/TEME/km/km/s and
literal expected outputs are recorded. Published-reference checks retain the
existing `1e-5 km` / `1e-8 km/s` tolerances, relative zero, allowing printed precision
and datetime epoch representation. They are separate from the stricter replay
comparison against OrbitIQ's own captured output. No OrbitIQ-generated value is
labelled independent scientific truth. EOP/leap inputs are explicitly not applicable
to this nominal-UTC TEME case; terrestrial replay is separately exercised with
exact genuine-archive resources and existing transformation references.

The test archive's source URL/retrieval adapter metadata and serialized OMM body
are clearly labelled fixture scaffolding, **not a genuine provider acquisition**.
The fixture changes only the object-name label, not published orbital elements.
No fixture enters the normal database. Expected vectors are numerical references,
not independent satellite observations.

Existing version-1 files retain their layout and meaning. New validation requires
complete scientific metadata already emitted by Phase 10. Historical bundles
whose recorded backend hashes differ intentionally return `runtime_incompatible`;
use their exact separately retained trusted checkout/environment. No automatic
translation, code execution or software/resource substitution is provided. Five
retained Phase 10 bundles were checked intact against their original trusted
manifest digests and correctly blocked under the changed backend, not relabelled
as reproduced by Phase 10.1.

Independent observation-based prediction validation remains **blocked** and orbital
prediction uncertainty **unquantified**. Exact replay and numerical reference
agreement do not establish physical prediction accuracy, maneuvers, anomalies,
collision risk or operational safety. Production infrastructure remains a separate
Phase 8 boundary; local artifacts are not off-machine backups.
