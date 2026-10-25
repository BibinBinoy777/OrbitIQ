# E8.7.9 — IGS ERP acquisition and qualification

**Exact acquisition and integrity: PASS. Interpretation: PARTIAL. Scientific
comparison: BLOCKED — NO-GO.** The requested ERP is now available privately.
Its acquisition closes E8.7.8's missing-payload issue, not the remaining
time/model/frame/physical-point/authorization requirements. No active EOP policy
or transformation was changed.

Study `ORBITIQ-IGS-GPS-RETRO-001`, 25 October 2026 UTC. Work remains in
`/workspace/OrbitIQ-e82`, branch `engineering-e8.2-igs-reference-qualification`,
HEAD `b0a03205e3930b55651232d8b7ffbc9e879ae8c6`.
The [evidence ledger](engineering-e8.7.9-erp-evidence.json) contains 18 requirements
with precise source/line/column locators, evidence category, exact versions/hashes,
status, limitations and next evidence. D = direct observation; P = authoritative
documentation; I = inference; U = unknown. PASS is scoped to the named requirement.

## Acquisition and immutable original

Only this scientific product was requested:

```text
IGS0OPSFIN_20233650000_07D_01D_ERP.ERP.gz
```

**D:** anonymous public HTTPS retrieval from the existing BKG IGS archive route:

`https://igs.bkg.bund.de/root_ftp/IGS/products/2295/IGS0OPSFIN_20233650000_07D_01D_ERP.ERP.gz`

| Acquisition evidence | Actual result                                                      |
| -------------------- | ------------------------------------------------------------------ |
| Request started      | `2026-10-25T07:28:58.405822+00:00`                                 |
| Retrieval completed  | `2026-10-25T07:29:00.340641+00:00`                                 |
| HTTP status / type   | **200**, `application/x-gzip`; no redirect to another file         |
| Compressed size      | **419 bytes**                                                      |
| Compressed SHA-256   | `2a201026f27e1265e77b9af8b81636bca0b0dfbf425ca4de0797ee5e587b1fd3` |
| Expanded size        | **1,173 bytes**                                                    |
| Expanded SHA-256     | `beae93c08035ac1749d23e9a62a13faffa8efa8f893c99acce17ed4805f97268` |
| HTTP Last-Modified   | `Thu, 14 Mar 2024 05:43:18 GMT`                                    |

The exact named original is preserved at:

```text
/workspace/OrbitIQ-e82/data/e8.7.9-erp-qualification/original/IGS0OPSFIN_20233650000_07D_01D_ERP.ERP.gz
```

The original and HTTP-body capture match byte-for-byte. Gzip decompression was
bounded and validated its footer/checksum; expanded text was inspected in memory.
The compressed file was never rewritten. Original, raw inspection, receipts,
coverage audit and test evidence are in the Git-ignored private area, files mode
600 and directories mode 700. Public deliverables contain metadata and precise
private-evidence locators, not the seven raw EOP quantity records. These artifacts
are not routine CI inputs or artifacts.

**U:** HTTP Last-Modified is archive metadata, not proof of original creation,
publication, availability at the reference date or a specific processing run.
HTTPS plus the local hash establishes captured-file traceability, not a producer
digital signature or scientific accuracy. No account, authentication, purchase,
rapid/ultra-rapid substitution or external resource creation was involved.

## Applicable documentation and naming

Read the official format specification **before interpreting the file**:

