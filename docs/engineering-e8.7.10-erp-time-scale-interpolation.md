# E8.7.10 — ERP time-scale and interpolation qualification

**Epoch-scale gate: BLOCKED. Synthetic interpolation feasibility: PASS within its
test scope. Real ERP adapter: NOT AUTHORIZED. Scientific study: BLOCKED — NO-GO.**
No active EOP/transformation policy, original input, database, protocol or prior
report changed. This phase specifies requirements and tests invented values;
it does not authorize applying the prototype to the acquired ERP.

Study `ORBITIQ-IGS-GPS-RETRO-001`, 25 October 2026 UTC. Work remains in
`/workspace/OrbitIQ-e82`, branch `engineering-e8.2-igs-reference-qualification`,
HEAD `b0a03205e3930b55651232d8b7ffbc9e879ae8c6`.
The [evidence ledger](engineering-e8.7.10-erp-time-scale-evidence.json) separates
direct file evidence, official format requirements, installed implementation,
published operational guidance, inference, synthetic results and unknowns.
The [clarification draft](engineering-e8.7.10-igs-clarification-draft.md) is
**UNSENT**; no provider clarification or approval was received in this phase.

## Actual file and complete field audit

Reused, without downloading another scientific input:

```text
/workspace/OrbitIQ-e82/data/e8.7.9-erp-qualification/original/IGS0OPSFIN_20233650000_07D_01D_ERP.ERP.gz
```

**Direct evidence:** original **419 bytes**, SHA-256
`2a201026f27e1265e77b9af8b81636bca0b0dfbf425ca4de0797ee5e587b1fd3`.
Expansion **1,173 bytes**, SHA-256
`beae93c08035ac1749d23e9a62a13faffa8efa8f893c99acce17ed4805f97268`.
The original, E8.7.9 HTTP capture and prior seven-row inspection still agree.
All four header lines and all seven data rows were inspected again. The exact
expanded bytes and a complete 18-column raw-token audit are preserved privately
under `data/e8.7.10-erp-time-scale/`, without rewriting earlier captures.

Actual header: `version 2`, `EOP  SOLUTION`; data lines **5–11** have seven
unique daily tags `60309.50` through `60315.50`, all increments `1.00` day.
No new real EOP interpolation was performed. The private audit retains each
native token, column, data-line locator, zero occurrence and interpretation.
Raw EOP quantity rows remain outside Git and routine CI.

