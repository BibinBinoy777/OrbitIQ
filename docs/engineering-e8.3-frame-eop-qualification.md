# E8.3 — Frame, time and Earth-orientation qualification

Study **ORBITIQ-IGS-GPS-RETRO-001**, 24 October 2026.
**Overall scientific status: BLOCKED.** This is a specification and evidence
audit, not real-input propagation, a spacecraft transformation or a residual run.
The historical GP XML has not arrived; no eligible record or pair is established.
The retained reference is `IGS0OPSFIN_20240010000_01D_15M_ORB.SP3.gz`.
The intended target remains GPS G30 / SVN G064 / NORAD 39533 / COSPAR 2014-008A;
that is not a claim that the missing GP identity has been qualified.

## Scope, sources and authority

Work remains in `/workspace/OrbitIQ-e82`, branch
`engineering-e8.2-igs-reference-qualification`, HEAD
`b0a03205e3930b55651232d8b7ffbc9e879ae8c6`. The existing E8.2 additions are preserved.
Only this report and the [E8.3 evidence ledger](engineering-e8.3-frame-eop-evidence.json)
are added. The ledger contains 13 qualification requirements, exact installed
source hashes/function locators, resource identities and public-document receipts.

This extends, rather than duplicates or rewrites, the
[E8.2 assessment](engineering-e8.2-reference-qualification.md), its
[ledger](engineering-e8.2-reference-evidence.json), the
[E8 feasibility report](engineering-e8-feasibility-report.md) and the unchanged
[proposed protocol v0.1](engineering-e8-comparison-protocol.md). Reference-point,
quality-statistic and source-dependency limitations from E8.2 remain in force.

Evidence is labelled **D — directly verified**, **P — authoritative documentation**,
**I — inference**, or **U — unknown**. Installed source establishes what this build
does; it does not by itself establish physical correctness for this comparison.