- [IGS ERP format / IGSMAIL-1943](https://files.igs.org/pub/data/format/erp.txt),
  10 July 1998, **version 2**, 3,839 bytes, SHA-256
  `0d06b4a1bbc3c4e5c755ded27e116923ccee4f80b9e616804af526fd5e764b52`.
  The [archived notice](https://lists.igs.org/pipermail/igsmail/1998/003315.html)
  corroborates it. The first guessed `erp2.txt` URL returned **404**; the official
  directory linked `erp.txt`, which returned **200**. The failure remains recorded.
- [IGS long product filenames](https://files.igs.org/pub/resource/guidelines/Guidelines_for_Long_Product_Filenames_in_the_IGS.pdf),
  **v2.2, February 2025**. This later guide explains the naming fields; it does not
  establish the exact 2024 generator release. The retained week-2295 summary and
  directory independently corroborate this product's historical naming family.
- [NASA final combined ERP catalog](https://www.earthdata.nasa.gov/data/catalog/cddis-gnss-igs-fnl-comb-erp-1),
  dataset version **1**, DOI `10.5067/GNSS/GNSS_IGSERP_001`.
  The old CDDIS URL returned an HTTP-200 relocation wrapper; its explicit public
  Earthdata link was followed. The wrapper was not mistaken for product data.

**P/D:** `IGS0` identifies combination/product line, `OPS` operational, `FIN`
final, `20233650000` nominal start on **31 December 2023**, `07D` nominal seven-day
period, `01D` daily sampling, `ERP.ERP` content/format and `.gz` gzip. This is
GPS week **2295**, containing January 1, 2024. Product-line `0`, header format
`version 2` and guide `v2.2` are different identifiers. Filename metadata was
checked against actual records rather than used as a substitute for inspection.

## Actual ERP structure, fields and coverage

**D:** expanded lines 1–4 contain exactly `version 2`, `EOP  SOLUTION`, the field
labels and units. Data lines **5–11** contain seven rows; a trailing blank follows.
All rows have 18 fields, valid integer quantity tokens, strictly increasing unique
MJD values, and nonnegative formal-error/count fields. There are no missing tokens,
embedded blanks, duplicate epochs, nonnumeric sentinel strings or row quality flags.
This passes the observed structural profile, not a universal ERP schema or
scientific qualification of every column.

| Epoch metadata                                 | Direct observation                                                                 |
| ---------------------------------------------- | ---------------------------------------------------------------------------------- |
| MJD lexemes                                    | `60309.50`, `60310.50`, `60311.50`, `60312.50`, `60313.50`, `60314.50`, `60315.50` |
| Calendar labels on the unspecified epoch scale | **2023-12-31 12:00 through 2024-01-06 12:00**                                      |
| Sampling                                       | All six differences **1.00 day**; half-day/noon knots                              |
| Internal completeness                          | No missing day within this seven-row sequence                                      |
| Explicit epoch time-system declaration         | **Absent**                                                                         |

**P/D/U:** the format calls field 1 MJD with 0.01-day resolution. The actual
quantity header explicitly chooses **UT1−UTC**, rather than the format's permitted
UT1R−UTC/UT1−TAI/UT1R−TAI alternatives. That label does **not** independently
declare the MJD epoch scale. The consulted format, actual header, naming guide,
catalog and retained summary do not explicitly settle this exact file's epoch
scale. Calendar labels above have no `Z` suffix. A UTC interpretation is a
conditional working hypothesis for the coverage audit, not an approved assumption.

| Actual columns                    | Published interpretation / limitation                                                                                                                              |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `MJD`                             | Format field 1, 0.01-day resolution. Epoch scale remains unqualified.                                                                                              |
| `Xpole`, `Ypole`                  | Integer units **10^-6 arcsec**.                                                                                                                                    |
| `UT1-UTC`                         | Integer units **10^-7 s**. Header declares the quantity variant.                                                                                                   |
| `LOD`                             | Format/header **10^-7 s/day**. Preserve native convention before any derivative/rate use.                                                                          |
| `Xsig`, `Ysig`, `UTsig`, `LODsig` | Published **unscaled formal solution sigmas**, corresponding scales. They are not calibrated spacecraft uncertainty.                                               |
| `Nr`, `Nf`, `Nt`                  | Format receiver, fixed-receiver and transmitter counts; actual all-zero fields require producer interpretation.                                                    |
| `Xrt`, `Yrt`, `Xrtsig`, `Yrtsig`  | Pole rates/formal rate sigmas, **10^-6 arcsec/day**. Rates were read, not applied.                                                                                 |
| `dpsi`, `deps`                    | Extra columns, both all zero. Not defined in IGSMAIL-1943's optional-field list; final unit token is merely `10**-6`. Exact angular units/meaning are unqualified. |

**D/U:** `UTsig`, `Nr`, `Nf`, `Nt`, `dpsi`, `deps` are zero in **every** row.
No consulted exact-product documentation assigns those zeros a missing/placeholder
meaning. Retain them as raw zero with semantics unknown. Do not interpret them as
zero uncertainty, no contributors or exact celestial-pole offsets. Do not relabel
the two extension fields as optional correlations, modern dX/dY, or add them to
the TEME rotation. Core-field syntax/scales can pass independently of extension
meaning. The official notice explicitly warns that increased stored resolution
does **not** imply GPS solution precision. No new uncertainty estimate was derived.

### All-reference coverage is conditional; direct substitution is blocked

The unchanged SP3 has 96 GPS epochs mapped previously to UTC
**2023-12-31T23:59:42Z–2024-01-01T23:44:42Z**. No time conversion was replaced,
reference epoch trimmed or GP record selected. Existing support is center and
±0.5 seconds per epoch.

**D/I:** assuming ERP MJD epochs mean UTC, exact-rational full-MJD arithmetic
brackets **all 96 targets and all 288 support instants** using the first three
knots, `60309.50`, `60310.50`, `60311.50`. There are 49 central targets in the
first interval and 47 in the second. An independent 50-digit Decimal bracket check
agrees with exact rational results. Original UTC strings and rational values are
preserved privately; no source timestamp was rounded or corrected. This checks
numeric containment only: no EOP values, rates or orbital states were interpolated.
Resolving the epoch scale and approved interpolation remains necessary before
scientific coverage can PASS. Nominal seven-day length alone does not authorize
extrapolating to either weekly boundary.

**D:** an important implementation incompatibility was established. Installed
Astropy **7.2.3** `IERS.mjd_utc` separates integer UTC-MJD and fractional day;
`IERS._interpolate` selects a bracket using the **integer** part, then uses the
fraction in its interpolation expression. That implementation assumes the usual
integer-MJD source knots. A synthetic noon-knot test against the installed code
demonstrates a false pre-range endpoint hold and an earlier-bracket extrapolation
for in-range fractional epochs.

A separate static index audit of the actual target labels, under the conditional
UTC interpretation, identifies index **0** as pre-range and indices **49–95** as
using the earlier bracket. Actual ERP values were **not** installed in an Astropy
table or interpolated. This is not a defect claim about the current midnight-knot
Bulletin-B application path. It rules out treating the acquired noon rows as a
direct replacement in the unmodified IERS interpolator. A future adapter would
also require correct units, statuses, provenance and convention treatment; none
was implemented or activated. Do not shift noon knots to midnight to hide the issue.

## Link to the IGS SP3 and existing EOP inventory

**P/D:** reuse the preserved week-2295 summary
`IGS0OPSFIN_20233650000_07D_01D_SUM.SUM.gz` and cached archive directory:

- Summary lines **111–122** identify the daily orbit family and weekly ERP family,
  explicitly describing ERP/UT1/LOD **associated with IGS ephemerides**.
- Lines **93–105** describe SINEX-combined PM/rates and LOD bias calibration
  against Bulletin A, integrated UT1−UTC with a Bulletin-A starting anchor.
  The exact Bulletin A issue/anchor used for these records remains unknown.
- Lines **225–239** describe IGS20/repro3 standards and daily SINEX AC alignment
  rotations. These are producer combination details, not corrections to apply
  to a GP spacecraft state.
- Lines **410–413** say the ERP statistics tables are consistency diagnostics,
  **not** the official accompanying SINEX combination ERP product. Those tables
  were not used as missing input or as a new uncertainty estimate.

**P:** NASA describes AC solutions combined by the IGS ACC into final products
generated weekly. The retained [IGS frame page](https://igs.org/wg/reference-frame/)
distinguishes definitive RF/SINEX ERP from other ACC combination ERP products;
the [IGS products page](https://igs.org/products/) records Bulletin-A/VLBI LOD
bias calibration and remaining time-correlated errors. These descriptions support
family traceability and dependencies, not identical treatment for every product.

**I/U:** same archive week, filename family and explicit summary association are
stronger provenance evidence than availability alone. They do **not** establish
that these exact downloaded ERP bytes were direct inputs to generation of the
particular SP3 bytes. No producer run manifest, exact processing revision,
byte-level link, full correction inventory or historical calibration revision
was acquired. ERP body has no frame identifier. It cannot independently certify
IGS20 or computed ITRS compatibility.

| Aspect                  | Acquired ERP                                                                 | Existing active path, unchanged                                                                  |
| ----------------------- | ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Source                  | BKG weekly IGS OPSFIN archive; exact receipt/hash                            | Pinned astropy-iers-data **0.2026.10.12.1.3.27**, `finals2000A.all`                              |
| Coverage/sampling       | Seven .50-MJD daily rows, epoch scale unconfirmed                            | Daily 0h UTC, usable MJD 41684–61682; target B values                                            |
| UT1/PM                  | Explicit UT1−UTC, integer scaled quantities                                  | Seconds/arcseconds, finite Bulletin-B fields preferred over A                                    |
| Related fields          | LOD, PM rates, formal fields; opaque dpsi/deps                               | A-only error fields cannot be assigned to merged B values; selected TEME branch uses only UT1/PM |
| Interpolation           | No policy supplied by this header; fractional-knot-aware evaluation required | Linear UTC-MJD, leap-jump handling, explicit coverage/status refusal                             |
| Finalization evidence   | FIN product family; no per-row I/P/final flags                               | Actual resource source flags label historical UT1/PM final B                                     |
| Provenance/dependencies | IGS/SINEX/GNSS processing; published Bulletin-A anchor path                  | IERS final series; independence from IGS is not established                                      |
| Other local resource    | No substitution performed                                                    | Bundled `eopc04.1962-now` available but unused; not identified with the active B columns         |

Fourteen installed source/resource hashes, the existing lockfile, application
sources and all EOP/leap identities still match E8.7.8. No numerical EOP
difference or spacecraft transformation was calculated. More fields and a matched
processing family do not by themselves justify a replacement policy.

## Subdaily, regularization, TIO and frame decision

Reuse the approved **IERS Conventions (2010), TN36**, §§5.5.1.1–3,
§§5.5.3.1–3 and Chapter 8. The retained official IERS index explicitly describes
later working updates as not definitive or officially approved. The published
2010 baseline is not automatically the exact 2024 operational routine inventory.

**P/D/U:** the new file's UT1−UTC header settles its declared quantity variant;
it does not document regularization, removed/restored ocean-tide or libration
models, exact revisions or subdaily evaluation. TN36 prescribes specified
subdaily ocean-tide PM/UT1 and libration contributions after interpolation;
long-period/secular PM libration is already present in observed PM and must not
be added again. A composite routine plus its constituent corrections can also
double-count. No blind corrections, UT1R assumption, higher-order interpolation
or rate application is approved by this phase.

**D/U:** Astropy's same-obstime TEME→ITRS path still uses GMST82(UT1), polar
motion and **s′ = 0** for Vallado consistency. The ERP has no TIO field and sets
no comparison accuracy objective. Acquisition does not justify zero TIO, adding
`sp00`, replacing GMST82 with ERA or inserting another celestial matrix.
No numerical TIO effect or uncertainty was calculated.

**P/U:** the named IGS20–ITRF2020 underlying datum relationship remains
established. Actual computed-coordinate equivalence still requires a reviewed
full convention crosswalk and acceptance criteria. An ITRS class name, ERP
availability or shared IGS family is insufficient. Spacecraft physical point,
historical calibration, quality/claim disposition, GP provenance limitations,
independent scientific review and explicit comparison authorization remain open.
Source matching can improve consistency while sharing dependencies; no statistical
independence, zero covariance, independent accuracy or forecasting claim follows.

## Qualification matrix and next evidence

| ID / requirement                 | Status  | Scope or missing evidence                                                                |
| -------------------------------- | ------- | ---------------------------------------------------------------------------------------- |
| R01 Exact acquisition            | PASS    | Exact target, anonymous HTTPS 200; no substitute.                                        |
| R02 Integrity/decompression      | PASS    | Original and expanded hashes, bounded gzip validation.                                   |
| R03 Naming/nominal period        | PASS    | Matching weekly final family; actual records independently checked.                      |
| R04 Observed structure           | PASS    | Narrow 18-column profile only; extensions not scientifically interpreted.                |
| R05 Epoch scale                  | PARTIAL | Product-era MJD time-system confirmation.                                                |
| R06 Numeric span/cadence         | PASS    | Seven unique daily .50 knots; not full scientific coverage.                              |
| R07 Quantities/units             | PARTIAL | Core definitions available; dpsi/deps definitions/units unresolved.                      |
| R08 Zero fields/quality          | PARTIAL | Producer meaning of UTsig/count/extension zeros; no inferred zero variance.              |
| R09 Target/support coverage      | PARTIAL | Numeric bracketing succeeds conditionally; epoch/interpolation qualification missing.    |
| R10 Direct IERS substitution     | BLOCKED | Noon knots require separately reviewed full-epoch adapter, not a path switch.            |
| R11 Finalization interpretation  | PARTIAL | Final-family classification supported; row flags/processing details absent.              |
| R12 Exact SP3 relationship       | PARTIAL | Association documented, direct generating-input link unproven.                           |
| R13 Bulletin-B comparison        | PARTIAL | Provenance/representation crosswalk, no approved replacement policy.                     |
| R14 Subdaily/regularization      | BLOCKED | Exact product-era removed/retained component inventory and reviewed treatment.           |
| R15 TIO adequacy                 | BLOCKED | Complete convention/acceptance derivation and independent review.                        |
| R16 Realized frame compatibility | BLOCKED | Computed TEME/terrestrial-to-IGS20 qualification and physical-point treatment.           |
| R17 Independence/dependencies    | PARTIAL | Known shared paths and unknown covariance/fit lineage; bounded claims only after review. |
| R18 Protocol/authorization       | BLOCKED | All essential gates, unchanged-rule selection, frozen packet and explicit authorization. |

**Recommendation: retain NO-GO and the active Bulletin-B policy unchanged.** Keep
the acquired ERP as reference evidence for further qualification. The smallest
next clarification package concerns this exact weekly file: MJD epoch scale,
zero-field and extension meaning, product-era interpolation/regularization and
subdaily component inventory, and the associated-versus-generating relationship
to the orbit/SINEX combination. No inquiry was sent here. Some zero/extension
questions need closure only if those fields will be used; core time/model gates
cannot be bypassed because unused fields are left uninterpreted.

Before any adapter implementation, independently specify full-epoch bracketing,
boundary/leap/UT1/rate handling, source-quality labels, nonoverlapping correction
models, precision/acceptance and complete frame/TIO treatment. Do not choose by
preferred residual. Future real comparison also needs common spacecraft point,
reviewed quality/claims, a record selected under unchanged rules, a reproducible
run packet and explicit user authorization. This phase grants none of those.

G30 remains the administrative first review. G05's two in-window same-epoch
records remain **HOLD**; six admitted records are unchanged. G30 retains nine
admitted and two rejected records. Neither case has a scientifically qualified
or selected record. Original protocols and retrospective admission remain intact.
E8.6's G30 quality-statistic reconciliation is not resolved by this ERP acquisition.

## Changes and actual verification

Four repository-facing files added:

- This report and [its evidence ledger](engineering-e8.7.9-erp-evidence.json).
- [Offline inspector](../scripts/inspect_igs_erp.py): explicit local file and
  mandatory expected hash; bounded gzip/ASCII inspection of the observed profile,
  immutable raw lexemes and conditional numeric bracketing. No network, database,
  EOP adapter, state propagation or scientific approval switch.
- [Synthetic tests](../backend/tests/test_igs_erp.py): deterministic fixtures,
  clearly labelled as synthetic evidence, including actual installed-Astropy
  behavior on invented EOP values. No acquired files are test inputs.

Example local inspection, with output directed only to a new private file:

```bash
umask 077
set -o noclobber
python scripts/inspect_igs_erp.py \
  data/e8.7.9-erp-qualification/original/IGS0OPSFIN_20233650000_07D_01D_ERP.ERP.gz \
  --sha256 2a201026f27e1265e77b9af8b81636bca0b0dfbf425ca4de0797ee5e587b1fd3 \
  > data/e8.7.9-erp-qualification/new-local-inspection.json
```

The command prints raw EOP tokens: do not paste its full output into public
documentation or CI logs. Exit 0 means the narrow structure/hash inspection
succeeded; scientific status remains BLOCKED. The real invocation, return code,
source fingerprint and actual inspection timestamps were captured privately.

**Executed verification:**

- Final targeted pytest: **37 passed in 0.49 s**. Covers valid synthetic input,
  hashes, bounds, malformed/truncated/non-ASCII/gzip/HTML inputs, unsupported
  columns/units, missing values/sentinels, negative formal/count fields,
  duplicate/unordered epochs, coverage boundaries, CLI behavior and synthetic
  noon-knot behavior in installed Astropy. An overlong string found by Ruff was
  corrected; the final test run occurred afterward.
- Targeted **Ruff lint and formatting passed**. JSON, Prettier documentation
  formatting, local links, source/ledger consistency, privacy, complete new-file
  diffs and whitespace/preservation checks passed.
- Real-file CLI inspection passed with the expected seven rows and both hashes.
  Exact-rational/Decimal conditional coverage checks passed for 96 targets/288
  supports. These are not propagation/residual results.
- Before/after preservation verifies all existing files and branches/HEADs in
  four worktrees, **199 entries** in prior private manifests, the original **72**
  private files and older **178-file** research inventory. New private evidence
  has a **22-entry** manifest. Original GP XML/capture pairs, original compressed
  and expanded SP3 hashes, EOP resources, protocols, policy definition and
  activation record are unchanged.
- The database was opened read-only: schema **3**, **two** snapshots, unchanged
  SHA-256 `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Local preservation does not establish independent backup/recovery.

Full application, frontend, browser, PDF and remote CI suites were **not run**;
existing application/dependency code did not change. No existing user change was
discarded, staged, committed or published. Earlier reports, including their
historical missing-ERP statements, were preserved rather than overwritten.

**No real GP initialization/propagation, spacecraft transformation, orbital
interpolation/extrapolation, residual calculation, new uncertainty estimation,
record selection, active policy change, private-account access, publication or
deployment occurred.** Phase 11.3.1 remains PARTIAL with evaluation BLOCKED;
E4 production readiness remains OPEN. Scientific study remains **BLOCKED — NO-GO**.
