# Reference-frame alignment investigation — 22 October 2026

Phase 11.3.1 **PARTIAL**; genuine Swarm-A evaluation **BLOCKED**. This investigation
supports [comparison protocol v1](phase-11.3.1-comparison-protocol.md), not an
operational transform. ESA substantive clarification under user-supplied support
reference `RITM0144536` remains pending. A tracking reference/acknowledgement is
not a technical answer. Original files and prior evidence are unchanged.

## Evidence categories and sources reviewed

Source review date is **22 October 2026**. Existing retained documents were
hash-checked and reread; their original acquisition was 21 October. New IERS
chapter 4 and Astropy ITRS documentation were retrieved on 22 October with TLS
verification. Source captures stay private; this report publishes conclusions,
minimal metadata and synthetic controls, not source products or correspondence.

| Reference | Precisely supported evidence |
| --- | --- |
| [ESA L2 product specification](https://earth.esa.int/eogateway/documents/d/earth-online/swarm-level-2-product-specification), `SW-DS-DTU-GS-0001`, revision 3.0, 2021-02-25, §§4.3.2, 5.9.1, pp.28,94–95 | GPS time, KIN center-of-mass ITRF positions at observation epochs; formal specifications; detailed VAL definition includes KIN and COM |
| [SP3-d specification](https://files.igs.org/pub/data/format/sp3d.pdf), 21 February 2016, field tables pp.4–5 and descriptions pp.14–17 | Calendar seconds and week seconds F11.8/F15.8, fractional MJD F15.13; units, uncertainty and missing-value conventions |
| [IGS frame chronology](https://igs.org/wg/reference-frame/) | IGb08 aligned to ITRF2008 datum; GPS weeks 1709–1933, 2012-10-07 through 2017-01-28 |
| [IGS Mail 6663](https://lists.igs.org/pipermail/igsmail/2012/000497.html), 24 September 2012 | IGb08 station discontinuity repairs, local ties and antenna/metadata changes; not one satellite-wide offset |
| [IERS chapter 4](https://iers-conventions.obspm.fr/content/chapter4/icc4.pdf), **complete chapter update 1 April 2019**, §§4.1.1,4.2.6,4.2.7, equations 4.2–4.5, Table 4.1 | Similarity transform, rates, full velocity derivative and station-specific simplification; ITRF2014→earlier-frame parameters at 2010.0 |
| [IERS chapter 5](https://iers-conventions.obspm.fr/content/chapter5/icc5.pdf) | Earth orientation and terrestrial/celestial convention context; not a TEME→IGb08 approval |
| [Astropy satellite guide](https://docs.astropy.org/en/stable/coordinates/satellites.html), installed source 7.2.3, [ITRS source documentation](https://docs.astropy.org/en/stable/_modules/astropy/coordinates/builtin_frames/itrs.html) | Same-epoch TEME→ITRS method, geocentric/topocentric distinction and actual frame attributes |
| [USNO TAI–UTC history](https://maia.usno.navy.mil/ser7/tai-utc.dat), [Astropy TimeGPS](https://docs.astropy.org/en/stable/api/astropy.time.TimeGPS.html) | Independent historical offset check and GPS epoch/TAI definition |

IERS chapter-4 PDF SHA-256:
`30172aa50942afb464c791ddadda6d1c494c844bf4d4b74e183a5d215a852016`.
Do not describe its updated ITRF2014 table as the original 2010 table.
The prior [pairing report](phase-11.3.1-scientific-pairing-report.md) pins the
other core source hashes. Two attempted IGN transformation routes redirected to
the same generic homepage, without a parameter table; a guessed online Astropy
intermediate-transform source route returned 404. None establishes parameter
values or absence of documentation. Installed source and the actual IERS PDF were
used instead; no authentication bypass, provider message or bulk search occurred.

## Original-product audit and time derivation

Reused the preserved KIN/VAL archives, validating their pinned SHA-256, ZIP CRC,
XML lengths/checksums, identities and processing metadata. Rechecked the actual
CSV statically and reconciled all 51 fields using the existing explicit adapter.
No source was normalized, replaced or redownloaded. No GP was dynamically
initialized. The exact SP3 member SHA-256 remains
`c6c9c0c610c64258abf7b0e7c38d0429fb73a90768b0c600a43f6c3f1f43eb27`.

Actual first-calendar metadata: GPS `2014-01-01T00:02:20.00000000`.
The first `*` epoch agrees. The fixed-column `##` fields are:

| Field / SP3-d columns (one based) | Original text | Literal interpretation, not approved canonical time |
| --- | --- | --- |
| Week, 4–7 | `1773` | GPS week from its specified epoch |
| Week seconds, 9–23 | `259220.00000000` | GPS 2014-01-01 00:00:20, **120 s before** the calendar tag |
| Interval, 25–38 | `0` (space padded) | Zero; normative positive-interval requirement remains unexplained |
| MJD day, 40–44 | `56658` | 2014-01-01 in the declared GPS time system |
| MJD fraction, 46–60 | `0.0016203703708` | 140.00000003712 seconds into that GPS day, **37.12 ns after** the calendar tag |

These are GPS fields, not UTC timestamps. The independent nominal January-2014
check has TAI−UTC=35 s and TAI−GPS=19 s, giving GPS−UTC=16 s. Thus the calendar
interpretation conditionally corresponds to UTC 00:02:04 and week-seconds to
UTC 00:00:04. UTC XML validity is a separate metadata clock. Neither it nor the
apparent convenience of the calendar tags chooses the authoritative field.

Exact rational arithmetic avoids floating cancellation:

`(0.0016203703708 - 140/86400) * 86400 = 0.00000003712 s`.

F15.13 has a **representational quantum of 8.64 ns** (10^-13 day); nearest
rounding of an exact fraction alone would contribute at most 4.32 ns. For the
literal 140-s day fraction, nearest rounding is `0.0016203703704`, yielding
**+2.56 ns**, rather than the supplied **+37.12 ns**. The supplied difference is
116/27 quanta. This rules out *only* final nearest-decimal rounding of that exact
fraction as the sole explanation. It does not identify the producer's internal
arithmetic, physical clock error, field precedence or a permissible tolerance.
Truncation at that digit also cannot alone explain this positive difference.
No field is changed. Format resolution is not demonstrated clock accuracy.

<!-- time-control -->
```python
from fractions import Fraction


def time_control():
    quantum = Fraction(86400, 10**13)
    supplied = Fraction("0.0016203703708") * 86400 - 140
    nearest = Fraction("0.0016203703704") * 86400 - 140
    return {
        "mjd_delta_s": supplied,
        "quantum_s": quantum,
        "nearest_delta_s": nearest,
        "week_delta_s": 259220 - 259340,
    }
```

The unchanged parser uses exact Decimal source calendars for diagnostics. Its
qualifier rejects GPS second 60 and nonzero submicrosecond fractions **before**
Astropy split whole/fraction TimeGPS→UTC conversion. The fresh audit accounts for
7,647 epochs: **5,118 conditional conversions, 1,806 submicrosecond exclusions,
723 second-60 exclusions**. All 5,118 conditional epochs pass EOP preflight,
including ±0.5-s support; this is not state transformation or frame qualification.
No rounding, carry, interpolation or policy relaxation occurred. Time remains
PARTIAL; scientific epoch eligibility remains BLOCKED.

Producer information needed: authoritative representation and any erratum for
the 120-s disagreement; exact MJD generation/rounding semantics; SP3-c/d and zero
interval conventions; GPS second-60 and eight-decimal fraction handling, with
independently checkable examples and applicable version. Physical significance
of any small residual time discrepancy belongs in a justified precision/error
budget, not an arbitrary matching tolerance.

## What the current TEME→ITRS implementation establishes

SGP4/WGS72 is evaluated with nominal UTC calendar Julian days split into day and
fraction. Its output has geocentric TEME position km and velocity km/s, carrying
the actual requested UTC epoch. `earth_fixed()` builds `Time(at, scale="utc")`
and supplies that same object as both TEME and target ITRS `obstime`; it does not
transform the GP element epoch's position and then relabel it as another time.
Unvalidated leap-spanning transformations are refused. No real Swarm state was
used to check this path; published/synthetic reference controls were used.

Installed Astropy **7.2.3**, PyERFA **2.0.1.5**, sgp4 **2.27**:

1. `teme_to_itrs_mat` computes ERFA **GMST82 with UT1**, consistent with its
   cited Vallado 2006 TEME convention; this is not substitution of TEME by GCRS.
2. Polar motion uses local `xp`, `yp` through `pom00(xp, yp, 0)`. The TIO locator
   s′ is deliberately zero for this convention. No new precession/nutation or
   ITRF datum correction is added by OrbitIQ.
3. Position is rotated by that matrix. Velocity uses Astropy's
   `FunctionTransformWithFiniteDifference`, symmetric **1-s** differences, including
   input velocity reorientation and frame-motion effects. Its time support is
   ±0.5 s; it is not simply the position matrix multiplied by velocity.
4. Explicit bundled `finals2000A.all` and leap data are loaded under the existing
   lock/context. UT1 and polar-motion status for the historical subset is
   `IERS_B_final`. Range/finite/expiry/quality checks cover all support instants;
   no automatic download or degraded fallback. Final-resource flags do not
   establish a particular terrestrial realization or satellite uncertainty.
5. ITRS attributes are **`obstime` and `location`**. Output is geocentric in this
   pipeline; there is no ITRF-realization selector or implemented IGb08 mapping.
   WGS84 geodetic conversion is a subsequent presentation calculation, not a
   change to the Cartesian residual frame.

Resource package `astropy-iers-data 0.2026.10.12.1.3.27`; EOP SHA-256
`9fbc14ae5e71de96cc1e6b43b54a547acc80c7a6ce910c0209ad6230ff3d30cd`,
leap SHA-256 `6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7`,
expiry 2027-06-28. These identities are reproducibility inputs, not an error budget.

The existing fixed-EOP Vallado controls use 2e-5 km position and 1e-6 km/s velocity
absolute numerical tolerances; bundled-EOP controls use 3e-4 km and 1e-5 km/s.
These inherited reference-comparison tolerances are not proposed Swarm accuracy
targets or bounds on IGb08 alignment. Floating representation, finite differences
and interpolation require a separate precision assessment for a stated objective.

## Realization alternatives and a useful mathematical control

The actual SP3 declares **IGb08**; XML describes generic ITRF Earth-fixed
spacecraft-COM positions. IGS chronology establishes IGb08's ITRF2008 datum
alignment. It does not identify the exact processing alignment, GNSS orbit/clock,
station/antenna, EOP versions or error covariance used by this 0201 product.
Reprocessing dates 2021/2022 do not replace the declared realization with a newer
frame. General ITRS output is also not automatically ITRF2014, ITRF2020 or IGb08.

| Approach | Required frames, parameters, epoch and validity | Verification / precision / decision |
| --- | --- | --- |
| Existing pipeline sufficient for a stated precision scope | Explicit convention/realization relationship, applicable 2014 interval and justified bounds; no unexplained identity assumption | Numerical TEME controls exist; no actual-pair alignment/systematic bound or accepted precision objective. **Not adopted** |
| Documented global realization transform | Identify source realization and IGb08 alignment; authoritative direction, translations/rotations/scale and rates, epoch, time units, validity, covariance and product conventions | General IERS method and one published parameter row tested below; actual source/target mapping and independent product controls absent. **Not implemented operationally** |
| Another compatible reference product | New exact product, acquisition/reuse evidence, time/quality/frame qualification, lineage and independent controls | No replacement acquired or presumed compatible; evaluate separately if needed |
| Current outcome | Keep provenance and all unresolved terms explicit | **Alignment BLOCKED**; lack of an Astropy IGb08 class alone does not prove comparison impossible |

A genuine global similarity transform can map compatible geocentric coordinates
when its endpoints/conventions are established; the fact that its parameters were
estimated from stations does not automatically prohibit satellite use. Conversely,
IGS station-local ties, antenna offsets, tectonic motion, solid-Earth tide or
post-seismic corrections cannot be copied as satellite-wide corrections.
IERS §4.2.6 also distinguishes TT/TCG scale and mean/instantaneous geocenter
conventions; assess relevance at the eventual precision scope rather than
automatically applying station corrections to this orbit.

IERS equations 4.3–4.4 give, to their stated linearized order:

`x2 = x1 + T + D*x1 + R*x1`

`v2 = v1 + Tdot + Ddot*x1 + D*v1 + Rdot*x1 + R*v1`.

`R` is the skew matrix for `(R1,R2,R3) × x`. Convert mm→m, ppb→10^-9 and
mas→radians; propagate parameters from their stated epoch with defined year/time
units. Equation 4.5 drops `D*v1` and `R*v1` under the document's **station-motion**
scale assumption. That simplification is not automatically valid for a moving
satellite. Using position-only KIN does not justify inventing observed velocity.

The reviewed **2019 update**, Table 4.1, supplies this illustrative row:
**ITRF2014→ITRF2008**, epoch **2010.0**, T=(1.6,1.9,2.4) mm,
D=−0.02 ppb, R=(0,0,0) mas; rates Tdot=(0,0,−0.1) mm/year,
Ddot=+0.03 ppb/year, Rdot=(0,0,0). This is **not** a discovered
OrbitIQ-ITRS→IGb08 parameter set. Its adjusted global parameters are not a complete
product uncertainty model or a validity guarantee for this pair.

<!-- frame-control -->
```python
from decimal import Decimal


def published_frame_control(dt_years, xyz_m):
    # Synthetic control only: IERS 2019 Table 4.1, ITRF2014 -> ITRF2008.
    dt = Decimal(dt_years)
    translation = [
        Decimal("0.0016"),
        Decimal("0.0019"),
        Decimal("0.0024") - Decimal("0.0001") * dt,
    ]
    scale = (Decimal("-0.02") + Decimal("0.03") * dt) * Decimal("1e-9")
    return [x + t + scale * x for x, t in zip(xyz_m, translation, strict=True)]
```

Independent literal controls for the **synthetic** point (7,000,000,0,0) m:
at 2010.0 → (7,000,000.00146,0.0019,0.0024) m;
at 2014.0 → (7,000,000.0023,0.0019,0.0020) m. Decimal comparisons are exact for
these finite constants; they are not statements of physical precision. Tests
also check the full derivative with hypothetical rates and a moving synthetic
point. There is no independent physical IGb08 reference vector for the actual
pipeline/product pair; mathematical success cannot supply that missing evidence.
No station simplified-velocity equation, identity/Helmert operation or numerical
approximation is introduced into the application.

## KIN-specific quality and lineage

The fresh inspection confirms 7,647 P/EP epochs, no V/EV records, no zero XYZ
components, zero EP format-review flags and no extended P quality fields.
This is structural evidence, not complete temporal coverage or quality acceptance.
Header accuracy exponent 0 means unknown. EP axis formal sigmas range X 5–95,
Y 5–85, Z 6–97 mm; clock sigma 36–311 ps, with six scaled correlation integers.
Formal estimates, coordinate text resolution (1 mm), nominal specification
“10 cm 3D” and demonstrated external accuracy remain distinct.

The hash-matching nine-page VAL PDF was inspected through its existing reviewed
renderings; pages 5,6,8 were visually revisited. Fresh PDF text extraction yields
page numbers only, not numeric plot evidence. Page 5's GPS tracking/status colors
lack an adequate acceptance legend; page 6 names RDOD ephemerides; pages 8–9
say “Swarm-A POD” without uniquely identifying the KIN member. The detailed
specification does apply VAL to KIN and COM, but this does not identify each plot
as a validation of this exact KIN member. No provider plot statistic was turned
into an OrbitIQ accuracy result. No new reference interval, outage/discontinuity
mask or quality threshold was inferred. Accepted quality indices remain empty.

The KIN XML lists spacecraft GPS RINEX, attitude, model and dynamics inputs with
0401 filenames; the specification lists IGS/IERS/CODE contributions. Exact
external versions and actual-pair GP observation/fit dependencies remain unknown.
No upstream input was downloaded here. Independence is **NOT ESTABLISHED**.
ESA must explain applicable KIN masks, discontinuities, VAL plots/codes and EP
formal-error scope/calibration for version 0201; otherwise quality stays BLOCKED.

## Provisional error-budget framework — no numerical total

| Contributor | Quantified evidence | Type / correlations / statistical use | Missing information |
| --- | --- | --- | --- |
| GP elements, fit and propagation | No actual-pair covariance or empirical bound; reference tests verify implementation only | Random/systematic components unknown; correlations with reference unknown; do not combine | Fit span/sensors/model lineage, covariance or defensible empirical scope |
| KIN reference | EP formal ranges and nominal 10-cm specification only | Formal per-epoch estimates; external bias and calibration unknown, temporal/cross-source correlations unknown | KIN-specific validation, acceptance mask and uncertainty interpretation |
| Time | Exact −120-s and +37.12-ns representation conflicts, 10-ns/8.64-ns text quanta | Known discrepancies, **not calibrated random sigmas**; do not add by RSS | Canonical time/producer erratum, physical time uncertainty and permitted representation policy |
| Realization/alignment | General ITRF2008 datum relationship and illustrative IERS parameters, no pair-specific bound | Possible scale/origin/rotation systematics; not independent scalar noise | Actual endpoints, parameters/rates, covariance, epoch, validity, precision objective |
| EOP/leaps | Pinned resource hashes, final historical flags, coverage | Interpolation/model and resource errors not quantified here; potentially shared with reference | Relevant EOP uncertainty/covariance and processing-series comparison |
| Coordinate/velocity transformation | Passing published controls and known finite-difference method | Numerical/method effects; inherited test tolerances are not physical sigmas | Objective-specific numerical sensitivity and full state derivative if needed |
| Numeric representation | Decimal/rational metadata diagnostics; source/app precision contracts known | Quantization bounds only under specified rounding; not empirical accuracy | Approved treatment of unsupported timestamps and computation-error analysis |
| Quality, gaps and reference point | Counts/exclusions, ESA spacecraft-COM description | Selection effects and discontinuities, not an independent variance term | Accepted mask, completeness limits, relevant antenna/COM/origin conventions |
| Shared upstream dependencies | General IGS/IERS/CODE and SSN descriptions only | Cross-covariance unknown; different organizations do not remove correlation | Exact-record fit and reference-processing lineage |

For compatible Cartesian estimates, `C_delta = C_ref + C_pred - C_ref,pred -
C_ref,pred.T` when those covariances are actually known. They are not known here.
Do not assume zero cross-covariance, add formal sigmas by root-sum-square, produce
an error ellipse or divide by sqrt(N). Known systematic bounds should be kept
separate from calibrated random uncertainties. A conservative bound can only be
formed if its contributing bounds and applicability are established.

Useful first-order sensitivities are `delta_x ≈ delta_T + delta_D*x +
delta_theta × x`, and separate epoch errors contribute approximately
`v_ref*delta_t_ref - v_pred*delta_t_pred`. A shared epoch error affects the
relative trajectory derivative; it is not always an independent speed×time term
for each source. No genuine state is used to assign those sensitivities a number.
There is **no defensible numerical total or accuracy threshold yet**.

## Requirement status and next evidence

| Requirement | Status for this milestone |
| --- | --- |
| Original intake/integrity and static model evidence | PASS for inspection; authentication/availability limitations retained |
| Objective, residual/statistics definitions and selection policy | PREDECLARED; executable scientific study BLOCKED |
| Exact time discrepancies and format quantum derivation | VERIFIED arithmetic; canonical time policy BLOCKED |
| Existing TEME transformation and same-epoch behavior | DOCUMENTED / numerical-reference tested; not IGb08 qualification |
| IGb08 relationship and alternatives | Datum relationship documented; actual-pair alignment BLOCKED |
| Independent mathematical controls | Supported limited controls; no independent physical IGb08 pair vector |
| KIN applicability / quality | General VAL applicability documented; exact accepted KIN epochs BLOCKED |
| Error-budget structure | PREPARED; numerical bounds/correlations and total unresolved |
| Genuine record / reference-epoch selection | NONE; selected source null, accepted index set empty |
| Historical availability / lineage / independence | Unknown / incomplete / NOT ESTABLISHED |
| Operational evaluation | BLOCKED; adapter inactive, genuine calculations and residuals zero |

Before real evaluation: resolve time interpretation with independently checked
producer evidence; approve KIN quality/epoch criteria; identify the common-frame
treatment and precision/error budget with independent controls; finalize the
predeclared selection under the qualified interval; freeze all provenance/resource
hashes and limitations; obtain separate authorization. A retained limitation on
historical availability may permit only a retrospective claim, but it does not
excuse unresolved time/frame/quality gates. If essential product evidence is
unavailable, retain BLOCKED or qualify an alternative reference independently.

Actual checks and preservation results are in
[protocol verification](phase-11.3.1-protocol-verification.json). No commit, push,
remote CI, deployment, DNS or infrastructure change is part of this task.