The applicable [official ERP-v2 text](https://files.igs.org/pub/data/format/erp.txt)
is **IGSMAIL-1943, 10 July 1998**; it requires `version 2` at the first column
of line 1 and defines the core field scales. Its explicit warning matters:
storage resolution does not imply GPS solution precision. The
[archived notice](https://lists.igs.org/pipermail/igsmail/1998/003315.html)
and existing product-era combination summary were reused. The format's optional
fields must be identified by their actual labels, not inferred from column number.

| Column | Actual field | Format/header interpretation                                                      | Observed zeros / consequence                                                   |
| -----: | ------------ | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
|      1 | MJD          | Modified Julian day, 0.01-day stored resolution; scale not explicitly specified   | None; `.50` is a fractional day, not a quality flag.                           |
|      2 | Xpole        | 10^-6 arcsec                                                                      | None.                                                                          |
|      3 | Ypole        | 10^-6 arcsec                                                                      | None.                                                                          |
|      4 | UT1-UTC      | Actual chosen variant, 10^-7 s; other format variants include UT1R/TAI references | None; a dependent difference does not define the epoch scale.                  |
|      5 | LOD          | Actual LOD label, format/header 10^-7 s/day                                       | None; no derivative or Hermite use inferred.                                   |
|      6 | Xsig         | Unscaled formal solution sigma, 10^-6 arcsec                                      | None; not calibrated spacecraft uncertainty.                                   |
|      7 | Ysig         | Same scale/limitation as Xsig                                                     | None.                                                                          |
|      8 | UTsig        | Formal field, 10^-7 s                                                             | Seven zeros; numerical versus unestimated/placeholder meaning unresolved.      |
|      9 | LODsig       | Formal field, 10^-7 s/day                                                         | None; no new uncertainty calculation.                                          |
|     10 | Nr           | Receiver count in format                                                          | Seven zeros; do not conclude that no receivers contributed.                    |
|     11 | Nf           | Fixed-coordinate receiver count in format                                         | Seven zeros; product-specific meaning unresolved.                              |
|     12 | Nt           | Transmitter/satellite count in format                                             | Seven zeros; do not conclude no satellites contributed.                        |
|     13 | Xrt          | Pole rate, 10^-6 arcsec/day                                                       | None; presence does not prescribe its use.                                     |
|     14 | Yrt          | Pole rate, 10^-6 arcsec/day                                                       | None.                                                                          |
|     15 | Xrtsig       | Formal pole-rate field, 10^-6 arcsec/day                                          | None.                                                                          |
|     16 | Yrtsig       | Formal pole-rate field, 10^-6 arcsec/day                                          | None.                                                                          |
|     17 | dpsi         | Actual trailing extension, not the optional XYCorr label                          | Seven zeros; definition/reference model and explicit angular unit unqualified. |
|     18 | deps         | Actual trailing extension; final header token only `10**-6`                       | Seven zeros; do not map to a correlation or modern dY.                         |

**42 numerical zero occurrences** exist: seven each in UTsig, Nr, Nf, Nt,
dpsi and deps. They are syntactically valid integers. Neither the retained v2
format nor the exact header defines a zero sentinel rule for these values.
Their product-specific physical/statistical meaning is therefore **ambiguous**,
not silently assigned unavailable, missing, perfectly known or precisely zero.
The optional correlation fields absent from this file are absent, not numeric
zeros. No optional-field filling or extension reinterpretation was performed.

## What is established about time tags

**Official format:** field 1 is MJD with fractional-day resolution. It does not
explicitly name UTC, GPS, TAI, TT or UT1 as that field's scale. In general, MJD
is the Julian-date offset `JD - 2400000.5` on an identified scale; the offset
alone does not choose a time scale. `.50` is half a nominal day on that declared
coordinate. It is not permission to subtract half a day or relabel noon as midnight.

**Published operational guidance:** the retained [IGS products page](https://igs.org/products/),
Earth Rotation / Final / Sample Interval, says **“daily integrations at 12 UTC.”**
This supports noon-UTC operational practice. The v2 example itself uses `.50`
epochs. These facts are relevant supporting evidence, rather than an explicit
definition binding the independent-variable tags in this exact 2024 artifact.

**Direct evidence:** the filename's nominal start is `20233650000` (31 December
2023 at nominal midnight); its first row is `60309.50` (calendar label 31 December
at noon on an unspecified scale). A nominal coverage start need not equal a
solution's reference epoch or daily-arc midpoint. No timestamp was shifted to
make these two metadata fields identical. Calendar labels for the first/last
rows are **2023-12-31 12:00 / 2024-01-06 12:00**, without `Z` suffixes.

**Inference / unknown:** noon UTC is plausible and supported by published
operational guidance, but the exact MJD scale and arc-reference convention are
not conclusively established by the consulted sources. AC documentation using
GPS observation epochs or TDT force-model arguments describes different variables;
it cannot relabel combined ERP MJD tags. The actual UT1−UTC label states what
difference is stored, not when its row is tagged. An incorrect epoch scale would
evaluate otherwise correctly scaled EOP at the wrong instant.

**Disposition: BLOCKED**, pending the precise product-era confirmation requested
in the unsent draft. E8.7.9's conditional 96-target/288-support coverage is reused
as conditional arithmetic evidence only. It was not promoted to qualified time
coverage, recomputed as a state calculation, or used to select a GP record.

## Exact installed behavior and boundary implications

Astropy **7.2.3** installed `IERS.mjd_utc` / `IERS._interpolate` source was read,
hashed and rechecked. Exact-version [IERS documentation source](https://raw.githubusercontent.com/astropy/astropy/v7.2.3/docs/utils/iers.rst)
was retrieved successfully: **12,696 bytes**, SHA-256
`c442d84ee634104f36eb35410151edef2f4130a99e88d83370d1fd7c59b03536`.
Its daily-series and general interpolation descriptions do not promise correct
handling of an arbitrary fractional-knot ERP table; inspected code decides actual
behavior. No other version was substituted. An additional IGS ACC-format-page
lookup returned HTTP 404 and was not treated as documentation read.

The code splits a UTC date into integer MJD and fractional day, uses the
**integer MJD** in `searchsorted(..., side="right")`, then includes the fraction
in the interpolation weight. That is suitable for the normal integer-MJD source
knots; it is not a general full-fractional-knot bracket search. UT1 differences
also have a rounded integer leap jump removed before interpolation; this is not
rounding an input source epoch or approving a new leap policy.

Fresh tests against **invented** EOP values confirm:

- An exact first `.50` knot can be labelled before range and held at the endpoint.
- A later fractional query can use the preceding bracket instead of its actual
  adjacent samples.
- A query after the final noon, but before the next midnight, can extrapolate
  while retaining `FROM_IERS_B` status. A nonnegative status alone is insufficient
  to enforce the true fractional domain.

These are synthetic implementation diagnostics, not real EOP differences or
spacecraft errors. They extend E8.7.9's conditional static index finding. The
active midnight-sampled Bulletin-B path is unchanged; no defect in that normal
path is asserted. No real ERP table was installed in Astropy.

## Future adapter contract — specified, not approved or integrated

A future adapter needs an independently approved time/model/source contract
before reading real data for scientific evaluation:

1. **Independent variable.** First qualify the ERP epoch scale and reference-epoch
   convention. Convert an aware comparison instant to that scale with pinned,
   validated leap/EOP resources as needed. Retain two-part dates or exact
   rational representations; do not collapse to a low-precision float, round to
   the file's 0.01-day storage grid, assume UTC, or create a circular UT1-based
   independent variable without a justified procedure. UTC quasi-JD/leap-day
   conventions must be explicit if UTC is confirmed.
2. **Data validation.** Retain original lexemes, hashes, units and row identities;
   require strictly ordered unique finite epochs. No sorting away a conflict,
   dropping bad neighbors, filling missing fields or nearest-sample substitution.
   Set and review the maximum permissible gap for this daily product; the toy
   prototype permits unequal spacing to test mathematics, not to approve bridging
   missing days in a real file.
3. **Adjacent full-epoch bracket.** For an approved continuous scalar, find actual
   knots `t_i <= t <= t_(i+1)` using the complete fractional coordinate. Set
   `w = (t - t_i)/(t_(i+1) - t_i)` and `y(t) = (1-w)y_i + w*y_(i+1)`.
   At an exact knot return that sample's scaled value and source identity.
   Include both first and last knots; reject strictly outside the complete
   domain, even if a library status is nonnegative. No endpoint clamping or
   extrapolation. This is a proposed numerical model, not proof of suitability.
4. **Units/allowed fields.** Scale PM integers by 10^-6 arcsec and the declared
   UT1−UTC integers by 10^-7 seconds exactly. A future conversion to radians must
   occur once at a declared interface. Do not automatically interpolate LOD,
   rates, counts, sigmas, covariance, quality flags or opaque extensions. LOD and
   rates could support a different method only after derivative/time/model and
   producer-convention review. Never interpolate sigmas as a substitute for a
   justified covariance model or infer zero variance from UTsig=0.
5. **Leap/discontinuity handling.** A conservative initial specification refuses
   intervals crossing a leap step until independently reviewed. A possible later
   design uses the continuous quantity `UT1-TAI = (UT1-UTC) - (TAI-UTC)` on a
   qualified continuous axis, then restores the query's TAI−UTC. That requires
   authoritative epoch semantics, a pinned leap table, boundary tests and model
   review; it is not implemented or approved here. Do not interpolate blindly
   through a UT1−UTC step or apply Astropy's integer-jump rule to unknown metadata.
6. **Quality and provenance.** Return the resource hash/version, native row/epoch
   identifiers, query scale, exact bracket/weight, units, interpolation method,
   and contributing quality labels. Preserve unknowns and the distinction between
   exact samples and interpolated results. Do not relabel IGS final-family data
   as `IERS_B_final`, upgrade endpoint quality or assume independence from the
   reference orbit. Retain native errors uninterpreted until separately qualified.
7. **Physical-model boundary.** Specify interpolation and subdaily restoration
   together, including which source terms were removed/retained, routines and
   time arguments, TIO convention and acceptance criteria. A mathematically
   correct table interpolator is not the complete terrestrial transformation.

## Synthetic feasibility prototype and its limits

Added [prototype](../scripts/prototype_erp_interpolation.py) and
[tests](../backend/tests/test_erp_interpolation_prototype.py). The module has no
file/network loader, CLI, application import, database access, real time conversion
or active policy hook. Callers must explicitly supply a synthetic fixture, an
abstract fractional-MJD axis identifier, continuous/no-discontinuities declaration,
synthetic provenance and requested fields. A marker is an audit label, **not**
authentication that arbitrary caller-supplied numbers are invented.

The implementation accepts exact integers, decimal strings, finite Decimals and
Fractions, rejects floats/nonfinite/missing requested values, and computes exact
rational weights. Original epoch lexemes remain unchanged. It only permits selected
toy PM/offset fields with explicit unit definitions: arcsec/microarcsec and
seconds/tenth-microseconds. Unsupported rates, counts, formal errors and other
fields cannot be requested; extra unrequested fields are listed as ignored.
Every row's requested values and provenance are validated before evaluation.

An invented fixture has epochs **60000.50, 60001.50, 60003.50**. Its x values,
after explicitly declared toy unit conversion, are **1, 3, 11 arcsec**. At
60002.00 the correct adjacent bracket is the second interval, weight **1/4**,
yielding **5 arcsec**. The unequal spacing makes a hidden half-day shift or
previous-interval selection detectable. These numbers are **SYNTHETIC**, not
acquired EOP, physical uncertainty or a result for GPS G30/G05.

Tests preserve all original sample epochs, validate exact first/last samples and
subdecimal queries, distinguish a synthetic numerical zero from an absent field,
reject outside-domain/mismatched-axis/discontinuous/invalid inputs, and retain
contributing source/quality labels without upgrading them. Outputs explicitly say
`NOT_A_SCIENTIFIC_RESULT` and real epoch scale `UNQUALIFIED`. Leap handling and
real UTC/GPS semantics are deliberately absent. Technical feasibility passes its
synthetic scope; a scientifically qualified real adapter remains BLOCKED.

## Subdaily and TIO findings remain separate

The retained [Using IGS Products guide](https://files.igs.org/pub/resource/pubs/UsingIGSProductsVer21.pdf),
**May 2009 §5.2.4**, explicitly describes regularized ERP lacking subdaily tidal
variations and the need for corresponding ERP augmented with subdaily models in
inertial-frame processing. This supplies published IGS context, not an exact 2024
model/routine manifest. Its historical eight-wave example is not silently adopted
instead of later approved conventions.

Approved **IERS Conventions (2010), TN36**, §§5.5.1.1–3, §§5.5.3.1–3 and Chapter 8,
describe ocean-tide and specified libration contributions. Long-period/secular PM
libration is already present in observed PM; do not add it again. Source-specific
regularization, a composite routine's contents, exact revisions and operational
2024 IGS processing still need qualification to avoid duplicate or omitted terms.
Later IERS working updates remain not definitive or officially approved, as
recorded by the retained official index. No correction was added here.

The installed TEME path still uses GMST82(UT1), polar motion and **zero TIO locator**
for Vallado consistency. Neither ERP fields, dpsi/deps zeros nor an exact
interpolator establish that choice's adequacy for this IGS20 comparison. The
complete frame/TIO convention and intended acceptance require independent review.
No TIO effect, new uncertainty or residual was calculated.

## Disposition and actual verification

| Gate                                  | Status  | Meaning                                                                             |
| ------------------------------------- | ------- | ----------------------------------------------------------------------------------- |
| Exact original/expanded integrity     | PASS    | Existing bytes and seven-row inspection reproduced.                                 |
| Format core definitions               | PASS    | Version/core scales documented; not all extensions qualified.                       |
| Exact ERP epoch scale                 | BLOCKED | Noon-UTC guidance supports an inference, not a conclusive exact-product definition. |
| Every-field / zero interpretation     | PARTIAL | Complete inventory; 42 zeros and extra fields retain explicit unknowns.             |
| Installed interpolation behavior      | PASS    | Source and synthetic diagnostics, not scientific accuracy.                          |
| Synthetic full-epoch interpolation    | PASS    | Exact arithmetic/units/endpoints on invented values only.                           |
| Future adapter contract               | PARTIAL | Specified; real time/leap/model/source qualifications pending.                      |
| Real ERP use / frame / subdaily / TIO | BLOCKED | No integration, no scientific authorization.                                        |
| Clarification draft                   | PASS    | Saved locally, UNSENT; no response claimed.                                         |

The next useful evidence is a response to the five precise questions in the draft,
especially the exact MJD scale/reference epoch, zero/extension meanings and
product-era interpolation/subdaily/TIO conventions. Those answers would inform
independent review; they would not automatically authorize a comparison. GP
provenance limits, spacecraft physical point, quality/claims, unchanged-rule
record selection and final run-packet authorization remain separate gates.

**Executed:** combined ERP-inspector and prototype tests **101 passed in 0.57 s**
(37 existing inspector tests + 64 new synthetic tests). Targeted Ruff lint and
format checks passed on all four associated code/test files. JSON, Markdown/link,
Prettier, evidence/source consistency, privacy, complete diff, whitespace and
preservation checks passed. JUnit is explicitly marked SYNTHETIC. No full
application, browser, PDF or remote CI suite ran; no relevant application or
dependency change warranted those suites.

Five repository-facing files were added: this report, its ledger, the unsent draft,
the prototype and its tests. No preexisting file changed. All four worktree
branches/HEADs, **221 prior private manifest entries**, **72 original private files**,
the older **178-file** research inventory, ERP/SP3/XML hashes, database, policies,
activation record and earlier reports were preserved. The database remains schema
**3**, **two snapshots**, SHA-256
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
Existing installed source/EOP identities are unchanged. Private field audits,
expanded bytes and documentation captures remain Git-ignored; preservation is
not independent backup verification.

G05's two held records remain HOLD, all G05/G30 admission results and original
protocols remain unchanged, and no record was selected. Phase 11.3.1 remains
PARTIAL with evaluation BLOCKED; E4 production readiness remains OPEN.
**No real-input propagation, spacecraft transformation, real EOP interpolation,
orbital interpolation/extrapolation, residual calculation, new uncertainty estimate,
policy activation, email, publication or deployment occurred.** The study remains
**BLOCKED — NO-GO**.
