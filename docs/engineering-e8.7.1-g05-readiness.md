# E8.7.1 — G05 intake and comparison readiness

**Engineering readiness verified locally using synthetic inputs; scientific study
BLOCKED.** No requested historical GP XML was inspected, real GP selected,
spacecraft state transformed, orbit propagated/interpolated/extrapolated,
residual calculated or new numerical uncertainty estimated.

See the [pre-inspection G05 protocol proposal](engineering-e8.7.1-g05-protocol-proposal.md)
and [machine-readable evidence/qualification ledger](engineering-e8.7.1-readiness-evidence.json).
Evidence categories are **D** direct local verification, **P** authoritative
published documentation, **I** proposal/inference and **U** unknown. A software
PASS does not make a scientific input eligible.

## Inspection and integration

Actual worktree: `/workspace/OrbitIQ-e82`, branch
`engineering-e8.2-igs-reference-qualification`, HEAD
`b0a03205e3930b55651232d8b7ffbc9e879ae8c6`. Its twelve existing E8.2–E8.7
documentation additions were preserved. The uncommitted E8.1.1 inspector,
synthetic tests and report existed only in `/workspace/OrbitIQ-e811`; their
originals are preserved there. They were copied forward into this worktree,
then the inspector/tests were extended here. The copied E8.1.1 report remains
byte-identical historical documentation; this report describes the newer scope.
No branch/HEAD, tracked source, scientific algorithm, dependency or lock changed.

Reused implementation: `sgp4.omm.parse_xml`, strict bounded OMM preflight,
historical intake's safe file capture/SHA-256/receipt/manifest, CSV numeric and
exact-epoch validators, and `Elements` static validation. No satellite initialization
is necessary. The existing 58 G30 tests and assertions are retained; 25 synthetic
G05/configuration controls were added in the same test module.

The [XML inspector](../scripts/inspect_historical_xml.py) now accepts
`--norad-id 35752` or `--norad-id 39533`, retaining default **39533**. These are
the two reviewed configurations for the existing grid, not an arbitrary-satellite
resolver. Unsupported IDs are rejected before capture. Programmatic
`inspect_attachment(..., norad_id=35752)` uses the same policy. There is no
comparison/approval switch.

The requested ID is explicit in the private report and stdout. Numeric NORAD
is the primary check; OBJECT_ID must also match the configured COSPAR. OBJECT_NAME
must be nonempty but need not equal “G05”, “NAVSTAR” or another display name.
SVN/PRN are not fields in the supported OMM profile; the report records that they
cannot be checked from it. Unexpected SVN or user-defined XML fields are refused
for review, not silently interpreted. Dated external identity remains separate.

Wrong/missing identity, malformed fields, XML errors and exact timestamp errors
are reported without repair. New aggregate fields expose mixed-object content
and whole-response identity consistency. Same-epoch conflicting field groups are
listed separately from exact parsed-field duplicates. The original per-record
candidate count/latest-static diagnostic behavior remains for G30 compatibility;
it is not a whole-document or provenance acceptance. Both targets always have
`selected_source_index: null`, `scientifically_accepted_count: 0` and BLOCKED
scientific status. A mixed response must be reviewed even if a target record
has a per-record static diagnostic index.

## Future local command — not executed against an attachment

After a separate intake instruction, from this worktree with locked dependencies:

```sh
mkdir -m 700 "$PWD/data/e8-g05-xml-intake"
PYTHONPATH=backend uv run --locked python scripts/inspect_historical_xml.py \
  --norad-id 35752 \
  --attachment /absolute/private/path/original-provider.xml \
  --archive-root "$PWD/data/e8-g05-xml-intake"
```

