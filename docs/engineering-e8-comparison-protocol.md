# ORBITIQ-IGS-GPS-RETRO-001 — proposed protocol v0.1

Status: **BLOCKED — ADDITIONAL EVIDENCE REQUIRED**. Predeclared on 24 October 2026
before any comparison outcomes. This is a review proposal, not an executable
comparison. E8 authorizes source inspection and feasibility only. Explicit user
approval and scientific prerequisites are required before implementing or running
any real comparison. No residuals have been calculated.

## Question and interpretation

For one fixed, compatible historic GP initial condition for GPS SVN G064, what
would the Cartesian difference from a qualified IGS final orbit be at the exact
reference epochs, after justified time, reference-point and frame alignment?

The permitted future interpretation is **retrospective disagreement between two
estimated/modelled orbit products for these frozen inputs**. It would not identify
an absolute truth, a pure propagation error, historical forecasting performance,
independently verified prediction accuracy, maneuver/anomaly or operational safety.
Different provider names do not establish statistical independence.

This study is independent of the ESA helpdesk response and Swarm-A reference files.
IGS is an international combined service: the actual final's header lists ESA among
analysis-centre submissions, and the processing summary records ESA involvement.
It must not be described as having no ESA upstream contribution. If all ESA
contributions must be excluded, this candidate must be reconsidered before review;
no source will be silently substituted.

## Frozen reference candidate and identifiers