| Source                                                                                                                                             | Exact scope and authority                                                                                                                                |
| -------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [IERS Conventions (2010), Technical Note 36](https://www.iers.org/fileadmin/SharedDocs/Publikationen/EN/IERS/Publications/tn/TechnNote36/tn36.pdf) | Published official text; Chapter 4, §§5.5.1 and 5.5.3, Chapter 8. Newly acquired from the publisher's current link, not the failing legacy URLs.         |
| [Current official IERS conventions page](https://www.iers.org/iers/en/dataproducts/conventions/conventions)                                        | Identifies the published conventions and says the later working version is not definitive or officially approved.                                        |
| [USNO/IERS Rapid Service finals2000A format](https://maia.usno.navy.mil/ser7/readme.finals2000A)                                                   | Defines UTC-MJD, UT1-UTC seconds, polar motion arcseconds, A/B columns and I/P flags. It is format documentation, not a full product-processing history. |
| Installed Astropy **7.2.3** source/docstrings                                                                                                      | Exact TEME/ITRS implementation, IERS merge/interpolation, TimeGPS and finite-difference behavior; hash-pinned in the ledger.                             |
| Installed PyERFA **2.0.1.5**, ERFA **2.0.1**, SOFA **20231011**                                                                                    | `gmst82`, `pom00` and `c2tcio` interfaces and implementation identity.                                                                                   |
| Installed `sgp4` **2.27** plus unchanged OrbitIQ source                                                                                            | OMM field extraction, WGS72 initialization and the existing nominal-UTC/TEME output contract.                                                            |
| Retained E8/E8.2 product, time, frame and IGS-source evidence                                                                                      | Actual SP3 metadata/hashes; existing conversion/preflight; correct IGSMAIL-8238 and published CoM evidence. No product redownload.                       |

**D/P:** the published TN36 PDF is 2,926,081 bytes, SHA-256
`b0570ff245a6d76977dc56918c64130cc5bf68b679fa8fffb989137f2b833eea`.
Its successful acquisition does not rewrite earlier failed retrieval evidence.
The legacy publisher/Gazette URLs returned 404, the Conventions Center chapter
URLs returned 503, and the exact online Astropy **v7.2.3** satellite page returned 403. Those responses were not treated as documentation read. No other Astropy
documentation version was silently substituted: this audit uses the installed
7.2.3 source and its installed docstrings. Prior Phase 3 analysis is historical
evidence, not a claim that its web sources were freshly retrieved here.

**P/U:** TN36 is the published **2010** baseline, not proof of every convention
actually used by the 2024 combination. The later working chapter was unavailable
and was not read or promoted over the published text. No current working-routine
coefficients or implementation versions are asserted from a routine name alone.

## Actual GP/SGP4 convention and the missing input

**D:** `Elements` accepts Earth-centered, TEME, UTC, SGP4, ephemeris-type-zero
inputs, with finite bounded numeric fields. Its defaults for omitted invariant
fields are the existing **CelesTrak GP JSON** convention; defaults do not establish
metadata in a missing XML file. The separately preserved E8.1.1 XML inspector
requires explicit declarations and checks source timestamp precision before model
validation. Its uncommitted source was inspected and hashed without modification
or incorporation into this branch.

The locked `sgp4.omm.parse_xml` extracts OMM fields; it is not a historical-source
authenticator or a complete scientific qualifier. `Elements.satellite()` formats
the validated UTC epoch to microseconds and passes WGS72 to `omm.initialize`.
The locked initializer selects improved operation mode `i`. No initialization
of a real input was performed in E8.3.
The installed API selects accelerated `sgp4.wrapper.Satrec`, a subclass of
`sgp4.vallado_cpp.Satrec`; this was identified without constructing a satellite.
NumPy **2.5.4**, the wrapper/compiled binding identities and the unchanged uv-lock
hash are also recorded in the ledger.

**D:** the current engine evaluates a two-part Julian date formed from an aware
UTC calendar timestamp. Its output contract is **geocentric TEME**, position
**km**, velocity **km/s**, calculated rather than observed. It uses the existing
nominal UTC-day/86,400-second convention and an inclusive seven-day guard. The
`UTC` label does not make the SGP4 argument UT1 or TAI, or validate propagation
across a leap second. The Earth-fixed path separately rejects unsupported
epoch-to-target leap crossings; the TEME engine was not rewritten here.

**D/P:** the installed Astropy TEME docstring defines **True Equator Mean Equinox**
and explicitly follows Vallado et al. (2006), noting that TEME implementations
differ. This is not a generic J2000/GCRS state or Earth-fixed XYZ. The fact that
an OMM uses mean elements is separate from the name of the TEME reference frame.

**U:** actual historical OMM declarations, identity, epoch, publication/availability,
fit lineage and model eligibility remain unverified. A library interface and
synthetic fixtures cannot substitute for the original record.

## Specified frame chain — not validated for real comparison

The future chain, conditional on qualified inputs and separate authorization, is:

1. Preserve original OMM fields and exact epoch; validate the supported model.
2. Evaluate the existing SGP4/WGS72 model at each approved common UTC instant,
   obtaining geocentric TEME km/km/s. This operation is **not performed here**.
3. Use the installed same-instant TEME→ITRS path with the qualified local
   Earth-orientation convention and resources.
4. Establish the relationship of those computed terrestrial coordinates to
   ITRF2020/IGS20, including axes, origin, scale, time evolution and model choices.
5. Establish a common spacecraft physical point before any subtraction.

**D:** Astropy 7.2.3 `teme_to_itrs_mat` performs the following calls. This is a
description of inspected code, not a new transform implementation or execution:

```text
gst = erfa.gmst82(*get_jd12(time, "ut1"))
xp, yp = get_polar_motion(time)
pmmat = erfa.pom00(xp, yp, 0)
matrix = erfa.c2tcio(identity_matrix, gst, pmmat)
```

The first step uses **IAU 1982 GMST in UT1**, deliberately for Vallado consistency.
The third argument to `pom00` is **zero TIO locator s′**, not `sp00(...)`.
The identity first argument to `c2tcio` is this branch's documented TEME adaptation;
it does not assert that TEME is GCRS/CIRS or execute a full IAU 2006/2000A chain.
Use the library's rotation/sign conventions, not an independently invented active
rotation. `teme_to_itrs` constructs ITRS at source obstime and then the requested
target frame; OrbitIQ supplies the same obstime and a geocentric location.

OrbitIQ attaches velocity. Astropy uses a symmetric **one-second** finite
difference for differential/frame-motion handling, hence existing EOP preflight
at target and **±0.5 seconds**. SP3 is P-only; this implementation detail is not
permission to invent reference velocities or velocity residuals.

**P:** TN36 Chapter 4 distinguishes an ideal reference system from a realized
frame: an ITRF realizes ITRS origin, axes, scale and their time evolution. The
geocenter concerns the whole Earth, including oceans and atmosphere. It is not
the center of mass of the satellite. TN36's then-current ITRF examples do not
replace the later IGS20 evidence.

**D/P:** the actual SP3 declares **IGS20**. The retained correct IGSMAIL-8238 states
that named ITRF2020 and IGS20 datums have zero underlying transformation parameters,
while station-specific antenna-related coordinate offsets are separate. Astropy's
installed ITRS frame has `obstime` and `location`, not an ITRF-release selector.

**I/U:** no additional nonzero datum transformation is justified by current
evidence. A justified identity alignment may be appropriate if the actual computed
conventions are established; an ITRS class name alone does not establish it.
Do not apply station offsets to satellite states, add full precession/nutation
to this TEME shortcut, substitute ERA for GMST82 without a complete derivation,
or add a TIO term merely because a different branch uses it. The selected sequence
is reproducibly specified; its sufficiency for this IGS comparison is not validated.

## Earth-orientation resource and safety policy

**D:** normal operation explicitly loads `IERS_A.open(finals2000A.all)` and
`Leap_Second.dat` from locked `astropy-iers-data 0.2026.10.12.1.3.27`. It does not
select IERS-Auto. The default is `ORBITIQ_EOP_POLICY=measured_or_predicted`;
`measured_only` is available. This describes source/configuration policy, not
an assertion about deployed service configuration. Parsed resources are cached;
updates require the existing controlled resource/environment procedure.

| Resource evidence               | Actual result                                                                                           |
| ------------------------------- | ------------------------------------------------------------------------------------------------------- |
| EOP SHA-256                     | `9fbc14ae5e71de96cc1e6b43b54a547acc80c7a6ce910c0209ad6230ff3d30cd`                                      |
| Leap-file SHA-256               | `6cb6f5d4b819f2e568e25db4b0b26d89dedf031fdffb18bc94d40f4e94e268d7`                                      |
| Raw EOP coverage                | MJD **41684–61682**; first predictive MJD **61315**                                                     |
| Leap expiry                     | **2027-06-28**; target/support-time checks are a separate bound from raw EOP coverage                   |
| Newly inspected bracketing rows | MJD **60309, 60310, 60311**: merged UT1, polar-motion and nutation flags all **B**                      |
| Reused E8 preflight             | All 96 reference instants and velocity support covered; 192 central UT1/polar-motion flags IERS-B-final |

**D/P:** the installed `IERS_A` merger prefers finite Bulletin-B values and uses
A rapid/predicted values otherwise. The provider readme gives UTC-MJD, UT1-UTC in
seconds and polar motion in arcseconds. The historical rows are not predictions;
the mere class name `IERS_A` does not make every value rapid or predictive.
The NutFlag/dX/dY columns are separate from terrestrial polar motion; the selected
TEME branch does not consume those celestial-pole-offset fields.

**D:** `_interpolate` linearly interpolates bracketing values in UTC-MJD. For UT1
it removes the rounded integer jump from the adjacent UT1-UTC difference to handle
a leap discontinuity. That internal difference operation is not silent rounding
of an input timestamp. The base IERS table has no automatic refresh. This is EOP
parameter interpolation, distinct from prohibited orbital-state interpolation.

**D:** raw Astropy helpers can otherwise warn and use mean polar motion or an
assumed zero UT1-UTC out of range. OrbitIQ's preflight rejects out-of-range,
nonfinite or unknown-status values before the transform, and treats Astropy/ERFA
warnings as errors. It disables downloads and remote leap URLs, selects explicit
local data and requires degraded accuracy to error. No such fallback is approved.

Prediction support is rejected in `measured_only`. Under the default policy it
is labelled and rejected when current/replay evaluation MJD minus the table's
first predictive MJD exceeds 30 days. Historical final values do not become
predictions because the package also contains a predictive region. Missing or
invalid local resources fail explicitly; neither network loss nor a coverage
failure authorizes a replacement table, clamped time or zero EOP.

The RLock/configuration scopes protect process-global Astropy state for cooperating
application users. Replay additionally saves/restores ERFA leap state; regular
operation initializes it from the selected local leap file. This audit does not
claim that arbitrary code bypassing these scopes has the same safety behavior.

## Subdaily models: what is established and what is not

**P:** the published TN36 is explicit, rather than merely a list of possible
corrections. §§5.5.1.1–5.5.1.3 (printed pp.50–51) state that subdaily ocean-tide
and specified diurnal libration polar-motion contributions are added after
interpolating the reported IERS series; long-period and secular polar-motion
libration are already in the observed values. §§5.5.3.1–5.5.3.3 describe UT1/LOD
ocean-tide and semidiurnal libration additions. Chapter 8 §8.2 contains the ocean
tide treatment; **Tables** 8.2a/b and 8.3a/b are not the same as **sections** 8.2/8.3.

| Component                                   | Published baseline                                                                        | Installed path / unresolved treatment                                                                                                   |
| ------------------------------------------- | ----------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| Diurnal/semidiurnal ocean-tide polar motion | TN36 §§5.5.1.1–5.5.1.2; §8.2, Tables 8.2a/b                                               | **D:** no explicit addition identified. **U:** reconcile with the actual IGS processing/model inventory.                                |
| Diurnal polar-motion libration              | TN36 §5.5.1.3, Table 5.1a; `PMSDNUT2` described                                           | **D:** no separate addition identified. A current routine's exact contents/version were not acquired merely by reading its name.        |
| Diurnal/semidiurnal ocean-tide UT1          | TN36 §5.5.3.1; §8.2, Tables 8.3a/b                                                        | **D:** no explicit addition identified; the transform consumes UT1, not LOD directly.                                                   |
| Semidiurnal UT1 libration                   | TN36 §5.5.3.3, Table 5.1b; `UTLIBR` described                                             | **D:** no separate addition identified. No numerical effect is calculated here.                                                         |
| Long-period/secular polar-motion libration  | TN36 §5.5.1.1: already in observed polar motion                                           | Do not add these again. Absence of a separate routine is not evidence that the reported series lacks them.                              |
| Zonal tides / UT1R / UT1S                   | TN36 §8.1 recommends unambiguous UT1/LOD exchange and explicit research model definitions | **D:** no remove/restore step identified. Do not append a full zonal series to ordinary observed UT1 just because no routine is called. |
| Celestial-pole dX/dY; TIO s′                | Separate model quantities, not replacements for xp/yp/UT1 high-frequency treatment        | **D:** dX/dY unused in this branch; s′ deliberately zero. Do not mix branches or use either as a substitute for an EOP component audit. |

**D:** the inspected application, IERS interpolator and selected ERFA call chain
contain no explicit `INTERP`, `ORTHO_EOP`, `PMSDNUT2`, `UTLIBR` or equivalent
subdaily model addition. The linear lookup and rotation calls do not reconstruct
those terms automatically.

**I:** standard IERS series semantics plus that implementation identify an
unresolved difference from a complete published subdaily treatment. **U:** this
does not establish the actual 2024 IGS combination's complete ERP, tide,
regularization or later-model chain, or the numerical impact in this comparison.
The combination summary's “directly in ITRF, without Bulletin-B alignment” does
not make an IERS-B coverage flag proof of matching IGS ERP.

No correction is added here. A future proposal must inventory **physical
components**, source series, routine contents/versions, units, arguments and
remove/restore steps. Adding both an interpolator that includes ocean terms and
another ocean routine could count a component twice; re-adding long-period
observed terms also could. Conversely, equal tidal frequencies do not prove two
different physical contributions are duplicates. The exact routine/model chain,
not function names or a general “tidal correction” label, must resolve this.

## Time chain and epoch contract

**D, reused:** the retained SP3 declares **GPS**, with 96 original 15-minute tags
from GPS-calendar `2024-01-01T00:00:00.00000000` to
`2024-01-01T23:45:00.00000000`. Existing resource-backed conversion gives UTC
**2023-12-31T23:59:42.000000Z** to **2024-01-01T23:44:42.000000Z**. E8.3 does not
repeat that conversion, add samples, shift clock corrections or relabel the GPS
calendar as UTC. The reference's IGST clock convention is not its epoch scale.

**D:** the existing converter preserves Decimal whole/fractional GPS seconds and
passes a split value to Astropy `Time(..., format="gps", scale="tai")`, then UTC.
Installed TimeGPS anchors zero at **1980-01-06 00:00:19 TAI**, corresponding to the
GPS origin; it does not mean GPS calendar fields are TAI. Historical UTC offsets
come from the selected leap table. No fixed GPS→UTC offset is used.

The specified, unexecuted common-instant chain is:

```text
original SP3 GPS tag -> exact GPS elapsed seconds -> pinned-leap UTC instant t
original OMM UTC epoch -> static/model/provenance and fixed-window qualification
t -> existing nominal-UTC SGP4 evaluation -> TEME state
same t -> UTC/UT1 EOP lookup -> reviewed terrestrial/frame/point treatment
original SP3 sample at t -> future authorized comparison only
```

Timestamp conversion alone does not evaluate SGP4 or create an orbital state.
The GP epoch need not equal an SP3 epoch; connecting them would require future
separately authorized propagation, not interpolation of mean elements or SP3 XYZ.

**D/U:** the contract retains original timestamp text and source indices, accepts
only supported exact instants and rejects nonzero submicrosecond content before
the model view. Additional zero fractional digits do not change the instant.
GPS second-60 encodings, UTC leap-second labels that Python datetime cannot
represent, and unsupported epoch-to-target leap crossings are refused. Source-
appropriate timezone-free CelesTrak UTC treatment is explicit, not local time.
The generic `Elements` datetime field alone is not the precision gate: future
historical input must pass the exact intake checks before use.

The fixed GP-epoch interval remains
**[2023-12-25T23:44:42Z, 2023-12-31T23:59:42Z], inclusive**. No nearest-epoch
selection, nonzero-digit rounding, new time anchor, record switching, orbital
interpolation/extrapolation or altered mask is proposed. Actual GP metadata,
selection, leap compatibility and source receipt/publication claims await the file.

## Qualification matrix and next evidence

The machine-readable ledger records each requirement, source/version/category,
status, outstanding question and evidence needed to resolve it. Its summary is:

| Requirement                         | Status      | Remaining boundary                                                                                                            |
| ----------------------------------- | ----------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Actual GP frame/time metadata       | **BLOCKED** | Original XML and provenance absent; defaults cannot establish it.                                                             |
| SGP4 output convention              | **PARTIAL** | Implemented convention identified; accepted-record/model and claims review outstanding.                                       |
| IGS frame/realization               | **PARTIAL** | Header and named datum relation established; computed-frame compatibility is not.                                             |
| ITRS/ITRF relationship              | **PARTIAL** | System/realization distinction documented; actual datum linkage needs independent evidence.                                   |
| TEME→terrestrial sequence           | **PARTIAL** | Exact installed sequence specified; product/model sufficiency not validated.                                                  |
| UT1 resource/coverage only          | **PASS**    | Actual pinned historical B coverage verified; not a full EOP-model pass.                                                      |
| Polar-motion resource/coverage only | **PASS**    | Actual pinned historical B coverage verified; subdaily compatibility remains separate.                                        |
| Subdaily EOP treatment              | **PARTIAL** | Published/component and implementation audit advances E8.2's NOT ASSESSED item; actual IGS/model reconciliation remains open. |
| GPS/leap conversion                 | **PARTIAL** | Reference mapping and resource identities established; actual GP compatibility missing.                                       |
| Precision/exact matching            | **PARTIAL** | Guards specified; genuine record, final indices/mask and review missing.                                                      |
| Satellite reference point           | **PARTIAL** | Published general IGS CoM convention is not proof of GP/2024-product point compatibility.                                     |
| Provenance/independence             | **BLOCKED** | No historical source record; fit lineage/availability/shared dependencies remain unestablished.                               |
| Final review/authorization          | **BLOCKED** | Complete input/resource/software manifest, quality/claims review and explicit approval required.                              |

Before GP arrival, the ERP/component inventory, applicable historical processing
documentation and independent frame-control design can advance. None is promoted
to completion merely because a relevant routine exists. No nonzero datum map,
subdaily patch, new precision tolerance or protocol change is approved here.

After arrival, inspect the original XML, receipt/source evidence, every record's
identity/model/time declarations and exact epoch. Apply the unchanged latest-
unique-eligible selection rule, retaining ambiguity/exclusions and unknown
creation/publication/availability. Then resolve pair reference point, source/fit
dependencies, leap compatibility and final manifests/review. A valid XML still
does not establish independence, historical forecasting validity or accuracy.

## Verification and preservation

Actual local results:

- The 13-item matrix passed status/category/source/version/closure-field checks.
  Both PASS rows are scoped to actual historical resource identity and coverage;
  neither is a full scientific EOP-model acceptance.
- Source/ledger checks passed against **14 pinned installed files**, **eight
  unchanged application files**, the actual historical bracketing flags, TimeGPS
  anchor and inspected rotation/interpolation/safety-policy functions. IERS
  normative and publication-authority text was cross-checked against the retained
  original captures. No rotation function or spacecraft-state routine was called
  by these checks.
- All **10 public-source response receipts** and the separate **20-file private
  preservation manifest** passed size/hash/status checks. Success and failure
  responses remain distinguished. Original raw captures are under ignored
  `data/`, not in Git or ordinary CI.
- Markdown/JSON Prettier, JSON parsing, local links, fences, whitespace and
  credential/contact-pattern checks passed. External source statuses are the
  actual capture results, not a claim that every old URL works now.
- Both original reference hashes remain unchanged: compressed
  `26f16fa5f97cce851948fa88711aed47f60ee2e4ddfe36f0e98b1076e79fbe38`, expanded
  `8a638375273ab74011aebd9ffcc480df02b5718440c8fb7c51c408ff220d231c`.
  The old **53-file E8** and **eight-file E8.2** private manifests and their files
  also remain unchanged. No IGS orbit or EOP resource was downloaded or replaced.
- The **72 original private files** and database retain the trusted baseline:
  schema **3**, **two** snapshots, database SHA-256
  `ac93a71ca7a742c5425ac06ead4b5e0cc8dd15e0cdeb868db9cdee46f820c2f9`.
  Database validation used the established read-only transaction procedure.
- The four existing worktrees retain their branches/HEADs and all pre-existing
  file contents, including the three E8.1.1 additions and the two E8.2 additions.
  Current Git status has those two preserved E8.2 files plus exactly **two new,
  unstaged/uncommitted E8.3 documentation files**. No application, test,
  dependency, scientific algorithm or protocol changed.
- No pytest suite, spacecraft reference-vector transformation audit, frontend,
  browser/PDF, build or remote CI was rerun for this documentation-only phase.
  Earlier test results remain historical evidence, not fresh E8.3 verification.

No correction was installed, no real spacecraft operation was run, and no Git
publication, private account access, authentication or deployment occurred. Local
preservation is not an independent backup. E4 remains **OPEN** and Swarm-A Phase
11.3.1 remains **PARTIAL**, with scientific evaluation **BLOCKED**.

**The overall scientific study remains BLOCKED while historical input and
essential frame/EOP/reference-point/quality/provenance/review evidence are missing.**