The filename is a command placeholder, not a claim that such a file arrived.
Use a new private archive root (0700); paths must meet the existing regular-file,
no-symlink and absolute-path policy. Each capture is exclusive and preserves
original bytes before parsing. `--expected-sha256` verifies a known original hash;
`--metadata` accepts explicit private operator assertions including actual receipt
time, if known. Unknown receipt stays null; capture time is not receipt. Never
use `--synthetic` on real evidence. All tests here are labelled synthetic.

Exit 0 means the inspection completed, potentially with excluded records;
it does not mean eligible or scientifically approved. Exit 1 means intake or
whole-document refusal; malformed readable bytes are preserved in their new
capture. Exit 2 is command configuration refusal. Review the private inspection,
aggregate identity flags and all record errors. Supported profile limits remain
OMM 2.0, namespace-free, 2 MiB, 512 records, depth 12, 30000 nodes and 4096-character
fields. No schema fetch, authentication, DTD, entity expansion or normalization.
Original bytes, private receipt and detailed inspection stay outside Git, build
contexts and routine CI artifacts.

## Acquisition state and exact proposed selection

**User-reported submission only:** NORAD **35752**, dates **2023-12-25 through
2023-12-31**, individual OMM XML, submitted **2026-10-24T18:08:31Z**, SUBMITTED.
The contact name/email and private correspondence are not copied here. Delivery
expectations do not establish receipt. States 2–8 (received, captured/hashed,
parsed, identity validated, eligible record, scientific prerequisites qualified,
scientific authorization) are **NOT ESTABLISHED**. Filename, receipt, hash,
returned count and selected record are null. No actual requested attachment was
opened during this phase, whether or not one becomes available elsewhere.

The [proposal](engineering-e8.7.1-g05-protocol-proposal.md) preserves the original
96 indices and 900-second sampling, UTC **2023-12-31T23:59:42.000000Z through
2024-01-01T23:44:42.000000Z**. One fixed GP, forward-only from the fixed first
epoch, must satisfy the inclusive seven-day guard at **every** reference epoch.
The exact GP window is **[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]**.
After identity/static/provenance review, latest unique eligible epoch is proposed;
same-epoch duplicates/conflicts block without fallback. No source-order,
element-set-number, revolution or smallest-residual tie-break. No discretionary
subset, moved anchor, nearest-time match, rounding or GP switching. The helper's
partial diagnostic indices do not relax the protocol's full-grid requirement.

## G05 quality: directly inspected own fields

**D:** compressed/expanded reference hashes still match E8. The ledger pins a private metadata record retaining
all **96 G05 quality-field slices**, their 1-based SP3 lines and GPS tags, without
XYZ positions or clock corrections. All 288 XYZ exponent fields are present;
no blank/99 marker, stored missing-position exclusion, maneuver or predicted-orbit
marker occurs. G05 also has no missing-clock marker. All four flag characters
(clock event/prediction and maneuver/orbit prediction) are blank at all 96 epochs.
This is a field-level finding, not proof that no physical event occurred.

| G05 item                     | Actual source                             | Interpretation / limit                                     |
| ---------------------------- | ----------------------------------------- | ---------------------------------------------------------- |
| Header raw `"  2"`           | SP3 line 8, columns 22–24                 | `2**2 = 4` format-mm indicator; not guaranteed truth error |
| XYZ sigma raw exponents      | P columns 62–63, 65–66, 68–69; all 96     | X codes 4–9, Y 2–8, Z 2–7; no blanks/99                    |
| `%f` position base           | Original header                           | 1.25; axis definition is `base**n` mm, not `2**n`          |
| Clock sigma raw fields       | P columns 71–73                           | Recorded separately, not used as position uncertainty      |
| Maneuver/orbit prediction    | P columns 79/80                           | Blank; source-format limitations still apply               |
| Summary G05 row              | Day 1/MJD 60310, Table 3.2295.1, line 698 | Label `5`, no X/E/M; not another day's row                 |
| Weighted-average IGS entry   | Same row, left-hand IGS field             | Raw `3`, combination statistic as published                |
| Orbit Dynamics (7 days), IGS | Same row, right-hand IGS field            | Raw `82`, fit statistic, not an 82-mm truth bound          |

