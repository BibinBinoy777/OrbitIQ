# E8.7.8 — Reference-frame and Earth-orientation compatibility

**Decision: NO-GO for scientific comparison; study BLOCKED.** This audit establishes
the historical IGS frame relationship, exact installed transformation behavior,
and local resource identities. It does **not** establish the complete computed
TEME-to-IGS20 convention or approve the current EOP treatment for comparison.
No active algorithm, configuration, protocol or admission policy changes.

Study `ORBITIQ-IGS-GPS-RETRO-001`, assessed 25 October 2026 UTC, in
`/workspace/OrbitIQ-e82`, branch `engineering-e8.2-igs-reference-qualification`,
HEAD `b0a03205e3930b55651232d8b7ffbc9e879ae8c6`.
The [evidence ledger](engineering-e8.7.8-frame-eop-evidence.json) records 21 scoped
requirements, exact sources/versions/hashes, observations, evidence categories,
limitations and closure evidence. **D** = direct observation, **P** = authoritative
documentation, **I** = inference, **U** = unknown. A PASS applies only to its
stated requirement, never automatically to the whole scientific chain.

## Evidence reused and current inputs

Reviewed the [E8.2 reference assessment](engineering-e8.2-reference-qualification.md),
[E8.3 implementation audit](engineering-e8.3-frame-eop-qualification.md),
[E8.4 quality/point assessment](engineering-e8.4-quality-qualification.md),
[E8.5 dependency assessment](engineering-e8.5-source-provenance.md),
[E8.6 statistic reconciliation](engineering-e8.6-g30-statistic-reconciliation.md)
and [E8.7.7 readiness decision](engineering-e8.7.7-pre-comparison-readiness.md),
their ledgers, actual installed source, resources and existing tests. Earlier
reports remain dated snapshots: their old missing-input statements are not the
current acquisition status and were not overwritten.

**D:** both original XML attachments and preserved captures still match:

| Input                               |  Bytes | SHA-256                                                            | Admission under explicit v1    |
| ----------------------------------- | -----: | ------------------------------------------------------------------ | ------------------------------ |
| G05 `sat000035752.xml`, NORAD 35752 | 10,072 | `c398ecdc707013d0c9bf245b9eeb1894aef1f2a7bafd60f9a687ce797e0a0828` | 6 admitted, 2 HOLD, 2 rejected |
| G30 `sat000039533.xml`, NORAD 39533 | 11,057 | `34ccec7bd8fd4be88346e03787027a5ecc71a6d75db75668bd4c641fcd713da5` | 9 admitted, 0 HOLD, 2 rejected |

All 10/11 OMM identities were rechecked without satellite initialization.
The strict policy remains the default; `historical-retrospective-admission-v1`
remains explicitly activated for these exact artifacts only. Present-empty
creation/originator metadata remains PARTIAL, not reconstructed. Historical
availability, publication times and complete fitting lineage remain unknown.
Fifteen records are admitted **for further qualification only**; zero are
scientifically qualified or selected. G05 indices [3,4] remain HOLD. G30 review
comes first for continuity with its original protocol, not because a scientific
comparison or particular epoch has been chosen.

**D:** retained `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz` still has 102,609 bytes,
SHA-256 `26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`.
Its in-memory expansion remains 253,250 bytes, SHA-256
`8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`.
No expanded reference was rewritten. The SP3-c header declares `ORBIT IGS20 HLM IGS`,
GPS time, 96 position epochs and 900-second cadence. Existing inspection records
32 satellites and 3,072 P records, without reference velocities. XYZ is geocentric
terrestrial Cartesian km; conventional axes are reference pole Z, reference
meridian X and right-handed 90-degree-east Y. The header is not a full processing
manifest or uncertainty statement.

## Published frame relationship and its limits