- Product: `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`.
- Acquired source: [BKG IGS global data-centre HTTPS mirror](https://igs.bkg.bund.de/root_ftp/IGS/products/2295/IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz).
- Compressed SHA-256:
  `26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`;
  102,609 bytes.
- Expanded SHA-256:
  `8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`;
  253,250 bytes.
- Actual header: SP3-c positions; `ORBIT`, `IGS20`, `HLM`, `IGS`, GPS time;
  GPS week 2295 / seconds 86400, MJD 60310 / fraction zero, 900-second cadence.
- Target: PRN **G30**, SVN **G064**, NORAD **39533**, COSPAR **2014-008A**.
  Official satellite-metadata SHA-256:
  `ac93d053eac7d8b08ce129b6af98667e1867296e1685417d38c081cd046558ae`.
  Preserve `2014:052:00000` to open-ended `0000:000:00000` assignment strings.
  The nominal-calendar lookup is not a sub-second assignment-time qualification.
- Full product: 32 GPS identifiers, 96 epochs, 3,072 P records; no velocity or EP
  covariance records. Candidate G30 has 96 records with no missing XYZ, maneuver,
  predicted-position or unknown-axis-sigma markers under the inspected profile.
- Secondary compatibility investigation: G10 / SVN G073 / NORAD 41019. It is not
  an alternative selected to improve numerical results; no outcomes exist.

CDDIS returned an Earthdata login page, not product bytes. Do not claim this
mirror download authenticates a NASA archive copy or demonstrates byte identity
with an unacquired CDDIS copy. All raw products remain private/unpublished.

## GP initial condition: deliberately unfilled scientific input

**No eligible GP record is selected.** The inspected current GP dataset SHA-256 is
`8e1b961369ba5d083ec99b792453e26e82217f0ac609dc6f4eece432a0f5ef87`, acquired
2026-10-24T04:58:29.302996Z from CelesTrak `GROUP=gps-ops&FORMAT=JSON`.
Its G30 record is at zero-based index 14, epoch
2026-10-23T07:38:57.767424Z, canonical derived-record SHA-256
`da1c730d1fc16648e57d2954f3f7c7eb7d8c3c14a71522bde262022f41c6f70d`.
These facts identify an **excluded current input**, not the proposed initial state.
Canonical record hashing uses UTF-8 JSON with sorted keys, compact separators and
no NaN; it is distinct from hashing the original full response bytes.

A later review must freeze an original historical response hash, exact record
index/fields, epoch, acquisition provenance and selected derived-record hash.
Use only existing `Elements` acceptance: Earth, nominal UTC epoch, TEME, SGP4,
ephemeris type zero, WGS72, supported catalog range and finite fields. Current
G30/G10 records passed those static checks and initialized the existing deep-space
method `d`; no position was calculated. This does not validate prediction accuracy.
Do not duplicate the engine or change the inclusive ±7-day source-epoch guard.

For this proposal use **one fixed GP record**, forward propagation only. Require
its epoch no later than the frozen reference start and within the guard of every
frozen reference epoch. The resulting eligible GP-epoch interval is:

`[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z]`, inclusive.

After identity/static/provenance qualification, rank available eligible records by
decreasing epoch and propose the first **unique** record for review. Competing
same-epoch records block selection; source order, element-set/revolution numbers
and smallest residual are not tie-breakers. Do not fall back to another record
following ambiguity or switch GP records during the arc. No eligible record means
BLOCKED. Historical availability before that epoch and full fitting lineage
remain unknown unless separately evidenced; the element epoch is not a creation,
publication or availability timestamp.

## Exact time and sampling policy

Freeze the original 96 source indices, with GPS-calendar tags from
2024-01-01T00:00:00.00000000 through 2024-01-01T23:45:00.00000000.
The conditional UTC diagnostic interval is
**[2023-12-31T23:59:42.000000Z, 2024-01-01T23:44:42.000000Z]**.
GPS-to-UTC uses the existing split-second Astropy TimeGPS conversion under the
explicit local leap/EOP context; the observed 18-second offset is not hard-coded.
Pin package versions, source hashes, policies and execution time from the evidence.
Calendar, GPS-week and MJD start fields agree exactly in this acquired file.

The `%c GPS` declaration describes epoch tags. The comment about IGS Time (IGST)
describes the clock reference; it does not authorize shifting position epochs or
subtracting satellite clock corrections. No clock comparison is in scope.
Reject unsupported GPS second 60, UTC leap-second propagation labels,
submicrosecond epochs, inconsistent headers, reversed/duplicate epochs, unsupported
cadence and ambiguous identities. Do not round, snap to a UTC quarter hour, select
a nearest point, interpolate or extrapolate. Missing records are not filled.

Future SGP4 states would be evaluated exactly at the approved converted reference
epochs. GP epoch and reference epoch need not coincide; propagation is what would
connect them. Freeze the interval anchor from the first original reference epoch,
never the first surviving quality sample. Retain rejected source indices/reasons.
Changing the target, grid, GP policy or interval requires a versioned review before
outcomes, not a change after seeing residuals.

## Frame and physical reference point — blocking gates

Proposed path, **not implemented/qualified here**:

`existing SGP4/WGS72 TEME at UTC → existing same-epoch Astropy ITRS → reviewed IGS20 alignment → common Cartesian reference point`.

Actual IGS20 is aligned to the ITRF2020 datum and associated with the IGS20 antenna
models. Astropy's ITRS output has no selected ITRF/IGS realization attribute.
Document origin, axes, scale, frame epoch, rates, handedness, position/velocity
conventions, applicable alignment evidence and independently checked controls
before treating outputs as comparable. Do not assume a zero alignment or apply a
station Helmert table to orbit states without demonstrated applicability.

The existing local EOP preflight checked UT1/polar-motion coverage and ±0.5-second
support for all 96 reference epochs; it returned IERS_B_final resource flags.
That establishes resource availability, not realization alignment or a satellite
uncertainty budget. Missing/degraded resources block the run; no automatic
resource download or zero-EOP fallback is permitted.

Separately qualify the **satellite physical point** and the Earth-centred frame
origin. Metadata SINEX explains dynamic CoM and antenna eccentricities; that is
not by itself product-specific proof that the GP-derived state and this SP3
state describe the same physical point. Pin applicable historical antenna/attitude
and processing conventions, or justify why a correction is unnecessary. The
current `igs20.atx` retrieved in October 2026 is not established as the exact
calibration version used for the 2024 combination and was not applied.

## Quality, exclusions and uncertainty

Check the actual weekly combination summary and per-target flags before acceptance.
The header's list of ten AC submissions is not proof all contributed with weight.
The inspected summary records exclusions including JPL, SIO and EMR and inclusion
of JGX from week 2289; preserve dated product-specific evidence. Do not infer
statistical independence from the summary's independent evaluation terminology.

Position units follow SP3 P records: **km**; six-decimal formatting has a 1-mm
representational quantum, not demonstrated 1-mm accuracy. Clock fields are µs and
unused. Header accuracy exponents use `2**n mm`, with zero unknown; per-epoch XYZ
sigmas use `1.25**n mm`, with zero equal to 1 mm and blank unknown. G30's header
code 2 represents a quantized 4-mm indicator. This is not an acceptance threshold,
calibrated truth, full covariance or a quantified GP-minus-reference error budget.

Predeclare exclusions for target/identity disagreement, bad hashes, unsupported
time/precision/frame/units, missing XYZ, predicted orbit or maneuver markers,
unknown required XYZ sigmas, absent records, unqualified point/frame/resources,
and an ineligible/ambiguous GP input. Keep all original indices/reasons. The
current global file contains unknown axis-sigma fields on other satellites and
missing G27 clocks; those facts must not be hidden by G30's complete basic flags.
A missing unused clock is recorded rather than silently used as a position error.

A qualified uncertainty/claims policy is required before an executable run. GP
covariance and full fitting lineage are not provided by the inspected input; no
joint cross-provider/cross-time covariance is established, and this product has
no EP covariance records. Keep uncertainty unquantified where evidence is missing.
No normalized residuals, chi-square tests, confidence intervals, independence
claims or numerical scientific pass/fail threshold are authorized. The existing
numerical-library regression tolerances remain unchanged and are not GPS accuracy
requirements. Different providers may share GNSS observations/models/resources;
the relevant GP tracking/fit dependencies remain unestablished.

## Residual convention and future outputs — specification only

Only after qualification and explicit approval, define:

`delta_r_km(t) = reference_IGS20_km(t) - calculated_aligned_IGS20_km(t)`.

Preserve that sign for all three Cartesian axes. Define 3D norm from those
components; m displays must explicitly multiply km by 1000 and label the unit.
No along-track/cross-track claims are proposed because qualified velocity is not
provided by this P-only reference profile. No residual code is present in E8.

Future diagnostic outputs would include source/epoch eligibility tables, time
alignment/resource checks, per-axis/norm time plots, actual gap/exclusion markers,
mean signed components, median norm, `sqrt(mean(norm**2))`, maximum norm and sample
count. These are descriptive summaries of this arc, not independent samples or
statistical confidence. Do not smooth, trim based on residual size, fit away an
offset or choose the lowest-error input. Report exclusions and incomplete coverage.

## Review gates and next inputs

Obtain an eligible original historical GP input for NORAD 39533 (a scoped request
covering 2023-12-25 through 2024-01-01 would contain the required epoch window).
Then qualify exact identity, reference point/processing, IGS20 alignment, epoch
conversions/resources, per-sample quality and the uncertainty/claims policy. Freeze
the manifest and mask, retain software/lock/resource hashes, independently review
the protocol and obtain explicit user approval **before implementation/calculation**.

An alternative prospective acquisition plan could retain current GP bytes now and
wait for the final product covering the corresponding epochs. It requires a
separate interval/version and actual later acquisition; neither availability nor
independent prediction accuracy is established by that suggestion. No scheduler,
new account or provider request was created by E8.

The preserved ESA Swarm-A study remains **PARTIAL**, scientific evaluation
**BLOCKED**, with no qualified residuals. E4 production readiness remains **OPEN**.