**P:** the retained [SP3-c specification](https://files.igs.org/pub/data/format/sp3c.txt)
defines header accuracy as intended file-wide one-standard-deviation orbit-error
representation, base 2, zero unknown. Per-epoch XYZ uses the actual floating base,
zero means 1 mm, blank unknown, 99 too large to represent. Optional EP records
provide direct sigmas/correlations; this product has **no EP records**. No zero
correlations or diagonal covariance can be supplied merely because EP is absent.
The six-decimal km position format is not a demonstrated 1-mm accuracy.

**P/U:** the existing summary explains its weighted combination and seven-day
orbit-dynamics statistics; these are not measured truth or pure SGP4 errors.
G05's **3 / header-code 2 / format 4** relationship is independently unresolved
at the exact producer-encoding/rounding/version level. It is not resolved by a
similar-looking G30 relationship. G30's report remains untouched and its open
question is not a universal blocker on investigating G05. Here, formal field
definitions and metadata are established; calibration, joint uncertainty and
quantitative accuracy claims are not. No new numerical sigma, covariance,
confidence interval or comparison uncertainty was calculated.

## Frame, time and Earth orientation

**D/P:** reuse [E8.3](engineering-e8.3-frame-eop-qualification.md) and its source
hashes; the application sources were re-read and remain unchanged. The reference
declares IGS20 and GPS tags; IGS20 is aligned to the ITRF2020 datum. Astropy ITRS
has no selected ITRF/IGS realization attribute. That distinction remains relevant
to G05 without requiring its GP file.

The existing engine uses WGS72 SGP4, nominal UTC calendar Julian dates and outputs
calculated geocentric TEME km/km/s. The existing transform uses same-obstime
Astropy TEME→ITRS: UT1/GMST82 and polar motion, `pom00` with s-prime zero.
It is not a full GCRS/CIRS chain or an IGS20 realization certificate. No transform
was executed here. Actual future XML Earth/TEME/UTC/SGP4 declarations and epoch
precision still need inspection; JSON defaults cannot authenticate XML metadata.

The offline explicit IERS resources, finite/status/range checks, disabled remote
downloads and warnings-as-errors policy are established in source. The reused
E8 preflight covered all 96 epochs and ±0.5-second velocity support with
IERS-B-final flags. **This was reused, not freshly rerun.** Astropy's EOP parameter
interpolation is distinct from prohibited orbital-state interpolation.

**U:** the applicable 2024 combined-product ERP and high-frequency/subdaily
processing inventory remain unestablished; the audited branch has no explicit
INTERP/ORTHO_EOP/PMSDNUT2/UTLIBR treatment. Whether corrections are needed, already
represented or inappropriate needs a documented avoid-double-counting review.
Do not introduce correction models or a station Helmert transformation on this
evidence. Resource coverage is PASS within its scope; frame realization is
BLOCKED and EOP model compatibility PARTIAL.

## Satellite physical point and historical calibration

**D:** the already acquired current `igs20.atx`, original SHA-256
`0cd58d0d9ee678d5586de6c01f576e5aceb86f4a0735a168f733dfd091c0a614`,
has one G050 entry at lines **1098–1113**, BLOCK IIR-M / G05 / G050 / 2009-043A.
Metadata gives method-date text **29-JAN-17**, validity from **2009-08-17**, code
**IGS20_2437**, and frequencies G01/G02 with satellite-body offsets/PCV records.
These frequency identifiers are signals, not PRN G01/G02. No validity end is
supplied in that entry. The labels are not delivery time or proof of the actual
2024 processing calibration. Offsets were inspected as metadata, not applied.

**D/P:** the retained satellite SINEX has G050 COM at line **2689** and transmit
antenna eccentricity at line **3203**, with zero-origin coordinates. Its notes
at lines **310–320** require consistent body-axis/COM/eccentricity conventions
and describe the current CoM-as-antenna-reference-point convention. Those zeros
are conventional reference origins; they do not prove zero antenna phase-center
offset or physical agreement with GP. The metadata discusses ANTEX 2.0 while the
retained calibration file is 1.4: do not silently assert a common revision.

**P:** the retained [IGS product-use guide](https://files.igs.org/pub/resource/pubs/UsingIGSProductsVer21.pdf)
describes general precise-GPS CoM conventions, and
[ANTEX 1.4](https://files.igs.org/pub/data/format/antex14.txt) defines satellite
body axes, mm offsets and phase-center treatment. General conventions and current
satellite-specific metadata are useful evidence, not a complete history of this
combined product or its AC inputs.

**U:** the exact historical ANTEX revision/model changes and attitude/AC processing
used for G050 on this date, and the future historical GP fitted physical point,
are unknown. Required next evidence: product-era calibration/attitude processing
provenance, consistency of COM/equipment definitions, and justified GP point
treatment or a reviewed limitation/claims bound. No correction, vector rotation
or numerical effect estimate is authorized here. Physical-point compatibility
remains BLOCKED.

## Verification and remaining gates

Executed from this worktree with the existing locked Python environment:

```sh
python -m pytest backend/tests/test_historical_xml_intake.py -q
python -m pytest backend/tests/test_historical_xml_intake.py \
  backend/tests/test_historical_csv_intake.py \
  backend/tests/test_historical_gp_intake.py \
  backend/tests/test_historical_gp_reconciliation.py \
  backend/tests/test_igs_feasibility.py -q
ruff check scripts/inspect_historical_xml.py backend/tests/test_historical_xml_intake.py
ruff format --check scripts/inspect_historical_xml.py backend/tests/test_historical_xml_intake.py
```

- XML module: **83 passed in 10.90 seconds** (58 preserved + 25 new synthetic
  controls). Related five-module run, including those same 83: **321 passed in
  15.07 seconds**. Counts are overlapping, not 404 distinct tests. JUnit files
  are explicitly named `SYNTHETIC-...` under the local task verification directory.
  These tests use synthetic/published test fixtures, not acquired GPS evidence.
- The first lint invocation found one long line in new code; formatting fixed it.
  Final lint/format, Markdown/JSON formatting, local-link, ledger/source/quality,
  acquisition-state, exact-window, privacy and whitespace checks passed. No
  full application, frontend, browser, PDF, build or remote CI run is claimed.
- The complete additions and delta from the original E8.1.1 source/tests were
  reviewed. All four worktree branches/HEADs, 380 tracked files, twelve existing
  E8.2–E8.7 additions, original E8.1.1 files, 72 original private files, 103
  prior private-manifest entries and original protocol/reference hashes are
  preserved. Read-only DB check retains schema 3, two snapshots and SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Local preservation does not demonstrate independent backup/recovery.
- This task adds six repository files: inspector, test module and byte-identical
  historical E8.1.1 report copied forward; this readiness report; G05 protocol
  proposal; readiness JSON ledger. Nothing was staged, committed, published or
  deployed. No external services or private accounts were accessed.

The 13-row matrix scopes software/request/time-grid/resource/field PASS findings
separately from scientific gates. Still required: original historical GP and
receipt/provenance, exact identity/model/unique eligibility, reviewed G05 quality
and uncertainty claims, frame/EOP compatibility, historical physical-point
evidence, source-dependency assessment, protocol review and explicit scientific
authorization. Availability, complete fitting lineage and statistical independence
remain unknown. IGS contributions include ESA; this is not an ESA-free truth set.

**Study BLOCKED.** No actual requested XML inspected and no real scientific
calculation performed. Swarm-A Phase 11.3.1 remains **PARTIAL**, evaluation
**BLOCKED**; E4 production readiness remains **OPEN**.