**P:** the freshly checked [IGS frame page](https://igs.org/wg/reference-frame/)
lists IGS20 for **27 November 2022–1 February 2025, GPS weeks 2238–2351**, aligned
to ITRF2020. Week 2295/January 2024 is inside that interval. Some narrative on
that page is older; the dated chronology is the evidence used here. The retained
week-2295 summary says 28 November 2022 in its adoption remarks; neither that
one-day wording difference nor the earlier advance notice changes this case's era.

**P:** the retained correct [IGSMAIL-8238](https://lists.igs.org/pipermail/igsmail/2022/008234.html)
states that IGS20 and ITRF2020 share underlying origin, scale and orientation,
with zero underlying datum transformation parameters. It separately describes
station-specific coordinate adjustments associated with antenna calibrations.
Its planned week-2230 switch is not substituted for the actual chronology.
IGS20 is an ITRF2020-derived station realization with associated `igs20.atx`
ground/satellite antenna conventions, not simply an arbitrary SP3 label.

**D/P:** the retained weekly summary's remarks 6/7 say the products adopt
IGS20/repro3 standards and that daily SINEX-derived AC rotations align orbit/ERP
solutions to the IGS frame. Those producer rotations are **not** an instruction
to rotate a GP-derived spacecraft state using AC station parameters. E8.4's
current ANTEX metadata is not proof of the exact calibration revision used in 2024.

**I/U:** no additional nonzero datum transformation is justified by these sources.
An eventual identity alignment requires a reviewed convention crosswalk for the
actual computed terrestrial state. Astropy's ITRS class name does not certify
an ITRF2020 realization, the physical satellite point or this chain's accuracy.
Do not apply station offsets, WGS72-to-WGS84 geodetic substitutions or AC alignment
parameters as an invented satellite datum correction.

## Exact installed implementation and documentation

**D:** versions reverified: Python **3.12.14**, Astropy **7.2.3**, PyERFA
**2.0.1.5**, ERFA **2.0.1**, SOFA **20231011**, NumPy **2.5.4**, sgp4 **2.27**,
astropy-iers-data **0.2026.10.12.1.3.27**. Fourteen installed module/resource hashes
match E8.3. The ledger pins unchanged application/lockfile hashes and eight exact
function locators. No dependency installation or update was performed.

**P/D:** [Astropy's documentation source tagged v7.2.3](https://raw.githubusercontent.com/astropy/astropy/v7.2.3/docs/coordinates/satellites.rst)
was retrieved successfully (6,300 bytes; SHA-256
`493bf8bbf7a566de2d140765810e9f4d46f41e1c3b57c557549fa0debe1cf0cd`).
It describes SGP4 output in TEME, differing TEME definitions, Vallado 2006 and
same-obstime ITRS conversion. Its examples were **not executed**. The matching
rendered v7.2.3 page returned HTTP 404 this time (E8.3 recorded 403); no other
documentation version was substituted. Installed docstrings/source are also
exact-version evidence.

**D:** the existing element layer interprets explicit EARTH/TEME/UTC/SGP4,
ephemeris-type-zero inputs, validates bounded finite fields and initializes
WGS72/improved mode `i` only when requested by application code. The engine
forms a split Julian date from aware UTC, uses the existing nominal
86,400-second UTC-day convention and produces calculated TEME km/km/s, not
observations. No real input was initialized or evaluated here.

The audited transformation order is:

```text
UTC instant -> UT1 two-part JD using selected table
GMST82(UT1) -> sidereal rotation
table xp, yp [arcsec] -> radians
pom00(xp, yp, s-prime=0) -> polar-motion matrix
c2tcio(identity, GMST82, polar-motion matrix) -> Cartesian rotation
ITRS at the same obstime, geocentric location
```

In ERFA's matrix convention this is `W * R3(GMST82)`, applied to a column
vector. `pom00` defines pole coordinates along the 0 and 90-degree-west
meridians; that is distinct from the Cartesian Y-axis convention. The installed
TEME branch deliberately uses GMST82 instead of ERA for Vallado consistency.
Its identity celestial matrix is part of that TEME adaptation, not a statement
that TEME is GCRS/CIRS and not a full modern precession/nutation chain.
`ITRS` exposes obstime/location, with no ITRF-release selector. This path is
geocentric; no observer displacement, aberration or geodetic round trip is
required for a future Cartesian product comparison.

Astropy's differential handling uses a symmetric one-second finite difference;
OrbitIQ preflights EOP at the center and **±0.5 s**. This is software behavior,
not reference velocity evidence. Split JD avoids unnecessarily collapsing time
precision. XML's six fractional digits are preserved; millisecond-separated G30
epochs remain distinct. Floating-point computation and preserved microseconds
do not establish scientific accuracy. Unsupported epoch-to-target leap crossings
are explicitly refused, rather than silently treating UTC as UT1/TAI.

Existing `test_phase3_science.py` checks a published Vallado vector with fixed
and bundled EOP. Its fixture position tolerances are respectively **0.00002 km**
and **0.0003 km**, velocity tolerances **0.000001 km/s** and **0.00001 km/s**.
Other tests cover the Astropy example, time conversion, resource failures,
prediction policies and configuration restoration. These are reference/software
tests, not G30/IGS20 truth validation or an approved comparison error budget.
They were inspected, not rerun; no new numerical error or uncertainty was calculated.

## Local resources, interpolation and fail-closed behavior

**D:** resource inventory includes workspace/research manifests, installed data
and test fixtures, and the Astropy home cache (absent). No matching IGS ERP
payload was found within that inspected scope; no claim is made about external
storage. Legacy Astropy test excerpts are test-only, not alternate study EOP.

| Resource from astropy-iers-data 0.2026.10.12.1.3.27 | Role and coverage                                                                                                                                                    | Provenance/convention limits                                                                                                                      |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `finals2000A.all`, 3,769,212 bytes                  | **Active**: explicit `IERS_A.open`, 19,999 usable daily rows, UTC-MJD 41684–61682, first prediction 61315. MJD 60309/60310/60311 merge B flags for UT1/polar motion. | Package source URLs identify IERS/USNO finals2000A; precise provider issue identifier absent. Final B preferred, otherwise rapid A or prediction. |
| `eopc04.1962-now`, 5,174,166 bytes                  | **Available, unused**: 23,623 daily rows, MJD 37665–61287. Header: EOP (IERS) **20 C04**, consistent with ITRF2020, sampled 0h UTC, IAU2000.                         | `IERS_B` is its loader class; this does not make the active finals2000A B columns identical to C04. No per-row I/P flags in this format.          |
| `Leap_Second.dat`, 1,352 bytes                      | **Active**: TAI−UTC step table; expires **2027-06-28**.                                                                                                              | IERS Bulletin-C source through the package; not an Earth-rotation/polar-motion series.                                                            |

SHA-256 identities, respectively:

```text
finals2000A.all   9fbc14ae5e71de96cc1e6b43b54a547acc80c7a6ce910c0209ad6230ff3d30cd
eopc04.1962-now   c7817d842083f74ffe724f1ef419a6b869f6d9c391a48db5018694bb19dbcff7
Leap_Second.dat   6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7
```

**D/P:** bundled/provider finals2000A readmes specify UTC-MJD, UT1−UTC seconds,
PM arcseconds, A I/P flags and separate B columns. A-only error columns are
**not** B uncertainties after merging. C04 has PM/UT1, rates, LOD, dX/dY and
labelled error columns; the exact local column units and availability are recorded
in the ledger. Those fields were read, not combined into any new uncertainty
estimate, and none is a satellite-position uncertainty. The live C04 description
request returned HTTP 503; its contents were not treated as read. Its local
header/readme remains usable metadata, not a complete component specification.

**D:** base Astropy `IERS._interpolate` uses linear interpolation in UTC-MJD,
with rounded integer jump removed from the adjacent UT1 difference at a leap.
This does not round an OMM epoch. Outside the table it holds endpoint values and
returns negative status; raw coordinate helpers can otherwise warn and use mean
PM or assumed zero UT1. OrbitIQ rejects negative/unknown statuses and nonfinite
values before transformation, treats Astropy/ERFA warnings as errors, and disables
downloads and remote leap URLs. No degraded fallback is approved.

The effective local mode remains `measured_or_predicted`; `measured_only` is
available. Prediction support is refused in measured-only mode; otherwise labelled
and refused when prediction-table age exceeds 30 days. Final historical values
are not predictions because the same resource has a future predictive tail.
Leap expiry and all three velocity-support instants are checked separately.
Explicit resources are cached, not auto-refreshed; an intentional environment/
resource update changes their identity and must be controlled. Process-global
configuration/science state is scoped with the existing lock; replay also restores
ERFA leap state. No replay, policy switch or resource update occurred here.

**D:** the prior all-96-epoch GPS/UTC/support preflight is reused, with matching
resource hashes and 192 central UT1/PM final-source flags. UTC grid is
**2023-12-31T23:59:42Z–2024-01-01T23:44:42Z**, GPS−UTC 18 s from the pinned
resource, not a new hardcoded offset. Old exclusions for E8's then-current 2026
GP input are **not** reused as historical admission decisions. Coverage and
instant mapping pass their narrow requirements; model compatibility remains blocked.

## Subdaily and TIO disposition

**P:** use the retained approved **IERS Conventions (2010), TN36**, not an assumed
latest working chapter. Its hash remains
`b0570ff245a6d76977dc56918c64130cc5bf68b679fa8fffb989137f2b833eea`.
The freshly checked [official IERS index](https://www.iers.org/iers/en/dataproducts/conventions/conventions)
explicitly calls later updates a working version that is not definitive or
officially approved. TN36 is a published baseline, not evidence of every detail
of actual 2024 IGS processing.

| Component                         | Approved published baseline                                               | Current implementation / closure                                                                                                                |
| --------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Diurnal/semidiurnal ocean-tide PM | TN36 §§5.5.1.1–2; §8.2, Tables 8.2a/b: restore after interpolation        | No explicit restoration in selected path. Obtain actual series and 2024 combination model/regularization inventory.                             |
| Diurnal PM libration              | §5.5.1.3, Table 5.1a; `PMSDNUT2` described                                | No explicit addition. Exact routine revision/content must be pinned if proposed, not inferred from its name.                                    |
| Ocean-tide UT1/LOD                | §5.5.3.1–2; Chapter 8, Tables 8.3a/b                                      | No explicit addition. Current TEME rotation consumes UT1, not LOD directly.                                                                     |
| Semidiurnal UT1 libration         | §5.5.3.3, Table 5.1b; `UTLIBR` described                                  | No explicit addition. A composite interpolation routine may already include some terms; inventory before combining routines.                    |
| Long-period/secular PM libration  | §5.5.1.1 says already present in observed PM                              | Do not add again. Source-specific long-period UT1 regularization, if proposed, also requires documentation; do not assume every series is UT1R. |
| TIO locator s′                    | Chapter 5 / installed ERFA docs describe its role in terrestrial rotation | Astropy explicitly uses zero for Vallado 2006. That software rationale does not establish adequacy for the intended IGS comparison.             |

**P/D/U:** TN36 explicitly says distributed IERS series omit the relevant
subdaily PM and UT1/LOD variations and prescribes restoration. The audited code
does not implement that explicit full treatment. Daily sampling, B flags or a C04
ITRF2020 header do not close this model question. Exact resource-specific and
2024 IGS producer model inventories remain unknown. Repro3 recommendations and
AC descriptions retained in E8.5 do not pin every operative correction/version.

**Decision:** no blind correction additions. Specify base series, removed/retained
terms, exact routines/revisions, interpolation, time arguments and restoration
order. Prevent composite-plus-constituent and long-period double counting.
Independently review how the Vallado TEME shortcut relates to the intended
terrestrial convention. An explicit accuracy/acceptance objective and complete
derivation are needed to justify zero TIO or an alternative; no new numerical
effect/uncertainty calculation is authorized here. Merely inserting `sp00`, ERA
or a GCRS precession/nutation matrix into the current chain is not justified.

## Matching IGS ERP: identifiable, not locally acquired

**D:** the preserved BKG week-2295 listing names exactly:

```text
IGS0OPSFIN_20233650000_07D_01D_ERP.ERP.gz
```

Listing location: `https://igs.bkg.bund.de/root_ftp/IGS/products/2295/`.
This is the weekly final family beginning 2023 day 365, not an invented
January-1 daily filename. The cached listing is evidence of an archive entry,
not an acquired/validated payload. No ERP data was downloaded or inspected here.

**P/D:** the already acquired week-2295 summary gives more specific evidence:

- Lines **93–105** describe PM/rates from the SINEX combination, AC LOD biases
  calibrated to Bulletin A, combined LOD integrated into UT1−UTC, and the UT1
  starting value anchored to Bulletin A. The actual Bulletin A issue/anchor and
  values used in that run are not established by this prose alone.
- Lines **117–121** name this associated weekly ERP family, including UT1−UTC
  and LOD associated with the ephemerides. That documents the intended product
  association; it does not verify the missing file's actual columns/units/rows.
- Lines **225–239** describe IGS20/repro3 and daily SINEX alignment rotations.
- Lines **410–413** warn that Tables 6/7 are combination-consistency statistics,
  **not the official accompanying SINEX ERP combination products**. They cannot
  replace the absent ERP input.

**P:** the freshly checked [IGS products page](https://igs.org/products/), Earth
Rotation Note 2, independently describes Bulletin-A/VLBI LOD bias calibration
and remaining time-correlated errors. The frame page distinguishes definitive
RF/SINEX-combined ERP from other ACC orbit-combination ERP products. Their
different roles must be reconciled when selecting a future source; a FIN name
alone does not establish identical processing or epoch conventions.

**I/U:** an inspected associated final ERP could improve traceability to the
reference combination. First establish its actual time tags, units, coverage of
all target/support brackets, rates/interpolation, absolute-UT1 anchor, errors,
regularization/subdaily conventions and relationship to the definitive SINEX
product. Published noon/daily-integration descriptions cannot stand in for its
header. Shared GNSS/frame/ERP processing and IERS anchoring introduce dependencies;
using it would not establish independence, agreement or independent accuracy.

No acquisition is requested or performed as a publication step. A future,
separately authorized data acquisition/review may inspect that exact product;
scientific use would still require qualification and explicit authorization.

## G30-first conceptual chain and requirement matrix

| Stage                         | Established or specified                                                          | Remaining scientific gate                                                                      |
| ----------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| 1. Original GP interpretation | Genuine preserved XML, identity/fields/UTC/TEME; explicit retrospective admission | Present-empty provenance remains PARTIAL; availability/complete fitting lineage unknown.       |
| 2. SGP4 TEME generation       | Existing WGS72/mode-i engine inspected                                            | No real initialization/propagation, no independent truth claim.                                |
| 3. Time scales                | Existing GPS→UTC grid/resource evidence; exact original epochs                    | Full UT1 convention distinct from nominal SGP4 UTC days; preserve leap refusal.                |
| 4. EOP evaluation             | Final B coverage and source hashes                                                | Interpolation/subdaily/ERP convention not qualified.                                           |
| 5. Terrestrial rotation       | Exact GMST82/polar-motion/zero-TIO implementation                                 | Reviewed convention/acceptance still required.                                                 |
| 6. IGS20 compatibility        | Named IGS20–ITRF2020 datum relationship                                           | Computed realization equivalence not established.                                              |
| 7. Satellite point            | General IGS CoM/current antenna metadata                                          | Historical processing and GP fitted-point treatment unresolved.                                |
| 8. Prescribed epochs          | 15 admitted records pass guard at all 96 original instants                        | No qualified record selection, independent final review or explicit calculation authorization. |

The [original G30 v0.1 protocol](engineering-e8-comparison-protocol.md) retains
the inclusive GP window **2023-12-25T23:44:42Z–2023-12-31T23:59:42Z**, forward-only
full-window/single-record/latest-unique rules and original grid. No selection,
fallback, trimming or rounding. The
[G05 proposal](engineering-e8.7.1-g05-protocol-proposal.md) remains separate;
no G05 exception or physical-point conclusion is transferred to G30.

| Ledger ID / requirement               | Status       | Remaining evidence or scope limit                                         |
| ------------------------------------- | ------------ | ------------------------------------------------------------------------- |
| F01 IGS20 era                         | PASS         | Product/date scope only.                                                  |
| F02 Named datum relation              | PASS         | No computed-state equivalence inferred.                                   |
| F03 SP3 metadata                      | PASS         | Header is not full processing history.                                    |
| F04 Installed implementation          | PASS         | Software behavior, not scientific accuracy.                               |
| F05 TEME convention                   | PARTIAL      | Review source/model-to-terrestrial consistency.                           |
| F06 UT1 source/coverage               | PASS         | Does not pass subdaily/model adequacy.                                    |
| F07 PM source/coverage                | PASS         | Does not pass realized axes/model adequacy.                               |
| F08 Interpolation/precision adequacy  | PARTIAL      | Agreed precision, regularization and reconstruction policy.               |
| F09 TIO adequacy                      | BLOCKED      | Intended acceptance and convention derivation/review.                     |
| F10 Subdaily conventions              | BLOCKED      | Source/producer-era component inventory and reviewed restoration.         |
| F11 Bulletin-B scientific suitability | BLOCKED      | Complete convention and acceptance disposition.                           |
| F12 Matching ERP availability         | BLOCKED      | Actual preserved payload/metadata, if acquisition authorized later.       |
| F13 ERP scientific suitability        | NOT ASSESSED | Inspect absent payload and reconcile product/convention roles.            |
| F14 Time/instant mapping              | PASS         | Exact metadata/time grid only; not state calculation approval.            |
| F15 Computed ITRS→IGS20 alignment     | BLOCKED      | Independently supported realization/convention crosswalk.                 |
| F16 Full comparison chain             | BLOCKED      | All essential gates plus unchanged-rule selection.                        |
| F17 Dependencies                      | PARTIAL      | Record shared/unknown sources; no zero covariance or independence.        |
| F18 Spacecraft point                  | BLOCKED      | Historical point/calibration and GP fit interpretation.                   |
| F19 Quality/claims                    | PARTIAL      | G30 statistic/uncertainty limitations and bounded claim review.           |
| F20 Review/authorization              | BLOCKED      | Qualified packet, independent review, explicit user authorization.        |
| F21 Available C04 alternative         | PARTIAL      | Header/coverage available, suitability/component inventory not qualified. |

## Recommended EOP policy and remaining work

**NO-GO for the scientific comparison now.** Preserve the current application
policy and pinned Bulletin-B resources for reproducibility. This does not approve
them as the final comparison treatment. Do not choose the source by a preferred
residual or use source availability as an accuracy test.

The smallest useful next evidence is the actual product-era IGS ERP/component
specification and independent review of the complete TEME/GMST82/polar-motion/TIO
to IGS20 chain against explicit acceptance criteria. The named ERP is a justified
future acquisition candidate, not an approved replacement. A properly documented
Bulletin-B or C04 treatment remains possible if its complete physical conventions
can be justified. Any proposal must specify absolute-UT1 provenance, all required
brackets, interpolation/regularization, nonoverlapping subdaily model inventory,
precision and shared-source limitations before implementation.

Named datum relationship, reference era, time mapping, installed behavior and
source coverage can be treated as resolved within their stated scopes. Common
frame/EOP treatment, spacecraft point, quality/claim disposition, full run packet,
independent review and explicit authorization remain essential. G30's E8.6
statistic relationship remains PARTIALLY RESOLVED; it was neither solved nor made
a universal blocker for every future bounded descriptive study. No unweighted
claim limitation or alternative policy is approved as a waiver here.

## Actual verification and preservation

Only this report and its JSON ledger were added to the repository-facing work.
No application, test, dependency, policy or protocol code changed. No pytest,
full application, browser, PDF or remote CI suite was run. E8.7.6's 160 targeted
tests remain a historical result, not fresh verification of this audit.

Fresh checks passed: exact installed versions/14 source-resource hashes/eight
function locators; active/unused EOP metadata and all original/reference hashes;
21-row status/source/version/closure consistency; local documentation links;
JSON parsing and Prettier formatting; privacy and whitespace review; complete
two-file diff/status and preservation review. Public documentation acquisition
had four successful responses and two recorded failures (Astropy rendered page
404, C04 description 503); failures were not counted as sources read. No new
scientific input was downloaded.

Before/after inventories verified all four worktrees' existing files/branch/HEAD,
186 entries in prior private evidence manifests, the original 72 private files,
and the older 178-file research inventory. Both original XMLs/captures match and
the compressed/expanded SP3 hashes match. The existing database remains schema 3,
two snapshots, SHA-256
`ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
It was inspected read-only. Prior reports, original G30/G05 protocols, policy
definition and activation record are unchanged. New public-document receipts and
source audit are in the Git-ignored local evidence area, with a 13-entry manifest;
raw scientific inputs are not in these deliverables or routine CI artifacts.
Local preservation is not independent backup/recovery verification.

**No real-input initialization/propagation, spacecraft transformation, orbital
interpolation/extrapolation, residual calculation, new uncertainty calculation,
record selection, scientific authorization, private-account access, publication
or deployment occurred.** Phase 11.3.1 remains PARTIAL with evaluation BLOCKED;
E4 production readiness remains OPEN. The NASA/IGS study remains **BLOCKED**.
